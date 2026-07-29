# QLoRA Self-Learning Runbook (Tier-2 #6) — ready to execute

Goal: a monthly LoRA fine-tune of qwen3-8b on Brian's OWN approved drafts, so the
fleet's default model progressively writes more like Brian. Confirmed feasible on
the 4070 (Unsloth QLoRA: ~7.2 GB peak VRAM, ~90 min/run).

## Training data the fleet ALREADY collects
- `comms/review/approved/*.md` — drafts Brian approved (style ground truth)
- `comms/review/rejected/*.md` — negative examples (what NOT to sound like)
- `logs/trajectory.jsonl` — tool-use patterns (later; text style first)
- voice samples — once Brian feeds `voice-match` 3-5 real writing samples

## One-time setup (~20 min, needs ~6 GB disk)
```powershell
python -m venv C:\Brian\tools\unsloth-venv
C:\Brian\tools\unsloth-venv\Scripts\pip install unsloth  # pulls torch cu124
```

## Monthly run (overnight; do NOT run while daytime apps need the GPU)
1. Build the dataset (approved drafts -> chat-format JSONL):
   instruction = the draft's task header, response = the approved text.
   Threshold: need 30+ approved drafts before a run is worth it (currently ~0 —
   approve more drafts first; this is the REAL gate, not GPU).
2. Train: Unsloth QLoRA, qwen3-8b base, r=16, 2-3 epochs, ~90 min.
3. Export: merge LoRA -> GGUF q4_K_M -> `ollama create brian-8b -f Modelfile`.
4. Eval: `python tests\eval_models.py` A/B brian-8b vs qwen3:8b on the fleet's
   5 real task types + a style-match judge pass.
5. Adopt ONLY if it wins: set `FLEET_MODEL=brian-8b` in .env (one place, reversible).

## Guardrails
- Never train on rejected/unreviewed text as positives.
- Keep the base model installed — rollback is `FLEET_MODEL=qwen3:8b`.
- Redact secrets/PII from the dataset (reuse fc.redact_secrets / redact_pii).
- Log every run + eval verdict here.

Refs: unsloth.ai/docs/models/tutorials/qwen3-how-to-run-and-fine-tune ·
buildmvpfast.com/blog/fine-tune-llm-laptop-qlora-local-gpu-2026
