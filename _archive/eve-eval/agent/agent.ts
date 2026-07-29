import { defineAgent } from "eve";

// Model resolves via Vercel AI Gateway (no provider keys to manage on deploy).
// Per our ROUTING doctrine: a strong-but-cheap Tier-A model for tailoring; you can
// swap to a frontier model (anthropic/claude-opus-4-8) for the final "going out with
// my name on it" pass. Cheap Tier-A alternatives: moonshotai/kimi-k2.7-code,
// google/gemini-3.1-pro (see ../MODELS_AND_TOOLS_REVIEW_2026-06-17.md).
export default defineAgent({
  model: "anthropic/claude-sonnet-4.6",
});
