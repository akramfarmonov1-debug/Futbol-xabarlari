"""AI Agent quvuri: yig'ish -> dublikat filtri -> tahlil -> saqlash.

AUTO_PUBLISH=true (standart) bo'lsa maqolalar darhol saytga chiqadi va
muhimlari (AUTO_TELEGRAM_MIN_IMPORTANCE dan yuqori) Telegram kanalga
avtomatik yuboriladi. AUTO_PUBLISH=false bo'lsa eski rejim: maqolalar
pending holatda admin tasdig'ini kutadi.

Ishga tushirish:  python -m app.pipeline
Muntazam ishlashi uchun cron'ga qo'ying, masalan har soatda:
  0 * * * * cd /path/backend && .venv/bin/python -m app.pipeline
"""

from datetime import datetime

from .config import (
    AUTO_PUBLISH,
    AUTO_PUBLISH_MIN_IMPORTANCE,
    AUTO_TELEGRAM,
    AUTO_TELEGRAM_MIN_IMPORTANCE,
    IMAGE_GENERATION,
    TELEGRAM_BOT_TOKEN,
)
from .database import Base, SessionLocal, engine
from .models import Article, ArticleQuality, Category
from .seed import seed_categories
from .services.ai_agent import analyze_news
from .services.collector import (
    collect_news,
    improve_image_url,
    upgrade_existing_images,
)
from .services.content_quality import (
    analysis_is_publishable,
    cleanup_existing_articles,
    infer_category,
    is_football_content,
)
from .services.image_gen import generate_image
from .services.ingestion_log import record_ingestion_decision
from .services.event_dedup import (
    attach_article_source,
    find_duplicate_article,
)
from .services.runtime_lock import (
    PIPELINE_LOCK_ID,
    release_runtime_lock,
    try_runtime_lock,
)
from .services.telegram import send_to_channel
from .utils import slugify


def run_pipeline(per_feed: int = 5) -> int:
    runtime_lock = try_runtime_lock(PIPELINE_LOCK_ID)
    if not runtime_lock.acquired:
        print("⏭ Pipeline boshqa instance'da ishlayapti; bu ishga tushirish o'tkazib yuborildi.")
        return 0

    try:
        return _run_pipeline(per_feed)
    finally:
        release_runtime_lock(runtime_lock)


