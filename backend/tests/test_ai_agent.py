import json
import os
import unittest
from unittest.mock import MagicMock, patch

import httpx

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.services import ai_agent  # noqa: E402


def _sample_analysis(**overrides):
    data = {
        "kategoriya": "premyer-liga",
        "sarlavha": "Arsenal muhim g'alabaga erishdi",
        "seo_sarlavha": "Arsenal APLda muhim g'alabaga erishdi",
        "xulosa": "Arsenal o'z maydonida g'alaba qozondi.",
        "maqola": "Arsenal safar uchrashuvida 2:0 hisobida zafar quchdi.",
        "amaliy_ahamiyat": "Turnir jadvalidagi o'rin mustahkamlandi.",
        "teglar": ["Arsenal", "APL"],
        "ahamiyati": 3,
        "entities": ["Arsenal"],
        "facts": [
            {
                "subject": "Arsenal",
                "predicate": "won",
                "value": "2-0",
                "evidence": "Arsenal won 2-0",
            }
        ],
        "event_key": "arsenal-win-2-0",
        "football_confidence": 95,
        "category_confidence": 92,
        "fact_confidence": 94,
        "baho_sababi": "Top-liga uchrashuvi natijasi.",
    }
    data.update(overrides)
    return data


def _mock_response(status_code: int, body: dict | str):
    resp = MagicMock()
    resp.status_code = status_code
    if isinstance(body, dict):
        resp.json.return_value = body
        resp.text = json.dumps(body)
    else:
        resp.text = body
    return resp


class ExtractResponseTextTests(unittest.TestCase):
    def test_extract_response_text_skips_thought_parts(self):
        data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"thought": True, "text": "internal reasoning"},
                            {"text": '{"ok": true}'},
                        ]
                    }
                }
            ]
        }

        text = ai_agent._extract_response_text(data, "Gemini")

        self.assertEqual(text, '{"ok": true}')


class GeminiFallbackTests(unittest.TestCase):
    def test_analyze_with_gemini_falls_back_on_503(self):
        payload_text = json.dumps(_sample_analysis())
        calls = []

        def fake_post(url, json=None, headers=None, timeout=None):
            calls.append((url, timeout))
            if "gemini-3.8-flash:" in url:
                return _mock_response(503, "Service Unavailable")
            return _mock_response(
                200,
                {"candidates": [{"content": {"parts": [{"text": payload_text}]}}]},
            )

        with (
            patch.object(ai_agent, "GEMINI_API_KEY", "test-key"),
            patch.object(ai_agent, "GEMINI_MODEL", "gemini-3.8-flash"),
            patch.object(
                ai_agent,
                "GEMINI_FALLBACK_MODELS",
                ("gemini-4-hydrogen", "gemini-3.5-flash-lite"),
            ),
            patch.object(ai_agent.time, "sleep") as sleep_mock,
            patch.object(ai_agent.httpx, "post", side_effect=fake_post),
        ):
            result = ai_agent._analyze_with_gemini("Arsenal won 2-0")

        self.assertEqual(result["sarlavha"], "Arsenal muhim g'alabaga erishdi")
        self.assertEqual(len(calls), 2)
        self.assertIn("gemini-3.8-flash:generateContent", calls[0][0])
        self.assertIn("gemini-4-hydrogen:generateContent", calls[1][0])
        self.assertEqual(calls[0][1], 60)
        sleep_mock.assert_called_once_with(1)

    def test_analyze_with_gemini_falls_back_on_timeout(self):
        payload_text = json.dumps(_sample_analysis())
        calls = []

        def fake_post(url, json=None, headers=None, timeout=None):
            calls.append(url)
            if "gemini-3.8-flash:" in url:
                raise httpx.ReadTimeout("timed out")
            return _mock_response(
                200,
                {"candidates": [{"content": {"parts": [{"text": payload_text}]}}]},
            )

        with (
            patch.object(ai_agent, "GEMINI_API_KEY", "test-key"),
            patch.object(ai_agent, "GEMINI_MODEL", "gemini-3.8-flash"),
            patch.object(
                ai_agent,
                "GEMINI_FALLBACK_MODELS",
                ("gemini-4-hydrogen", "gemini-3.5-flash-lite"),
            ),
            patch.object(ai_agent.time, "sleep") as sleep_mock,
            patch.object(ai_agent.httpx, "post", side_effect=fake_post),
        ):
            result = ai_agent._analyze_with_gemini("Arsenal won 2-0")

        self.assertEqual(result["kategoriya"], "premyer-liga")
        self.assertEqual(len(calls), 2)
        sleep_mock.assert_called_once_with(1)


