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
from .models import Article, Category
from .seed import seed_categories
from .services.ai_agent import analyze_news
from .services.collector import collect_news, fetch_og_image
from .services.image_gen import generate_image
from .services.telegram import send_to_channel
from .utils import slugify


def run_pipeline(per_feed: int = 5) -> int:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    saved = 0
    try:
        seed_categories(db)
        categories = {c.slug: c for c in db.query(Category).all()}

        print("📡 Yangiliklar yig'ilmoqda...")
        fresh = collect_news(db, per_feed=per_feed)
        print(f"   {len(fresh)} ta yangi yangilik topildi.")

        for i, news in enumerate(fresh, 1):
            print(f"🤖 [{i}/{len(fresh)}] {news['title'][:65]}")
            try:
                analysis = analyze_news(
                    title=news["title"],
                    content=news["content"],
                    url=news["url"],
                    source=news["source"],
                )
            except Exception as error:
                print(f"   ✗ Tahlil xatosi: {error}")
                continue

            slug = slugify(analysis["sarlavha"])
            if db.query(Article).filter(Article.slug == slug).first():
                slug = f"{slug}-{saved + 1}"

            auto_publish = AUTO_PUBLISH and analysis["ahamiyati"] >= AUTO_PUBLISH_MIN_IMPORTANCE

            # Rasm zanjiri: RSS -> maqola sahifasidan og:image -> (ixtiyoriy) Gemini
            image_url = news["image_url"] or fetch_og_image(news["url"])
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
