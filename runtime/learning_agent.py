#!/usr/bin/env python3
"""Learning agent - a real spaced-repetition loop (audit D2), not random questions.
Surfaces the cards that are DUE today; generates new ones (from the fleet's lessons +
notes Brian drops in comms/learn/) only when the due pool runs low. Grading moves cards
up/down the Leitner boxes so you review what you're about to forget.

Normal run (cron):   python3 learning_agent.py            -> writes comms/recall.md
Grade a card:        python3 learning_agent.py --grade <id> 1   (1=got it, 0=missed)
"""
import os, sys, re, glob, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc
import srs


def _generate_questions():
    src = fc.read(f"{fc.ROOT}/TIPS_AND_OPTIMIZATIONS.md")[:3500]
    for f in sorted(glob.glob(f"{fc.COMMS}/learn/*.md")):
        src += "\n\n" + fc.wrap_untrusted(fc.read(f)[:2000], "dropped note")
    prompt = (
        "From the notes below, write exactly 3 short active-recall questions that test the most "
        "important, practical things to remember. Questions only - no answers. Number them 1-3. "
        "Keep each under 20 words.\n\nNOTES:\n" + src)
    out = fc.ollama_generate(prompt, num_ctx=8192, temperature=0.5, num_predict=250,
                             timeout=90, retries=1, fallback="")
    return [m.group(1).strip() for m in re.finditer(r"^\s*\d+[.)]\s*(.+)$", out, re.M)]


def run_grade(cid, score):
    cards = srs.load()
    ok = srs.grade(cards, cid, bool(int(score)))
    srs.save(cards)
    print(f"graded {cid}: {'promoted' if int(score) else 'reset'} -> "
          f"{'ok' if ok else 'card not found'}")
    fc.log_run("learning", "ok", f"graded {cid}")


def main():
    if "--grade" in sys.argv:
        i = sys.argv.index("--grade")
        try:
            run_grade(sys.argv[i + 1], sys.argv[i + 2])
        except Exception as e:
            print(f"usage: learning_agent.py --grade <id> <0|1>  ({e})")
        return

    cards = srs.load()
    if len(srs.due(cards)) < 3:
        for q in _generate_questions():
            srs.add_question(cards, q)
    due = srs.due(cards)[:3]
    for cid, _ in due:
        srs.mark_seen(cards, cid)
    srs.save(cards)

    stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    lines = [f"# Recall - {stamp}"]
    if due:
        lines += [f"{n}. [id {cid}] {c['q']}" for n, (cid, c) in enumerate(due, 1)]
        lines.append("Grade: `learning_agent.py --grade <id> 1` (got it) or 0 (missed).")
    else:
        lines.append("1. (no cards due - all caught up)")
    fc.atomic_write(f"{fc.COMMS}/recall.md", "\n".join(lines) + "\n")

    fc.state_update("learning", {"last_run": stamp, "status": "ok",
                                 "summary": f"{len(due)} cards due", "needs_human": []})
    print("\n".join(lines))
    fc.log_run("learning", "ok", f"{len(due)} due")


if __name__ == "__main__":
    main()
