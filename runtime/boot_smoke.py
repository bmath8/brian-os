#!/usr/bin/env python3
"""Boot / recovery smoke-test (#6). Runs a 5-second self-test of the things the
morning brief depends on, then messages Brian DIRECTLY via the Telegram Bot API
(not the gateway - so it lands even while the gateway is restarting).

Invoked by the keepalive: once when the keepalive loop starts (boot) and again
after any gateway REVIVE (recovery). An optional arg is a context label, e.g.
  python boot_smoke.py "Gateway revived"
A second optional arg carries a crash-loop warning (#5).

Exit 0 always (it's a notifier, never a blocker). Quiet (no Telegram) if the
result is all-green AND context is "boot" on a normal run? No - we always send
on boot/revive so Brian gets positive confirmation the fleet is alive.
"""
import os, sys, json, urllib.request, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fleet_common as fc

context = sys.argv[1] if len(sys.argv) > 1 else "Boot"
extra = sys.argv[2] if len(sys.argv) > 2 else ""


def _check(name, fn):
    try:
        ok, detail = fn()
        return (name, ok, detail)
    except Exception as e:
        return (name, False, f"{type(e).__name__}: {str(e)[:60]}")


def _ollama():
    data = json.load(urllib.request.urlopen(f"{fc.ollama_url()}/api/tags", timeout=6))
    models = [m.get("name", "") for m in data.get("models", [])]
    has = any(fc.SMALL_MODEL in m for m in models)
    return has, (fc.SMALL_MODEL if has else f"{fc.SMALL_MODEL} MISSING ({len(models)} models)")


def _telegram():
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        return False, "no token"
    r = json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getMe", timeout=8))
    return bool(r.get("ok")), ("@" + r.get("result", {}).get("username", "?") if r.get("ok") else "getMe failed")


def _env():
    have = all((os.environ.get(k) or "").strip() for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_HOME_CHANNEL"))
    return have, ("ok" if have else "missing telegram keys")


# Import names of the REQUIRED block in requirements.txt. Kept as import names
# (not pip names) because that is what actually fails at 6:45am. Added 2026-07-28
# after the calendar agent sat broken on a missing 'icalendar' with nothing to
# catch it -- every other check here was green while an agent was dead.
REQUIRED_IMPORTS = ("icalendar", "recurring_ical_events")


def _deps():
    import importlib.util
    missing = [m for m in REQUIRED_IMPORTS if importlib.util.find_spec(m) is None]
    if missing:
        return False, f"MISSING {', '.join(missing)} (pip install -r runtime/requirements.txt)"
    return True, f"{len(REQUIRED_IMPORTS)} required ok"


def main():
    checks = [_check("Ollama+model", _ollama), _check("Telegram", _telegram),
              _check(".env", _env), _check("Deps", _deps)]
    all_ok = all(ok for _, ok, _ in checks)
    icon = "✅" if all_ok else "⚠️"
    head = f"{icon} {context} - fleet health {fc.now()}"
    lines = [head] + [f"  {'✓' if ok else '✗'} {n}: {d}" for n, ok, d in checks]
    if extra:
        lines.append(f"⚠️ {extra}")
    msg = "\n".join(lines)
    # A crash loop or an unhealthy check is urgent (overrides quiet hours); a healthy
    # boot/recovery is not (no 3am ping just to say all-good).
    sent = fc.telegram_send(msg, urgent=bool(extra) or not all_ok)
    fc.log_run("boot_smoke", "ok" if all_ok else "alert", f"{context}; sent={sent}")
    print(msg)


if __name__ == "__main__":
    main()
