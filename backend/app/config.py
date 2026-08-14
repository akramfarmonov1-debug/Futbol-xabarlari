import os
from dotenv import load_dotenv

load_dotenv()

# Ma'lumotlar bazasi: prod'da PostgreSQL, lokal ishlab chiqishda SQLite yetarli.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./futbolxabar.db")

# AI provayder: "gemini" (standart), "vertex" yoki "claude"
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

# Render kabi Google Cloud'dan tashqaridagi serverlar uchun Vertex AI + ADC.
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
VERTEX_GEMINI_MODEL = os.getenv("VERTEX_GEMINI_MODEL", "gemini-3.7-flash")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")

# Admin panelga kirish uchun maxfiy token (X-Admin-Token sarlavhasi orqali).
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-token-o'zgartiring")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")  # masalan: @ai_news_uz

# Jonli natijalar va turnir jadvali uchun football-data.org API kaliti.
# Bepul tarif: football-data.org/client/register (10 so'rov/daqiqa).
# Bo'sh bo'lsa — "Bugungi o'yinlar" va "Jadval" bloklari yashiriladi.
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")

# O'zbekiston Superligasi uchun API-Football (API-Sports).
# Kalit faqat backendda saqlanadi: https://dashboard.api-football.com/
API_FOOTBALL_KEY = (
    os.getenv("API_FOOTBALL_KEY", "") or os.getenv("API_SPORTS_KEY", "")
).strip()
API_FOOTBALL_UZ_LEAGUE_ID = os.getenv(
    "API_FOOTBALL_UZ_LEAGUE_ID", ""
).strip()
API_FOOTBALL_SEASON = os.getenv("API_FOOTBALL_SEASON", "").strip()

# Liga belgilari, bannerlari va qo'shimcha metadata uchun TheSportsDB.
# "123" — TheSportsDB tomonidan rasmiy taqdim etilgan umumiy bepul V1 kalit.
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "123").strip()


def _bool(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "ha")


# Avto-chop etish xavfsiz standart sifatida o'chiq. Faqat quality gate
# ishonchli deb topgan maqolalar uchun production'da ongli ravishda yoqiladi.
AUTO_PUBLISH = _bool("AUTO_PUBLISH", "false")
# Faqat shu bahodan yuqori maqolalar avto-chop etiladi (qolganlari pending)
AUTO_PUBLISH_MIN_IMPORTANCE = int(os.getenv("AUTO_PUBLISH_MIN_IMPORTANCE", "1"))
# Avtomatik nashr oddiy quality gate'dan qat'iyroq: uchala confidence ham
# alohida 90+ bo'lishi kerak. Qiymatlar env orqali boshqariladi.
AUTO_PUBLISH_MIN_FOOTBALL_CONFIDENCE = int(
    os.getenv("AUTO_PUBLISH_MIN_FOOTBALL_CONFIDENCE", "90")
)
AUTO_PUBLISH_MIN_CATEGORY_CONFIDENCE = int(
    os.getenv("AUTO_PUBLISH_MIN_CATEGORY_CONFIDENCE", "90")
)
AUTO_PUBLISH_MIN_FACT_CONFIDENCE = int(
    os.getenv("AUTO_PUBLISH_MIN_FACT_CONFIDENCE", "90")
)
AUTO_PUBLISH_TRUSTED_SOURCES = frozenset(
    source.strip().casefold()
    for source in os.getenv(
        "AUTO_PUBLISH_TRUSTED_SOURCES",
        "BBC Sport Football,The Guardian Football,Sky Sports Football,"
        "ESPN Soccer,Sports.uz",
    ).split(",")
    if source.strip()
)
MIN_FOOTBALL_CONFIDENCE = int(os.getenv("MIN_FOOTBALL_CONFIDENCE", "85"))
MIN_CATEGORY_CONFIDENCE = int(os.getenv("MIN_CATEGORY_CONFIDENCE", "75"))
MIN_FACT_CONFIDENCE = int(os.getenv("MIN_FACT_CONFIDENCE", "80"))

# Muhim yangiliklarni Telegram kanalga avtomatik yuborish
AUTO_TELEGRAM = _bool("AUTO_TELEGRAM", "true")
AUTO_TELEGRAM_MIN_IMPORTANCE = int(os.getenv("AUTO_TELEGRAM_MIN_IMPORTANCE", "1"))


# Kunlik dayjest: har kuni DAILY_DIGEST_TIME (Toshkent vaqti) da kanalga
# bugungi muhim yangiliklarni bitta xulosa posti sifatida yuborish.
DAILY_DIGEST = _bool("DAILY_DIGEST", "false")
DAILY_DIGEST_TIME = os.getenv("DAILY_DIGEST_TIME", "09:00")
DAILY_DIGEST_LIMIT = int(os.getenv("DAILY_DIGEST_LIMIT", "5"))
DAILY_DIGEST_MIN_IMPORTANCE = int(os.getenv("DAILY_DIGEST_MIN_IMPORTANCE", "3"))
# Loop qanchalik tez-tek tekshirishi (sekund) — oyna ichida bir marta yuboriladi.
DAILY_DIGEST_INTERVAL = int(os.getenv("DAILY_DIGEST_INTERVAL", "600"))
# Maqsadli vaqt atrofidagi oyna (daqiqa) — aniq daqiqani o'tkazib yubormaslik uchun.
DAILY_DIGEST_WINDOW_MINUTES = int(os.getenv("DAILY_DIGEST_WINDOW_MINUTES", "30"))

# Rasm topilmaganda Gemini bilan generatsiya qilish (pullik — standart o'chiq)
IMAGE_GENERATION = _bool("IMAGE_GENERATION", "false")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
# Yaratilgan rasmlar saqlanadigan papka va ularning ommaviy manzili
MEDIA_DIR = os.getenv("MEDIA_DIR", "./media")
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")

# Frontend manzili (CORS uchun)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
