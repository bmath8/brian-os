#!/usr/bin/env python3
"""Tests for hybrid retrieval in memory_index (BM25 + vector + RRF + rerank, #1.1).
Reuses a deterministic mock embed endpoint so ranking is verifiable offline."""
import os, sys, json, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

_TMP = tempfile.mkdtemp(prefix="fleet_rag_")
os.environ["FLEET_ROOT"] = _TMP
os.environ["FLEET_COMMS"] = os.path.join(_TMP, "comms")
os.environ["FLEET_LOGS"] = os.path.join(_TMP, "logs")
os.environ["HARMONY_DIR"] = os.path.join(_TMP, "harmony")
os.environ["HARMONY_BACKUP_DIR"] = os.path.join(_TMP, "harmony_bk")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))
import fleet_common as fc          # noqa: E402
import memory_index as mem         # noqa: E402

VOCAB = ["gateway", "ollama", "kubernetes", "finance", "health", "python", "telegram"]


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


class TokenizeTests(unittest.TestCase):
    def test_drops_stopwords_and_shorts(self):
        toks = mem.tokenize("The gateway is on Kubernetes")
        self.assertIn("gateway", toks)
        self.assertIn("kubernetes", toks)
        self.assertNotIn("the", toks)
        self.assertNotIn("is", toks)


class HybridTests(unittest.TestCase):
    def setUp(self):
        _write(os.path.join(fc.HARMONY, "infra.md"),
               "The gateway runs on kubernetes.\n\npython supervises the telegram bot.")
        _write(os.path.join(fc.HARMONY, "money.md"),
               "finance runway is tight.\n\nhealth and exercise matter weekly.")

    def test_bm25_finds_exact_keyword(self):
        with _MockEmbed():
            mem.build()
        idx = mem._load()
        ranks = mem._bm25_rank("kubernetes", idx["items"], 5)
        self.assertTrue(ranks)
        self.assertIn("kubernetes", idx["items"][ranks[0]]["text"].lower())

    def test_hybrid_ranks_relevant_chunk(self):
        with _MockEmbed():
            mem.build()
            hits = mem.hybrid_search("kubernetes gateway", k=2)
        self.assertTrue(hits)
        self.assertIn("kubernetes", hits[0]["text"].lower())

    def test_hybrid_degrades_to_bm25_without_embed(self):
        with _MockEmbed():
            mem.build()                       # index written (has vecs)
        # Now no embed endpoint -> query-time embedding fails -> BM25-only path.
        os.environ["OLLAMA_URL"] = "http://127.0.0.1:1"   # dead
        try:
            hits = mem.hybrid_search("finance runway", k=2)
        finally:
            os.environ.pop("OLLAMA_URL", None)
        self.assertTrue(hits)
        self.assertIn("finance", hits[0]["text"].lower())

    def test_context_for_uses_hybrid_and_falls_back(self):
        # No index yet -> fallback.
        # (fresh comms dir for isolation)
        self.assertEqual(mem.context_for("anything", fallback="FB"), "FB")
        with _MockEmbed():
            mem.build()
            ctx = mem.context_for("telegram python bot", fallback="FB")
        self.assertNotEqual(ctx, "FB")
        self.assertIn("telegram", ctx.lower())

    def test_rrf_fuses_rankings(self):
        fused = mem._rrf([[2, 0, 1], [0, 1, 2]])
        self.assertEqual(set(fused), {0, 1, 2})
        self.assertEqual(fused[0], 0)        # 0 ranks high in both -> top


if __name__ == "__main__":
    unittest.main()
