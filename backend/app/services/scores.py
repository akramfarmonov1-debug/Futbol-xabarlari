"""Jonli natijalar va turnir jadvali — football-data.org (bepul tarif).

API kaliti (FOOTBALL_DATA_API_KEY) bo'lmasa, funksiyalar bo'sh natija qaytaradi
— sayt xatosiz ishlashda davom etadi, tegishli bloklar shunchaki ko'rinmaydi.

Bepul tarif 10 so'rov/daqiqa bilan cheklangan, shuning uchun javoblar
xotirada keshlanadi (o'yinlar 60s, jadval 1 soat).
"""

import time
from datetime import datetime, timedelta, timezone

import httpx

from ..config import FOOTBALL_DATA_API_KEY
from . import api_football, pfl

BASE = "https://api.football-data.org/v4"

# Bepul tarifda mavjud asosiy turnirlar (kod -> o'zbekcha nom)
COMPETITIONS = {
    "PL": "Angliya Premyer-ligasi",
    "PD": "La Liga",
    "SA": "Seriya A",
    "BL1": "Bundesliga",
    "FL1": "Fransiya Ligasi 1",
    "CL": "Chempionlar ligasi",
}

# Holat kodlarini o'zbekchaga o'girish
STATUS_UZ = {
    "SCHEDULED": "Rejalashtirilgan",
    "TIMED": "Rejalashtirilgan",
    "IN_PLAY": "Jonli",
    "PAUSED": "Tanaffus",
    "FINISHED": "Tugadi",
    "SUSPENDED": "To'xtatildi",
    "POSTPONED": "Keyinga qoldirildi",
    "CANCELLED": "Bekor qilindi",
}

_cache: dict[str, tuple[float, object]] = {}


def _cached(key: str, ttl: int, producer):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]

    try:
        value = producer()
        if value is not None:
            # Agar bo'sh ro'yxat qaytsa va bizda eski yaxshi ma'lumot bo'lsa, eskisini saqlab qolamiz
            if isinstance(value, list) and len(value) == 0 and hit and hit[1]:
                return hit[1]
            _cache[key] = (now, value)
            return value
    except Exception as err:
        print(f"  ⚠ scores kesh yangilash xatosi ({key}): {err}")

    # Agar API xato bersa yoki javob bo'sh bo'lsa, eski keshni saqlab qaytaramiz (Stale-While-Revalidate)
    if hit and hit[1] is not None:
        return hit[1]

    return [] if key == "today" else None


def _get(path: str, params: dict | None = None) -> dict | None:
    if not FOOTBALL_DATA_API_KEY:
        return None
    try:
        with httpx.Client(timeout=12) as client:
            resp = client.get(
                f"{BASE}{path}",
                params=params,
                headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception as error:
        print(f"  ✗ football-data xato ({path}): {error}")
        return None


def _short_team(team: dict) -> str:
    return team.get("shortName") or team.get("tla") or team.get("name") or "?"


def get_today_matches() -> list[dict]:
    """Bugungi va ertangi o'yinlar, turnirlar bo'yicha guruhlangan."""
    def _produce():
        if not FOOTBALL_DATA_API_KEY:
            return []
        today = datetime.now(timezone.utc).date()
        params = {
            "dateFrom": today.isoformat(),
            "dateTo": (today + timedelta(days=1)).isoformat(),
            "competitions": ",".join(COMPETITIONS),
        }
        data = _get("/matches", params)
        if not data:
            return []

        groups: dict[str, dict] = {}
        for m in data.get("matches", []):
            code = (m.get("competition") or {}).get("code")
            if code not in COMPETITIONS:
                continue
            score = (m.get("score") or {}).get("fullTime") or {}
            kickoff = m.get("utcDate", "")
            group = groups.setdefault(
                code, {"competition": COMPETITIONS[code], "code": code, "matches": []}
            )
            group["matches"].append({
                "home": _short_team(m.get("homeTeam") or {}),
                "away": _short_team(m.get("awayTeam") or {}),
                "home_crest": (m.get("homeTeam") or {}).get("crest"),
                "away_crest": (m.get("awayTeam") or {}).get("crest"),
                "home_score": score.get("home"),
                "away_score": score.get("away"),
                "status": STATUS_UZ.get(m.get("status"), m.get("status")),
                "is_live": m.get("status") in ("IN_PLAY", "PAUSED"),
                "kickoff": kickoff,
            })
        return list(groups.values())

    groups = _cached("today", 60, _produce)
    uzbek_matches = pfl.get_matches() or api_football.get_matches()
    if uzbek_matches and uzbek_matches.get("matches"):
        groups = [*groups, uzbek_matches]
    return groups


def get_standings(code: str) -> dict | None:
    """Bitta turnirning joriy jadvali."""
    if code == api_football.CODE:
        return pfl.get_standings() or api_football.get_standings()
    if not FOOTBALL_DATA_API_KEY or code not in COMPETITIONS:
        return None

    def _produce():
        data = _get(f"/competitions/{code}/standings")
        if not data:
            return None
        tables = data.get("standings", [])
        total = next((t for t in tables if t.get("type") == "TOTAL"), None)
        if not total:
            return None
        rows = []
        for r in total.get("table", []):
            rows.append({
                "position": r.get("position"),
                "team": _short_team(r.get("team") or {}),
                "crest": (r.get("team") or {}).get("crest"),
                "played": r.get("playedGames"),
                "won": r.get("won"),
                "draw": r.get("draw"),
                "lost": r.get("lost"),
                "points": r.get("points"),
                "goal_diff": r.get("goalDifference"),
            })
        return {
            "competition": COMPETITIONS[code],
            "code": code,
            "source": "football-data.org",
            "table": rows,
        }

    return _cached(f"standings:{code}", 3600, _produce)


def list_competitions() -> list[dict]:
    """Jadval mavjud turnirlar ro'yxati (agar kalit sozlangan bo'lsa)."""
    competitions = (
        [{"code": c, "name": n} for c, n in COMPETITIONS.items()]
        if FOOTBALL_DATA_API_KEY
        else []
    )
    competitions.append({"code": pfl.CODE, "name": pfl.NAME})
    return competitions
