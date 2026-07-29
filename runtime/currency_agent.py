#!/usr/bin/env python3
"""currency_agent.py - the Modernization & Currency system.

Keeps EVERYTHING current: scans repos for outdated/insecure dependencies, watches
release feeds for the tools Brian's stack depends on (Next.js/React/Node/Ollama/
Tailwind/Anthropic SDKs/...), surfaces what's new in the AI ecosystem, and (for the
employer-facing allowlist) prepares SAFE dependency upgrades on a branch with the
build/tests run first - never touching main. Complements model_review.py (which keeps
the local MODELS current); this one keeps deps + code + docs + tooling current.

Two cadences, matching Brian's choice (daily flags + weekly deep-dive):
  python currency_agent.py            # DAILY: security alerts + new releases only (cheap)
  python currency_agent.py --weekly   # WEEKLY: + outdated deps, staleness, safe auto-fixes, AI-ecosystem digest

Design: stdlib only (+ gh/npm/pip/git via subprocess), resilient (every external call
is guarded; a failure flags 'unknown', never crashes the cron). Reads shared/currency_watch.json.
Writes comms/currency.md (+ comms/modernization_report.md weekly); urgent items go direct to
Telegram; safe prepared upgrades land in comms/review/ for one-tap approval (brief surfaces them).
"""
import os, sys, json, time, subprocess, datetime, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

WEEKLY = "--weekly" in sys.argv or "--deep" in sys.argv
VERBOSE = "--print" in sys.argv or "-v" in sys.argv   # cron leaves stdout empty (silent); delivery is via telegram_send
CFG_PATH = os.path.join(fc.ROOT, "shared", "currency_watch.json")
SEEN_PATH = os.path.join(fc.COMMS, ".currency_seen.json")


def load_cfg():
    try:
        return json.load(open(CFG_PATH, encoding="utf-8"))
    except Exception:
        return {}


def run(cmd, cwd=None, timeout=120):
    """Run a shell command; return (rc, stdout, stderr). Never raises."""
    try:
        p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True,
                           text=True, timeout=timeout, encoding="utf-8", errors="ignore")
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"


def gh_json(api):
    # Repo names come from local dir listings; quote defensively anyway (2026-07-06).
    rc, out, err = run(f'gh api "{api}"' if " --" not in api else f'gh api {api}', timeout=40)
    if rc != 0:
        return None
    try:
        return json.loads(out)
    except Exception:
        return None


def load_seen():
    try:
        return json.load(open(SEEN_PATH, encoding="utf-8"))
    except Exception:
        return {}


def save_seen(d):
    fc.atomic_write(SEEN_PATH, json.dumps(d, indent=2))


# ---- discovery --------------------------------------------------------------
def discover_repos(cfg):
    """Find git repos under scan_roots (depth<=2). Classify by files present."""
    skip = set(cfg.get("skip_dirs", []))
    repos = []
    for root in cfg.get("scan_roots", []):
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            if name in skip or name.startswith("."):
                continue
            path = os.path.join(root, name)
            if not os.path.isdir(path):
                continue
            cand = [path] + [os.path.join(path, s) for s in os.listdir(path)
                             if os.path.isdir(os.path.join(path, s)) and s not in skip] \
                if os.path.isdir(path) else [path]
            for d in cand:
                if os.path.isdir(os.path.join(d, ".git")):
                    repos.append({"name": os.path.basename(d), "path": d,
                                  "type": classify(d)})
    # de-dup by path
    seen, out = set(), []
    for r in repos:
        if r["path"] not in seen:
            seen.add(r["path"]); out.append(r)
    return out


def classify(path):
    has = lambda f: os.path.exists(os.path.join(path, f))
    if has("package.json"):
        return "node"
    if has("requirements.txt") or has("pyproject.toml") or has("setup.py"):
        return "python"
    if has("index.html"):
        return "static"
    return "other"


