"""fleet-commands Hermes plugin - native slash commands for the agent fleet.

Registers /fleet /queue /approve /reject /grade /snooze in CLI + gateway sessions.
Each delegates to the tested handler in ~/.hermes/scripts/commands.py, which acts
only over the comms blackboard (file/queue/grade/snooze) - never sends/spends/deploys.

Because these are NATIVE registered commands, Hermes only routes matching slash
commands here; ordinary chat is never intercepted. Built-in name conflicts are
auto-skipped by Hermes with a warning.

Handler contract (hermes_cli.plugins.PluginContext.register_command):
    handler(raw_args: str) -> str | None   # returned string is delivered as the reply
"""
import os
import sys

# Find the fleet scripts dir on both native Windows (%LOCALAPPDATA%\hermes\scripts
# or $HERMES_HOME\scripts) and WSL (~/.hermes/scripts).
for _c in (os.path.join(os.environ.get("HERMES_HOME", ""), "scripts"),
           os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "scripts"),
           os.path.expanduser("~/.hermes/scripts")):
    if _c and os.path.isdir(_c):
        if _c not in sys.path:
            sys.path.insert(0, _c)
        break


def _make(verb):
    def _handler(raw_args: str = "") -> str:
        import commands as fleet  # imported lazily so a deploy in progress can't break load
        return fleet.handle(f"/{verb} {raw_args}".strip())
    return _handler


def register(ctx) -> None:
    # /fleet -> status (avoids any built-in /status conflict)
    ctx.register_command("fleet", _make("status"),
                         description="Fleet status (per-agent + snoozes)")
    # /queue and /approve collide with built-in Hermes commands (they get skipped),
    # so the fleet versions use non-colliding names.
    ctx.register_command("addtask", _make("queue"),
                         description="Add a task for tonight's overnight worker", args_hint="<task>")
    ctx.register_command("approvedraft", _make("approve"),
                         description="File an overnight draft as approved", args_hint="<id>")
    ctx.register_command("rejectdraft", _make("reject"),
                         description="File an overnight draft as rejected", args_hint="<id>")
    ctx.register_command("grade", _make("grade"),
                         description="Grade a recall card", args_hint="<id> 1|0")
    ctx.register_command("snooze", _make("snooze"),
                         description="Mute an agent's Needs-you items", args_hint="<agent> <days>")
    ctx.register_command("research", _make("research"),
                         description="Research KB status, or queue a tweet/link", args_hint="[text or url]")
    ctx.register_command("watchlist", _make("watchlist"),
                         description="Show the X watchlist, or add an account", args_hint="[@handle]")
    ctx.register_command("digest", _make("digest"),
                         description="End-of-day wrap: done / open / tomorrow")
    ctx.register_command("ask", _make("ask"),
                         description="Ask about your world (runway, #1, saved notes)", args_hint="<question>")
    ctx.register_command("tailor", _make("tailor"),
                         description="Draft a tailored application kit from a JD", args_hint="<job description>")
    ctx.register_command("prep", _make("prep"),
                         description="Interview prep: likely questions + your angles", args_hint="<role|jd>")
    ctx.register_command("code", _make("code"),
                         description="Coding help from qwen3-coder", args_hint="<question>")
    ctx.register_command("network", _make("network"),
                         description="Log a networking touch", args_hint="<note>")
