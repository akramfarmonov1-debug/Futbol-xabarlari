import os
from dotenv import load_dotenv

load_dotenv()

# Ma'lumotlar bazasi: prod'da PostgreSQL, lokal ishlab chiqishda SQLite yetarli.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./futbolxabar.db")

# AI provayder: "gemini" (standart) yoki "claude"
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")

# Admin panelga kirish uchun maxfiy token (X-Admin-Token sarlavhasi orqali).
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-token-o'zgartiring")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")  # masalan: @ai_news_uz


def _bool(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "ha")


# Avto-chop etish: pipeline maqolalarni admin tasdig'isiz to'g'ridan-to'g'ri
# saytga chiqaradi. O'chirish uchun: AUTO_PUBLISH=false
AUTO_PUBLISH = _bool("AUTO_PUBLISH", "true")
# Faqat shu bahodan yuqori maqolalar avto-chop etiladi (qolganlari pending)
AUTO_PUBLISH_MIN_IMPORTANCE = int(os.getenv("AUTO_PUBLISH_MIN_IMPORTANCE", "1"))

# Muhim yangiliklarni Telegram kanalga avtomatik yuborish
AUTO_TELEGRAM = _bool("AUTO_TELEGRAM", "true")
AUTO_TELEGRAM_MIN_IMPORTANCE = int(os.getenv("AUTO_TELEGRAM_MIN_IMPORTANCE", "4"))

# Rasm topilmaganda Gemini bilan generatsiya qilish (pullik — standart o'chiq)
IMAGE_GENERATION = _bool("IMAGE_GENERATION", "false")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
# Yaratilgan rasmlar saqlanadigan papka va ularning ommaviy manzili
MEDIA_DIR = os.getenv("MEDIA_DIR", "./media")
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")

# Frontend manzili (CORS uchun)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
