# Sentinel — Adversarial Reliability Testing for Agentic Workflows

> Sentinel is an agentic test harness that validates the quality and reliability of AI-infused workflows — adversarially probing whether their built-in governance controls actually hold before an agent acts on production business systems.

**SF Hackathon 2026 · Prize Tracks: Main ($1,000 USD) · Wasmer ($5,000 credits) · Tenki ($10,000 credits)**

---

## The Problem

Enterprises are putting AI agents into real business processes, but two critical gaps make that risky:

1. Systems ship **detective guardrails** for agents — but have no deterministic way to **prove** they actually fire.
2. Native LLM-as-judge evaluators score an agent's **correctness** and **semantic tone**, but cannot prove whether an action took a path that **violates strict business policy while still looking correct** (e.g. skipping a required human approval or invoking unauthorized tools).

Today teams re-validate agents by hand or ship blind. **Sentinel is the deterministic certification layer:** it stress-tests an agent's controls and produces auditable cryptographic evidence that they hold — before the agent reaches production.

---

## Key Architecture & Prize Tracks

Sentinel enforces governance through isolated, disposable execution boundaries where untrusted agent actions are evaluated against pure contracts:

### 1. Main Track: Deterministic Policy Contracts & Benchmark Leaderboard
- Evaluates agent actions against strict, machine-enforceable `PolicyContract` definitions (`allowed`, `approval_required`, `forbidden`).
- Dual-oracle audit: real-time pre-action interception coupled with post-trajectory deterministic verification.
- Tracks agent reliability scores (0–100) across revisions on an auditable leaderboard (FAILED → CERTIFIED).

### 2. Wasmer Track: Ephemeral WebAssembly Sandbox (`sentinel/wasm_runner.py`)
- Evaluates the interceptor inside a fresh WebAssembly container spawned via the Wasmer SDK.
- The container executes the PolicyContract logic in a microsecond sandbox and is destroyed the moment the verdict returns.
- **Zero persistent process. Zero state. Nothing to escape from.**

### 3. Tenki Cloud Track: Remote Disposable Linux VM Sandboxes (`sentinel/tenki_runner.py`)
- Offloads enforcement and adversarial scenario execution to remote ephemeral Linux VMs via the Tenki CLI.
- Boots in sub-seconds with zero host filesystem access, isolated network boundaries, and per-second billing.
- Demonstrates agent confinement inside cloud-native disposable virtualization.

---

## How It Works — A Paired Experiment

Sentinel runs every scenario under two conditions:

- **Detection (Guardrail OFF):** The agent runs unguarded. Failing scenarios prove that, without controls, LLM-prompted violations *actually execute* against business tools (Score: **0 / 100 FAILED**).
- **Enforcement (Guardrail ON):** The pre-action interceptor enforces the PolicyContract gate before any tool invocation. Passing scenarios prove the violation was blocked before execution (Score: **100 / 100 CERTIFIED**).

Both halves are required — either one alone proves nothing. The **OFF → FAILED / ON → CERTIFIED** flip is deterministic proof that the control works.

---

## Test Suite & Verification

Sentinel is strictly tested with full deterministic regression coverage:

```bash
# Set up environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run full test suite (47 / 47 passing)
pytest -v
```

```text
tests/test_contracts.py ........                                         [ 17%]
tests/test_e2e.py ...                                                    [ 23%]
tests/test_interceptor.py .....                                          [ 34%]
tests/test_leaderboard.py ...                                            [ 40%]
tests/test_notify.py ..                                                  [ 44%]
tests/test_red_agent.py .....                                            [ 55%]
tests/test_report.py ...                                                 [ 61%]
tests/test_scenarios.py ....                                             [ 70%]
tests/test_score.py .....                                                [ 80%]
tests/test_sut.py .....                                                  [ 91%]
tests/test_verdict.py ....                                               [100%]
============================== 47 passed in 0.72s ==============================
```

---

## Running the Demo

Sentinel features a side-by-side terminal demo and synchronized AppKit teleprompter:

```bash
# Configure API keys in .env:
# ANTHROPIC_API_KEY=...
# WASMER_TOKEN=...
# TENKI_SESSION=sentinel-demo

# Launch split-screen demo
bash run_demo.sh
```

---

## License

[PolyForm Noncommercial 1.0.0](LICENSE) — free for noncommercial use.
Commercial licensing: matrixbuilderops@proton.me
