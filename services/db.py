"""SQLite storage. Stores only results and account info. Never stores uploaded files."""
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    pro_until TEXT
);
CREATE TABLE IF NOT EXISTS otp (
    email TEXT PRIMARY KEY,
    code_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    expires_at REAL NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_sent REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    created_at TEXT NOT NULL,
    score INTEGER NOT NULL,
    summary TEXT NOT NULL,
    issues_json TEXT NOT NULL,
    checklist_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audits_email ON audits(email, id DESC);
CREATE TABLE IF NOT EXISTS usage (
    email TEXT NOT NULL,
    feature TEXT NOT NULL,
    month TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (email, feature, month)
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    method TEXT NOT NULL,
    amount INTEGER NOT NULL,
    txn_ref TEXT NOT NULL,
    sender TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    reviewed_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_pay_unique ON payments(method, txn_ref);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    created_at TEXT NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT
);
"""

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def norm_email(email: str) -> str:
    return (email or "").strip().lower()

@contextmanager
def conn():
    folder = os.path.dirname(config.DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    c = sqlite3.connect(config.DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()

def init_db() -> None:
    with conn() as c:
        c.executescript(SCHEMA)

def ensure_user(email: str) -> None:
    email = norm_email(email)
    with conn() as c:
        c.execute("INSERT OR IGNORE INTO users(email, created_at) VALUES (?, ?)", (email, _iso(_now())))

def pro_until(email: str):
    with conn() as c:
        row = c.execute("SELECT pro_until FROM users WHERE email=?", (norm_email(email),)).fetchone()
    if not row or not row["pro_until"]:
        return None
    try:
        dt = datetime.strptime(row["pro_until"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return dt if dt > _now() else None

def is_pro(email: str) -> bool:
    return pro_until(email) is not None

def grant_pro(email: str, days: int) -> datetime:
    email = norm_email(email)
    ensure_user(email)
    start = pro_until(email) or _now()
    end = start + timedelta(days=days)
    with conn() as c:
        c.execute("UPDATE users SET pro_until=? WHERE email=?", (_iso(end), email))
    return end

def _month() -> str:
    return _now().strftime("%Y-%m")

def usage_count(email: str, feature: str) -> int:
    with conn() as c:
        row = c.execute("SELECT count FROM usage WHERE email=? AND feature=? AND month=?", (norm_email(email), feature, _month())).fetchone()
    return row["count"] if row else 0

def bump_usage(email: str, feature: str) -> None:
    with conn() as c:
        c.execute("INSERT INTO usage(email, feature, month, count) VALUES (?,?,?,1) ON CONFLICT(email, feature, month) DO UPDATE SET count = count + 1", (norm_email(email), feature, _month()))

def quota_left(email: str, feature: str):
    if is_pro(email):
        return None
    limit = config.FREE_LIMITS.get(feature, 0)
    return max(0, limit - usage_count(email, feature))

def seconds_until_resend(email: str) -> int:
    with conn() as c:
        row = c.execute("SELECT last_sent FROM otp WHERE email=?", (norm_email(email),)).fetchone()
    if not row:
        return 0
    return max(0, int(config.OTP_RESEND_SECONDS - (time.time() - row["last_sent"])))

def _hash_code(salt: str, code: str) -> str:
    return hashlib.sha256((salt + code).encode()).hexdigest()

def store_otp(email: str, code: str) -> None:
    salt = secrets.token_hex(8)
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO otp(email, code_hash, salt, expires_at, attempts, last_sent) VALUES (?,?,?,?,0,?)", (norm_email(email), _hash_code(salt, code), salt, time.time() + config.OTP_MINUTES * 60, time.time()))

def verify_otp(email: str, code: str):
    email = norm_email(email)
    code = (code or "").strip()
    with conn() as c:
        row = c.execute("SELECT * FROM otp WHERE email=?", (email,)).fetchone()
        if not row:
            return False, "Please ask for a new code."
        if row["attempts"] >= config.OTP_MAX_TRIES:
            return False, "Too many wrong tries. Please ask for a new code."
        if time.time() > row["expires_at"]:
            return False, "This code has expired. Please ask for a new code."
        if hmac.compare_digest(_hash_code(row["salt"], code), row["code_hash"]):
            c.execute("DELETE FROM otp WHERE email=?", (email,))
            ok = True
        else:
            c.execute("UPDATE otp SET attempts = attempts + 1 WHERE email=?", (email,))
            left = config.OTP_MAX_TRIES - row["attempts"] - 1
            return False, f"Wrong code. You have {max(0, left)} tries left."
    if ok:
        ensure_user(email)
    return True, "Verified."

def save_audit(email: str, result: dict) -> int:
    with conn() as c:
        cur = c.execute("INSERT INTO audits(email, created_at, score, summary, issues_json, checklist_json) VALUES (?,?,?,?,?,?)", (norm_email(email), _iso(_now()), int(result.get("readiness_score", 0)), result.get("ai_summary", ""), json.dumps(result.get("issues", []), ensure_ascii=False), json.dumps(result.get("checklist", []), ensure_ascii=False)))
        return cur.lastrowid

def list_audits(email: str, limit: int = 30) -> list:
    with conn() as c:
        rows = c.execute("SELECT * FROM audits WHERE email=? ORDER BY id DESC LIMIT ?", (norm_email(email), limit)).fetchall()
    out = []
    for r in rows:
        out.append({"id": r["id"], "created_at": r["created_at"], "readiness_score": r["score"], "ai_summary": r["summary"], "issues": json.loads(r["issues_json"]), "checklist": json.loads(r["checklist_json"])})
    return out

def delete_user_data(email: str) -> None:
    email = norm_email(email)
    with conn() as c:
        for table in ("audits", "usage", "otp", "payments", "feedback", "users"):
            c.execute(f"DELETE FROM {table} WHERE email=?", (email,))

def add_feedback(email: str, rating: int, comment: str) -> None:
    with conn() as c:
        c.execute("INSERT INTO feedback(email, created_at, rating, comment) VALUES (?,?,?,?)", (norm_email(email), _iso(_now()), int(rating), (comment or "")[:1000]))

def add_payment(email: str, method: str, amount: int, txn_ref: str, sender: str) -> int:
    with conn() as c:
        cur = c.execute("INSERT INTO payments(email, method, amount, txn_ref, sender, created_at) VALUES (?,?,?,?,?,?)", (norm_email(email), method, int(amount), txn_ref.strip().upper(), sender.strip(), _iso(_now())))
        return cur.lastrowid

def list_payments(status: str = None, email: str = None) -> list:
    sql, args = "SELECT * FROM payments WHERE 1=1", []
    if status:
        sql += " AND status=?"
        args.append(status)
    if email:
        sql += " AND email=?"
        args.append(norm_email(email))
    sql += " ORDER BY id DESC LIMIT 100"
    with conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]

def set_payment_status(payment_id: int, status: str) -> None:
    with conn() as c:
        c.execute("UPDATE payments SET status=?, reviewed_at=? WHERE id=? AND status='pending'", (status, _iso(_now()), payment_id))

def get_payment(payment_id: int):
    with conn() as c:
        row = c.execute("SELECT * FROM payments WHERE id=?", (payment_id,)).fetchone()
    return dict(row) if row else None