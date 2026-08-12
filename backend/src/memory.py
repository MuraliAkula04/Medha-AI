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

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ref_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                caller_name TEXT,
                reason TEXT NOT NULL,
                summary TEXT NOT NULL,
                checked_steps TEXT,
                urgency TEXT NOT NULL DEFAULT 'medium',
                language TEXT DEFAULT 'English',
                contact_method TEXT DEFAULT 'Phone Call',
                status TEXT DEFAULT 'Open',
                created_at TEXT NOT NULL
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


def save_escalation(
    ref_id: str,
    user_id: str,
    reason: str,
    summary: str,
    caller_name: str | None = None,
    checked_steps: str | None = None,
    urgency: str = "medium",
    language: str = "English",
    contact_method: str = "Phone Call",
) -> dict:
    """Save a new human escalation request to SQLite database."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO escalations (
                ref_id, user_id, caller_name, reason, summary,
                checked_steps, urgency, language, contact_method, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)
            """,
            (
                ref_id,
                user_id,
                caller_name or "Anonymous Student",
                reason,
                summary,
                checked_steps
                or "Agent verified learning materials and basic explanation.",
                urgency.lower(),
                language,
                contact_method,
                now,
            ),
        )
        connection.commit()

    return {
        "ref_id": ref_id,
        "user_id": user_id,
        "caller_name": caller_name or "Anonymous Student",
        "reason": reason,
        "summary": summary,
        "checked_steps": checked_steps or "Agent verified learning materials.",
        "urgency": urgency.lower(),
        "language": language,
        "contact_method": contact_method,
        "status": "Open",
        "created_at": now,
    }


def get_escalations(
    user_id: str | None = None, status: str | None = None
) -> list[dict]:
    """Retrieve escalation requests filtered optionally by user_id or status."""
    query = "SELECT * FROM escalations WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def update_escalation_status(ref_id: str, status: str) -> bool:
    """Update the status of an escalation ticket (Open, In Progress, Resolved)."""
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE escalations SET status = ? WHERE ref_id = ?",
            (status, ref_id),
        )
        connection.commit()
        return cursor.rowcount > 0
