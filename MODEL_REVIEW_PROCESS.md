# Model Review Process — keep the fleet's models current
_Serves Brian's standing goal: "always be updating our models to the best for our computer."_

## The tool
`runtime/model_review.py` spot-checks every installed local Ollama model (latency + ok/fail on a
tiny prompt) and writes `comms/model_review.md` plus a refresh checklist. It's **safe on the
16 GB box** — tiny prompts, `keep_alive=0`, and a 60s per-model timeout so a model too heavy to
load right now is flagged, not left thrashing.

Run by hand anytime:
```
python3 ~/.hermes/scripts/model_review.py          # all installed models
python3 ~/.hermes/scripts/model_review.py --quick  # only the light ones (safe under memory pressure)
```

## Cadence: monthly
The review has two halves:
1. **Automated spot-check** (the script) — confirms what's installed still runs and how fast.
2. **Human/agent research pass** (the checklist the script prints):
   - Web-search "best local LLM <month> 12 GB VRAM" + scan the Ollama library for newer small models.
   - Compare any candidate vs the current default (`qwen3:8b`) on the fleet's real tasks.
   - Update `shared/models.json` + `shared/ROUTING.md`; refresh the cloud Tier-A ladder.
   - Re-check the RAM-upgrade trigger (64 GB → bigger local models are fine; set `BIG_MODEL` in `fleet_common.py`).

Last full research pass: `MODELS_AND_TOOLS_REVIEW_2026-06-17.md`.

## Enabling the monthly cron (do AFTER the reboot is confirmed)
Not wired yet — deliberately, to avoid touching the live scheduler right before a reboot. To enable
(monthly, 1st at 3am, deliver to Telegram), in WSL Ubuntu mirror how the other jobs were created:
```
hermes cron --help          # confirm exact flags for this Hermes version
# then add a job named 'model-review', schedule '0 3 1 * *', script model_review.py,
# deliver telegram:7910659638  — same shape as the daily-brief job.
systemctl --user restart hermes-gateway   # gateway caches cron at startup
```
Or just tell the assistant "enable the monthly model review" and it'll wire + verify it.
