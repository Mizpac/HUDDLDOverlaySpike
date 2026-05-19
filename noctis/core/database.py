import sqlite3
import json
import os
from datetime import datetime
from config import DB_PATH


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), "../schema/schema.sql")
    with open(schema_path, "r") as f:
        schema = f.read()
    with get_connection() as conn:
        conn.executescript(schema)


# ── Activity log ──────────────────────────────────────────────

def log_activity(action: str, detail: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO activity_log (action, detail, status) VALUES (?, ?, 'running')",
            (action, detail),
        )
        return cur.lastrowid


def complete_activity(log_id: int, api_calls: int = 0, status: str = "completed"):
    with get_connection() as conn:
        conn.execute(
            "UPDATE activity_log SET status=?, api_calls_used=?, completed_at=? WHERE id=?",
            (status, api_calls, datetime.now(), log_id),
        )


def get_recent_activity(limit: int = 10) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM activity_log ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_daily_api_calls() -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(api_calls_used), 0) as total FROM activity_log "
            "WHERE DATE(started_at) = DATE('now')"
        ).fetchone()
        return row["total"]


# ── Niches ────────────────────────────────────────────────────

def create_niche(name: str, keywords: list, notes: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO niches (name, keywords, notes) VALUES (?, ?, ?)",
            (name, json.dumps(keywords), notes),
        )
        return cur.lastrowid


def get_all_niches() -> list:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM niches ORDER BY created_at DESC").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["keywords"] = json.loads(d["keywords"]) if d["keywords"] else []
            result.append(d)
        return result


def get_niche(niche_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM niches WHERE id=?", (niche_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["keywords"] = json.loads(d["keywords"]) if d["keywords"] else []
        return d


def update_niche_status(niche_id: int, status: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE niches SET status=?, updated_at=? WHERE id=?",
            (status, datetime.now(), niche_id),
        )


def update_niche_score(niche_id: int, score: float, confidence: float):
    with get_connection() as conn:
        conn.execute(
            "UPDATE niches SET score=?, confidence=?, updated_at=? WHERE id=?",
            (score, confidence, datetime.now(), niche_id),
        )


def get_pipeline_counts() -> dict:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM niches GROUP BY status"
        ).fetchall()
        counts = {r["status"]: r["count"] for r in rows}
        return {
            "collecting": counts.get("collecting", 0),
            "calibrating": counts.get("calibrating", 0),
            "validated": counts.get("validated", 0),
            "blocked": counts.get("blocked", 0),
            "in_progress": counts.get("in_progress", 0),
            "listed": counts.get("listed", 0),
            "archived": counts.get("archived", 0),
        }


# ── Samples & Listings ────────────────────────────────────────

def create_sample(niche_id: int, sample_type: str, query_variant: str, sort_on: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO samples (niche_id, sample_type, query_variant, sort_on) VALUES (?,?,?,?)",
            (niche_id, sample_type, query_variant, sort_on),
        )
        return cur.lastrowid


def save_listings(sample_id: int, listings: list):
    with get_connection() as conn:
        for l in listings:
            conn.execute(
                """INSERT OR IGNORE INTO listings
                   (sample_id, etsy_listing_id, title, price, currency, tags,
                    views, num_favorers, quantity, shop_id, creation_timestamp)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    sample_id,
                    l.get("listing_id"),
                    l.get("title"),
                    l.get("price", {}).get("amount", 0) / max(l.get("price", {}).get("divisor", 1), 1),
                    l.get("price", {}).get("currency_code"),
                    json.dumps(l.get("tags", [])),
                    l.get("views", 0),
                    l.get("num_favorers", 0),
                    l.get("quantity", 0),
                    l.get("shop_id"),
                    l.get("creation_tsz"),
                ),
            )
        conn.execute(
            "UPDATE samples SET listing_count=? WHERE id=?",
            (len(listings), sample_id),
        )


def get_samples_for_niche(niche_id: int) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM samples WHERE niche_id=? ORDER BY collected_at",
            (niche_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_listings_for_sample(sample_id: int) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM listings WHERE sample_id=?", (sample_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["tags"] = json.loads(d["tags"]) if d["tags"] else []
            result.append(d)
        return result


# ── Flags ─────────────────────────────────────────────────────

def create_flag(item_type: str, item_id: int, flag_type: str, message: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO flags (item_type, item_id, flag_type, message) VALUES (?,?,?,?)",
            (item_type, item_id, flag_type, message),
        )


def get_open_flags() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM flags WHERE resolved=FALSE ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def resolve_flag(flag_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE flags SET resolved=TRUE, resolved_at=? WHERE id=?",
            (datetime.now(), flag_id),
        )


# ── Dream Lab ─────────────────────────────────────────────────

def create_dream_session(title: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO dream_lab_sessions (title) VALUES (?)", (title,)
        )
        return cur.lastrowid


def save_dream_messages(session_id: int, messages: list):
    with get_connection() as conn:
        conn.execute(
            "UPDATE dream_lab_sessions SET messages=?, updated_at=? WHERE id=?",
            (json.dumps(messages), datetime.now(), session_id),
        )


def get_dream_sessions() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM dream_lab_sessions ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_dream_session(session_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM dream_lab_sessions WHERE id=?", (session_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["messages"] = json.loads(d["messages"]) if d["messages"] else []
        return d


def stage_idea(session_id: int, idea_text: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO staged_ideas (session_id, idea_text) VALUES (?,?)",
            (session_id, idea_text),
        )
        return cur.lastrowid


def get_staged_ideas(session_id: int) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM staged_ideas WHERE session_id=? AND status='staged'",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def promote_idea_to_pipeline(idea_id: int, niche_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE staged_ideas SET status='promoted', niche_id=? WHERE id=?",
            (niche_id, idea_id),
        )
