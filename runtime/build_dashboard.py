#!/usr/bin/env python3
"""Build a self-contained HTML dashboard over the comms blackboard.
One glanceable file (comms/dashboard.html, no server, no external assets): per-agent
status, today's brief, system status, fleet-health flags, and RAM. Regenerate it
after the morning agents (or on demand). Observability is day-one infra (audit E2)."""
import os, sys, json, html, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc


def esc(x):
    return html.escape(str(x))


def main():
    st = fc.load_state()
    agents = st.get("agents", {})
    brief = fc.read(f"{fc.COMMS}/daily_brief.md")
    sysmd = fc.read(f"{fc.COMMS}/system_status.md")
    health = fc.read(f"{fc.COMMS}/fleet_health.md")
    try:
        r = json.load(open(f"{fc.COMMS}/resource_status.json"))
        ram = f"RAM {r.get('ram_free_gb','?')} GB free ({r.get('ram_pct','?')}% used) · commit {r.get('commit_pct','?')}%"
    except Exception:
        ram = "RAM: no probe yet"
    # Disk + guardian tiles (2026-07-11): today's cascade (dead guardian -> orphans ->
    # pagefile -> disk full) would have been visible here a day earlier.
    try:
        import shutil as _sh
        _free = _sh.disk_usage("C:\\" if fc.WINDOWS else "/")[2] / 1e9
        ram += f" · disk {_free:.0f} GB free"
    except Exception:
        pass
    try:
        _glog = os.path.join(fc.LOGS, ".guardian_beat")
        if not os.path.exists(_glog):
            _glog = os.path.join(fc.LOGS, "guardian.log")
        _gage = (datetime.datetime.now().timestamp() - os.path.getmtime(_glog)) / 60
        _glog = os.path.join(fc.LOGS, "guardian.log")
        _last = [l for l in fc.read(_glog).splitlines() if "RAM" in l][-1:]
        _reap = ""
        if _last and "reaped" in _last[0]:
            _reap = " · reaped " + _last[0].rsplit("reaped", 1)[1].strip()
        ram += f" · guardian {_gage:.0f}m ago{_reap}"
    except Exception:
        ram += " · guardian: no log"

    cards = []
    for name in sorted(agents):
        a = agents[name]
        status = a.get("status", "?")
        color = {"ok": "#1f9d55", "alert": "#d97706"}.get(status, "#888")
        needs = a.get("needs_human", []) or []
        needs_html = ("<ul>" + "".join(f"<li>{esc(n)}</li>" for n in needs) + "</ul>") if needs else ""
        cards.append(
            f'<div class="card"><div class="dot" style="background:{color}"></div>'
            f'<h3>{esc(name)}</h3>'
            f'<div class="meta">{esc(a.get("last_run","-"))} · <b style="color:{color}">{esc(status)}</b></div>'
            f'<div class="sum">{esc(a.get("summary",""))}</div>{needs_html}</div>')

    # Job-hunt banner (#54) - the mission, front and center.
    cst = agents.get("career", {})
    jobbanner = f'<div class="banner">🧭 Job hunt: {esc(cst.get("summary", ""))}</div>' if cst.get("summary") else ""

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="900">
<title>Brian OS Fleet</title>
<style>
 body{{font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0f1115;color:#e7e9ee}}
 header{{padding:18px 22px;background:#161922;border-bottom:1px solid #262a36}}
 header h1{{margin:0;font-size:18px}} header .sub{{color:#9aa3b2;font-size:13px;margin-top:4px}}
 .banner{{padding:12px 22px;background:#10241a;border-bottom:1px solid #1f6f46;color:#7ee2a8;font-weight:600}}
 .wrap{{padding:18px 22px;max-width:1100px;margin:0 auto}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}}
 .card{{background:#171a23;border:1px solid #262a36;border-radius:10px;padding:12px 14px;position:relative}}
 .card h3{{margin:0 0 2px;font-size:14px}} .dot{{width:9px;height:9px;border-radius:50%;position:absolute;top:14px;right:14px}}
 .meta{{color:#9aa3b2;font-size:12px}} .sum{{margin-top:6px;font-size:13px}}
 .card ul{{margin:6px 0 0;padding-left:18px;color:#f0b450;font-size:12px}}
 section{{margin-top:22px}} h2{{font-size:14px;color:#9aa3b2;text-transform:uppercase;letter-spacing:.04em}}
 pre{{background:#171a23;border:1px solid #262a36;border-radius:10px;padding:14px;white-space:pre-wrap;font:13px/1.5 ui-monospace,Menlo,monospace}}
</style></head><body>
<header><h1>☀️ Brian OS Fleet</h1><div class="sub">{esc(ram)} · generated {esc(fc.now())} · auto-refresh 15m</div></header>
{jobbanner}
<div class="wrap">
 <section><h2>Agents</h2><div class="grid">{''.join(cards) or '<div class="card">no state yet</div>'}</div></section>
 <section><h2>Today's brief</h2><pre>{esc(brief) or 'no brief yet'}</pre></section>
 <section><h2>Fleet health</h2><pre>{esc(health) or 'run log_analyzer.py'}</pre></section>
 <section><h2>System</h2><pre>{esc(sysmd) or 'no watchdog report yet'}</pre></section>
</div></body></html>"""

    out = f"{fc.COMMS}/dashboard.html"
    fc.atomic_write(out, page)
    print(f"Dashboard written: {out}")
    fc.log_run("build_dashboard", "ok", f"{len(agents)} agents")


if __name__ == "__main__":
    main()
