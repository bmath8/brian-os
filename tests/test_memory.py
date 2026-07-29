#!/usr/bin/env python3
"""Tests for runtime/memory_index.py (local RAG). Uses a deterministic mock embed
endpoint (bag-of-words over a tiny vocab) so cosine ranking is verifiable without
the real nomic-embed-text model."""
import os, sys, json, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

_TMP = tempfile.mkdtemp(prefix="fleet_mem_")
os.environ["FLEET_ROOT"] = _TMP
os.environ["FLEET_COMMS"] = os.path.join(_TMP, "comms")
os.environ["FLEET_LOGS"] = os.path.join(_TMP, "logs")
os.environ["HARMONY_DIR"] = os.path.join(_TMP, "harmony")
os.environ["HARMONY_BACKUP_DIR"] = os.path.join(_TMP, "harmony_bk")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))
import fleet_common as fc          # noqa: E402
import memory_index as mem         # noqa: E402

VOCAB = ["gateway", "ollama", "job", "finance", "health", "python", "memory"]


def _vec(text):
    t = text.lower()
    return [float(t.count(w)) for w in VOCAB]


class _MockEmbed:
    def __enter__(self):
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n) or b"{}")
                items = payload.get("input")
                if isinstance(items, str):
                    items = [items]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"embeddings": [_vec(t) for t in items]}).encode())

        self.server = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        os.environ["OLLAMA_URL"] = f"http://127.0.0.1:{self.server.server_address[1]}"
        return self

    def __exit__(self, *a):
        self.server.shutdown()
        os.environ.pop("OLLAMA_URL", None)


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        _write(os.path.join(fc.HARMONY, "notes_gateway.md"),
               "The gateway and ollama sometimes crash.\n\npython restarts the gateway automatically.")
        _write(os.path.join(fc.HARMONY, "notes_money.md"),
               "finance runway is tight.\n\njob hunt is the number one priority.")

    def test_build_and_search_ranks_relevant_chunk(self):
        with _MockEmbed():
            n = mem.build()
            self.assertGreaterEqual(n, 2)
            hits = mem.search("gateway ollama python", k=3)
        self.assertTrue(hits)
        self.assertEqual(hits[0]["source"], "notes_gateway.md")

    def test_search_money_query(self):
        with _MockEmbed():
            mem.build()
            hits = mem.search("finance job runway", k=3)
        self.assertTrue(hits)
        self.assertEqual(hits[0]["source"], "notes_money.md")

    def test_context_for_falls_back_without_index(self):
        try:
            os.remove(mem.INDEX)
        except OSError:
            pass
        # no index on disk -> must return the fallback verbatim
        self.assertEqual(mem.context_for("anything", fallback="FB"), "FB")

    def test_build_noops_when_embed_unavailable(self):
        # no mock server running -> embed returns None -> build writes nothing
        os.environ["OLLAMA_URL"] = "http://127.0.0.1:9"   # nothing listening
        try:
            self.assertEqual(mem.build(), 0)
        finally:
            os.environ.pop("OLLAMA_URL", None)


if __name__ == "__main__":
    unittest.main()
