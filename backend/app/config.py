import os
from dotenv import load_dotenv

load_dotenv()

# Ma'lumotlar bazasi: prod'da PostgreSQL, lokal ishlab chiqishda SQLite yetarli.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./futbolxabar.db")

# AI provayder: "gemini" (standart), "vertex" yoki "claude"
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Render kabi Google Cloud'dan tashqaridagi serverlar uchun Vertex AI + ADC.
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
VERTEX_GEMINI_MODEL = os.getenv("VERTEX_GEMINI_MODEL", "gemini-2.5-flash-lite")

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
MIN_FOOTBALL_CONFIDENCE = int(os.getenv("MIN_FOOTBALL_CONFIDENCE", "85"))
MIN_CATEGORY_CONFIDENCE = int(os.getenv("MIN_CATEGORY_CONFIDENCE", "75"))
MIN_FACT_CONFIDENCE = int(os.getenv("MIN_FACT_CONFIDENCE", "80"))

# Muhim yangiliklarni Telegram kanalga avtomatik yuborish
AUTO_TELEGRAM = _bool("AUTO_TELEGRAM", "false")
AUTO_TELEGRAM_MIN_IMPORTANCE = int(os.getenv("AUTO_TELEGRAM_MIN_IMPORTANCE", "4"))

# Rasm topilmaganda Gemini bilan generatsiya qilish (pullik — standart o'chiq)
IMAGE_GENERATION = _bool("IMAGE_GENERATION", "false")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
# Yaratilgan rasmlar saqlanadigan papka va ularning ommaviy manzili
MEDIA_DIR = os.getenv("MEDIA_DIR", "./media")
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")

# Frontend manzili (CORS uchun)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
