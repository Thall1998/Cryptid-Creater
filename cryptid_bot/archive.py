from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StoryRecord:
    id: int
    discord_user_id: int
    discord_username: str
    command: str
    title: str
    created_at: str


class StoryArchive:
    def __init__(self, database_path: str):
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_user_id INTEGER NOT NULL,
                    discord_username TEXT NOT NULL,
                    command TEXT NOT NULL,
                    title TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    response_text TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stories_user_created
                ON stories (discord_user_id, created_at DESC)
                """
            )

    def save_story(
        self,
        *,
        discord_user_id: int,
        discord_username: str,
        command: str,
        title: str,
        request: dict[str, Any],
        response_text: str,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO stories (
                    discord_user_id,
                    discord_username,
                    command,
                    title,
                    request_json,
                    response_text
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    discord_user_id,
                    discord_username,
                    command,
                    title,
                    json.dumps(request, sort_keys=True),
                    response_text,
                ),
            )
            return int(cursor.lastrowid)

    def list_user_stories(self, discord_user_id: int, limit: int = 5) -> list[StoryRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, discord_user_id, discord_username, command, title, created_at
                FROM stories
                WHERE discord_user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (discord_user_id, limit),
            ).fetchall()

        return [StoryRecord(**dict(row)) for row in rows]

    def get_user_story(self, discord_user_id: int, story_id: int) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT response_text
                FROM stories
                WHERE discord_user_id = ? AND id = ?
                """,
                (discord_user_id, story_id),
            ).fetchone()

        if row is None:
            return None
        return str(row["response_text"])
