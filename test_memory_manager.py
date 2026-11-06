import json
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from memory_manager import MemoryStore, make_handler


class MemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.store = MemoryStore(Path(self.temp.name) / "memory.sqlite3")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_event_admission_and_provenance(self):
        result = self.store.add_event(
            "I prefer concise technical explanations in future conversations.", "user_chat"
        )
        self.assertTrue(result["admitted"])
        records = self.store.search("concise technical explanations")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["kind"], "preference")
        self.assertEqual(records[0]["provenance"], "user_chat")

    def test_transient_event_is_archived_but_not_admitted(self):
        result = self.store.add_event("I am tired right now.", "user_chat")
        self.assertFalse(result["admitted"])
        self.assertEqual(self.store.search("tired"), [])

    def test_candidate_is_typed_and_duplicate_is_not_added(self):
        content = "Always verify credential access before retrying a production deployment."
        first = self.store.save_candidate(content, "deployment notes")
        second = self.store.save_candidate(content, "deployment notes")
        self.assertTrue(first["admitted"])
        self.assertFalse(second["admitted"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(self.store.search("credential access")[0]["kind"], "procedural")

    def test_context_returns_only_matching_active_memories(self):
        self.store.save_candidate("I prefer short responses for technical questions.", "user")
        result = self.store.context("technical response style")
        self.assertEqual(len(result["memories"]), 1)
        self.assertIn("evidence", result["notice"])

    def test_audit_records_actions_without_query_text(self):
        self.store.save_candidate("The goal is to finish the local memory prototype.", "user")
        self.store.search("memory")
        rows = self.store.db.execute("SELECT action,detail FROM audit_log ORDER BY id").fetchall()
        self.assertEqual([row["action"] for row in rows], ["candidate_save", "memory_search"])
        self.assertNotIn("memory", rows[1]["detail"])


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.store = MemoryStore(Path(self.temp.name) / "memory.sqlite3")
        self.token = "test-only-token"
        self.server = HTTPServer(("127.0.0.1", 0), make_handler(self.store, self.token))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.store.close()
        self.temp.cleanup()

    def request(self, path, payload=None, token=None):
        data = None if payload is None else json.dumps(payload).encode()
        headers = {"Authorization": "Bearer " + (token or self.token)}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = Request(self.base + path, data=data, headers=headers)
        return urlopen(req, timeout=3)

    def test_health_does_not_expose_memory(self):
        with urlopen(self.base + "/health", timeout=3) as response:
            self.assertEqual(json.loads(response.read()), {"ok": True, "storage": "local"})

    def test_api_requires_token_and_rejects_browser_origin(self):
        with self.assertRaises(HTTPError) as unauthorized:
            self.request("/v1/search?q=anything", token="wrong")
        self.assertEqual(unauthorized.exception.code, 401)
        req = Request(self.base + "/v1/search?q=anything", headers={
            "Authorization": "Bearer " + self.token, "Origin": "https://example.invalid"
        })
        with self.assertRaises(HTTPError) as forbidden:
            urlopen(req, timeout=3)
        self.assertEqual(forbidden.exception.code, 403)

    def test_candidate_and_context_endpoints(self):
        response = self.request("/v1/memories/candidate", {
            "content": "I prefer short, direct project updates.", "provenance": "user"
        })
        self.assertEqual(response.status, 201)
        with self.request("/v1/context?task=project%20updates") as context:
            self.assertEqual(len(json.loads(context.read())["memories"]), 1)


if __name__ == "__main__":
    unittest.main()
