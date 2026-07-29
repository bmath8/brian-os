#!/usr/bin/env python3
"""Local RAG memory - a tiny semantic index over Harmony + the fleet docs + comms.
Replaces "read the first 4000 chars" with "retrieve the RELEVANT chunks" (audit D1).

All local/free: embeddings via Ollama `nomic-embed-text`, vectors stored in a plain
JSON file, cosine search in pure Python (no numpy, no pip deps - CI-safe). If the embed
model isn't pulled yet, build() no-ops and search() returns [] so every caller degrades
cleanly to truncation.

Build (cron, e.g. nightly):  python3 memory_index.py
Query from code:             memory_index.context_for("job hunt status", fallback=...)
"""
import os, sys, json, glob, datetime, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

MEM_DIR = os.path.join(fc.COMMS, ".memory")
INDEX = os.path.join(MEM_DIR, "index.json")
MAX_CHUNKS = 500
CHUNK_CHARS = 800


def _chunk(text):
    out, buf = [], ""
    for para in (text or "").split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if len(buf) + len(para) + 2 <= CHUNK_CHARS:
            buf = (buf + "\n\n" + para) if buf else para
        else:
            if buf:
                out.append(buf)
            buf = para[:CHUNK_CHARS] if len(para) > CHUNK_CHARS else para
    if buf:
        out.append(buf)
    return out


def _sources():
    """(label, path) pairs to index - curated + bounded."""
    paths = []
    for pat in (os.path.join(fc.HARMONY, "*.md"),
                os.path.join(fc.HARMONY, "**", "*.md"),
                os.path.join(fc.ROOT, "*.md"),
                os.path.join(fc.COMMS, "*.md")):
        paths += glob.glob(pat, recursive=True)
    seen, out = set(), []
    for p in paths:
        rp = os.path.realpath(p)
        if rp in seen or not os.path.isfile(p):
            continue
        seen.add(rp)
        out.append((os.path.basename(p), p))
    return out


def build():
    items = []
    for label, path in _sources():
        for ch in _chunk(fc.read(path)):
            items.append({"source": label, "text": ch})
            if len(items) >= MAX_CHUNKS:
                break
        if len(items) >= MAX_CHUNKS:
            break
    if not items:
        print("memory_index: nothing to index")
        return 0
    vecs = fc.ollama_embed([it["text"] for it in items])
    if not vecs:
        print(f"memory_index: embed model '{fc.EMBED_MODEL}' unavailable - "
              f"run `ollama pull {fc.EMBED_MODEL}` then rebuild. (Index not written; "
              f"callers fall back to truncation.)")
        return 0
    for it, v in zip(items, vecs):
        it["vec"] = [round(x, 6) for x in v]
    fc.atomic_write(INDEX, json.dumps(
        {"model": fc.EMBED_MODEL, "built": fc.now(), "items": items}))
    return len(items)


def _load():
    try:
        return json.load(open(INDEX, encoding="utf-8"))
    except Exception:
        return None


def search(query, k=5, min_score=0.2):
    idx = _load()
    if not idx or not idx.get("items"):
        return []
    qv = fc.ollama_embed(query)
    if not qv:
        return []
    scored = [(fc.cosine(qv, it.get("vec", [])), it) for it in idx["items"]]
    scored.sort(key=lambda s: s[0], reverse=True)
    return [{"source": it["source"], "text": it["text"], "score": round(sc, 3)}
            for sc, it in scored[:k] if sc >= min_score]


# ---- hybrid retrieval: BM25 (keyword) + vector, fused with RRF (#1.1) --------
# Pure-Python, stdlib only. Hybrid search is the single biggest quality jump over
# naive vector-only RAG: keyword recall catches exact terms (names, IDs, acronyms)
# that embeddings blur, while vectors catch paraphrase. We fuse the two rankings
# with Reciprocal Rank Fusion, then apply a light term-coverage rerank.
_TOK = re.compile(r"[a-z0-9]+")
_STOP = set("the a an and or of to in is for on with at by from this that it as be "
            "are was were will to into your you i".split())


def tokenize(text):
    return [t for t in _TOK.findall((text or "").lower()) if len(t) > 1 and t not in _STOP]


def _bm25_rank(query, items, n, k1=1.5, b=0.75):
    """Classic BM25 over the indexed chunk texts. Returns chunk indices, best first."""
    qset = set(tokenize(query))
    if not qset:
        return []
    docs = [tokenize(it.get("text", "")) for it in items]
    N = len(docs) or 1
    avgdl = (sum(len(d) for d in docs) / N) or 1
    df = {}
    for d in docs:
        for term in set(d):
            df[term] = df.get(term, 0) + 1
    scored = []
    for i, d in enumerate(docs):
        if not d:
            continue
        dl = len(d)
        tf = {}
        for term in d:
            if term in qset:
                tf[term] = tf.get(term, 0) + 1
        s = 0.0
        for term, f in tf.items():
            idf = math.log(1 + (N - df[term] + 0.5) / (df[term] + 0.5))
            s += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl))
        if s > 0:
            scored.append((s, i))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [i for _, i in scored[:n]]


def _vector_rank(qv, items, n):
    if not qv:
        return []
    scored = [(fc.cosine(qv, it.get("vec", [])), i) for i, it in enumerate(items)]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [i for sc, i in scored[:n] if sc > 0]


def _rrf(rankings, rrf_k=60):
    """Reciprocal Rank Fusion: combine rankings without needing comparable scores."""
    agg = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            agg[idx] = agg.get(idx, 0.0) + 1.0 / (rrf_k + rank + 1)
    return sorted(agg, key=lambda i: agg[i], reverse=True)


def _rerank(query, idxs, items):
    """Light, dependency-free rerank: prefer chunks covering more DISTINCT query
    terms (a cheap cross-encoder proxy), breaking ties by the fused order. A true
    cross-encoder rerank is a later upgrade that needs a reranker model."""
    qset = set(tokenize(query))
    if not qset:
        return idxs
    order = {idx: r for r, idx in enumerate(idxs)}
    return sorted(idxs, key=lambda i: (len(qset & set(tokenize(items[i].get("text", "")))),
                                       -order[i]), reverse=True)


def hybrid_search(query, k=5, candidates=20):
    """BM25 + vector, RRF-fused, light-reranked. Degrades to BM25-only if the embed
    model is unavailable at query time, and to [] if there's no index."""
    idx = _load()
    if not idx or not idx.get("items"):
        return []
    items = idx["items"]
    qv = fc.ollama_embed(query)                      # None -> BM25-only
    vrank = _vector_rank(qv, items, candidates)
    brank = _bm25_rank(query, items, candidates)
    fused = _rrf([r for r in (vrank, brank) if r])
    if not fused:
        return []
    fused = _rerank(query, fused, items)[:k]
    return [{"source": items[i]["source"], "text": items[i]["text"]} for i in fused]


def context_for(query, fallback="", k=4, max_chars=4000):
    """Top relevant chunks joined for a prompt, via HYBRID retrieval (BM25+vector+RRF).
    Falls back to `fallback` (e.g. a truncated doc) when there's no index."""
    hits = hybrid_search(query, k=k)
    if not hits:
        return fallback
    buf = []
    total = 0
    for h in hits:
        piece = f"[{h['source']}] {h['text']}"
        if total + len(piece) > max_chars:
            break
        buf.append(piece)
        total += len(piece)
    return "\n\n".join(buf) if buf else fallback


def main():
    n = build()
    if n:
        print(f"memory_index: indexed {n} chunks -> {INDEX}")
    fc.log_run("memory_index", "ok", f"{n} chunks")


if __name__ == "__main__":
    main()
