"""TheSportsDB V1 integratsiyasi.

Bepul ``123`` kalit daqiqasiga 30 ta so'rov bilan cheklangan. Shu sababli
liga vizuallari 24 soat xotirada keshlanadi. API ishlamasa, frontendga
statik liga nomlari bilan xavfsiz fallback qaytariladi.
"""

import time

import httpx

from ..config import THESPORTSDB_API_KEY

BASE_URL = "https://www.thesportsdb.com/api/v1/json"
CACHE_TTL = 24 * 60 * 60

# football-data.org kodi -> TheSportsDB liga ID
LEAGUE_IDS = {
    "PL": "4328",
    "PD": "4335",
    "SA": "4332",
    "BL1": "4331",
    "FL1": "4334",
    "CL": "4480",
}

LEAGUE_NAMES = {
    "PL": "Angliya Premyer-ligasi",
    "PD": "La Liga",
    "SA": "Seriya A",
    "BL1": "Bundesliga",
    "FL1": "Fransiya Ligasi 1",
    "CL": "Chempionlar ligasi",
}

_cache: dict[str, tuple[float, dict]] = {}


def _fallback(code: str) -> dict:
    return {
        "code": code,
        "id": LEAGUE_IDS[code],
        "name": LEAGUE_NAMES[code],
        "international_name": None,
        "country": None,
        "formed_year": None,
        "badge": None,
        "banner": None,
        "poster": None,
        "fanart": None,
        "website": None,
        "source": "TheSportsDB",
    }


def get_league_profile(code: str) -> dict | None:
    """Liga badge/banner ma'lumotini xavfsiz fallback bilan qaytaradi."""
    code = code.upper()
    league_id = LEAGUE_IDS.get(code)
    if not league_id:
        return None

    now = time.time()
    cached = _cache.get(code)
    if cached and now - cached[0] < CACHE_TTL:
        return cached[1]

    fallback = _fallback(code)
    if not THESPORTSDB_API_KEY:
        _cache[code] = (now, fallback)
        return fallback

    try:
        with httpx.Client(timeout=12) as client:
            response = client.get(
                f"{BASE_URL}/{THESPORTSDB_API_KEY}/lookupleague.php",
                params={"id": league_id},
            )
        response.raise_for_status()
        rows = response.json().get("leagues") or []
        if not rows:
            _cache[code] = (now, fallback)
            return fallback

        league = rows[0]
        profile = {
            **fallback,
            "international_name": league.get("strLeague"),
            "country": league.get("strCountry"),
            "formed_year": league.get("intFormedYear"),
            "badge": league.get("strBadge"),
            "banner": league.get("strBanner"),
            "poster": league.get("strPoster"),
            "fanart": league.get("strFanart1"),
            "website": league.get("strWebsite"),
        }
        _cache[code] = (now, profile)
        return profile
    except (httpx.HTTPError, ValueError, TypeError) as error:
        print(f"  TheSportsDB xato ({code}): {error}")
        _cache[code] = (now, fallback)
        return fallback


def list_league_profiles() -> list[dict]:
    """Qo'llab-quvvatlanadigan barcha ligalar vizuallarini qaytaradi."""
    return [
        profile
        for code in LEAGUE_IDS
        if (profile := get_league_profile(code)) is not None
    ]
