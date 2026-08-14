"""Futbol kontenti va o'zbekcha matn sifati uchun markaziy nazorat."""

import re
from collections import Counter
from urllib.parse import urlparse

from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from ..models import Article
from ..config import (
    AUTO_PUBLISH_MIN_CATEGORY_CONFIDENCE,
    AUTO_PUBLISH_MIN_FACT_CONFIDENCE,
    AUTO_PUBLISH_MIN_FOOTBALL_CONFIDENCE,
    AUTO_PUBLISH_MIN_IMPORTANCE,
    AUTO_PUBLISH_TRUSTED_SOURCES,
    MIN_CATEGORY_CONFIDENCE,
    MIN_FACT_CONFIDENCE,
    MIN_FOOTBALL_CONFIDENCE,
)
from .names_glossary import canonicalize_names


FOOTBALL_TERMS = re.compile(
    r"\b(?:football|soccer|futbol|uefa|fifa|transfer|goalkeeper|defender|"
    r"midfielder|striker|manager|head coach|premier league|champions league|"
    r"world cup|la liga|serie a|bundesliga|superliga|chempionlar ligasi|"
    r"jahon chempionati|terma jamoa|paxtakor|nasaf|navbahor|bunyodkor|"
    r"barselona|barcelona|real madrid|manchester|liverpool|liverpul|arsenal|"
    r"chelsea|chelsi|juventus|yuventus|bayern|psg|tottenham|hearts|wrexham|"
    r"milan|inter|roma|napoli|atletico|dortmund|st mirren|st johnstone|"
    r"partick thistle|livingston|al[-\s]?ahli|ал[-\s–—]?аҳли|"
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
    "/racing/",
    "/netball/",
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
    ("â€ ", "”"),
    ("â€“", "–"),
    ("â€”", "—"),
)


def normalize_text(value: str | None) -> str:
    """Ko'p uchraydigan kodlash, imlo va nom (transliteratsiya) xatolarini tuzatadi."""
    text = str(value or "")
    for broken, fixed in TEXT_REPLACEMENTS:
        text = text.replace(broken, fixed)
    text = canonicalize_names(text)
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
    analysis["entities"] = [
        normalize_text(entity)
        for entity in (analysis.get("entities") or [])
        if normalize_text(entity)
    ][:12]
    normalized_facts = []
    for fact in analysis.get("facts") or []:
        if not isinstance(fact, dict):
            continue
        normalized_facts.append(
            {
                key: normalize_text(fact.get(key))
                for key in ("subject", "predicate", "value", "evidence")
            }
        )
    analysis["facts"] = normalized_facts[:12]
    analysis["event_key"] = normalize_text(analysis.get("event_key")).lower()[:300]
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

    # Sky RSS tasmasida oddiy xabarlar sport turini URL yo'lida ko'rsatadi,
    # ammo futbol videolari ham /watch/video/... ko'rinishida kelishi mumkin.
    if "sky sports" in source_lower:
        if "/football/" in url_lower:
            return True
        if NON_FOOTBALL_TERMS.search(text):
            return False
        if any(part in url_lower for part in NON_FOOTBALL_URL_PARTS):
            return False
        return bool(FOOTBALL_TERMS.search(text))

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


def _evidence_text(value: str) -> str:
    return re.sub(r"[^a-z0-9а-яёўқғҳ]+", " ", str(value or "").lower()).strip()


def _is_evidence_supported(evidence_str: str, normalized_source: str) -> bool:
    """Fakt dalili manba matnida borligini tekshiradi."""
    evidence = _evidence_text(evidence_str)
    if len(evidence) < 8:
        return False
    if evidence in normalized_source:
        return True
    evidence_tokens = [w for w in re.findall(r"[a-z0-9а-яёўқғҳ]+", evidence) if len(w) >= 3]
    if not evidence_tokens:
        return False
    source_tokens = set(re.findall(r"[a-z0-9а-яёўқғҳ]+", normalized_source))
    matching = sum(1 for token in evidence_tokens if token in source_tokens)
    return (matching / len(evidence_tokens)) >= 0.65


# O'zbekcha tahrir qoidalari — NEXT_TASKS #2 bo'yicha.
# Sarlavha uchun qat'iy uzunlik chegarasi (maqsad: 70-90 belgi).
MAX_TITLE_LENGTH = 110
REPETITION_MIN = 6
REPETITION_RATIO = 0.15

# Takrorlanishi tabiiy bo'lgan nomlar va so'zlar — hisobga olinmaydi.
_COMMON_NAMES = {
    "chelsi", "liverpul", "barselona", "bavariya", "juventus", "yuventus",
    "manchester", "futbolchi", "jamoasi", "jamoa", "klub", "murabbiy",
    "o'yin", "o'yinga", "mavsum", "shartnoma", "natija",
}


