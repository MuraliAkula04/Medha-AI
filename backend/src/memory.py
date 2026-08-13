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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT UNIQUE NOT NULL,
                room_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                caller_name TEXT DEFAULT 'Anonymous Student',
                channel TEXT NOT NULL DEFAULT 'browser',
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                outcome TEXT NOT NULL DEFAULT 'failure',
                failure_reason TEXT,
                topic TEXT DEFAULT 'General Learning',
                exercises_completed INTEGER DEFAULT 0,
                concept_lookups INTEGER DEFAULT 0,
                first_response_latency_ms INTEGER DEFAULT 0,
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


def save_call_log(
    call_id: str,
    room_name: str,
    user_id: str,
    channel: str = "browser",
    start_time: str | None = None,
    end_time: str | None = None,
    duration_seconds: int = 0,
    outcome: str = "failure",
    failure_reason: str | None = None,
    topic: str = "General Learning",
    exercises_completed: int = 0,
    concept_lookups: int = 0,
    first_response_latency_ms: int = 0,
    caller_name: str | None = None,
) -> dict:
    """Record the outcome of a voice call session into SQLite database."""
    now = datetime.now(timezone.utc).isoformat()
    st = start_time or now
    et = end_time or now

    # Fetch user name if not explicitly provided
    if not caller_name:
        user = get_user(user_id)
        caller_name = (user.get("name") if user else None) or "Anonymous Student"

    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO call_logs (
                call_id, room_name, user_id, caller_name, channel,
                start_time, end_time, duration_seconds, outcome,
                failure_reason, topic, exercises_completed, concept_lookups,
                first_response_latency_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                call_id,
                room_name,
                user_id,
                caller_name,
                channel.lower(),
                st,
                et,
                max(0, int(duration_seconds)),
                outcome.lower(),
                failure_reason,
                topic,
                int(exercises_completed),
                int(concept_lookups),
                int(first_response_latency_ms),
                now,
            ),
        )
        connection.commit()

    return {
        "call_id": call_id,
        "room_name": room_name,
        "user_id": user_id,
        "caller_name": caller_name,
        "channel": channel.lower(),
        "start_time": st,
        "end_time": et,
        "duration_seconds": duration_seconds,
        "outcome": outcome.lower(),
        "failure_reason": failure_reason,
        "topic": topic,
        "exercises_completed": exercises_completed,
        "concept_lookups": concept_lookups,
        "first_response_latency_ms": first_response_latency_ms,
        "created_at": now,
    }


def get_call_logs(limit: int = 50) -> list[dict]:
    """Retrieve recent call logs sorted by created_at DESC."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM call_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_call_analytics() -> dict:
    """Retrieve aggregated call analytics metrics for Day 8 dashboard."""
    with get_connection() as connection:
        total_calls = (
            connection.execute("SELECT COUNT(*) FROM call_logs").fetchone()[0] or 0
        )
        successful_calls = (
            connection.execute(
                "SELECT COUNT(*) FROM call_logs WHERE outcome = 'success'"
            ).fetchone()[0]
            or 0
        )
        failed_calls = (
            connection.execute(
                "SELECT COUNT(*) FROM call_logs WHERE outcome = 'failure'"
            ).fetchone()[0]
            or 0
        )

        success_rate = (
            round((successful_calls / total_calls) * 100, 1) if total_calls > 0 else 0.0
        )

        total_exercises = (
            connection.execute(
                "SELECT COALESCE(SUM(exercises_completed), 0) FROM call_logs"
            ).fetchone()[0]
            or 0
        )

        total_concept_lookups = (
            connection.execute(
                "SELECT COALESCE(SUM(concept_lookups), 0) FROM call_logs"
            ).fetchone()[0]
            or 0
        )

        avg_duration = (
            connection.execute(
                "SELECT COALESCE(AVG(duration_seconds), 0) FROM call_logs"
            ).fetchone()[0]
            or 0.0
        )

        avg_latency = (
            connection.execute(
                "SELECT COALESCE(AVG(first_response_latency_ms), 0) FROM call_logs WHERE first_response_latency_ms > 0"
            ).fetchone()[0]
            or 0.0
        )

        # Channel counts
        browser_calls = (
            connection.execute(
                "SELECT COUNT(*) FROM call_logs WHERE channel = 'browser'"
            ).fetchone()[0]
            or 0
        )
        sip_calls = (
            connection.execute(
                "SELECT COUNT(*) FROM call_logs WHERE channel = 'sip'"
            ).fetchone()[0]
            or 0
        )

        # Failure reasons breakdown
        failure_rows = connection.execute(
            """
            SELECT failure_reason, COUNT(*) as count
            FROM call_logs
            WHERE outcome = 'failure' AND failure_reason IS NOT NULL
            GROUP BY failure_reason
            """
        ).fetchall()
        failure_types = {r["failure_reason"]: r["count"] for r in failure_rows}

        recent_calls = get_call_logs(limit=20)

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": success_rate,
            "total_exercises": total_exercises,
            "total_concept_lookups": total_concept_lookups,
            "avg_duration_seconds": round(avg_duration, 1),
            "avg_latency_ms": round(avg_latency, 1),
            "channels": {
                "browser": browser_calls,
                "sip": sip_calls,
            },
            "failure_types": failure_types,
            "recent_calls": recent_calls,
        }
