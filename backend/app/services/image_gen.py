"""Ixtiyoriy: rasm topilmagan maqolalar uchun Gemini bilan rasm generatsiya.

.env orqali yoqiladi: IMAGE_GENERATION=true (standart: o'chiq — har rasm pullik).
Yaratilgan rasm MEDIA_DIR ga saqlanadi va backend /media/... orqali tarqatadi.
"""

import base64
from pathlib import Path

import httpx

from ..config import (
    BACKEND_PUBLIC_URL,
    GEMINI_API_KEY,
    GEMINI_IMAGE_MODEL,
    MEDIA_DIR,
)


def generate_image(title: str, slug: str) -> str | None:
    """Sarlavha asosida yangilik illyustratsiyasini yaratadi.
    Muvaffaqiyatda ommaviy URL, xatoda None qaytaradi."""
    if not GEMINI_API_KEY:
        return None

    prompt = (
        "Create a clean, modern editorial illustration for a technology news "
        f"article titled: \"{title}\". Abstract tech aesthetic, blue and dark "
        "tones, suitable as a news cover image. No text, no letters, no logos."
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_IMAGE_MODEL}:generateContent"
    )
    try:
        response = httpx.post(
            url,
            json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
            headers={"x-goog-api-key": GEMINI_API_KEY},
            timeout=120,
        )
        if response.status_code != 200:
            print(f"   ✗ Rasm generatsiya xatosi {response.status_code}: {response.text[:200]}")
            return None

        parts = response.json()["candidates"][0]["content"]["parts"]
        image_part = next((p["inlineData"] for p in parts if "inlineData" in p), None)
        if not image_part:
            return None

        media_dir = Path(MEDIA_DIR)
        media_dir.mkdir(parents=True, exist_ok=True)
        extension = "png" if "png" in image_part.get("mimeType", "image/png") else "jpg"
        file_path = media_dir / f"{slug}.{extension}"
        file_path.write_bytes(base64.b64decode(image_part["data"]))

        return f"{BACKEND_PUBLIC_URL}/media/{file_path.name}"
    except Exception as error:
        print(f"   ✗ Rasm generatsiya xatosi: {error}")
        return None