class GeminiKeyRotationTests(unittest.TestCase):
    def test_rotates_to_next_api_key_on_429(self):
        payload_text = json.dumps(_sample_analysis())
        used_keys = []

        def fake_post(url, json=None, headers=None, timeout=None):
            used_keys.append(headers["x-goog-api-key"])
            if headers["x-goog-api-key"] == "key-0":
                return _mock_response(429, "quota exceeded")
            return _mock_response(
                200,
                {"candidates": [{"content": {"parts": [{"text": payload_text}]}}]},
            )

        with (
            patch.object(ai_agent, "GEMINI_API_KEY", "key-0"),
            patch.object(ai_agent, "GEMINI_EXTRA_API_KEYS", ("key-1", "key-0")),
            patch.object(ai_agent, "GEMINI_MODEL", "gemini-3.8-flash"),
            patch.object(ai_agent, "GEMINI_FALLBACK_MODELS", ("gemini-4-hydrogen",)),
            patch.object(ai_agent.time, "sleep"),
            patch.object(ai_agent, "safe_print"),
            patch.object(ai_agent.httpx, "post", side_effect=fake_post),
        ):
            result = ai_agent._analyze_with_gemini("Arsenal won 2-0")

        self.assertEqual(used_keys, ["key-0", "key-1"])
        self.assertEqual(result["kategoriya"], "premyer-liga")


class VertexToGeminiFallbackTests(unittest.TestCase):
    def test_analyze_news_falls_back_from_vertex_to_gemini_when_key_present(self):
        sample = _sample_analysis()
        with (
            patch.object(ai_agent, "AI_PROVIDER", "vertex"),
            patch.object(ai_agent, "GEMINI_API_KEY", "test-key"),
            patch.object(
                ai_agent,
                "_analyze_with_vertex",
                side_effect=RuntimeError("403 billing disabled"),
            ),
            patch.object(
                ai_agent, "_analyze_with_gemini", return_value=sample
            ) as gemini_mock,
            patch.object(ai_agent, "safe_print") as print_mock,
        ):
            result = ai_agent.analyze_news("Title", "Arsenal won 2-0", "https://x.uz", "BBC")

        gemini_mock.assert_called_once()
        print_mock.assert_called_once()
        self.assertEqual(result["kategoriya"], "premyer-liga")
        self.assertEqual(result["ahamiyati"], 3)

    def test_analyze_news_reraises_vertex_error_when_no_gemini_key(self):
        with (
            patch.object(ai_agent, "AI_PROVIDER", "vertex"),
            patch.object(ai_agent, "GEMINI_API_KEY", ""),
            patch.object(
                ai_agent,
                "_analyze_with_vertex",
                side_effect=RuntimeError("403 billing disabled"),
            ),
        ):
            with self.assertRaises(RuntimeError):
                ai_agent.analyze_news("Title", "Content")


class PromptContractTests(unittest.TestCase):
    def test_system_prompt_specifies_0_to_100_confidence_scale(self):
        for field in ("football_confidence", "category_confidence", "fact_confidence"):
            self.assertIn(field, ai_agent.SYSTEM_PROMPT)
        self.assertIn("0 dan 100 gacha", ai_agent.SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
