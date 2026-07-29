"""Futbol kontenti va o'zbekcha matn sifati uchun markaziy nazorat."""

import re

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from ..models import Article


FOOTBALL_TERMS = re.compile(
    r"\b(?:football|soccer|futbol|uefa|fifa|transfer|goalkeeper|defender|"
    r"midfielder|striker|manager|head coach|premier league|champions league|"
    r"world cup|la liga|serie a|bundesliga|superliga|chempionlar ligasi|"
    r"jahon chempionati|terma jamoa|paxtakor|nasaf|navbahor|bunyodkor|"
    r"barselona|barcelona|real madrid|manchester|liverpool|liverpul|arsenal|"
    r"chelsea|chelsi|juventus|yuventus|bayern|psg|tottenham|hearts|wrexham|"
    r"milan|inter|roma|napoli|atletico|dortmund|"
    r"футбол|суперлига|пфл|чемпионлар лигаси|уефа|фифа|трансфер|"
    r"терма жамоа|ҳужумчи|ҳимоячи|дарвозабон|мураббий|"
    r"пахтакор|бунёдкор|насаф|навбаҳор|барселона|барса|реал|"
    r"манчестер|сити|ливерпуль|арсенал|челси|ювентус|милан|"
    r"бавария|псж|ҳусанов|абдуқодир)\b",
    re.IGNORECASE,
)

NON_FOOTBALL_TERMS = re.compile(
    r"\b(?:formula[\s-]?1|f1|grand prix|golf|tennis|cricket|darts|boxing|"
    r"snooker|rugby|basketball|nba|hockey|wta|atp|pga|solheim|wicket|"
    r"innings|driver ratings|the hundred)\b",
    re.IGNORECASE,
)

NON_FOOTBALL_URL_PARTS = (
    "/f1/",
    "/golf/",
    "/tennis/",
    "/cricket/",
    "/darts/",
    "/boxing/",
    "/snooker/",
    "/rugby-",
    "/basketball/",
    "/nba/",
    "/hockey/",
)

TEXT_REPLACEMENTS = (
    ("Liverpoool", "Liverpul"),
    ("liverpoool", "Liverpul"),
    ("Keysingi", "Keyingi"),
    ("Arsenali uchun", "Arsenal uchun"),
    ("Rencers", "Reynjers"),
    (
        "Derek MakInnes Reynjers dubligidan oldin o'tkaziladigan uchrashuvda "
        "maydonda bo'lishi kutilmoqda",
        "Derek MakInnes diskvalifikatsiyaga qaramay Reynjers o'yinida "
        "qatnashishi mumkin",
    ),
    ("muhim START", "muhim boshlanish"),
    ("Â«", "«"),
    ("Â»", "»"),
    ("Ã©", "é"),
    ("Ã¨", "è"),
    ("Ã¡", "á"),
    ("Ã³", "ó"),
    ("â€™", "’"),
    ("â€œ", "“"),
    ("â€", "”"),
    ("â€“", "–"),
    ("â€”", "—"),
)


def normalize_text(value: str | None) -> str:
    """Ko'p uchraydigan kodlash va imlo xatolarini tuzatadi."""
    text = str(value or "")
    for broken, fixed in TEXT_REPLACEMENTS:
        text = text.replace(broken, fixed)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def normalize_analysis(analysis: dict) -> dict:
    """AI javobining foydalanuvchiga ko'rinadigan barcha matnlarini tozalaydi."""
    for key in (
        "sarlavha",
        "seo_sarlavha",
        "xulosa",
        "maqola",
        "amaliy_ahamiyat",
    ):
        analysis[key] = normalize_text(analysis.get(key))
    analysis["teglar"] = [
        normalize_text(tag)
        for tag in (analysis.get("teglar") or [])
        if normalize_text(tag)
    ][:6]
    return analysis


def is_football_content(
    title: str,
    summary: str = "",
    url: str = "",
    source: str = "",
) -> bool:
    """Manba URL'i va matn bo'yicha faqat futbol xabarini qabul qiladi."""
    source_lower = source.lower()
    url_lower = url.lower()
    text = f"{title} {summary}"

    # Aralash Sky RSS tasmasida sport turi URL yo'lida aniq ko'rsatiladi.
    if "sky sports" in source_lower:
        return "/football/" in url_lower

    # Quyidagi maxsus tasmalar URL darajasida futbolga tegishli.
    if "guardian" in source_lower and "/football/" in url_lower:
        return True
    if "espn" in source_lower and "/soccer/" in url_lower:
        return True
    if "bbc" in source_lower and "/sport/football/" in url_lower:
        return True

    if NON_FOOTBALL_TERMS.search(text):
        return False
    return bool(FOOTBALL_TERMS.search(text))


