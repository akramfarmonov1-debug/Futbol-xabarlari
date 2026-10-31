import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.bot.bot import (
    article_buttons,
    cmd_legionnaires,
    cmd_scores,
    handle_table_callback,
)


class BotHandlersTests(unittest.IsolatedAsyncioTestCase):
    async def test_cmd_scores_calls_today_endpoint_and_formats_groups(self):
        message = MagicMock()
        message.answer = AsyncMock()

        sample_groups = [
            {
                "competition": "Angliya Premyer-ligasi",
                "code": "PL",
                "matches": [
                    {
                        "home": "Arsenal",
                        "away": "Chelsi",
                        "home_score": 2,
                        "away_score": 1,
                        "status": "Tugadi",
                        "is_live": False,
                    }
                ],
            }
        ]

        with patch("app.bot.bot.api_get", new=AsyncMock(return_value=sample_groups)) as mock_get:
            await cmd_scores(message)

        mock_get.assert_awaited_once_with("/api/scores/today")
        message.answer.assert_awaited_once()
        sent_text = message.answer.await_args.args[0]
        self.assertIn("Angliya Premyer-ligasi", sent_text)
        self.assertIn("Arsenal", sent_text)
        self.assertIn("2 : 1", sent_text)

    async def test_handle_table_callback_uses_path_param_and_team_field(self):
        callback = MagicMock()
        callback.data = "table:UZB"
        callback.answer = AsyncMock()
        callback.message = MagicMock()
        callback.message.answer = AsyncMock()

        sample_standings = {
            "competition": "O'zbekiston Superligasi",
            "code": "UZB",
            "table": [
                {"position": 1, "team": "Nasaf", "points": 52, "played": 24},
                {"position": 2, "team": "Paxtakor", "points": 48, "played": 24},
            ],
        }

        with patch("app.bot.bot.api_get", new=AsyncMock(return_value=sample_standings)) as mock_get:
            await handle_table_callback(callback)

        mock_get.assert_awaited_once_with("/api/scores/standings/UZB")
        callback.answer.assert_awaited_once()
        sent_text = callback.message.answer.await_args.args[0]
        self.assertIn("O&#x27;zbekiston Superligasi", sent_text)
        self.assertIn("Nasaf", sent_text)

    async def test_cmd_legionnaires_handles_list_response(self):
        message = MagicMock()
        message.answer = AsyncMock()

        sample_legionnaires = [
            {
                "id": "khusanov",
                "name": "Abduqodir Husanov",
                "club": "Lans (RC Lens)",
                "league": "Ligue 1 (Fransiya)",
                "country_flag": "🇫🇷",
                "position": "Markaziy himoyachi",
                "market_value": "€12.0M",
                "recent_articles": [
                    {"id": 1, "title": "Husanov asosiy tarkibda tushdi", "slug": "husanov-asosiy"}
                ],
            }
        ]

        with patch("app.bot.bot.api_get", new=AsyncMock(return_value=sample_legionnaires)) as mock_get:
            await cmd_legionnaires(message)

        mock_get.assert_awaited_once_with("/api/legionnaires")
        message.answer.assert_awaited_once()
        sent_text = message.answer.await_args.args[0]
        self.assertIn("Abduqodir Husanov", sent_text)
        self.assertIn("Husanov asosiy tarkibda tushdi", sent_text)

    def test_article_buttons_caps_callback_data_under_64_bytes(self):
        long_slug = "a" * 150
        markup = article_buttons({"slug": long_slug, "original_url": "https://example.com"})
        save_btn = markup.inline_keyboard[1][0]
        self.assertLessEqual(len(save_btn.callback_data.encode("utf-8")), 64)


if __name__ == "__main__":
    unittest.main()
