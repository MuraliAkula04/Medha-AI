import sqlite3
from pathlib import Path
from datetime import datetime, timezone


DB_PATH = Path(__file__).resolve().parent / "medha_memory.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                language_preference TEXT,
                current_level TEXT,
                topics_covered TEXT,
                common_mistakes TEXT,
                last_interaction TEXT
            )
            """
        )
        connection.commit()


def get_user(user_id: str):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                user_id,
                name,
                language_preference,
                current_level,
                topics_covered,
                common_mistakes,
                last_interaction
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)


def save_user(
    user_id: str,
    name: str | None = None,
    language_preference: str | None = None,
    current_level: str | None = None,
    topics_covered: str | None = None,
    common_mistakes: str | None = None,
):
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if existing:
            connection.execute(
                """
                UPDATE users
                SET
                    name = COALESCE(?, name),
                    language_preference = COALESCE(?, language_preference),
                    current_level = COALESCE(?, current_level),
                    topics_covered = COALESCE(?, topics_covered),
                    common_mistakes = COALESCE(?, common_mistakes),
                    last_interaction = ?
                WHERE user_id = ?
                """,
                (
                    name,
                    language_preference,
                    current_level,
                    topics_covered,
                    common_mistakes,
                    now,
                    user_id,
                ),
            )
        else:
            connection.execute(
                """
                INSERT INTO users (
                    user_id,
                    name,
                    language_preference,
                    current_level,
                    topics_covered,
                    common_mistakes,
                    last_interaction
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    language_preference,
                    current_level,
                    topics_covered,
                    common_mistakes,
                    now,
                ),
            )

        connection.commit()