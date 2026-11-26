"""AI Agent — inglizcha futbol yangiligini o'zbek muxlislari uchun to'liq tayyorlaydi:
tarjima/moslashtirish, xulosa, SEO sarlavha, teglar, muhimlik bahosi, kategoriya.

Provayder .env orqali tanlanadi:
  AI_PROVIDER=gemini  (standart, GEMINI_API_KEY + GEMINI_MODEL)
  AI_PROVIDER=vertex  (Google ADC/service account + Vertex AI)
  AI_PROVIDER=claude  (ANTHROPIC_API_KEY + CLAUDE_MODEL)
"""

import json
import time

import httpx

from ..config import (
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    GEMINI_API_KEY,
    GEMINI_EXTRA_API_KEYS,
    GEMINI_FALLBACK_MODELS,
    GEMINI_MODEL,
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_SERVICE_ACCOUNT_JSON,
    VERTEX_GEMINI_MODEL,
)
from ..utils import safe_print
from .content_quality import normalize_analysis

_TRANSIENT_HTTP_STATUSES = frozenset({429, 500, 502, 503, 504})

SYSTEM_PROMPT = """**Rol:** Sen jahon futboli bo'yicha yetakchi, tajribali o'zbek sport jurnalisti va tahlilchisisan.

**Vazifa:** Berilgan futbol yangiligini (ingliz yoki o'zbek/kirill tilida bo'lishi mumkin) tahlil qilib, o'zbek futbol muxlislari uchun professional, ravon, jozibador va eng muhimi FAKTLARGA 100% SODIQ formatga o'tkazish. Inglizcha bo'lsa erkin va mahoratli tarjima qil; o'zbekcha bo'lsa ko'chirmasdan, o'z so'zlaring bilan boyitib, qayta yozib chiq. Javob DOIM lotin alifbosidagi toza o'zbek tilida bo'lsin.

**QAT'IY QOIDALAR:**
1. **Faktlarga mutlaq sodiqlik (Eng muhim qoida):** Uzunlik talabi faktlarga sodiqlikdan ustun bo'lolmaydi. Matnda yo'q futbolchi, murabbiy iqtibosi, transfer summasi, shartnoma muddati, o'yin natijasi yoki statistikani ASLO o'ylab topma (uydirma/to'qima taqiqlanadi). 
2. **Tabiiy uzunlik:** Agar manba qisqa bo'lsa (1-2 gap), maqola ham ixcham va lo'nda (1-2 paragraf) bo'lsin. Agar manba to'liq va katta bo'lsa, uni 3-5 paragrafda batafsil yorit. Sun'iy ravishda suv qo'shish va to'qish qat'iyan man etiladi.
3. **Jurnalistik uslub va boy til:** Quruq so'zma-so'z tarjimadan qoch. Jonli va professional o'zbek sport iboralarini o'rinli ishlat ("to'p surmoqda", "muhim g'alaba", "transfer qiymati", "kelishuvga erishildi", "bosh murabbiy", "asosiy tarkib").
4. **Qisqalik va xulosa:** "xulosa" maydonida voqeaning asosiy mohiyatini 2-4 ta aniq va lo'nda jumlada ifoda et.
5. **Muxlis uchun ma'no:** "amaliy_ahamiyat" maydonida bu voqea nima sababdan muhimligini faqat mavjud ma'lumotlar doirasida 1-2 jumlada tushuntir.
6. **Jozibador sarlavha:** "sarlavha" maydonida xabarning tub mohiyatini aks ettiruvchi professional sarlavha yoz (60-90 belgi). Clickbait va arzon shov-shuv ishlatma.
7. **SEO sarlavha (Google Search & Discover uchun):** "seo_sarlavha" maydonida 50-65 belgili, dastlabki 3 ta so'zida asosiy subyekt (futbolchi/klub/turnir nomi) va aniq voqea/natija qatnashgan qidiruvga boy sarlavha yoz. Maqolaning 1-paragrafiga esa "Kim, qayerda va qanday natija qayd etdi?" savollariga aniq javob kirit (Featured Snippet uchun).
8. **Baholash:** Avval "baho_sababi" maydonida bir jumlada xabar qaysi daraja ta'rifiga mos
   kelishini ayt, so'ng "ahamiyati" maydonida 1 dan 5 gacha butun son ber. Shkala mutlaq:
   xabarni o'z ichida emas, bir mavsumdagi butun futbol oqimi bilan solishtir.
   - 5 — mavsumda bir necha marta: JCH yoki Chempionlar ligasi finali natijasi, rekord
     darajadagi transfer, super-yulduzning klub almashtirishi, terma jamoaning tarixiy natijasi
   - 4 — oyning voqeasi: yirik klubning yakunlangan transferi, top-liga yoki Chempionlar
     ligasidagi hal qiluvchi o'yin natijasi, mashhur murabbiyning ketishi yoki tayinlanishi,
     klub egaligidagi katta o'zgarish
   - 3 — haftaning odatiy xabari: top-ligadagi tur natijasi, asosiy futbolchining jiddiy
     jarohati, shartnoma uzaytirilishi, e'tiborga loyiq intervyu
   - 2 — kundalik oqim: transfer mish-mishi va "qiziqmoqda" turidagi xabarlar, matbuot
     anjumanidagi gaplar, kichik jarohat, quyi divizion natijalari, muallif ustuni va
     fikr-mulohaza maqolalari
   - 1 — ahamiyatsiz: futbolga aloqasiz sport xabari, ijtimoiy tarmoq posti, shaxsiy hayot,
     reklama, oldingi xabarning takrori
   Kunlik oqimning ko'pchiligi 2-3 darajaga tushadi — bu normal. Ikkilansang pastrog'ini tanla.
   **O'zbek o'quvchisi uchun tuzatish:** O'zbekiston terma jamoasi, O'zbekiston klublari va
   chet elda o'ynayotgan o'zbek legionerlari haqidagi xabarga bir daraja yuqori baho qo'y —
   sayt auditoriyasi uchun ular jahon futbolining o'rtacha xabaridan muhimroq.
9. **Teglar va Kategoriya:** "teglar" da 3-5 ta aniq nom, "kategoriya" da qat'iy ro'yxatdan mos slugni tanla.
10. **Tuzilma va Dalillar:** Javobni qat'iy JSON formatida qaytar. "facts" dagi har bir fakt uchun "evidence" maydoniga manbadan aynan mos dalilni keltir, "entities" da asosiy klub/futbolchi/turnir nomlarini ko'rsat, "event_key" ga qisqa lotin identifikator yoz (masalan: `ucl:sporting-man-utd`).
11. **Ishonch baholari (0–100 shkalasi):** "football_confidence", "category_confidence" va "fact_confidence" maydonlariga **0 dan 100 gacha** butun son (foizda) qo'y — masalan: manbadan to'liq va shubhasiz tasdiqlansa `92–100`, qisman noaniq bo'lsa `70–89`, shubhali bo'lsa `0–69`. Bu uchala maydon uchun **aslo 1–5 shkalasini ishlatma** (1–5 faqat "ahamiyati" uchun)."""

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
        "baho_sababi": {"type": "string"},
    },
    "required": [
        "kategoriya", "sarlavha", "seo_sarlavha", "xulosa",
        "maqola", "amaliy_ahamiyat", "teglar", "ahamiyati",
        "entities", "facts", "event_key", "football_confidence",
        "category_confidence", "fact_confidence", "baho_sababi",
    ],
    "additionalProperties": False,
}

