"""AI Agent — inglizcha futbol yangiligini o'zbek muxlislari uchun to'liq tayyorlaydi:
tarjima/moslashtirish, xulosa, SEO sarlavha, teglar, muhimlik bahosi, kategoriya.

Provayder .env orqali tanlanadi:
  AI_PROVIDER=gemini  (standart, GEMINI_API_KEY + GEMINI_MODEL)
  AI_PROVIDER=vertex  (Google ADC/service account + Vertex AI)
  AI_PROVIDER=claude  (ANTHROPIC_API_KEY + CLAUDE_MODEL)
"""

import json

import httpx

from ..config import (
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_SERVICE_ACCOUNT_JSON,
    VERTEX_GEMINI_MODEL,
)
from .content_quality import normalize_analysis

SYSTEM_PROMPT = """**Rol:** Sen jahon futboli bo'yicha yetakchi, tajribali o'zbek sport jurnalisti va tahlilchisisan.

**Vazifa:** Berilgan futbol yangiligini (ingliz yoki o'zbek/kirill tilida bo'lishi mumkin) tahlil qilib, o'zbek futbol muxlislari uchun professional, ravon, jozibador va tushunarli formatga o'tkazish. Inglizcha bo'lsa erkin va mahoratli tarjima qil; o'zbekcha bo'lsa ko'chirmasdan, O'Z SO'ZLARING bilan boyitib, qayta yozib chiq. Javob DOIM lotin alifbosidagi toza o'zbek tilida bo'lsin.

**Qoidalar:**
1. **Jurnalistik uslub va boy til:** Matn quruq so'zma-so'z tarjima bo'lmasin. Jonli o'zbek sport iboralarini ishlating (masalan: "to'p surmoqda", "shiddatli bahs", "muhim g'alaba", "transfer qiymati", "kelishuvga erishildi", "bosh murabbiy", "asosiy tarkib", "texnik hudud").
2. **Qisqalik va xulosa:** "xulosa" maydonida voqeaning asosiy mohiyatini 3-4 ta aniq, o'qilishi oson jumlada ifoda et.
3. **To'liq maqola:** "maqola" maydonida yangilikni 3-6 ta mantiqiy paragrafda, tahliliy sport jurnalistikasi uslubida to'liq yorit. Har bir paragraf o'rtasida bo'sh qator tashla.
4. **Muxlis uchun ma'no:** "amaliy_ahamiyat" maydonida bu voqea klub, turnir jadvali yoki o'zbek muxlislari uchun nima berishini 1-2 jumlada chuqur tushuntir.
5. **Jozibador sarlavha:** "sarlavha" maydonida voqeaning eng muhim qismini ochib beruvchi, jiddiy va qiziqarli sarlavha yoz (70-90 belgi). Arzon clickbait va soxta hayrat ("shok xabar", "bunaqasi bo'lmagan") ishlatma.
6. **SEO sarlavha:** "seo_sarlavha" maydonida qidiruv tizimlari (Google, Yandex) uchun kalit so'zlarga boy sarlavha yoz (60-70 belgi).
7. **Baholash:** "ahamiyati" maydonida yangilikning muxlislar uchun qimmati bo'yicha 1 dan 5 gacha baho ber (5 = top transfer, Chempionlar ligasi finali, rekord; 1-2 = kichik mayda xabar).
8. **Teglar:** "teglar" maydonida 3-5 ta aniq teg ber (klub, futbolchi yoki turnir nomi).
9. **Kategoriyalash:** "kategoriya" maydonida yangilik yo'nalishini qat'iy ro'yxatdan tanla.
10. **Tuzilma:** Javobni doim qat'iy JSON formatida qaytar.
11. **Faktlar va dalillar:** Asl matnda yo'q narsalarni o'ylab topma. "facts" ichidagi har bir fakt uchun "evidence" maydoniga manbadagi tegishli dalilni yoz.
12. **Entitylar va Event key:** "entities" da asosiy ism va klublar, "event_key" da voqea turini kichik harflarda ber (masalan: "transfer:valentin-barco:chelsea").
13. **Yagona to'g'ri nomlar:** O'zbek matbuoti qoidalariga rioya qil (Chelsea → Chelsi, Liverpool → Liverpul, Bayern → Bavariya, Real Madrid → Real, Juventus → Yuventus, Rangers → Reynjers)."""

CATEGORY_SLUGS = [
    "transferlar", "premyer-liga", "la-liga", "seriya-a", "bundesliga",
    "chempionlar-ligasi", "jahon-futboli", "uzbekiston-futboli", "terma-jamoalar",
]