def analysis_is_publishable(analysis: dict) -> tuple[bool, list[str]]:
    """AI maqolasini avtomatik nashrdan oldin minimal sifatdan o'tkazadi."""
    reasons: list[str] = []
    title = normalize_text(analysis.get("sarlavha"))
    summary = normalize_text(analysis.get("xulosa"))
    content = normalize_text(analysis.get("maqola"))

    if not 15 <= len(title) <= 180:
        reasons.append("sarlavha uzunligi noto'g'ri")
    if len(summary) < 80:
        reasons.append("xulosa juda qisqa")
    if len(content) < 250:
        reasons.append("maqola juda qisqa")
    if "\n" in title:
        reasons.append("sarlavhada yangi qator bor")

    suspicious = re.compile(
        r"(?:men bu vazifani|i cannot|as an ai|```|<html|lorem ipsum)",
        re.IGNORECASE,
    )
    if suspicious.search(f"{title} {summary} {content}"):
        reasons.append("modelning texnik yoki rad javobi aniqlandi")

    allowed_acronyms = {
        "FIFA",
        "UEFA",
        "USMNT",
        "VAR",
        "MLS",
        "PFL",
        "APL",
    }
    unexpected_acronyms = {
        word
        for word in re.findall(r"\b[A-Z]{4,}\b", f"{title} {summary} {content}")
        if word not in allowed_acronyms
    }
    if unexpected_acronyms:
        reasons.append(
            "keraksiz katta inglizcha so'z: "
            + ", ".join(sorted(unexpected_acronyms))
        )

    return not reasons, reasons


def infer_category(text: str, current: str) -> str:
    """AI kategoriyasini aniq futbol kalitlari bilan qayta tekshiradi."""
    haystack = normalize_text(text).lower()
    rules = (
        ("transferlar", r"\btransfer|o'tdi|o‘tadi|shartnoma|imzoladi|joins?|signs?\b"),
        ("premyer-liga", r"premyer|premier league|arsenal|chelsea|chelsi|liverpool|liverpul|manchester|tottenham"),
        ("la-liga", r"\bla liga\b|barselona|barcelona|real madrid|atletico"),
        ("seriya-a", r"\bserie a\b|\bseriya a\b|juventus|yuventus|inter|milan|napoli|roma"),
        ("bundesliga", r"bundesliga|bayern|dortmund|leverkusen"),
        ("chempionlar-ligasi", r"champions league|chempionlar ligasi|\buefa cl\b"),
        ("uzbekiston-futboli", r"o'zbekiston|o‘zbekiston|superliga|paxtakor|nasaf|navbahor|bunyodkor|\bpfl\b"),
        ("terma-jamoalar", r"terma jamoa|world cup|jahon chempionati|usmnt|uefa nations"),
    )
    for category, pattern in rules:
        if re.search(pattern, haystack, re.IGNORECASE):
            return category
    return current


def cleanup_existing_articles(db: Session) -> tuple[int, int]:
    """Eski noto'g'ri sport xabarlarini yashiradi va matn xatolarini tuzatadi."""
    bad_url_filters = [
        Article.original_url.contains(part)
        for part in NON_FOOTBALL_URL_PARTS
    ]
    sky_non_football = and_(
        Article.source_name.contains("Sky Sports"),
        ~Article.original_url.contains("/football/"),
    )
    rejected = (
        db.query(Article)
        .filter(
            Article.status == "published",
            or_(sky_non_football, *bad_url_filters),
        )
        .update(
            {Article.status: "rejected"},
            synchronize_session=False,
        )
    )

    corrected = 0
    for field in (
        Article.title,
        Article.seo_title,
        Article.summary,
        Article.content,
        Article.practical_note,
    ):
        for broken, fixed in TEXT_REPLACEMENTS:
            corrected += (
                db.query(Article)
                .filter(field.contains(broken))
                .update(
                    {field: func.replace(field, broken, fixed)},
                    synchronize_session=False,
                )
            )

    db.commit()
    return rejected, corrected