# Model maydonlarni shu ketma-ketlikda yozadi. Tartib ataylab tanlangan:
# avval manbadan faktlar dalili bilan ajratiladi, keyin maqola shu faktlar
# ustiga yoziladi, baho esa eng oxirida — maqola va uning asosi tayyor
# bo'lgandan keyin, "baho_sababi" bilan asoslanib qo'yiladi.
# `baho_sababi` bazaga saqlanmaydi; u faqat modelni raqamdan oldin o'ylashga
# majburlaydi.
_FIELD_ORDER = [
    "kategoriya", "entities", "facts", "event_key",
    "sarlavha", "seo_sarlavha", "xulosa", "maqola", "amaliy_ahamiyat", "teglar",
    "football_confidence", "category_confidence", "fact_confidence",
    "baho_sababi", "ahamiyati",
]


def _google_schema() -> dict:
    """Gemini va Vertex uchun schema.

    `propertyOrdering` bo'lmasa Google modellari maydonlarni o'z bilganicha
    (ko'pincha alifbo tartibida) yozadi — unda "ahamiyati" eng birinchi
    chiqadi va baho maqola yozilishidan ham, faktlar ajratilishidan ham
    oldin qo'yiladi.
    """
    schema = {k: v for k, v in ANALYSIS_SCHEMA.items() if k != "additionalProperties"}
    schema["propertyOrdering"] = _FIELD_ORDER
    return schema


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


