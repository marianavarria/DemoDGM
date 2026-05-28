"""
Esecuzione sandbox del codice generato da un LLM tramite Docker.

Il container:
- non ha accesso alla rete (--network=none)
- ha limiti CPU/RAM
- monta solo la cartella di lavoro in sola lettura

Se Docker non e' disponibile, evaluate_with_sandbox solleva RuntimeError.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import uuid
from typing import Any


FORBIDDEN_PATTERNS = [
    r"\bimport\s+os\b",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+sys\b",
    r"\bimport\s+shutil\b",
    r"\bimport\s+socket\b",
    r"\bimport\s+requests\b",
    r"\b__import__\s*\(",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bopen\s*\(",
    r"\bos\.",
    r"\bsubprocess\.",
]

DOCKER_IMAGE = os.environ.get("DGMH_SANDBOX_IMAGE", "python:3.12-slim")
DOCKER_TIMEOUT_SEC = int(os.environ.get("DGMH_SANDBOX_TIMEOUT", "30"))


def docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def code_is_safe(code: str) -> bool:
    """Blocca costrutti ovviamente pericolosi prima di mandare codice al container."""
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            return False
    return "def solve" in code


def _to_docker_path(path: str) -> str:
    """Converte un path Windows in formato accettato da Docker (-v)."""
    return os.path.abspath(path).replace("\\", "/")


def _build_runner_script(code: str, inputs: list[Any]) -> str:
    return (
        code.strip()
        + "\n\n"
        + "import json\n"
        + f"inputs = {json.dumps(inputs)}\n"
        + "results = []\n"
        + "for x in inputs:\n"
        + "    try:\n"
        + "        results.append(solve(x))\n"
        + "    except Exception as e:\n"
        + '        results.append({"__error__": str(e)})\n'
        + "print(json.dumps(results))\n"
    )


def run_in_docker(
    code: str,
    inputs: list[Any],
    workdir: str,
    run_id: str | None = None,
) -> list[Any]:
    """
    Esegue solve(x) su inputs dentro un container Docker.
    Restituisce la lista di output (o dict con __error__).
    """
    if not docker_available():
        raise RuntimeError(
            "Docker non disponibile. Installa Docker Desktop e verifica con: docker run hello-world"
        )
    if not code_is_safe(code):
        raise ValueError("Codice rifiutato dal filtro di sicurezza.")

    os.makedirs(workdir, exist_ok=True)
    run_id = run_id or uuid.uuid4().hex[:12]
    script_name = f"candidate_{run_id}.py"
    script_path = os.path.join(workdir, script_name)
    runner = _build_runner_script(code, inputs)

    with open(script_path, "w", encoding="utf-8") as file:
        file.write(runner)

    docker_workdir = _to_docker_path(workdir)
    command = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--cpus=1",
        "--memory=256m",
        "--stop-timeout=10",
        "-v",
        f"{docker_workdir}:/sandbox:ro",
        DOCKER_IMAGE,
        "python",
        f"/sandbox/{script_name}",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=DOCKER_TIMEOUT_SEC,
    )

    log_dir = os.path.join(os.path.dirname(workdir), "sandbox_logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{run_id}.log")
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("COMMAND:\n")
        log_file.write(" ".join(command) + "\n\n")
        log_file.write("STDOUT:\n")
        log_file.write(result.stdout or "")
        log_file.write("\n\nSTDERR:\n")
        log_file.write(result.stderr or "")
        log_file.write(f"\n\nEXIT CODE: {result.returncode}\n")

    if result.returncode != 0:
        raise RuntimeError(
            f"Sandbox Docker fallito (exit {result.returncode}): {result.stderr[:500]}"
        )

    stdout = (result.stdout or "").strip()
    if not stdout:
        raise RuntimeError("Sandbox Docker: stdout vuoto.")

    return json.loads(stdout.splitlines()[-1])


def evaluate_with_sandbox(
    code: str,
    data: list[tuple[Any, Any]],
    workdir: str,
    run_id: str | None = None,
) -> float:
    """Valuta un programma su un dataset usando il sandbox Docker."""
    inputs = [item for item, _ in data]
    expected = [exp for _, exp in data]
    try:
        predictions = run_in_docker(code, inputs, workdir, run_id=run_id)
    except (ValueError, RuntimeError, json.JSONDecodeError):
        return 0.0

    correct = 0
    for pred, exp in zip(predictions, expected):
        if isinstance(pred, dict) and "__error__" in pred:
            continue
        if pred == exp:
            correct += 1
    return correct / len(data) if data else 0.0
