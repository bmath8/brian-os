---
name: plan-first
description: Use BEFORE writing or changing code for any non-trivial task (a new feature, a refactor, a multi-file change, anything you're unsure about). Triggers on "build...", "add...", "implement...", "fix...", "change..." when the work touches more than one obvious line. Produces a short written plan with acceptance criteria and explicit out-of-scope BEFORE any code is written. Skip only for one-line/typo fixes.
---

# Plan First

Turn the request into a short written plan before touching code. Plans are cheap; wrong code is expensive. Freeze success criteria *before* results exist so you can't move the goalposts.

## Produce this plan (keep it tight — markdown, not prose)
1. **Goal** — one sentence: what's true when this is done.
2. **Acceptance criteria** — 3–6 checkable bullets. Each must be testable ("login returns 401 on bad password", not "auth works"). These are frozen — don't edit them after seeing results.
3. **Out of scope** — what you are explicitly NOT doing this pass (prevents scope creep).
4. **Files to touch** — the specific files/functions you expect to create or change.
5. **Build sequence** — the ordered steps. Note any step that's risky or irreversible.
6. **How it's verified** — the exact command/test/observation that proves each acceptance criterion (a test run, a screenshot, a curl). Tie every "done" claim to a real result.

## Rules
- **No code until the plan exists.** For anything beyond a trivial fix, write the plan first and (for big changes) get Brian's nod.
- If the task is vague, ask 1–3 clarifying questions before planning — don't guess at scope.
- If you hit a loop or the plan stops matching reality mid-build, **STOP and re-plan** rather than thrashing.
- Code lives in `C:\Brian` + git, never OneDrive. Branch for non-trivial work.
- Mark anything hard-to-reverse (deletes, deploys, schema changes) and get explicit approval for those steps.

## Done when
There's a written plan with frozen, testable acceptance criteria and an explicit verification step for each — and (for non-trivial work) Brian has seen it before implementation starts.
