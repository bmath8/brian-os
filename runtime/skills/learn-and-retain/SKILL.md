---
name: learn-and-retain
description: Use when Brian wants to understand a concept and actually remember it - "explain X", "teach me about Y", "I keep forgetting how Z works", "help me learn this". Ties into the fleet's spaced-repetition loop so what he learns sticks.
---

# Learn & Retain

Teach Brian a concept clearly AND wire it into his spaced-repetition system so it isn't forgotten. This serves his stated goal: find an effective way to learn and actually retain.

## Do
1. **Explain the concept** in plain language: a one-line gist, then the mental model, then a concrete example (ideally tied to his stack - React/TS, Next.js, Python, Node, AI agents). Short, not a textbook dump.
2. **Check understanding:** ask Brian one quick question to confirm it landed; correct gently if needed.
3. **Make it stick - write a recall note** for the learning agent to turn into spaced-repetition cards. Append to a file in the fleet's learn inbox:
   - Path: `C:\Brian\02_Projects\brian-os-fleet\comms\learn\<short-topic-slug>.md`
   - Content: a `# <topic>` heading, a 2-3 sentence summary, and 2-3 active-recall **questions** (no answers). The nightly learning agent picks these up and surfaces them in the morning brief's Recall section.
4. Confirm to Brian: "Added N recall questions on <topic> - they'll show up in your morning brief."

## Rules
- Accuracy first - if unsure, say so rather than inventing. Keep explanations tight and example-driven.
- Always create the learn-inbox note (that's what makes this different from a normal answer). Use a clean slug for the filename.
