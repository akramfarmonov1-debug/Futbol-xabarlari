"""PFL.UZ rasmiy web API orqali O'zbekiston Superligasi ma'lumotlari."""

import time
from datetime import datetime, timedelta, timezone
from typing import Callable

import httpx

BASE_URL = "https://api.pfl.uz/v1/web"
CODE = "UZB"
NAME = "O'zbekiston Superligasi"

_cache: dict[str, tuple[float, object]] = {}


def _cached(key: str, ttl: int, producer: Callable):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = producer()
    if value is not None:
        _cache[key] = (now, value)
    return value


def _get(path: str, params: dict | None = None) -> dict | list | None:
    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(
                f"{BASE_URL}{path}",
                params=params,
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
        payload = response.json()
        if payload.get("statusCode") != 200:
            print(f"  PFL.UZ xato ({path}): {payload.get('messages')}")
            return None
        return payload.get("data")
    except (httpx.HTTPError, ValueError, TypeError) as error:
        print(f"  PFL.UZ xato ({path}): {error}")
        return None


def _context() -> tuple[int, int, int] | None:
    """Superliga turnir ID, faol mavsum ID va yilini qaytaradi."""

    def _produce():
        data = _get("/game/options")
        if not isinstance(data, dict):
            return None

        tournament = next(
            (
                row
                for row in data.get("tournaments") or []
                if row.get("id") == 1 or row.get("title") == "Superliga"
            ),
            None,
        )
        seasons = data.get("seasons") or []
        season = next((row for row in seasons if row.get("isActive")), None)
        if not tournament or not season:
            return None
        return int(tournament["id"]), int(season["id"]), int(season["year"])

    return _cached("pfl:context", 24 * 60 * 60, _produce)


def get_standings() -> dict | None:
    """Joriy Superliga turnir jadvalini bir soatlik kesh bilan qaytaradi."""

    def _produce():
        context = _context()
        if not context:
            return None
        tournament_id, season_id, season_year = context
        data = _get(
            "/game/table",
            {"tournamentId": tournament_id, "seasonId": season_id},
        )
        if not isinstance(data, dict):
            return None

        raw_table = data.get("table") or []
        if raw_table and isinstance(raw_table[0].get("list"), list):
            general = next(
                (
                    group
                    for group in raw_table
                    if (group.get("title") or "").lower() == "umumiy"
                ),
                raw_table[0],
            )
            raw_table = general.get("list") or []
        if not raw_table:
            return None

        rows = []
        for position, row in enumerate(raw_table, start=1):
            rows.append(
                {
                    "position": position,
                    "team": row.get("title") or row.get("titleEn") or "?",
                    "crest": row.get("logo"),
                    "played": row.get("c_games"),
                    "won": row.get("c_games_vic"),
                    "draw": row.get("c_games_drw"),
                    "lost": row.get("c_games_def"),
                    "points": row.get("c_point"),
                    "goal_diff": row.get("c_goal_tf"),
                }
            )

        return {
            "competition": NAME,
            "code": CODE,
            "season": (data.get("season") or {}).get("year") or season_year,
            "source": "PFL.UZ",
            "table": rows,
        }

    return _cached("pfl:standings", 60 * 60, _produce)


def _match_status(kickoff: datetime, home_score, away_score) -> tuple[str, bool]:
    now = datetime.now(timezone.utc)
    if kickoff > now:
        return "Rejalashtirilgan", False
    if kickoff + timedelta(hours=3) >= now:
        return "Jonli", True
    if home_score is not None and away_score is not None:
        return "Tugadi", False
    return "Vaqti belgilanmoqda", False


def get_matches() -> dict | None:
    """Bugungi va ertangi Superliga uchrashuvlarini qaytaradi."""

    def _produce():
        context = _context()
        if not context:
            return None
        tournament_id, season_id, _ = context
        data = _get(
            "/game/calendar",
            {"tournamentId": tournament_id, "seasonId": season_id},
        )
        if not isinstance(data, dict):
            return None

        today = datetime.now(timezone.utc).date()
        last_day = today + timedelta(days=1)
        matches = []
        for tour in data.get("table") or []:
            for match in tour.get("matches") or []:
                raw_kickoff = match.get("startDate")
                if not raw_kickoff:
                    continue
                try:
                    kickoff = datetime.fromisoformat(
                        raw_kickoff.replace("Z", "+00:00")
                    )
                except ValueError:
                    continue
                if kickoff.date() < today or kickoff.date() > last_day:
                    continue

                home = match.get("homeTeam") or {}
                away = match.get("awayTeam") or {}
                home_club = home.get("club") or {}
                away_club = away.get("club") or {}
                home_score = match.get("homeGoal")
                away_score = match.get("awayGoal")
                status, is_live = _match_status(
                    kickoff, home_score, away_score
                )
                matches.append(
                    {
                        "home": (
                            home.get("title")
                            or home_club.get("title")
                            or "?"
                        ),
                        "away": (
                            away.get("title")
                            or away_club.get("title")
                            or "?"
                        ),
                        "home_crest": home_club.get("logo"),
                        "away_crest": away_club.get("logo"),
                        "home_score": home_score,
                        "away_score": away_score,
                        "status": status,
                        "is_live": is_live,
                        "kickoff": raw_kickoff,
                    }
                )

        return {
            "competition": NAME,
            "code": CODE,
            "matches": matches,
        }

    return _cached("pfl:matches", 15 * 60, _produce)
