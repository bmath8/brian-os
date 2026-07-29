#!/usr/bin/env python3
"""Gig scanner - second income lane (roadmap Tier-4 #16) while the job hunt runs.

Scans FREE public freelance/contract feeds for AI-app / React / Python gigs that
match Brian's real stack, scores them deterministically by keyword fit, and
surfaces the best matches on the blackboard (comms/gigs.md + brief). Strong
matches (score >= 4) also get queued for the overnight worker to draft a
proposal INTO THE REVIEW QUEUE - draft-only, Brian sends everything himself.

Free sources, no keys: RemoteOK JSON API + WeWorkRemotely RSS. Both cached
(TTL 6h) so rate limits/blips degrade to the last good result, never a crash.
All external text goes through wrap_untrusted (F1) before any model sees it.
"""
import os, sys, re, json, glob, datetime, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

UA = {"User-Agent": "Mozilla/5.0 (BrianOS gig scanner; personal use)"}
SKILLS = {"react": 2, "next.js": 2, "nextjs": 2, "typescript": 2, "python": 2,
          "ai": 1, "llm": 2, "gpt": 1, "claude": 2, "openai": 1, "chatbot": 2,
          "automation": 2, "supabase": 2, "tailwind": 1, "full stack": 1,
          "fullstack": 1, "full-stack": 1, "scraper": 1, "api": 1, "mvp": 2}
NEG = ("senior staff", "10+ years", "principal", ".net", "java ", "php", "wordpress")
CONTRACT_HINTS = ("contract", "freelance", "part-time", "part time", "hourly", "project")


def _fetch(url, timeout=20):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                      timeout=timeout).read().decode("utf-8", "ignore")
    except Exception:
        return ""


def _remoteok():
    """RemoteOK public JSON (first element is metadata/legal - skip)."""
    raw = fc.cache_get("gigs_remoteok", 6 * 3600)
    if raw is None:
        txt = _fetch("https://remoteok.com/api")
        try:
            raw = json.loads(txt)[1:]
        except Exception:
            raw = []
        if raw:
            fc.cache_set("gigs_remoteok", raw)
    out = []
    for j in raw or []:
        if not isinstance(j, dict):
            continue
        out.append({"title": str(j.get("position") or ""), "company": str(j.get("company") or ""),
                    "url": str(j.get("url") or ""), "text": str(j.get("description") or "")[:800],
                    "tags": " ".join(str(t) for t in (j.get("tags") or [])), "src": "RemoteOK"})
    return out


def _wwr():
    """WeWorkRemotely programming RSS (contract + full-time listings)."""
    xml = fc.cache_get("gigs_wwr", 6 * 3600)
    if xml is None:
        xml = _fetch("https://weworkremotely.com/categories/remote-programming-jobs.rss")
        if xml:
            fc.cache_set("gigs_wwr", xml)
    out = []
    for item in re.findall(r"<item>(.*?)</item>", xml or "", re.S)[:60]:
        def _tag(t):
            m = re.search(rf"<{t}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{t}>", item, re.S)
            return (m.group(1).strip() if m else "")
        out.append({"title": _tag("title"), "company": "", "url": _tag("link"),
                    "text": re.sub(r"<[^>]+>", " ", _tag("description"))[:800],
                    "tags": "", "src": "WWR"})
    return out


TITLE_MUST = ("developer", "engineer", "react", "next", "typescript", "python",
              "full stack", "fullstack", "full-stack", "frontend", "front-end",
              "web", "ai", "llm", "automation", "software", "app")


def _score(gig):
    title = (gig["title"] or "").lower()
    # Gate on the TITLE: description blobs mention 'api'/'part-time' on totally
    # unrelated posts (the first live run scored a nanny listing 4/10).
    if not any(k in title for k in TITLE_MUST):
        return 0
    blob = f"{title} {gig['tags']} {gig['text']}".lower()
    if any(n in blob for n in NEG):
        return 0
    s = sum(w for k, w in SKILLS.items() if k in blob)
    if any(h in blob for h in CONTRACT_HINTS):
        s += 1                                  # gigs > jobs for this lane
    return s


def main():
    gigs = _remoteok() + _wwr()
    seen_path = os.path.join(fc.COMMS, ".gigs_seen.json")
    try:
        seen = set(json.load(open(seen_path, encoding="utf-8")))
    except Exception:
        seen = set()

    scored = sorted(((g, _score(g)) for g in gigs if g["title"]),
                    key=lambda t: -t[1])
    fresh = [(g, s) for g, s in scored if s >= 3 and g["url"] not in seen][:8]
    stamp = datetime.date.today().isoformat()

    lines = [f"# Gig scanner - {stamp}", ""]
    if not gigs:
        lines.append("Feeds unreachable this run (cached results expired) - will retry tomorrow.")
    elif not fresh:
        lines.append(f"Scanned {len(gigs)} listings - no strong new stack-matches today.")
    else:
        lines.append(f"Top matches (of {len(gigs)} scanned):")
        for g, s in fresh:
            lines.append(f"- [{s}] {g['title'][:70]} — {g['company'] or g['src']} · {g['url']}")

    # Strong matches -> queue a proposal draft for the overnight worker (draft-only;
    # it lands in comms/review/ for approval like every other draft).
    queued = 0
    # Never queue the same gig twice (queue OR already-drafted review file).
    existing = ""
    for p in (glob.glob(os.path.join(fc.COMMS, "queue", "*.md")) +
              glob.glob(os.path.join(fc.COMMS, "review", "*.md"))):
        existing += fc.read(p)
    for g, s in fresh:
        if s < 4 or queued >= 2 or (g["url"] and g["url"] in existing):
            continue
        qstamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{queued}"
        fc.atomic_write(os.path.join(fc.COMMS, "queue", f"{qstamp}.md"),
            f"# Draft a freelance proposal: {g['title'][:60]}\n\n"
            f"Draft a short (120-160 word) proposal for this gig, in Brian's voice, "
            f"citing his REAL projects (AI Job Hunter, Pokemon Drop Intel, portfolio). "
            f"Do not invent experience. Include one clarifying question.\n\n"
            f"URL: {g['url']}\n\n" + fc.wrap_untrusted(g["text"], "gig description"))
        queued += 1
    if queued:
        lines += ["", f"Queued {queued} proposal draft(s) for tonight's worker -> review queue."]

    for g, s in fresh:
        seen.add(g["url"])
    try:
        fc.atomic_write(seen_path, json.dumps(sorted(seen)[-500:]))
    except Exception:
        pass

    fc.atomic_write(f"{fc.COMMS}/gigs.md", "\n".join(lines) + "\n")
    summary = (f"{len(fresh)} match(es), {queued} proposal(s) queued" if fresh
               else f"{len(gigs)} scanned, none matched")
    fc.state_update("gigs", {"last_run": stamp, "status": "ok", "summary": summary,
                             "needs_human": ([f"{len(fresh)} gig match(es) worth a look (comms/gigs.md)"]
                                             if fresh else [])})
    fc.log_run("gig_scanner", "ok", summary)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
