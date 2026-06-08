import unittest
from types import SimpleNamespace
from unittest.mock import patch

from google.genai import errors

from cryptid_bot.ai import AIQuotaError, AIServiceError, CryptidStoryAI


class FakeModels:
    def __init__(self, text: str, error: Exception | None = None):
        self.text = text
        self.error = error
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.text)


class FakeGeminiClient:
    def __init__(self, text: str, error: Exception | None = None):
        self.models = FakeModels(text, error=error)


class CryptidStoryAITest(unittest.TestCase):
    def test_create_origin_uses_gemini_and_origin_story_prompt(self):
        fake_client = FakeGeminiClient("Title: The Toll Road\nOrigin Story: It waits.")
        settings = SimpleNamespace(gemini_api_key="test-key", gemini_model="gemini-2.0-flash")

        with patch("cryptid_bot.ai.genai.Client", return_value=fake_client) as client_factory:
            ai = CryptidStoryAI(settings)
            result = ai.create_origin(name="Road Warden", details="seen near mile marker 13")

        self.assertEqual(result, "Title: The Toll Road\nOrigin Story: It waits.")
        client_factory.assert_called_once_with(api_key="test-key")

        call = fake_client.models.calls[0]
        self.assertEqual(call["model"], "gemini-2.0-flash")
        self.assertIn("name: Road Warden", call["contents"])
        self.assertIn("details: seen near mile marker 13", call["contents"])
        self.assertIn("Write a short origin story", call["config"].system_instruction)

    def test_empty_gemini_response_raises_clear_error(self):
        fake_client = FakeGeminiClient("")
        settings = SimpleNamespace(gemini_api_key="test-key", gemini_model="gemini-2.0-flash")

        with patch("cryptid_bot.ai.genai.Client", return_value=fake_client):
            ai = CryptidStoryAI(settings)
            with self.assertRaisesRegex(RuntimeError, "Gemini returned an empty response"):
                ai.create_origin(name="Road Warden", details="seen near mile marker 13")

    def test_quota_error_is_translated_to_user_safe_message(self):
        quota_error = errors.ClientError(
            429,
            {
                "error": {
                    "code": 429,
                    "message": "Quota exceeded for metric generate_content_free_tier_requests",
                    "status": "RESOURCE_EXHAUSTED",
                }
            },
        )
        fake_client = FakeGeminiClient("", error=quota_error)
        settings = SimpleNamespace(gemini_api_key="test-key", gemini_model="gemini-2.0-flash")

        with patch("cryptid_bot.ai.genai.Client", return_value=fake_client):
            ai = CryptidStoryAI(settings)
            with self.assertRaisesRegex(AIQuotaError, "AI service quota is exhausted"):
                ai.create_origin(name="Road Warden", details="seen near mile marker 13")

    def test_non_quota_api_error_is_translated_to_user_safe_message(self):
        api_error = errors.ServerError(
            500,
            {
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "status": "INTERNAL",
                }
            },
        )
        fake_client = FakeGeminiClient("", error=api_error)
        settings = SimpleNamespace(gemini_api_key="test-key", gemini_model="gemini-2.0-flash")

        with patch("cryptid_bot.ai.genai.Client", return_value=fake_client):
            ai = CryptidStoryAI(settings)
            with self.assertRaisesRegex(AIServiceError, "could not generate a response"):
                ai.create_origin(name="Road Warden", details="seen near mile marker 13")


if __name__ == "__main__":
    unittest.main()
