# Sentinel — Adversarial Reliability Testing for Agentic Workflows

> Sentinel is an agentic test harness that validates the quality and reliability of AI-infused workflows — adversarially probing whether their built-in governance controls actually hold before an agent acts on production business systems.

**UiPath AgentHack 2026 · Track 3: UiPath Test Cloud**

---

## The problem

Enterprises are putting AI agents into real business processes, but two gaps make that risky:

1. UiPath ships **detective guardrails** for agents — but no shipped way to **prove** they actually fire.
2. Native evaluators score an agent's **correctness** and **behavior**, but not whether it took an action that **violates business policy while still looking correct** (e.g. skipping a required human approval).

Today teams re-validate agents by hand or ship blind. **Sentinel is the missing certification layer:** it stress-tests an agent's controls and produces evidence they hold — before the agent reaches production.

## What it does

1. Takes an AI-infused workflow (a UiPath Maestro flow containing an AI agent + a human-approval gate).
2. Auto-generates focused **reliability test scenarios** native evaluations don't cover (HITL bypass, wait-state skip, tool-scope violation).
3. Runs them on **UiPath Test Cloud**, capturing each run's trajectory.
4. Renders a **verdict** from three layers: deterministic checks (this engine), **UiPath Agent Evaluations'** native LLM-as-judge (semantic similarity / faithfulness — we feed it, we don't rebuild it), and a hook-based pre-action interceptor as ground truth (this engine).
5. Produces a **Reliability Report** and, on critical findings, auto-files a **Jira** ticket + **Slack** alert.
6. Scores each run as a **Reliability Score (0–100)** and ranks every agent revision on a **leaderboard** — so a team watches a fix climb from FAILED to CERTIFIED across revisions. Sentinel isn't a one-shot test; it's a reliability **benchmark** for agents.

## How it works — a paired experiment

Sentinel runs every scenario under two conditions:

- **Detection (guardrail OFF):** the agent runs unguarded. A failing scenario is the evidence that, without controls, the violation *actually executes* in production.
- **Enforcement (guardrail ON):** the pre-action interceptor blocks the violation before it executes. A passing scenario is the evidence that the control *prevents* it.

Both halves are required — either one alone proves nothing. The **OFF → FAILED / ON → CERTIFIED** flip is the proof that the guardrails actually fire.

## Architecture

_(diagram added during build — see `docs/SENTINEL_DESIGN.md` for the full design)_

## UiPath components used

UiPath Test Cloud · Maestro · Agent Builder · Agent Evaluations · Action Center · API Workflows / Integration Service · UiPath for Coding Agents (Claude Code). External framework under test: CrewAI.

## Built with coding agents

Sentinel is built, tested, and deployed using **UiPath for Coding Agents (Claude Code)** via the UiPath CLI (`uip skills install --agent claude`). The build log is in `docs/BUILD_NOTES.md`.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -v
```

Prerequisites: Python 3.11+, and (for the agent-under-test and platform integration) Node.js 18+ with `@uipath/cli`, a UiPath Automation Cloud account, and CrewAI.

## Status

🚧 In active development for AgentHack 2026. Demo video: _(added in ship week)_.

## License

MIT — see [LICENSE](LICENSE).
