# Agent 17 — Gig Scanner
_Second income lane: freelance/contract gigs matching Brian's real stack._

- **Owns:** the "Gigs" section of the brief + proposal-draft queueing.
- **Why it exists:** income while the job hunt runs — contract React/Python/AI gigs. _Solves:_ single income dependency.
- **Cadence:** Mon–Sat 7:10 AM (cron `gig-scanner`, `no_agent` script `gig_scanner.py`).
- **Tier/model:** **free, no-key sources** (RemoteOK JSON + WeWorkRemotely RSS), cached (TTL 6h); deterministic scoring. No model needed for discovery.
- **Deliver:** writes `comms/gigs.md` + `state.json` slice; queues strong matches for the overnight worker.

## What it does (as implemented)
- Scans free feeds for AI-app / React / Python gigs matching Brian's stack.
- Scores deterministically by keyword fit; gates on the *title* (description blobs false-positive).
- Strong matches (score ≥4) get queued as proposal drafts → `comms/queue/` → overnight worker → `comms/review/` (draft-only).
- All external text wrapped `wrap_untrusted`.

## Output (writes)
- `comms/gigs.md` — the Gigs section source.
- `comms/queue/*.md` — proposal-draft requests (for the overnight worker).
- `state.json` slice `gigs`.

## Hard rule
Read-only discovery + draft queueing. Never contacts clients or sends proposals. Brian approves every draft.

## Done-when
Top matches in the brief; strong matches queued (not sent); no false positives from blob text.