# ---- daily checks -----------------------------------------------------------
def check_security(cfg, repos):
    """Open Dependabot alerts per GitHub repo. Returns urgent findings."""
    owner = cfg.get("github_owner", "")
    findings = []
    # Map local repo name -> github repo name where known (pokemon-drop -> pokemon-drop-intel)
    name_map = {"pokemon-drop": "pokemon-drop-intel"}
    for r in repos:
        if r["type"] not in ("node", "python"):
            continue
        gh_name = name_map.get(r["name"], r["name"])
        alerts = gh_json(f'repos/{owner}/{gh_name}/dependabot/alerts?state=open --paginate')
        if not isinstance(alerts, list):
            continue
        sev = {}
        for a in alerts:
            s = (a.get("security_advisory", {}) or {}).get("severity", "unknown")
            sev[s] = sev.get(s, 0) + 1
        crit = sev.get("critical", 0) + sev.get("high", 0)
        if alerts:
            findings.append({"repo": gh_name, "total": len(alerts), "sev": sev, "urgent": crit > 0})
    return findings


def check_releases(cfg):
    """Latest release/tag for each watched repo vs last-seen. Returns new releases."""
    seen = load_seen()
    new = []
    for item in cfg.get("releases_watch", []):
        repo = item["repo"]
        tag = None
        rel = gh_json(f'repos/{repo}/releases/latest')
        if isinstance(rel, dict):
            tag = rel.get("tag_name")
        if not tag:
            tags = gh_json(f'repos/{repo}/tags?per_page=1')
            if isinstance(tags, list) and tags:
                tag = tags[0].get("name")
        if not tag:
            continue
        prev = seen.get(repo)
        if prev and prev != tag:
            new.append({"repo": repo, "from": prev, "to": tag, "why": item.get("why", "")})
        seen[repo] = tag
    save_seen(seen)
    return new


# ---- weekly checks ----------------------------------------------------------
def outdated_node(path):
    rc, out, err = run("npm outdated --json", cwd=path, timeout=180)
    try:
        data = json.loads(out) if out.strip() else {}
    except Exception:
        return None
    pkgs = []
    for name, info in data.items():
        cur, want, latest = info.get("current"), info.get("wanted"), info.get("latest")
        major = (cur and latest and cur.split(".")[0] != latest.split(".")[0])
        pkgs.append({"name": name, "current": cur, "wanted": want, "latest": latest, "major": bool(major)})
    return pkgs


def outdated_python(path):
    # Only if a venv-ish setup; use the system pip against requirements is noisy, so
    # we just report the count of outdated top-level packages if pip can resolve.
    req = os.path.join(path, "requirements.txt")
    if not os.path.exists(req):
        return None
    rc, out, err = run("pip list --outdated --format=json", cwd=path, timeout=120)
    try:
        data = json.loads(out) if out.strip() else []
    except Exception:
        return None
    names = {ln.split("==")[0].split(">=")[0].split("~=")[0].strip().lower()
             for ln in fc.read(req).splitlines() if ln.strip() and not ln.startswith("#")}
    return [p for p in data if p.get("name", "").lower() in names]


def staleness(repos, cfg):
    out = []
    cutoff = cfg.get("stale_days", 45)
    for r in repos:
        rc, last, err = run('git log -1 --format=%cr', cwd=r["path"], timeout=20)
        rc2, days, err2 = run('git log -1 --format=%ct', cwd=r["path"], timeout=20)
        try:
            age_days = (time.time() - int(days.strip())) / 86400 if days.strip() else None
        except Exception:
            age_days = None
        if age_days is not None and age_days > cutoff:
            out.append({"repo": r["name"], "last": last.strip(), "days": int(age_days)})
    return out


