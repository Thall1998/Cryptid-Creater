import unittest

from cryptid_bot.ai import AIQuotaError
from cryptid_bot.bot import build_help_text, extract_title, format_generation_error
from cryptid_bot.discord_utils import split_discord_message


class BotHelperTest(unittest.TestCase):
    def test_extract_title_prefers_structured_output_fields(self):
        self.assertEqual(extract_title("Name: Moss Lantern\nHabitat: bog", "fallback"), "Moss Lantern")
        self.assertEqual(extract_title("Title: The Old Road\nOrigin Story: ...", "fallback"), "The Old Road")
        self.assertEqual(extract_title("Case Number: AR-12\nLocation: woods", "fallback"), "AR-12")
        self.assertEqual(extract_title("unstructured output", "fallback"), "fallback")

    def test_split_discord_message_keeps_chunks_within_limit(self):
        chunks = split_discord_message("x" * 4500)

        self.assertEqual(len(chunks), 3)
        self.assertTrue(all(len(chunk) <= 2000 for chunk in chunks))

    def test_help_text_lists_available_commands(self):
        help_text = build_help_text()

        for command in [
            "/cryptid",
            "/origin",
            "/sighting",
            "/mycryptids",
            "/cryptidstory",
            "/cryptidhelp",
        ]:
            self.assertIn(command, help_text)

    def test_generation_error_uses_safe_ai_error_message(self):
        message = format_generation_error("cryptid entry", AIQuotaError("quota exhausted"))

        self.assertEqual(message, "Could not create a cryptid entry: quota exhausted")

    def test_generation_error_hides_unexpected_exception_details(self):
        message = format_generation_error("cryptid entry", RuntimeError("secret provider payload"))

        self.assertIn("Could not create a cryptid entry", message)
        self.assertIn("bot logs", message)
        self.assertNotIn("secret provider payload", message)


if __name__ == "__main__":
    unittest.main()
