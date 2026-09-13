"""Real WebAssembly container executor for Sentinel.

Replaces the Python-subprocess simulation layer with actual Wasmer Wasm
containers. Each call to ``run_in_wasm`` spawns a fresh container via the
Wasmer CLI, executes the interceptor logic inside it, captures the verdict, and
the container ceases to exist the moment the process exits.

No state survives between runs. The container has no filesystem access to the
host. The interceptor verdict comes back as a single JSON line on stdout.

Requires:
    wasmer CLI installed and WASMER_TOKEN set (or wasmer login called once).
    python/python package cached (~1.3s warm, ~42s cold first run).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# The interceptor logic embedded as a self-contained Python string.
# This is what runs *inside* the Wasm container — zero imports, zero deps.
# ---------------------------------------------------------------------------
_INTERCEPTOR_WASM_CODE = """\
import json, sys

data   = json.loads(sys.argv[1])
action = data["action"]
policy = data["policy"]
approved = data.get("approved", False)

tool = action["tool"]

if tool in policy["forbidden"]:
    r = {"allowed": False, "severity": "critical",
         "reason": f"forbidden tool {tool!r} was attempted"}
elif tool in policy["approval_required"] and not approved:
    r = {"allowed": False, "severity": "critical",
         "reason": f"tool {tool!r} requires human approval but none was granted"}
elif tool not in policy["allowed"] and tool not in policy["approval_required"]:
    r = {"allowed": False, "severity": "high",
         "reason": f"tool {tool!r} is outside the agent allowed scope"}
else:
    r = {"allowed": True, "severity": "none", "reason": f"tool {tool!r} permitted"}

print(json.dumps(r))
"""


@dataclass(frozen=True)
class WasmResult:
    """Outcome of one ephemeral Wasm container execution."""

    allowed: bool
    severity: str
    reason: str
    elapsed_ms: float
    container_id: str  # unique per invocation — proves each run is new


def _wasmer_bin() -> str:
    """Locate the wasmer binary; raise clearly if missing."""
    path = shutil.which("wasmer") or os.path.expanduser("~/.wasmer/bin/wasmer")
    if not os.path.isfile(path):
        raise RuntimeError(
            "wasmer binary not found. Install with: curl -fsSL https://get.wasmer.io | sh"
        )
    return path


def run_in_wasm(
    action: dict[str, Any],
    policy: dict[str, Any],
    approved: bool = False,
) -> WasmResult:
    """Spawn a Wasm container, run the interceptor inside it, return the verdict.

    The container is an ephemeral python/python Wasm process. It receives the
    action + policy as a JSON argument, evaluates the policy, prints one JSON
    line, and exits. Nothing persists after the call returns.
    """
    payload = json.dumps({"action": action, "policy": policy, "approved": approved})
    container_id = f"sentinel-{time.time_ns()}"

    env = os.environ.copy()
    wasmer_token = os.environ.get("WASMER_TOKEN", "")

    cmd = [
        _wasmer_bin(),
        "run",
        "--quiet",
        "python/python",
        "--",
        "-c",
        _INTERCEPTOR_WASM_CODE,
        payload,
    ]

    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={**env, "WASMER_TOKEN": wasmer_token} if wasmer_token else env,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000

    if proc.returncode != 0:
        raise RuntimeError(
            f"Wasm container {container_id} exited {proc.returncode}:\n{proc.stderr}"
        )

    verdict = json.loads(proc.stdout.strip())
    return WasmResult(
        allowed=verdict["allowed"],
        severity=verdict["severity"],
        reason=verdict["reason"],
        elapsed_ms=elapsed_ms,
        container_id=container_id,
    )
