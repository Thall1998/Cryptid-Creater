import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptid_bot.archive import StoryArchive


class StoryArchiveTest(unittest.TestCase):
    def test_saves_and_loads_only_the_requesting_users_story(self):
        with TemporaryDirectory() as temp_dir:
            archive = StoryArchive(str(Path(temp_dir) / "stories.sqlite3"))
            story_id = archive.save_story(
                discord_user_id=123,
                discord_username="cryptid_user",
                command="cryptid",
                title="The Test Thing",
                request={"idea": "test"},
                response_text="Name: The Test Thing\nStory text",
            )

            records = archive.list_user_stories(123)

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].id, story_id)
            self.assertEqual(records[0].discord_user_id, 123)
            self.assertEqual(archive.get_user_story(123, story_id), "Name: The Test Thing\nStory text")
            self.assertIsNone(archive.get_user_story(456, story_id))


if __name__ == "__main__":
    unittest.main()
