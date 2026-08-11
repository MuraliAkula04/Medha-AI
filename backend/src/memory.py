import contextlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

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
                last_interaction TEXT,
                opted_out INTEGER DEFAULT 0
            )
            """
        )
        # Migration for existing database tables missing opted_out
        with contextlib.suppress(sqlite3.OperationalError):
            connection.execute(
                "ALTER TABLE users ADD COLUMN opted_out INTEGER DEFAULT 0"
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
                last_interaction,
                opted_out
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            return None

        data = dict(row)
        data["opted_out"] = bool(data.get("opted_out", 0))
        return data


def save_user(
    user_id: str,
    name: str | None = None,
    language_preference: str | None = None,
    current_level: str | None = None,
    topics_covered: str | None = None,
    common_mistakes: str | None = None,
    opted_out: bool | None = None,
):
    now = datetime.now(timezone.utc).isoformat()
    opt_val = 1 if opted_out is True else (0 if opted_out is False else None)

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
                    opted_out = COALESCE(?, opted_out),
                    last_interaction = ?
                WHERE user_id = ?
                """,
                (
                    name,
                    language_preference,
                    current_level,
                    topics_covered,
                    common_mistakes,
                    opt_val,
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
                    last_interaction,
                    opted_out
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    language_preference,
                    current_level,
                    topics_covered,
                    common_mistakes,
                    now,
                    opt_val if opt_val is not None else 0,
                ),
            )

        connection.commit()


def set_opt_out_status(user_id: str, opted_out: bool = True):
    """Set the caller's opt-out status for automated outbound calls."""
    save_user(user_id=user_id, opted_out=opted_out)