def _run_pipeline(per_feed: int = 5) -> int:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    saved = 0
    try:
        seed_categories(db)
        categories = {c.slug: c for c in db.query(Category).all()}

        rejected, corrected = cleanup_existing_articles(db)
        if rejected or corrected:
            print(
                f"🧹 Kontent tozalandi: {rejected} ta futbolga aloqasiz "
                f"xabar yashirildi, {corrected} ta matn xatosi tuzatildi."
            )

        upgraded = upgrade_existing_images(db)
        if upgraded:
            print(f"🖼 {upgraded} ta eski rasm yuqori sifatli variantga yangilandi.")

        print("📡 Yangiliklar yig'ilmoqda...")
        fresh = collect_news(db, per_feed=per_feed)
        print(f"   {len(fresh)} ta yangi yangilik topildi.")

        for i, news in enumerate(fresh, 1):
            print(f"🤖 [{i}/{len(fresh)}] {news['title'][:65]}")
            if not is_football_content(
                news["title"],
                news["content"],
                news["url"],
                news["source"],
            ):
                record_ingestion_decision(
                    db,
                    original_url=news["url"],
                    original_title=news["title"],
                    source_name=news["source"],
                    decision="non_football",
                    reasons=["Pipeline futbol filtri rad etdi"],
                )
                print("   ✗ Futbolga aloqasiz xabar o'tkazib yuborildi")
                continue

            duplicate, duplicate_match = find_duplicate_article(
                db,
                news["title"],
                news["content"],
                news["published_at"],
            )
            if duplicate:
                attach_article_source(
                    db,
                    duplicate,
                    original_url=news["url"],
                    original_title=news["title"],
                    source_name=news["source"],
                    source_published_at=news["published_at"],
                )
                record_ingestion_decision(
                    db,
                    original_url=news["url"],
                    original_title=news["title"],
                    source_name=news["source"],
                    decision="duplicate_event",
                    reasons=list(duplicate_match.reasons),
                    matched_article_id=duplicate.id,
                )
                print(
                    f"   ↪ Dublikat voqea: {duplicate.slug} "
                    f"(score={duplicate_match.score})"
                )
                continue
            try:
                analysis = analyze_news(
                    title=news["title"],
                    content=news["content"],
                    url=news["url"],
                    source=news["source"],
                )
            except Exception as error:
                record_ingestion_decision(
                    db,
                    original_url=news["url"],
                    original_title=news["title"],
                    source_name=news["source"],
                    decision="ai_error",
                    reasons=[str(error)[:500]],
                )
                print(f"   ✗ Tahlil xatosi: {error}")
                continue

            ai_category = analysis["kategoriya"]
            analysis["kategoriya"] = infer_category(
                " ".join(
                    [
                        news["title"],
                        news["content"],
                        analysis["sarlavha"],
                        analysis["xulosa"],
                    ]
                ),
                analysis["kategoriya"],
            )
            if analysis["kategoriya"] != ai_category:
                analysis["category_confidence"] = min(
                    analysis.get("category_confidence", 0),
                    70,
                )

            publishable, quality_reasons = analysis_is_publishable(
                analysis,
                source_text=f"{news['title']} {news['content']}",
                require_structured=True,
            )
            if analysis["kategoriya"] != ai_category:
                quality_reasons.append(
                    f"kategoriya validator tomonidan o'zgartirildi: "
                    f"{ai_category} -> {analysis['kategoriya']}"
                )
                publishable = False
            if not publishable:
                print(
                    "   ⚠ Qo'lda tekshiruvga yuborildi: "
                    + ", ".join(quality_reasons)
                )

            # Tarjima qilingan sarlavha va entitylar raw RSS bosqichida
            # ko'rinmagan dublikat voqeani aniqlashga yordam beradi.
            duplicate, duplicate_match = find_duplicate_article(
                db,
                f"{news['title']} {analysis['sarlavha']}",
                f"{news['content']} {analysis['xulosa']}",
                news["published_at"],
            )
            if duplicate:
                attach_article_source(
                    db,
                    duplicate,
                    original_url=news["url"],
                    original_title=news["title"],
                    source_name=news["source"],
                    source_published_at=news["published_at"],
                )
                record_ingestion_decision(
                    db,
                    original_url=news["url"],
                    original_title=news["title"],
                    source_name=news["source"],
                    decision="duplicate_event",
                    reasons=list(duplicate_match.reasons),
                    matched_article_id=duplicate.id,
                )
                print(
                    f"   ↪ AI tahlilidan keyin dublikat: {duplicate.slug} "
                    f"(score={duplicate_match.score})"
                )
                continue

            slug = slugify(analysis["sarlavha"])
            if db.query(Article).filter(Article.slug == slug).first():
                slug = f"{slug}-{saved + 1}"

            auto_publish = (
                publishable
                and AUTO_PUBLISH
                and analysis["ahamiyati"] >= AUTO_PUBLISH_MIN_IMPORTANCE
            )

            # Rasm zanjiri: yuqori sifatli RSS/og:image -> (ixtiyoriy) Gemini
            image_url = improve_image_url(
                news["image_url"],
                news["url"],
                news["source"],
            )
            if not image_url and IMAGE_GENERATION:
                image_url = generate_image(analysis["sarlavha"], slug)
                if image_url:
                    print("   ✓ Rasm generatsiya qilindi")

            article = Article(
                title=analysis["sarlavha"],
                seo_title=analysis["seo_sarlavha"],
                slug=slug,
                summary=analysis["xulosa"],
                content=analysis["maqola"],
                practical_note=analysis["amaliy_ahamiyat"],
                tags=analysis["teglar"],
                importance=analysis["ahamiyati"],
                original_title=news["title"],
                original_url=news["url"],
                source_name=news["source"],
                image_url=image_url,
                category_id=categories.get(analysis["kategoriya"], None) and categories[analysis["kategoriya"]].id,
                source_published_at=news["published_at"],
                status="published" if auto_publish else "pending",
                published_at=datetime.utcnow() if auto_publish else None,
            )
            db.add(article)
            db.commit()
            db.refresh(article)
            article_quality = ArticleQuality(
                article_id=article.id,
                football_confidence=analysis.get("football_confidence", 0),
                category_confidence=analysis.get("category_confidence", 0),
                fact_confidence=analysis.get("fact_confidence", 0),
                event_key=analysis.get("event_key", ""),
                entities=analysis.get("entities", []),
                facts=analysis.get("facts", []),
                decision="ready" if publishable else "needs_review",
                reasons=quality_reasons,
            )
            db.add(article_quality)
            db.commit()
            attach_article_source(
                db,
                article,
                original_url=news["url"],
                original_title=news["title"],
                source_name=news["source"],
                source_published_at=news["published_at"],
            )
            record_ingestion_decision(
                db,
                original_url=news["url"],
                original_title=news["title"],
                source_name=news["source"],
                decision="ready" if publishable else "needs_review",
                reasons=quality_reasons,
                matched_article_id=article.id,
            )
            saved += 1

            if auto_publish:
                print("   ✓ Saytga chiqarildi")

            # Muhim yangiliklarni Telegram kanalga avtomatik yuborish
            if (
                auto_publish
                and AUTO_TELEGRAM
                and TELEGRAM_BOT_TOKEN
                and analysis["ahamiyati"] >= AUTO_TELEGRAM_MIN_IMPORTANCE
            ):
                try:
                    send_to_channel(article)
                    article.sent_to_telegram = True
                    db.commit()
                    print("   ✓ Telegram kanalga yuborildi")
                except Exception as error:
                    print(f"   ✗ Telegram xatosi: {error}")

        mode = "saytga chiqarildi (avto)" if AUTO_PUBLISH else "pending — admin tasdig'ini kutmoqda"
        print(f"\n✅ {saved} ta maqola saqlandi ({mode}).")
        return saved
    finally:
        db.close()


if __name__ == "__main__":
    run_pipeline()