def _repetition_issue(text: str) -> list[str]:
    """Bitta so'z g'ayritabiiy ko'p takrorlangan bo'lsa sabablarni qaytaradi."""
    words = [
        word
        for word in re.findall(r"[A-Za-zÀ-žʻʼ']{4,}", str(text or "").lower())
        if word not in _COMMON_NAMES
    ]
    total = len(words)
    if total < 40:
        return []
    counter = Counter(words)
    return [
        f"'{word}' haddan tashqari ko'p takrorlangan ({count} marta)"
        for word, count in counter.most_common(6)
        if count >= REPETITION_MIN and count / total >= REPETITION_RATIO
    ]


def analysis_is_publishable(
    analysis: dict,
    source_text: str = "",
    require_structured: bool = False,
) -> tuple[bool, list[str]]:
    """AI maqolasini avtomatik nashrdan oldin minimal sifatdan o'tkazadi."""
    reasons: list[str] = []
    title = normalize_text(analysis.get("sarlavha"))
    summary = normalize_text(analysis.get("xulosa"))
    content = normalize_text(analysis.get("maqola"))

    if not 15 <= len(title) <= MAX_TITLE_LENGTH:
        reasons.append(
            f"sarlavha uzunligi noto'g'ri (15-{MAX_TITLE_LENGTH} belgi bo'lishi kerak)"
        )
    if len(summary) < 80:
        reasons.append("xulosa juda qisqa")
    if len(content) < 250:
        reasons.append("maqola juda qisqa")
    if "\n" in title:
        reasons.append("sarlavhada yangi qator bor")

    # O'zbekcha tahrir: g'ayritabiiy takrorlanishni aniqlash.
    reasons.extend(_repetition_issue(content))
    reasons.extend(_repetition_issue(summary))

    suspicious = re.compile(
        r"(?:men bu vazifani|i cannot|as an ai|```|<html|lorem ipsum)",
        re.IGNORECASE,
    )
    if suspicious.search(f"{title} {summary} {content}"):
        reasons.append("modelning texnik yoki rad javobi aniqlandi")

    allowed_acronyms = {
        "AQSH",
        "ESPN",
        "FIFA",
        "LAFC",
        "NWSL",
        "UEFA",
        "USMNT",
        "VAR",
        "YECHL",
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

    if require_structured:
        confidence_rules = (
            ("football_confidence", MIN_FOOTBALL_CONFIDENCE, "futbol confidence past"),
            ("category_confidence", MIN_CATEGORY_CONFIDENCE, "kategoriya confidence past"),
            ("fact_confidence", MIN_FACT_CONFIDENCE, "fakt confidence past"),
        )
        for field, minimum, reason in confidence_rules:
            try:
                confidence = int(analysis.get(field, 0))
            except (TypeError, ValueError):
                confidence = 0
            if confidence < minimum:
                reasons.append(reason)

        entities = analysis.get("entities") or []
        facts = analysis.get("facts") or []
        if not entities:
            reasons.append("entitylar ajratilmagan")
        if not facts:
            reasons.append("structured faktlar ajratilmagan")

        normalized_source = _evidence_text(source_text)
        for index, fact in enumerate(facts, 1):
            if not isinstance(fact, dict):
                reasons.append(f"{index}-fakt formati noto'g'ri")
                continue
            if not all(normalize_text(fact.get(key)) for key in ("subject", "predicate", "value")):
                reasons.append(f"{index}-fakt to'liq emas")
            if not _is_evidence_supported(str(fact.get("evidence") or ""), normalized_source):
                reasons.append(f"{index}-fakt dalili manbada topilmadi")

        if not normalize_text(analysis.get("event_key")):
            reasons.append("event key yaratilmagan")

    return not reasons, reasons


def analysis_is_auto_publishable(
    analysis: dict,
    source_name: str,
    source_url: str,
) -> tuple[bool, list[str]]:
    """Umumiy quality gate'dan o'tgan xabar uchun qat'iy avto-nashr qarori.

    Dublikat tekshiruvi pipeline'da bu funksiyadan oldin ikki bosqichda
    bajariladi. Bu yerda confidence, ahamiyat va ishonchli asl manba tekshiriladi.
    """
    reasons: list[str] = []
    confidence_rules = (
        (
            "football_confidence",
            AUTO_PUBLISH_MIN_FOOTBALL_CONFIDENCE,
            "avto-nashr uchun futbol confidence past",
        ),
        (
            "category_confidence",
            AUTO_PUBLISH_MIN_CATEGORY_CONFIDENCE,
            "avto-nashr uchun kategoriya confidence past",
        ),
        (
            "fact_confidence",
            AUTO_PUBLISH_MIN_FACT_CONFIDENCE,
            "avto-nashr uchun fakt confidence past",
        ),
    )
    for field, minimum, reason in confidence_rules:
        try:
            confidence = int(analysis.get(field, 0))
        except (TypeError, ValueError):
            confidence = 0
        if confidence < minimum:
            reasons.append(f"{reason} ({confidence} < {minimum})")

    try:
        importance = int(analysis.get("ahamiyati", 0))
    except (TypeError, ValueError):
        importance = 0
    if importance < AUTO_PUBLISH_MIN_IMPORTANCE:
        reasons.append(
            "avto-nashr uchun ahamiyat past "
            f"({importance} < {AUTO_PUBLISH_MIN_IMPORTANCE})"
        )

    parsed_source_url = urlparse(str(source_url or "").strip())
    if parsed_source_url.scheme != "https" or not parsed_source_url.netloc:
        reasons.append("ishonchli HTTPS manba URL'i mavjud emas")

    normalized_source = str(source_name or "").strip().casefold()
    if normalized_source not in AUTO_PUBLISH_TRUSTED_SOURCES:
        reasons.append("manba avto-nashr uchun ishonchli ro'yxatda emas")

    return not reasons, reasons


def infer_category(text: str, current: str) -> str:
    """AI kategoriyasini voqea konteksti bilan qayta tekshiradi.

    Yakka ``superliga`` yoki ``transfer`` so'zi kategoriya uchun yetarli emas:
    WSL ham Superliga deb tarjima qilinishi, transfer so'zi esa inkor gapida
    kelishi mumkin.
    """
    haystack = normalize_text(text).lower()

    uzbekistan_context = re.search(
        r"o'zbekiston|o‘zbekiston|uzbekistan|o'zbek|o‘zbek|"
        r"paxtakor|nasaf|navbahor|bunyodkor|sog'diyona|sog‘diyona|"
        r"qo'qon|qo‘qon|okmk|neftchi|surxon|dinamo samarqand|\bpfl\b",
        haystack,
        re.IGNORECASE,
    )
    if uzbekistan_context:
        return "uzbekiston-futboli"

    transfer_denial = re.search(
        r"transfer(?:lar)?\s+(?:haqida|bilan|ga)\b[^.!?]{0,80}"
        r"(?:emas|yo'q|yo‘q|ma'lumot bermaydi|ma’lumot bermaydi|bog'liq emas|bog‘liq emas)",
        haystack,
        re.IGNORECASE,
    )
    transfer_action = re.search(
        r"\b(?:sotib oldi|safiga qo'shildi|safiga qo‘shildi|"
        r"o'tdi|o‘tdi|o'tishi|o‘tishi|imzoladi|shartnoma imzol|"
        r"kelishuvga erish|taklif yubor|muzokara olib bor|ijaraga oldi|"
        r"joins?|signs?|signed|agreed (?:a )?deal)\b",
        haystack,
        re.IGNORECASE,
    )
    if transfer_action and not transfer_denial:
        return "transferlar"

    rules = (
        ("chempionlar-ligasi", r"champions league|chempionlar ligasi|\buefa cl\b"),
        (
            "premyer-liga",
            r"premyer|premier league|arsenal|chelsea|chelsi|liverpool|liverpul|"
            r"manchester|tottenham|bornmut|bournemouth|lids|leeds|newcastle|nyukasl",
        ),
        ("la-liga", r"\bla liga\b|barselona|barcelona|real madrid|atletico"),
        ("seriya-a", r"\bserie a\b|\bseriya a\b|juventus|yuventus|inter|milan|napoli|roma"),
        ("bundesliga", r"bundesliga|bayern|dortmund|leverkusen"),
        ("terma-jamoalar", r"terma jamoa|world cup|jahon chempionati|usmnt|uefa nations"),
    )
    for category, pattern in rules:
        if re.search(pattern, haystack, re.IGNORECASE):
            return category

    # Oldingi noto'g'ri, faqat umumiy kalit so'zdan kelgan kategoriyani saqlamaymiz.
    if current in {"uzbekiston-futboli", "transferlar"}:
        return "jahon-futboli"
    return current


def cleanup_existing_articles(db: Session) -> tuple[int, int]:
    """Eski noto'g'ri sport xabarlarini yashiradi va matn xatolarini tuzatadi."""
    bad_url_filters = [
        Article.original_url.contains(part)
        for part in NON_FOOTBALL_URL_PARTS
    ]
    rejected = (
        db.query(Article)
        .filter(
            Article.status == "published",
            or_(*bad_url_filters),
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
