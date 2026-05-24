# Day-1 Runbook — run the moment UiPath Labs credentials arrive

The single load-bearing unknown is whether we can observe an external agent's **intermediate tool calls / pre-action intent** through Maestro's Service task. This runbook settles it before any further platform build.

## Step 0 — Connect the coding agent (the AgentHack bonus, on camera)
```bash
npm i -g @uipath/cli
uip login                       # opens browser; reuse the AgentHack org credentials
uip skills install --agent claude
```
Expected: Claude Code can now pack/publish/deploy UiPath Solutions and run jobs.

## Step 1 — Minimal pipe
1. Create a trivial Maestro flow with one **"start and wait for external agent"** Service task pointing at the CrewAI agent in `sut/claims_agent.py` (run it as a reachable endpoint).
2. Add one Action Center human-approval gate.

## Step 2 — The go/no-go question
Trigger the flow and inspect the captured run.

- ✅ **You can see the agent's intermediate tool calls / pre-action intent** → architecture CONFIRMED. Proceed with the external-CrewAI agent-under-test. Continue Sub-plan B (B1→B6 in `SENTINEL_PLAN.md`).
- ❌ **Only final input/output is visible (no tool-call trace)** → PIVOT: make the agent-under-test a **UiPath-hosted coded agent** (`uipath` Python SDK; first-party hooks → guaranteed trajectory). The Sentinel engine (Tasks 2–9) is unchanged; only the agent-under-test moves.

## Step 3 — Log it
Record the result + any friction in `BUILD_NOTES.md`. This is real, specific platform feedback (Best Product Feedback prize).
