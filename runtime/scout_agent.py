#!/usr/bin/env python3
"""Scout agent - free daily job/opportunity discovery into the morning brief.

Reads Brian's target roles from the Harmony Job Tracker, searches DuckDuckGo for fresh
listings (stdlib only - no key, no paid API), and writes the top hits to comms/scout.md.
Producer on the blackboard; the Chief of Staff brief surfaces it. READ-only: it discovers
links, never applies.
"""
import os, sys, urllib.request, urllib.parse, re, html, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def target_roles():
    jt = fc.read_harmony("03_Career/Job_Tracker.md")
    m = re.search(r"Primary:\s*(.+)", jt)
    if m:
        roles = [re.sub(r"\(.*?\)", "", r).strip() for r in re.split(r"[·;,]", m.group(1)) if r.strip()]
        if roles:
            return roles[:3]
    return ["Full-Stack Developer", "React TypeScript Developer", "AI Application Engineer"]


def ddg_search(query, limit=5):
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        page = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    except Exception:
        return []
    out = []
    for m in re.finditer(r'class="result__a"[^>]*href="(.*?)"[^>]*>(.*?)</a>', page, re.S):
        href, title = m.group(1), re.sub(r"<.*?>", "", m.group(2))
        href = html.unescape(href)
        mu = re.search(r"[?&]uddg=([^&]+)", href)
        if mu:
            href = urllib.parse.unquote(mu.group(1))
        elif href.startswith("//"):
            href = "https:" + href
        out.append({"title": html.unescape(title).strip(), "url": href})
        if len(out) >= limit:
            break
    return out


# Fit-scoring (#22): rank raw listings against Brian's profile so the brief shows the
# best-fit roles first, not just whatever the search returned. Deterministic + token-free.
FIT_KEYWORDS = ["react", "typescript", "next.js", "nextjs", "javascript", "python", "node",
                "full stack", "full-stack", "front end", "frontend", "ai ", "ml ", "llm",
                "engineer", "developer", "founding", "junior", "mid-level", "remote"]
PENALTY_KEYWORDS = ["senior", "staff", "principal", "lead ", "manager", "director", "head of",
                    "10+ years", "clearance", "secret", "phd", "architect", " vp ", "sap ",
                    "salesforce", "wordpress", ".net", "c++", "golang", "rust ", "php"]


def score_hit(title):
    t = " " + title.lower() + " "
    return sum(2 for k in FIT_KEYWORDS if k in t) - sum(2 for k in PENALTY_KEYWORDS if k in t)


def main():
    roles = target_roles()
    seen, results = set(), []
    for role in roles:
        for hit in ddg_search(f"{role} remote jobs", limit=5):
            u = hit.get("url")
            if u and u not in seen and "duckduckgo.com" not in u:
                seen.add(u)
                hit["score"] = score_hit(hit["title"])
                results.append(hit)
    # Best-fit first; keep the top 6 by score.
    results.sort(key=lambda r: r.get("score", 0), reverse=True)
    results = results[:6]

    # Cache resilience (#53): cache good results; if DDG rate-limited us (empty),
    # fall back to the last good set (up to 3 days old) instead of a blank section.
    note = ""
    if results:
        fc.cache_set("scout_results", results)
    else:
        cached = fc.cache_get("scout_results", 60 * 60 * 24 * 3)
        if cached:
            results = cached
            note = " (cached - search returned nothing this run)"

    stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    lines = [f"# Scout - {stamp}",
             f"_Best-fit listings for: {', '.join(roles)} (free discovery, fit-ranked; verify + apply yourself){note}_", ""]
    if results:
        for r in results:
            tag = "⭐ " if r.get("score", 0) >= 4 else ""      # strong match
            lines.append(f"- {tag}[{r['title'][:70]}]({r['url']})")
    else:
        lines.append("- (no results this run - DuckDuckGo may be rate-limiting; try again later)")
    fc.atomic_write(f"{fc.COMMS}/scout.md", "\n".join(lines) + "\n")

    fc.state_update("scout", {"last_run": stamp, "status": "ok",
                              "summary": f"{len(results)} listings found", "needs_human": []})
    print(f"Scout: {len(results)} listings for {', '.join(roles)}")
    fc.log_run("scout", "ok", f"{len(results)} listings")


if __name__ == "__main__":
    main()
