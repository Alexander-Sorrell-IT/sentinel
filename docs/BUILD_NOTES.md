# Build Notes & Product Feedback Log

> Running log of friction, gaps, and suggestions encountered while building Sentinel on the UiPath platform. This file is the basis for the AgentHack **Best Product Feedback** submission. Append an entry every session — date · component · what happened · suggestion.

---

### 2026-05-24 · AgentHack resources page · gap
The AgentHack resources hub lists material for Agent Builder, Maestro, API Workflows, Coded Agents, and Document Understanding — but **no UiPath Test Cloud-specific resource**, even though Test Cloud is one of the three tracks. Suggestion: add a Test Cloud quickstart + sample to the resources hub for Track 3 participants.

### 2026-05-24 · UiPath Agent Evaluations docs · clarity
The native Agent Evaluations docs are written entirely around UiPath-built agents; whether/how external (CrewAI/LangChain) agents can be evaluated is not stated either way. Suggestion: explicitly document the supported path for evaluating external/coded agents (the Python SDK route) vs. the low-code Evaluations UI.

### 2026-05-24 · Engine (Sub-plan A) complete · note for Sub-plan B
Offline engine built + TDD'd (33 tests) against a *deterministic model* of the agent trajectory. Heads-up for Sub-plan B: the first 1–2 hours after credentials will be adapting the trajectory adapter to *real* CrewAI/Maestro traces — field names and tool-call structure may differ from the model. Contracts use `extra="forbid"`, so any drift fails loudly rather than silently (good). Run the Day-1 trajectory gate (docs/DAY1_RUNBOOK.md) before assuming the shape.
