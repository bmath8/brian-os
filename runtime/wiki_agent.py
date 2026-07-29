#!/usr/bin/env python3
"""wiki_agent.py - the LLM-wiki memory pattern (Karpathy, Apr 2026; built 2026-07-06).

The fleet's notes are append-only streams; knowledge should COMPOUND instead.
Weekly, this agent distills each topic's recent source material into ONE living
wiki page (comms/learn/wiki/<topic>.md) that gets UPDATED - new facts merged in,
stale facts removed - rather than appended to. The weekly review + /ask RAG can
then draw on a current, compact picture instead of a pile of dated notes.

Design: local/free (qwen3:8b via fc.ollama_generate), no-op-safe (any failure
keeps the existing page), draft-only (writes markdown; sends nothing).
Cron: Sunday 16:45 (before weekly-review 17:00, so the review can use it).
"""
import os, sys, glob, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

WIKI_DIR = os.path.join(fc.COMMS, "learn", "wiki")
MAX_SRC = 6000          # chars of source per topic
MAX_PAGE = 3000         # chars of existing page fed back for the merge

# topic -> list of source specs; "harmony:" prefix reads via read_harmony
TOPICS = {
    "job-hunt":  ["career.md", "networking.md", "harmony:03_Career/Job_Tracker.md"],
    "finance":   ["finance.md", "harmony:05_Finance/Overview.md"],
    "health":    ["health.md"],
    "fleet-ops": ["system_status.md", "fleet_health.md", "currency.md"],
    "learning":  ["learn/*.md", "recall.md", "scout.md"],
}


def gather(specs):
    parts = []
    for spec in specs:
        if spec.startswith("harmony:"):
            parts.append(fc.read_harmony(spec[8:]))
        elif "*" in spec:
            for p in sorted(glob.glob(os.path.join(fc.COMMS, spec)))[-5:]:
                parts.append(fc.read(p))
        else:
            parts.append(fc.read(os.path.join(fc.COMMS, spec)))
    return "\n\n".join(p for p in parts if p)[:MAX_SRC]


def update_page(topic, src):
    page_path = os.path.join(WIKI_DIR, f"{topic}.md")
    old = fc.read(page_path)[:MAX_PAGE]
    prompt = (
        "You maintain Brian's personal wiki. Rewrite the WIKI PAGE for the topic "
        f"'{topic}' by merging in what's new from the SOURCE NOTES and dropping "
        "anything now stale or superseded. Keep it under 350 words: current facts, "
        "key numbers, open items. Markdown, one # title, short sections. Do not "
        "invent facts; keep dates where given. Return ONLY the page.\n\n"
        f"CURRENT WIKI PAGE (may be empty):\n{old or '(none yet)'}\n\n"
        "SOURCE NOTES (recent, unstructured):\n"
        + fc.wrap_untrusted(src, f"{topic} notes"))
    new = fc.ollama_generate(prompt, num_ctx=8192, temperature=0.3,
                             num_predict=550, timeout=150, retries=1, fallback="")
    if not new or len(new.strip()) < 80:      # model failed -> keep the old page
        return False
    header = f"<!-- living wiki page - updated {fc.now()} by wiki_agent -->\n"
    fc.atomic_write(page_path, header + new.strip() + "\n")
    return True


def main():
    os.makedirs(WIKI_DIR, exist_ok=True)
    updated, skipped = [], []
    for topic, specs in TOPICS.items():
        src = gather(specs)
        if not src.strip():
            skipped.append(topic)
            continue
        (updated if update_page(topic, src) else skipped).append(topic)
    fc.state_update("wiki", {"last_run": fc.now(), "status": "ok",
                             "summary": f"wiki: {len(updated)} page(s) updated",
                             "needs_human": []})
    fc.log_run("wiki", "ok", f"updated={','.join(updated) or '-'} skipped={','.join(skipped) or '-'}")
    if updated:
        print(fc.ascii_fold(f"Wiki updated: {', '.join(updated)}"))


if __name__ == "__main__":
    main()
