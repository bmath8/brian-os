#!/usr/bin/env python3
"""Calendar agent - reads TODAY's calendar into comms/calendar.md for the morning brief.

Two sources (first one configured wins):
  1. Google Calendar via its PRIVATE iCal URL (recommended - Brian's calendar is Google,
     synced to his iPhone). In Google Calendar: Settings -> <your calendar> -> Integrate
     calendar -> "Secret address in iCal format". Put it in %LOCALAPPDATA%\\hermes\\.env:
        GCAL_ICS_URL=https://calendar.google.com/calendar/ical/.../basic.ics
  2. iCloud via CalDAV (APPLE_ID + APPLE_APP_PASSWORD) - fallback.

Shows today's events; if today is empty, shows the next upcoming event so the brief is
still useful on light days. Read-only; never modifies the calendar. Degrades to a
"(not configured)" line (which the brief omits) if nothing is set up.

Deps (installed via uv): caldav, icalendar, recurring-ical-events.
"""
import os, sys, datetime, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

UA = "Mozilla/5.0 (BrianOS calendar agent)"


def _load_env():
    if any(os.environ.get(k) for k in ("GCAL_ICS_URL", "APPLE_ID")):
        return
    for envpath in (os.path.join(os.environ.get("HERMES_HOME", ""), ".env"),
                    os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", ".env"),
                    os.path.expanduser("~/.hermes/.env")):
        if envpath and os.path.isfile(envpath):
            for line in fc.read(envpath).splitlines():
                s = line.strip()
                for key in ("GCAL_ICS_URL=", "APPLE_ID=", "APPLE_APP_PASSWORD="):
                    if s.startswith(key):
                        k, _, v = s.partition("=")
                        os.environ.setdefault(k.strip(), v.strip())
            break


def _show_time(dtv):
    if isinstance(dtv, datetime.datetime):
        return dtv.strftime("%H:%M")
    return "all-day"


def _collect_google(url):
    """Fetch the private iCal feed and expand events for today + the next 30 days."""
    import icalendar
    import recurring_ical_events
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=30).read()
    cal = icalendar.Calendar.from_ical(raw)
    today = datetime.date.today()
    horizon = today + datetime.timedelta(days=30)
    occurrences = recurring_ical_events.of(cal).between(today, horizon)
    today_events, upcoming = [], []
    for ev in occurrences:
        try:
            summary = str(ev.get("summary", "(busy)"))
            dtv = ev.get("dtstart").dt
            d = dtv.date() if isinstance(dtv, datetime.datetime) else dtv
            loc = str(ev.get("location", "") or "")
            rec = (d, _show_time(dtv), summary, loc)
            if d == today:
                today_events.append(rec)
            elif d > today:
                upcoming.append(rec)
        except Exception:
            continue
    today_events.sort(key=lambda r: r[1])
    upcoming.sort(key=lambda r: (r[0], r[1]))
    return today_events, upcoming


def _collect_icloud(aid, pw):
    import caldav
    today = datetime.date.today()
    start = datetime.datetime.combine(today, datetime.time.min)
    end = datetime.datetime.combine(today, datetime.time.max)
    client = caldav.DAVClient(url="https://caldav.icloud.com/", username=aid, password=pw)
    out = []
    for cal in client.principal().calendars():
        try:
            for ev in cal.search(start=start, end=end, event=True, expand=True):
                comp = ev.icalendar_component
                ds = comp.get("dtstart")
                dtv = ds.dt if ds is not None else None
                out.append((today, _show_time(dtv), str(comp.get("summary", "(busy)")),
                            str(comp.get("location", "") or "")))
        except Exception:
            continue
    return out, []


def main():
    _load_env()
    stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    gurl = os.environ.get("GCAL_ICS_URL")
    aid, pw = os.environ.get("APPLE_ID"), os.environ.get("APPLE_APP_PASSWORD")

    if not (gurl or (aid and pw)):
        fc.atomic_write(f"{fc.COMMS}/calendar.md",
                        "# Calendar\n(not configured - set GCAL_ICS_URL or APPLE creds in .env)\n")
        fc.log_run("calendar", "ok", "not configured")
        return

    try:
        if gurl:
            today_events, upcoming = _collect_google(gurl)
        else:
            today_events, upcoming = _collect_icloud(aid, pw)
    except Exception as e:
        fc.atomic_write(f"{fc.COMMS}/calendar.md", f"# Calendar - {stamp}\n(calendar fetch failed: {e})\n")
        fc.log_run("calendar", "alert", "fetch failed")
        return

    lines = [f"# Calendar - {stamp}"]
    if today_events:
        for _, shown, summary, loc in today_events:
            lines.append(f"- {shown}  {summary}" + (f"  @ {loc}" if loc else ""))
    elif upcoming:
        d, shown, summary, loc = upcoming[0]
        lines.append(f"- (nothing today) Next: {d.strftime('%a %b %d')} {shown} {summary}")
    else:
        lines.append("- (no events today)")
    fc.atomic_write(f"{fc.COMMS}/calendar.md", "\n".join(lines) + "\n")
    fc.state_update("calendar", {"last_run": stamp, "status": "ok",
                                 "summary": f"{len(today_events)} today", "needs_human": []})
    print(f"Calendar: {len(today_events)} today, {len(upcoming)} upcoming")
    fc.log_run("calendar", "ok", f"{len(today_events)} today")


if __name__ == "__main__":
    main()