# Kategoriya sluglari seed.py bilan mos bo'lishi shart.
ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "kategoriya": {"type": "string", "enum": CATEGORY_SLUGS},
        "sarlavha": {"type": "string"},
        "seo_sarlavha": {"type": "string"},
        "xulosa": {"type": "string"},
        "maqola": {"type": "string"},
        "amaliy_ahamiyat": {"type": "string"},
        "teglar": {"type": "array", "items": {"type": "string"}},
        "ahamiyati": {"type": "integer"},
        "entities": {"type": "array", "items": {"type": "string"}},
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "predicate": {"type": "string"},
                    "value": {"type": "string"},
                    "evidence": {"type": "string"},
                },
                "required": ["subject", "predicate", "value", "evidence"],
            },
        },
        "event_key": {"type": "string"},
        "football_confidence": {"type": "integer"},
        "category_confidence": {"type": "integer"},
        "fact_confidence": {"type": "integer"},
    },
    "required": [
        "kategoriya", "sarlavha", "seo_sarlavha", "xulosa",
        "maqola", "amaliy_ahamiyat", "teglar", "ahamiyati",
        "entities", "facts", "event_key", "football_confidence",
        "category_confidence", "fact_confidence",
    ],
    "additionalProperties": False,
}


def _validate(analysis: dict) -> dict:
    """Model javobini xavfsiz chegaralarga keltiradi."""
    analysis["ahamiyati"] = max(1, min(5, int(analysis.get("ahamiyati", 3))))
    if analysis.get("kategoriya") not in CATEGORY_SLUGS:
        analysis["kategoriya"] = "jahon-futboli"
    for field in (
        "football_confidence",
        "category_confidence",
        "fact_confidence",
    ):
        analysis[field] = max(0, min(100, int(analysis.get(field, 0))))
    return normalize_analysis(analysis)


def _analyze_with_gemini(user_text: str) -> dict:
    """Gemini API (generateContent) — strukturali JSON javob bilan."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY sozlanmagan")

    # Gemini responseSchema OpenAPI kichik to'plami — additionalProperties kerak emas
    schema = {k: v for k, v in ANALYSIS_SCHEMA.items() if k != "additionalProperties"}

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "maxOutputTokens": 8192,
        },
    }

    response = httpx.post(
        url,
        json=payload,
        headers={"x-goog-api-key": GEMINI_API_KEY},
        timeout=120,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Gemini API xatosi {response.status_code}: {response.text[:300]}")

    data = response.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Gemini javobi kutilmagan formatda: {json.dumps(data)[:300]}")
    return json.loads(text)


_vertex_credentials = None
_vertex_project = ""


def _analyze_with_vertex(user_text: str) -> dict:
    """Vertex AI generateContent — ADC yoki GOOGLE_SERVICE_ACCOUNT_JSON bilan autentifikatsiya."""
    global _vertex_credentials, _vertex_project

    import google.auth
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    if _vertex_credentials is None:
        if GOOGLE_SERVICE_ACCOUNT_JSON:
            info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
            _vertex_credentials = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            _vertex_project = GOOGLE_CLOUD_PROJECT or info.get("project_id") or ""
        else:
            _vertex_credentials, detected_project = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            _vertex_project = GOOGLE_CLOUD_PROJECT or detected_project or ""

    if not _vertex_project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT aniqlanmadi")

    if not _vertex_credentials.valid:
        _vertex_credentials.refresh(Request())

    schema = {k: v for k, v in ANALYSIS_SCHEMA.items() if k != "additionalProperties"}
    models_to_try = [VERTEX_GEMINI_MODEL]
    if VERTEX_GEMINI_MODEL != "gemini-2.5-flash":
        models_to_try.append("gemini-2.5-flash")

    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "maxOutputTokens": 8192,
        },
    }

    last_error = None
    for model_name in models_to_try:
        url = (
            "https://aiplatform.googleapis.com/v1/projects/"
            f"{_vertex_project}/locations/{GOOGLE_CLOUD_LOCATION}/publishers/google/models/"
            f"{model_name}:generateContent"
        )
        response = httpx.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {_vertex_credentials.token}"},
            timeout=120,
        )
        if response.status_code == 200:
            data = response.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            except (KeyError, IndexError):
                raise RuntimeError(f"Vertex AI javobi kutilmagan formatda: {json.dumps(data)[:300]}")
        last_error = f"Vertex AI xatosi ({model_name}) {response.status_code}: {response.text[:300]}"

    raise RuntimeError(last_error or "Vertex AI orqali tahlil qilib bo'lmadi")


def _analyze_with_claude(user_text: str) -> dict:
    """Claude API — strukturali JSON javob bilan."""
    import anthropic  # ixtiyoriy provayder — faqat kerak bo'lganda import qilinadi

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY or None)
    schema = dict(ANALYSIS_SCHEMA)
    schema["properties"] = dict(schema["properties"])
    schema["properties"]["ahamiyati"] = {"type": "integer", "enum": [1, 2, 3, 4, 5]}

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8192,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        output_config={"format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": user_text}],
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("Model tahlildan bosh tortdi (refusal)")

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def analyze_news(title: str, content: str, url: str = "", source: str = "") -> dict:
    """Bitta yangilikni tahlil qilib, o'zbekcha tayyor maqola ma'lumotlarini qaytaradi."""
    user_text = f"Title: {title}\nSource: {source}\nURL: {url}\n\n{content}"

    if AI_PROVIDER == "claude":
        analysis = _analyze_with_claude(user_text)
    elif AI_PROVIDER == "vertex":
        analysis = _analyze_with_vertex(user_text)
    else:
        analysis = _analyze_with_gemini(user_text)

    return _validate(analysis)
