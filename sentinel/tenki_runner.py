"""Tenki Cloud sandbox executor for Sentinel.

Mirrors wasm_runner.py but executes the interceptor inside a live remote
Tenki Linux sandbox instead of a local Wasm container. Each verdict is
evaluated inside an ephemeral full Linux VM (~100ms exec time). The sandbox
has no access to the host filesystem and is isolated from the network by
default.

Requires:
    tenki CLI installed and authenticated (tenki login --api-key <token>).
    A running sandbox session ID or name passed as TENKI_SESSION env var,
    or 'sentinel-demo' by default.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Any

_INTERCEPTOR_CODE = """\
import json, sys
data = json.loads(sys.argv[1])
action = data['action']
policy = data['policy']
approved = data.get('approved', False)
tool = action['tool']
if tool in policy['forbidden']:
    r = {'allowed': False, 'severity': 'critical', 'reason': f'forbidden tool {repr(tool)} was attempted'}
elif tool in policy['approval_required'] and not approved:
    r = {'allowed': False, 'severity': 'critical', 'reason': f'tool {repr(tool)} requires human approval but none was granted'}
elif tool not in policy['allowed'] and tool not in policy['approval_required']:
    r = {'allowed': False, 'severity': 'high', 'reason': f'tool {repr(tool)} is outside the agent allowed scope'}
else:
    r = {'allowed': True, 'severity': 'none', 'reason': f'tool {repr(tool)} permitted'}
print(json.dumps(r))
"""


@dataclass(frozen=True)
class TenkiResult:
    """Outcome of one Tenki sandbox interceptor execution."""

    allowed: bool
    severity: str
    reason: str
    elapsed_ms: float
    sandbox_id: str


def _tenki_bin() -> str:
    path = (
        shutil.which("tenki")
        or os.path.expanduser("~/.local/bin/tenki")
    )
    if not os.path.isfile(path):
        raise RuntimeError(
            "tenki CLI not found. Install: curl -fsSL https://tenki.cloud/install.sh | bash"
        )
    return path


def run_in_tenki(
    action: dict[str, Any],
    policy: dict[str, Any],
    approved: bool = False,
    session: str | None = None,
) -> TenkiResult:
    """Execute the interceptor inside a live Tenki Linux sandbox.

    The sandbox is a remote ephemeral VM. The interceptor logic runs as a
    one-shot python3 command; the result comes back as a single JSON line.
    Nothing is written to the sandbox filesystem.
    """
    session = session or os.environ.get("TENKI_SESSION", "sentinel-demo")
    payload = json.dumps({"action": action, "policy": policy, "approved": approved})
    # Escape single quotes in payload for sh -c wrapping
    safe_payload = payload.replace("'", "'\\''")
    code = _INTERCEPTOR_CODE.replace("'", "'\\''")
    shell_line = f"python3 -c '{code}' '{safe_payload}'"

    cmd = [
        _tenki_bin(), "sandbox", "exec",
        "--session", session,
        "-c", f"python3 -c \"{_INTERCEPTOR_CODE.strip()}\" '{safe_payload}'",
    ]

    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    if proc.returncode != 0:
        raise RuntimeError(f"Tenki sandbox exec failed:\n{proc.stderr}\n{proc.stdout}")

    # stdout contains the JSON verdict line + status lines — take first JSON line
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            verdict = json.loads(line)
            return TenkiResult(
                allowed=verdict["allowed"],
                severity=verdict["severity"],
                reason=verdict["reason"],
                elapsed_ms=elapsed_ms,
                sandbox_id=session,
            )

    raise RuntimeError(f"No JSON verdict in Tenki output:\n{proc.stdout}")
