"""Small, local-only memory service. Uses only the Python standard library."""

from __future__ import annotations

import argparse
import hmac
import json
import os
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

MAX_BODY_BYTES = 64 * 1024
MAX_CONTENT_CHARS = 4_000
KINDS = {
    "episodic", "semantic", "procedural", "prospective", "goal",
    "inhibitory", "causal", "social", "preference",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def classify_and_score(content: str) -> tuple[str, float, bool, list[str]]:
    """Conservative, inspectable admission baseline; no model or network calls."""
    text = " ".join(content.lower().split())
    reasons: list[str] = []
    if not text:
        return "semantic", 0.0, False, ["empty"]
    patterns = (
        ("prospective", ("remember to", "follow up", "by tomorrow", "next week", "after ")),
        ("inhibitory", ("do not", "don't", "never ", "avoid ", "must not")),
        ("preference", ("i prefer", "i like", "i dislike", "the user prefers", "prefers ")),
        ("goal", ("goal is", "the goal", "objective is", "we need to achieve")),
        ("procedural", ("step 1", "how to", "workflow", "procedure", "always use", "always verify")),
        ("causal", ("because ", "caused by", "resulted in", "led to")),
    )
    kind = "semantic"
    for candidate_kind, phrases in patterns:
        if any(phrase in text for phrase in phrases):
            kind = candidate_kind
            reasons.append(f"matched_{candidate_kind}_pattern")
            break

    transient = any(term in text for term in (
        "just for today", "right now", "for this task only", "temporary note",
        "i am tired", "i'm tired", "currently feeling",
    ))
    durable_signal = any(term in text for term in (
        "always", "never", "prefer", "goal", "deadline", "remember to",
        "follow up", "because", "caused", "workflow", "procedure", "do not",
    ))
    score = 0.25
    if len(text) >= 24:
        score += 0.15
        reasons.append("substantive_length")
    if durable_signal:
        score += 0.35
        reasons.append("durable_signal")
    if kind != "semantic":
        score += 0.20
    if transient and not durable_signal:
        score -= 0.55
        reasons.append("transient_signal")
    score = max(0.0, min(1.0, score))
    admitted = score >= 0.60
    reasons.append("admitted_threshold_met" if admitted else "below_admission_threshold")
    return kind, score, admitted, reasons


class MemoryStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.db = sqlite3.connect(self.path, timeout=3, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        with self._lock:
            self.db.execute("PRAGMA busy_timeout=3000")
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    source_event_id INTEGER REFERENCES events(id),
                    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                    admission_score REAL NOT NULL CHECK(admission_score >= 0 AND admission_score <= 1),
                    status TEXT NOT NULL CHECK(status IN ('active','uncertain','superseded','expired')),
                    created_at TEXT NOT NULL,
                    valid_until TEXT,
                    supersedes_id INTEGER REFERENCES memories(id)
                );
                CREATE INDEX IF NOT EXISTS memories_status_valid ON memories(status, valid_until);
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    item_id INTEGER,
                    detail TEXT NOT NULL DEFAULT '{}'
                );
            """)
            self.db.commit()

    def _audit(self, action: str, outcome: str, item_id: int | None = None, detail: dict | None = None) -> None:
        self.db.execute(
            "INSERT INTO audit_log(occurred_at,action,outcome,item_id,detail) VALUES(?,?,?,?,?)",
            (utc_now(), action, outcome, item_id, json.dumps(detail or {}, separators=(",", ":"))),
        )

    def add_event(self, content: str, source: str, event_type: str = "observation") -> dict:
        if not isinstance(content, str) or not content.strip() or len(content) > MAX_CONTENT_CHARS:
            raise ValueError("content must contain 1 to 4000 characters")
        for value, label, maximum in ((source, "source", 120), (event_type, "event_type", 40)):
            if not isinstance(value, str) or not value.strip() or len(value) > maximum:
                raise ValueError(f"{label} must contain 1 to {maximum} characters")
        with self._lock:
            cur = self.db.execute(
                "INSERT INTO events(occurred_at,event_type,source,content) VALUES(?,?,?,?)",
                (utc_now(), event_type, source, content.strip()),
            )
            event_id = cur.lastrowid
            kind, score, admitted, reasons = classify_and_score(content)
            memory_id = None
            if admitted:
                existing = self.db.execute(
                    "SELECT id FROM memories WHERE content=? AND status='active' LIMIT 1", (content.strip(),)
                ).fetchone()
                if existing:
                    memory_id = existing["id"]
                    reasons.append("duplicate_active_memory")
                else:
                    status = "active" if score >= 0.75 else "uncertain"
                    mcur = self.db.execute("""
                        INSERT INTO memories(kind,content,provenance,source_event_id,confidence,
                            admission_score,status,created_at)
                        VALUES(?,?,?,?,?,?,?,?)
                    """, (kind, content.strip(), source, event_id, score, score, status, utc_now()))
                    memory_id = mcur.lastrowid
            outcome = "admitted" if admitted else "not_admitted"
            self._audit("event_ingest", outcome, event_id, {"memory_id": memory_id, "reason_codes": reasons})
            self.db.commit()
            return {"event_id": event_id, "admitted": admitted, "memory_id": memory_id,
                    "kind": kind, "confidence": score, "reason_codes": reasons}

    def save_candidate(self, content: str, provenance: str, kind: str | None = None,
                       confidence: float | None = None, valid_until: str | None = None) -> dict:
        if not isinstance(content, str) or not content.strip() or len(content) > MAX_CONTENT_CHARS:
            raise ValueError("content must contain 1 to 4000 characters")
        if not isinstance(provenance, str) or not provenance.strip() or len(provenance) > 240:
            raise ValueError("provenance must contain 1 to 240 characters")
        inferred_kind, score, admitted, reasons = classify_and_score(content)
        chosen_kind = kind or inferred_kind
        if chosen_kind not in KINDS:
            raise ValueError("kind is not a supported memory type")
        chosen_confidence = score if confidence is None else confidence
        if isinstance(chosen_confidence, bool) or not isinstance(chosen_confidence, (int, float)) or not 0 <= chosen_confidence <= 1:
            raise ValueError("confidence must be a number from 0 to 1")
        if valid_until is not None:
            try:
                datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                raise ValueError("valid_until must be an ISO 8601 timestamp") from None
        with self._lock:
            if not admitted:
                self._audit("candidate_save", "not_admitted", detail={"reason_codes": reasons})
                self.db.commit()
                return {"admitted": False, "kind": chosen_kind, "confidence": chosen_confidence,
                        "admission_score": score, "reason_codes": reasons}
            duplicate = self.db.execute(
                "SELECT id FROM memories WHERE content=? AND status='active' LIMIT 1", (content.strip(),)
            ).fetchone()
            if duplicate:
                reasons.append("duplicate_active_memory")
                self._audit("candidate_save", "duplicate", duplicate["id"], {"reason_codes": reasons})
                self.db.commit()
                return {"admitted": False, "duplicate": True, "memory_id": duplicate["id"],
                        "reason_codes": reasons}
            status = "active" if chosen_confidence >= 0.75 else "uncertain"
            cur = self.db.execute("""
                INSERT INTO memories(kind,content,provenance,confidence,admission_score,status,created_at,valid_until)
                VALUES(?,?,?,?,?,?,?,?)
            """, (chosen_kind, content.strip(), provenance.strip(), float(chosen_confidence), score,
                  status, utc_now(), valid_until))
            self._audit("candidate_save", "admitted", cur.lastrowid,
                        {"kind": chosen_kind, "reason_codes": reasons})
            self.db.commit()
            return {"admitted": True, "memory_id": cur.lastrowid, "kind": chosen_kind,
                    "confidence": chosen_confidence, "admission_score": score,
                    "status": status, "reason_codes": reasons}

    def search(self, query: str, limit: int = 10) -> list[dict]:
        words = [w for w in query.strip().split() if w]
        if not words:
            raise ValueError("query must not be empty")
        if len(query) > 300:
            raise ValueError("query is too long")
        limit = max(1, min(int(limit), 50))
        # Broad lexical matching is intentional: a task description often uses
        # different words from the stored memory. Rank by confidence and recency.
        clauses = " OR ".join("content LIKE ?" for _ in words[:8])
        params = [f"%{w}%" for w in words[:8]]
        params.extend([utc_now(), limit])
        with self._lock:
            rows = self.db.execute(f"""
                SELECT id,kind,content,provenance,confidence,status,created_at,valid_until
                FROM memories WHERE status IN ('active','uncertain')
                  AND (valid_until IS NULL OR valid_until > ?) AND {clauses}
                ORDER BY confidence DESC, created_at DESC LIMIT ?
            """, [params[-2], *params[:-2], params[-1]]).fetchall()
            result = [dict(row) for row in rows]
            self._audit("memory_search", "ok", detail={"result_count": len(result)})
            self.db.commit()
            return result

    def context(self, task: str, limit: int = 8) -> dict:
        if not task.strip() or len(task) > 500:
            raise ValueError("task must contain 1 to 500 characters")
        words = [w for w in task.split() if len(w) > 2]
        if not words:
            words = task.split()
        matches: list[dict] = []
        if words:
            matches = self.search(" ".join(words[:8]), min(limit, 20))
        with self._lock:
            self._audit("memory_context", "ok", detail={"result_count": len(matches)})
            self.db.commit()
        return {"task": task, "memories": matches,
                "notice": "Retrieved memories are evidence; check provenance and confidence before relying on them."}

    def close(self) -> None:
        with self._lock:
            self.db.close()


def make_handler(store: MemoryStore, token: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "LocalMemory/0.1"
        sys_version = ""

        def log_message(self, fmt: str, *args) -> None:
            # Avoid logging URLs, queries, or request data that may contain personal information.
            return

        def _respond(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _authorized(self) -> bool:
            host = self.headers.get("Host", "").lower()
            if not (host == "localhost" or host.startswith("localhost:") or
                    host == "127.0.0.1" or host.startswith("127.0.0.1:")):
                self._respond(403, {"error": "loopback host required"})
                return False
            if self.headers.get("Origin"):
                self._respond(403, {"error": "browser-origin requests are not supported"})
                return False
            supplied = self.headers.get("Authorization", "")
            if not supplied.startswith("Bearer ") or not hmac.compare_digest(supplied[7:], token):
                self._respond(401, {"error": "valid bearer token required"})
                return False
            return True

        def _body(self) -> dict:
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Content-Type must be application/json")
            raw_length = self.headers.get("Content-Length", "")
            if not raw_length.isdigit() or int(raw_length) > MAX_BODY_BYTES:
                raise ValueError("request body is missing or exceeds 64 KiB")
            raw = self.rfile.read(int(raw_length))
            parsed = json.loads(raw.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise ValueError("JSON body must be an object")
            return parsed

        def do_GET(self) -> None:
            path = urlsplit(self.path)
            if path.path == "/health":
                self._respond(200, {"ok": True, "storage": "local"})
                return
            if not self._authorized():
                return
            try:
                query = parse_qs(path.query)
                if path.path == "/v1/search":
                    items = store.search(query.get("q", [""])[0], int(query.get("limit", [10])[0]))
                    self._respond(200, {"items": items})
                elif path.path == "/v1/context":
                    result = store.context(query.get("task", [""])[0], int(query.get("limit", [8])[0]))
                    self._respond(200, result)
                else:
                    self._respond(404, {"error": "not found"})
            except (ValueError, TypeError) as exc:
                self._respond(400, {"error": str(exc)})
            except Exception:
                self._respond(500, {"error": "request failed"})

        def do_POST(self) -> None:
            if not self._authorized():
                return
            try:
                data = self._body()
                if self.path == "/v1/events":
                    result = store.add_event(data.get("content", ""), data.get("source", ""),
                                             data.get("event_type", "observation"))
                elif self.path == "/v1/memories/candidate":
                    result = store.save_candidate(data.get("content", ""), data.get("provenance", ""),
                                                  data.get("kind"), data.get("confidence"),
                                                  data.get("valid_until"))
                else:
                    self._respond(404, {"error": "not found"})
                    return
                self._respond(201 if result.get("admitted") else 200, result)
            except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                self._respond(400, {"error": str(exc)})
            except Exception:
                self._respond(500, {"error": "request failed"})

    return Handler


def default_db_path() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "AgenticMemory" / "memory.sqlite3"
    return Path.home() / ".local" / "share" / "agentic-memory" / "memory.sqlite3"


def serve(port: int, db_path: str | None = None) -> None:
    token = secrets.token_urlsafe(32)
    store = MemoryStore(db_path or default_db_path())
    server = HTTPServer(("127.0.0.1", port), make_handler(store, token))
    print(f"Local memory service listening at http://127.0.0.1:{server.server_port}")
    print("Bearer token (shown once; keep private): " + token)
    print(f"Database: {store.path}")
    print("Press Ctrl+C to stop. No model or cloud service is started.")
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nStopping local memory service.")
    finally:
        server.server_close()
        store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local-first, low-dependency agent memory service")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db-path", help="SQLite path (defaults to the current user's local data directory)")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    serve(args.port, args.db_path)


if __name__ == "__main__":
    main()