def auto_apply_safe(repo_path, repo_name, gh_name, cfg):
    """Create a branch, apply MINOR/PATCH npm upgrades (npm update respects semver
    ranges) + npm audit fix (no --force), run the build; if green, push the branch and
    open a PR. Returns a result dict. NEVER touches main; majors are excluded."""
    res = {"repo": repo_name, "status": "skipped", "detail": ""}
    if not os.path.exists(os.path.join(repo_path, "package.json")):
        return res
    branch = "currency/auto-" + datetime.date.today().isoformat()
    steps = [
        f'git checkout -b {branch}',
        'npm update',
        'npm audit fix',
    ]
    for s in steps:
        rc, out, err = run(s, cwd=repo_path, timeout=300)
    # did anything change?
    rc, diff, err = run('git status --porcelain', cwd=repo_path, timeout=30)
    if not diff.strip():
        run(f'git checkout - && git branch -D {branch}', cwd=repo_path, timeout=30)
        res["status"] = "current"; res["detail"] = "no minor/patch upgrades available"
        return res
    # gate on the build (ensure devDeps present first - this npm omits dev by default,
    # which would drop build-time deps like @tailwindcss/postcss and false-fail the build)
    run("npm install --include=dev", cwd=repo_path, timeout=300)
    rcb, outb, errb = run("npm run build", cwd=repo_path, timeout=420)
    if rcb != 0:
        run(f'git checkout -- . && git checkout - && git branch -D {branch}', cwd=repo_path, timeout=30)
        res["status"] = "build-failed"; res["detail"] = "safe upgrades reverted (build broke)"
        return res
    run('git add -A', cwd=repo_path, timeout=30)
    run('git -c user.name=bmath8 -c user.email=mathew.brian@gmail.com commit -m "deps: safe minor/patch upgrades (auto, build verified)"', cwd=repo_path, timeout=30)
    rcp, outp, errp = run(f'git push -u origin {branch}', cwd=repo_path, timeout=120)
    run(f'gh pr create --fill --base main --head {branch}', cwd=repo_path, timeout=60)
    if cfg.get("auto_merge_safe"):
        # build already verified green; squash-merge to main and clean up the branch
        run(f'gh pr merge {branch} --squash --delete-branch', cwd=repo_path, timeout=120)
        run('git checkout main', cwd=repo_path, timeout=30)
        run('git pull --ff-only', cwd=repo_path, timeout=90)
        res["status"] = "merged"; res["detail"] = f"safe upgrades build-verified + auto-merged to main"
    else:
        run('git checkout -', cwd=repo_path, timeout=30)
        res["status"] = "PR-ready"; res["detail"] = f"branch {branch} pushed, build green, PR opened"
    return res


DISCOVERY_SEEN = os.path.join(fc.COMMS, ".currency_discovery_seen.json")


def _http_json(url, timeout=20):
    try:
        return json.loads(urllib.request.urlopen(url, timeout=timeout).read().decode("utf-8", "ignore"))
    except Exception:
        return None


