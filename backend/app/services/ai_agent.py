"""AI Agent — inglizcha futbol yangiligini o'zbek muxlislari uchun to'liq tayyorlaydi:
tarjima/moslashtirish, xulosa, SEO sarlavha, teglar, muhimlik bahosi, kategoriya.

Provayder .env orqali tanlanadi:
  AI_PROVIDER=gemini  (standart, GEMINI_API_KEY + GEMINI_MODEL)
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
)

SYSTEM_PROMPT = """**Rol:** Sen jahon futboli bo'yicha yetakchi o'zbek sport jurnalisti va tahlilchisisan.

**Vazifa:** Ingliz tilida berilgan futbol yangiliklarini tahlil qilib, o'zbek muxlislari uchun ixcham, tushunarli va qiziqarli formatga o'tkazish.

**Qoidalar:**
1. **Qisqalik:** "xulosa" maydonida asosiy ma'noni yo'qotmagan holda 3-5 jumlada xulosa qil.
2. **To'liq maqola:** "maqola" maydonida yangilikni o'zbek tilida 3-6 paragrafda to'liq, sport jurnalistikasi uslubida yorit. Jamoa va futbolchi ismlarini o'zbek matbuotida qabul qilingan shaklda yoz. Paragraflarni bo'sh qator bilan ajrat.
3. **Baholash:** "ahamiyati" maydonida yangilikning muxlislar uchun ahamiyatiga qarab 1 dan 5 gacha butun son bilan baho ber (yirik transfer, final, rekord = 5; kundalik mayda xabar = 1-2).
4. **Muxlis uchun ma'no:** "amaliy_ahamiyat" maydonida bu yangilik muxlislar yoki jamoa istiqboli uchun nimani anglatishini 1-2 jumlada tushuntir.
5. **SEO:** "seo_sarlavha" maydonida qidiruv tizimlari uchun optimallashtirilgan, kalit so'zlarga boy o'zbekcha sarlavha yoz (60-70 belgi atrofida).
6. **Teglar:** "teglar" maydonida 3-6 ta qisqa o'zbekcha teg ber (jamoa, futbolchi, musobaqa nomlari).
7. **Kategoriyalash:** "kategoriya" maydonida yangilik qaysi yo'nalishga tegishli ekanini belgila.
8. **Tuzilma:** Javobni doim qat'iy JSON formatida qaytar."""

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
    },
    "required": [
        "kategoriya", "sarlavha", "seo_sarlavha", "xulosa",
        "maqola", "amaliy_ahamiyat", "teglar", "ahamiyati",
    ],
    "additionalProperties": False,
}


def _validate(analysis: dict) -> dict:
    """Model javobini xavfsiz chegaralarga keltiradi."""
    analysis["ahamiyati"] = max(1, min(5, int(analysis.get("ahamiyati", 3))))
    if analysis.get("kategoriya") not in CATEGORY_SLUGS:
        analysis["kategoriya"] = "jahon-futboli"
    analysis["teglar"] = [str(t) for t in (analysis.get("teglar") or [])][:6]
    return analysis


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
    else:
        analysis = _analyze_with_gemini(user_text)

    return _validate(analysis)
