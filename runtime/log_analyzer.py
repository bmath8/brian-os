#!/usr/bin/env python3
"""Log analyzer - turns the write-only run_log.md into a health summary.
Parses lines of the form  'ISO | agent | tierN | status | detail [| Nms]'  and
reports, per agent: runs (window), failures, last status + time, and latency
(avg/max) when present. Writes comms/fleet_health.md so the dashboard + weekly
review can surface silent degradation (an agent failing for days, never alerting).

Run:  python3 log_analyzer.py [--days 7]
"""
import os, sys, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc


def analyze(days=7):
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    stats = {}
    for ln in fc.read(fc.RUN_LOG).splitlines():
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) < 4:
            continue
        ts_s, agent, _tier, status = parts[0], parts[1], parts[2], parts[3]
        try:
            ts = datetime.datetime.fromisoformat(ts_s)
        except Exception:
            continue
        if ts < cutoff:
            continue
        s = stats.setdefault(agent, {"runs": 0, "fail": 0, "last": None, "last_status": "", "ms": []})
        s["runs"] += 1
        if status.lower() not in ("ok", "alert"):
            s["fail"] += 1
        if s["last"] is None or ts > s["last"]:
            s["last"], s["last_status"] = ts, status
        m = re.search(r"(\d+)ms", ln)
        if m:
            s["ms"].append(int(m.group(1)))
    return stats


def render(stats, days=7):
    rows = []
    for agent in sorted(stats):
        s = stats[agent]
        avg = f"{sum(s['ms'])//len(s['ms'])}" if s["ms"] else "-"
        mx = f"{max(s['ms'])}" if s["ms"] else "-"
        fail_rate = f"{100*s['fail']//s['runs']}%" if s["runs"] else "-"
        last = s["last"].strftime("%m-%d %H:%M") if s["last"] else "-"
        rows.append((agent, s["runs"], s["fail"], fail_rate, s["last_status"], last, avg, mx))

    md = [f"# Fleet Health - last {days} days ({fc.now()})", "",
          "| Agent | Runs | Fails | Fail % | Last status | Last run | Avg ms | Max ms |",
          "|---|--:|--:|--:|---|---|--:|--:|"]
    md += [f"| {a} | {r} | {f} | {fr} | {ls} | {lr} | {av} | {mx} |"
           for (a, r, f, fr, ls, lr, av, mx) in rows]
    if not rows:
        md.append("| (no runs logged in window) | | | | | | | |")

    flags = [f"{a}: {f}/{r} runs failed" for (a, r, f, fr, ls, lr, av, mx) in rows if f]
    for a in stats:
        if stats[a]["last"] and (datetime.datetime.now() - stats[a]["last"]).total_seconds() > 36 * 3600:
            flags.append(f"{a}: no successful run in >36h")
    if flags:
        md += ["", "## Flags", *[f"- {x}" for x in flags]]
    return "\n".join(md) + "\n", flags


def main():
    days = 7
    if "--days" in sys.argv:
        try:
            days = int(sys.argv[sys.argv.index("--days") + 1])
        except Exception:
            pass
    stats = analyze(days)
    text, flags = render(stats, days)
    fc.atomic_write(f"{fc.COMMS}/fleet_health.md", text)
    print(text)
    fc.log_run("log_analyzer", "ok", f"{len(stats)} agents, {len(flags)} flags")


if __name__ == "__main__":
    main()
