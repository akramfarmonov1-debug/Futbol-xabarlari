"""O'zbekiston Superligasi uchun API-Football integratsiyasi.

Bepul tarifdagi kunlik limitni tejash uchun liga identifikatori 24 soat,
jadval bir soat va uchrashuvlar 15 daqiqa xotirada keshlanadi. API kaliti
bo'lmasa yoki xizmat javob bermasa saytning qolgan qismlari ishlashda davom
etadi.
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Callable

import httpx

from ..config import (
    API_FOOTBALL_KEY,
    API_FOOTBALL_SEASON,
    API_FOOTBALL_UZ_LEAGUE_ID,
)

BASE_URL = "https://v3.football.api-sports.io"
CODE = "UZB"
NAME = "O'zbekiston Superligasi"

STATUS_UZ = {
    "TBD": "Vaqti belgilanmagan",
    "NS": "Rejalashtirilgan",
    "1H": "Jonli",
    "HT": "Tanaffus",
    "2H": "Jonli",
    "ET": "Qo'shimcha vaqt",
    "BT": "Tanaffus",
    "P": "Penaltilar",
    "SUSP": "To'xtatildi",
    "INT": "To'xtatildi",
    "FT": "Tugadi",
    "AET": "Tugadi",
    "PEN": "Tugadi",
    "PST": "Keyinga qoldirildi",
    "CANC": "Bekor qilindi",
    "ABD": "To'xtatildi",
    "AWD": "Texnik natija",
    "WO": "Texnik natija",
}
LIVE_STATUSES = {"1H", "HT", "2H", "ET", "BT", "P", "SUSP", "INT"}

_cache: dict[str, tuple[float, object]] = {}


def is_configured() -> bool:
    return bool(API_FOOTBALL_KEY)


def _cached(key: str, ttl: int, producer: Callable):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = producer()
    if value is not None:
        _cache[key] = (now, value)
    return value


def _get(path: str, params: dict | None = None) -> list | None:
    if not API_FOOTBALL_KEY:
        return None

    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(
                f"{BASE_URL}{path}",
                params=params,
                headers={"x-apisports-key": API_FOOTBALL_KEY},
            )
        if response.status_code != 200:
            print(f"  API-Football xato ({path}): HTTP {response.status_code}")
            return None

        payload = response.json()
        errors = payload.get("errors")
        if errors:
            print(f"  API-Football xato ({path}): {errors}")
            return None
        return payload.get("response") or []
    except (httpx.HTTPError, ValueError, TypeError) as error:
        print(f"  API-Football xato ({path}): {error}")
        return None


def _league_context() -> tuple[int, int] | None:
    """Superliga ID va API'da mavjud joriy mavsumni aniqlaydi."""

    def _produce():
        league_row = None
        if API_FOOTBALL_UZ_LEAGUE_ID:
            try:
                league_id = int(API_FOOTBALL_UZ_LEAGUE_ID)
            except ValueError:
                print("  API_FOOTBALL_UZ_LEAGUE_ID raqam bo'lishi kerak")
                return None
        else:
            rows = _get(
                "/leagues",
                {
                    "country": "Uzbekistan",
                },
            )
            if not rows:
                return None
            league_row = next(
                (
                    row
                    for row in rows
                    if (row.get("league") or {}).get("name") == "Super League"
                ),
                rows[0],
            )
            league_id = (league_row.get("league") or {}).get("id")
            if not league_id:
                return None

        if API_FOOTBALL_SEASON:
            try:
                return int(league_id), int(API_FOOTBALL_SEASON)
            except ValueError:
                print("  API_FOOTBALL_SEASON yil ko'rinishida bo'lishi kerak")
                return None

        if league_row is None:
            rows = _get("/leagues", {"id": league_id})
            league_row = rows[0] if rows else {}

        seasons = league_row.get("seasons") or []
        current = next((season for season in seasons if season.get("current")), None)
        year = (current or (seasons[-1] if seasons else {})).get("year")
        return int(league_id), int(year or datetime.now(timezone.utc).year)

    return _cached("api-football:uzb:context", 24 * 60 * 60, _produce)


def get_standings() -> dict | None:
    if not API_FOOTBALL_KEY:
        return None

    def _produce():
        context = _league_context()
        if not context:
            return None
        league_id, season = context
        rows = _get("/standings", {"league": league_id, "season": season})
        if not rows:
            return None

        league = rows[0].get("league") or {}
        groups = league.get("standings") or []
        table = groups[0] if groups else []
        if not table:
            return None

        return {
            "competition": NAME,
            "code": CODE,
            "season": season,
            "source": "API-Football",
            "table": [
                {
                    "position": row.get("rank"),
                    "team": (row.get("team") or {}).get("name") or "?",
                    "crest": (row.get("team") or {}).get("logo"),
                    "played": (row.get("all") or {}).get("played"),
                    "won": (row.get("all") or {}).get("win"),
                    "draw": (row.get("all") or {}).get("draw"),
                    "lost": (row.get("all") or {}).get("lose"),
                    "points": row.get("points"),
                    "goal_diff": row.get("goalsDiff"),
                }
                for row in table
            ],
        }

    return _cached("api-football:uzb:standings", 60 * 60, _produce)


def get_matches() -> dict | None:
    """Bugungi va ertangi Superliga uchrashuvlarini bitta guruhda qaytaradi."""
    if not API_FOOTBALL_KEY:
        return None

    def _produce():
        context = _league_context()
        if not context:
            return None
        league_id, season = context
        today = datetime.now(timezone.utc).date()
        rows = _get(
            "/fixtures",
            {
                "league": league_id,
                "season": season,
                "from": today.isoformat(),
                "to": (today + timedelta(days=1)).isoformat(),
                "timezone": "Asia/Tashkent",
            },
        )
        if not rows:
            return None

        matches = []
        for row in rows:
            fixture = row.get("fixture") or {}
            teams = row.get("teams") or {}
            goals = row.get("goals") or {}
            status_code = (fixture.get("status") or {}).get("short")
            home = teams.get("home") or {}
            away = teams.get("away") or {}
            matches.append(
                {
                    "home": home.get("name") or "?",
                    "away": away.get("name") or "?",
                    "home_crest": home.get("logo"),
                    "away_crest": away.get("logo"),
                    "home_score": goals.get("home"),
                    "away_score": goals.get("away"),
                    "status": STATUS_UZ.get(status_code, status_code),
                    "is_live": status_code in LIVE_STATUSES,
                    "kickoff": fixture.get("date"),
                }
            )

        return {
            "competition": NAME,
            "code": CODE,
            "matches": matches,
        }

    return _cached("api-football:uzb:matches", 15 * 60, _produce)