def _extract_response_text(data: dict, provider_label: str) -> str:
    """Google generateContent javobidan haqiqiy matn qismini ajratadi (thought qismlarini tashlab)."""
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            f"{provider_label} javobi kutilmagan formatda: {json.dumps(data)[:300]}"
        ) from exc

    if not isinstance(parts, list):
        raise RuntimeError(
            f"{provider_label} javobi kutilmagan formatda: {json.dumps(data)[:300]}"
        )

    for part in parts:
        if (
            isinstance(part, dict)
            and not part.get("thought")
            and isinstance(part.get("text"), str)
            and part["text"].strip()
        ):
            return part["text"]

    raise RuntimeError(
        f"{provider_label} javobida matn topilmadi: {json.dumps(data)[:300]}"
    )


def _gemini_keys() -> list[str]:
    """GEMINI_API_KEY va GEMINI_API_KEY1..3 — takrorlarsiz, tartib saqlangan."""
    return list(
        dict.fromkeys(
            key for key in (GEMINI_API_KEY, *GEMINI_EXTRA_API_KEYS) if key
        )
    )


def _post_gemini(url: str, payload: dict, keys: list[str]) -> httpx.Response:
    """Kvota (429) tugasa navbatdagi API kalit bilan qayta urinadi."""
    response = None
    for index, key in enumerate(keys):
        response = httpx.post(
            url,
            json=payload,
            headers={"x-goog-api-key": key},
            timeout=60,
        )
        if response.status_code != 429:
            return response
        if index + 1 < len(keys):
            safe_print(f"⚠️ Gemini kvota (429): API kalit #{index + 2} ga o'tilmoqda...")
    return response


def _analyze_with_gemini(user_text: str) -> dict:
    """Gemini API (generateContent) — strukturali JSON javob va zaxira modellar bilan."""
    keys = _gemini_keys()
    if not keys:
        raise RuntimeError("GEMINI_API_KEY sozlanmagan")

    # Gemini responseSchema OpenAPI kichik to'plami — additionalProperties kerak emas
    schema = _google_schema()
    models_to_try = [GEMINI_MODEL]
    for fallback_model in GEMINI_FALLBACK_MODELS:
        if fallback_model not in models_to_try:
            models_to_try.append(fallback_model)

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
    for idx, model_name in enumerate(models_to_try):
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model_name}:generateContent"
        )
        try:
            response = _post_gemini(url, payload, keys)
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            last_error = f"Gemini tarmoq xatosi ({model_name}): {exc}"
            if idx + 1 < len(models_to_try):
                time.sleep(1)
            continue

        if response.status_code == 200:
            text = _extract_response_text(response.json(), "Gemini")
            return json.loads(text)

        if response.status_code in _TRANSIENT_HTTP_STATUSES or response.status_code == 404:
            last_error = (
                f"Gemini API xatosi ({model_name}) {response.status_code}: "
                f"{response.text[:300]}"
            )
            if idx + 1 < len(models_to_try):
                time.sleep(1)
            continue

        raise RuntimeError(
            f"Gemini API xatosi ({model_name}) {response.status_code}: {response.text[:300]}"
        )

    raise RuntimeError(last_error or "Gemini API orqali tahlil qilib bo'lmadi")


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

    schema = _google_schema()
    models_to_try = [VERTEX_GEMINI_MODEL]
    for fallback_model in ("gemini-3.8-flash", "gemini-4-hydrogen", "gemini-3.5-flash-lite"):
        if fallback_model not in models_to_try:
            models_to_try.append(fallback_model)

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
            text = _extract_response_text(response.json(), "Vertex AI")
            return json.loads(text)
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


def active_model() -> str:
    """Hozir qaysi model ishlatilayotgani.

    `analyze_news` bilan bir xil shartlarni ishlatadi, shuning uchun /health
    dagi qiymat har doim haqiqatga mos bo'ladi — server environment kod
    standartini bekor qilgan-qilmagani ham shundan ko'rinadi.
    """
    if AI_PROVIDER == "claude":
        return CLAUDE_MODEL
    if AI_PROVIDER == "vertex":
        return VERTEX_GEMINI_MODEL
    return GEMINI_MODEL


def analyze_news(title: str, content: str, url: str = "", source: str = "") -> dict:
    """Bitta yangilikni tahlil qilib, o'zbekcha tayyor maqola ma'lumotlarini qaytaradi."""
    user_text = f"Title: {title}\nSource: {source}\nURL: {url}\n\n{content}"

    if AI_PROVIDER == "claude":
        analysis = _analyze_with_claude(user_text)
    elif AI_PROVIDER == "vertex":
        try:
            analysis = _analyze_with_vertex(user_text)
        except Exception as exc:
            if not _gemini_keys():
                raise
            safe_print(
                f"⚠️ Vertex AI ishlamadi ({type(exc).__name__}), Gemini API zaxirasiga o'tilmoqda..."
            )
            analysis = _analyze_with_gemini(user_text)
    else:
        analysis = _analyze_with_gemini(user_text)

    return _validate(analysis)