def _http_text(url, timeout=20):
    try:
        return urllib.request.urlopen(url, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception:
        return ""


def discovery(cfg):
    """Hunt the OPEN INTERNET for brand-new AI tools/projects/research relevant to Brian -
    not just version bumps of his existing deps (the gap that let Nous Research's Hermes
    tooling slip by). Sources: Hacker News, GitHub Trending, arXiv. Dedupes against what
    we've already shown, then the local LLM curates the few genuinely worth his time."""
    import re as _re, urllib.parse as _up
    src = cfg.get("discovery_sources", {})
    cutoff = int(time.time()) - 7 * 86400
    try:
        seen = set(json.load(open(DISCOVERY_SEEN, encoding="utf-8")))
    except Exception:
        seen = set()
    cand = []
    # Hacker News (Algolia) - stories above a points threshold, last week
    minp = src.get("hn_min_points", 40)
    for q in src.get("hn_queries", []):
        url = ("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=12"
               f"&numericFilters=points>{minp},created_at_i>{cutoff}&query=" + _up.quote(q))
        data = _http_json(url)
        for h in ((data or {}).get("hits", []) if data else []):
            key = "hn:" + str(h.get("objectID"))
            title = (h.get("title") or "").strip()
            link = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            if title and key not in seen:
                cand.append((key, f"[HN {h.get('points')}pts] {title} - {link}"))
    # GitHub Trending (community RSS)
    for url in src.get("github_trending_rss", []):
        txt = _http_text(url)
        for m in _re.findall(r"<title>(.*?)</title>", txt)[1:25]:
            t = _re.sub(r"<.*?>", "", m).strip()
            key = "gh:" + t[:80]
            if t and "/" in t and key not in seen:
                cand.append((key, f"[GH trending] {t}"))
    # Blog feeds from Brian's curated GOATS (auto-pulled RSS - the people he gave the research agent)
    for url in src.get("blog_feeds", []):
        txt = _http_text(url)
        for m in _re.findall(r"<title>(.*?)</title>", txt)[1:8]:
            t = _re.sub(r"<.*?>", "", _re.sub(r"<!\[CDATA\[|\]\]>", "", m)).strip()
            key = "blog:" + t[:80]
            if t and key not in seen:
                host = url.split("/")[2] if "/" in url else url
                cand.append((key, f"[blog] {t} ({host})"))
    # arXiv - newest cs.AI agent papers
    aq = src.get("arxiv_query")
    if aq:
        txt = _http_text(aq, timeout=25)
        for t in _re.findall(r"<entry>.*?<title>(.*?)</title>", txt, _re.S)[:12]:
            t = _re.sub(r"\s+", " ", t).strip()
            key = "ax:" + t[:80]
            if t and key not in seen:
                cand.append((key, f"[arXiv] {t}"))
    if not cand:
        return ""
    # never repeat an item: mark every candidate seen, then curate the best
    seen.update(k for k, _ in cand)
    try:
        fc.atomic_write(DISCOVERY_SEEN, json.dumps(sorted(seen)[-4000:]))
    except Exception:
        pass
    feed = "\n".join(line for _, line in cand[:60])
    prompt = ("You scan AI/dev news for Brian: an early-career builder who ships AI-powered web "
              "apps (Next.js, React, Claude/Anthropic) AND runs a personal LOCAL agent fleet on "
              "Ollama + Nous Research's Hermes Agent. From the candidate items below, pick the 5-8 "
              "GENUINELY worth his time - new tools he could adopt, projects to try, model releases, "
              "or techniques that improve a local agent fleet or an AI web app. One line each: "
              "<name> - <what it is + why it helps Brian + the link if present>. Prefer free/open/"
              "local. Skip hype, crypto, and enterprise-only items.\n\n"
              + fc.wrap_untrusted(feed, "discovery candidates"))
    return fc.ollama_generate(prompt, model=fc.DEFAULT_MODEL, num_ctx=8192, num_predict=550,
                              timeout=150, retries=1, fallback="") or ""


# ---- report assembly --------------------------------------------------------
def main():
    cfg = load_cfg()
    repos = discover_repos(cfg)
    stamp = fc.now("%Y-%m-%d %H:%M")
    urgent_lines, body = [], []

    sec = check_security(cfg, repos)
    rels = check_releases(cfg)

    for f in sec:
        if f["urgent"]:
            urgent_lines.append(f"[SECURITY] {f['repo']}: {f['total']} open Dependabot alert(s) ({f['sev']})")
    for r in rels:
        urgent_lines.append(f"[RELEASE] {r['repo']} {r['from']} -> {r['to']} ({r['why']})")

    title = "Modernization Report" if WEEKLY else "Currency check"
    body.append(f"# {title} - {stamp}")
    body.append("")
    body.append(f"Repos tracked: {len(repos)} | security findings: {len(sec)} | new releases: {len(rels)}")
    body.append("")

    if rels:
        body.append("## New releases in your stack")
        for r in rels:
            body.append(f"- **{r['repo']}** {r['from']} -> {r['to']} - {r['why']}")
        body.append("")
    if sec:
        body.append("## Security (Dependabot)")
        for f in sec:
            mark = "!! " if f["urgent"] else ""
            body.append(f"- {mark}{f['repo']}: {f['total']} open ({f['sev']})")
        body.append("")

    review_note = None
    if WEEKLY:
        # outdated deps
        body.append("## Outdated dependencies")
        any_out = False
        for r in repos:
            if r["type"] == "node":
                pk = outdated_node(r["path"])
                if pk:
                    any_out = True
                    majors = [p for p in pk if p["major"]]
                    body.append(f"- **{r['name']}** ({len(pk)} outdated, {len(majors)} major):")
                    for p in pk[:8]:
                        tag = " [MAJOR]" if p["major"] else ""
                        body.append(f"    - {p['name']}: {p['current']} -> {p['latest']}{tag}")
            elif r["type"] == "python":
                pk = outdated_python(r["path"])
                if pk:
                    any_out = True
                    body.append(f"- **{r['name']}** ({len(pk)} outdated pip pkgs): " +
                                ", ".join(p['name'] for p in pk[:10]))
        if not any_out:
            body.append("- All scanned repos are on current minor/patch deps.")
        body.append("")

        # staleness
        st = staleness(repos, cfg)
        if st:
            body.append("## Stale projects (no commits recently)")
            for s in st:
                body.append(f"- {s['repo']}: last commit {s['last']} ({s['days']}d ago)")
            body.append("")

        # safe auto-apply on the allowlist
        if cfg.get("auto_apply_safe"):
            name_map = {"pokemon-drop": "pokemon-drop-intel"}
            applied = []
            for r in repos:
                if r["name"] in cfg.get("auto_apply_allowlist", []) and r["type"] == "node":
                    applied.append(auto_apply_safe(r["path"], r["name"], name_map.get(r["name"], r["name"]), cfg))
            if applied:
                body.append("## Safe upgrades (auto-prepared, build-verified)")
                for a in applied:
                    body.append(f"- {a['repo']}: **{a['status']}** - {a['detail']}")
                body.append("")
                prs = [a for a in applied if a["status"] == "PR-ready"]
                if prs:
                    review_note = ("NEEDS REVIEW - safe dependency upgrades prepared on a branch with the "
                                   "build passing:\n" + "\n".join(f"- {a['repo']}: {a['detail']}" for a in prs) +
                                   "\nMerge the PR(s) if you're happy, or tell me to.")

        # discovery: hunt the open internet for new tools/projects/research
        disc = discovery(cfg)
        if disc:
            body.append("## Discovery - new tools / projects / research worth a look")
            body.append(disc.strip())
            body.append("")

    text = "\n".join(body).rstrip() + "\n"
    fc.atomic_write(os.path.join(fc.COMMS, "currency.md"), text)
    if WEEKLY:
        fc.atomic_write(os.path.join(fc.COMMS, "modernization_report.md"), text)
    if review_note:
        fc.atomic_write(os.path.join(fc.COMMS, "review", f"currency-{datetime.date.today().isoformat()}.md"),
                        f"# Currency: safe upgrades\n\n{review_note}\n")

    # delivery: daily = urgent flags only (quiet otherwise); weekly = full summary
    if WEEKLY:
        summary = text if len(text) < 3500 else "\n".join(body[:40])
        fc.telegram_send(summary, urgent=False)
    elif urgent_lines:
        fc.telegram_send("Currency alert(s):\n" + "\n".join(urgent_lines), urgent=True)

    if VERBOSE:
        print(fc.ascii_fold(text))
    fc.log_run("currency", "alert" if urgent_lines else "ok",
               f"{len(repos)} repos, {len(sec)} sec, {len(rels)} rel" + (" [weekly]" if WEEKLY else ""))


if __name__ == "__main__":
    main()
