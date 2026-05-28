"""
Meta-agent che usa Ollama (via LiteLLM) per generare patch di codice.
"""

from __future__ import annotations

import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from common import ArchiveEntry, CandidateProgram, HyperAgent


DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "ollama/llama3.2")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")


@dataclass
class LLMMetaAgent:
    """
    Meta-agent basato su Ollama. Non eredita MetaAgent perche' non usa
    hidden_candidates: ogni iterazione chiede nuove patch al modello.
    """

    model: str = DEFAULT_MODEL
    task_description: str = ""
    train_data: list[tuple[Any, Any]] = field(default_factory=list)
    num_candidates: int = 1
    temperature: float = 0.2
    mutation_memory: list[str] = field(default_factory=list)
    request_log: list[dict[str, str]] = field(default_factory=list)

    def clone(self) -> "LLMMetaAgent":
        cls = type(self)
        return cls(
            model=self.model,
            task_description=self.task_description,
            train_data=list(self.train_data),
            num_candidates=self.num_candidates,
            temperature=self.temperature,
            mutation_memory=list(self.mutation_memory),
            request_log=list(self.request_log),
        )

    def generate_candidates(
        self,
        parent: "HyperAgent",
        archive: list["ArchiveEntry"],
    ) -> list["CandidateProgram"]:
        from common import CandidateProgram

        parent_code = parent.task_agent.program.code
        failures = _failed_examples(parent_code, self.train_data)
        prompt = _build_prompt(
            task_description=self.task_description,
            parent_code=parent_code,
            train_data=self.train_data,
            failures=failures,
            archive=archive,
        )

        candidates: list[CandidateProgram] = []
        for index in range(self.num_candidates):
            raw = _call_ollama(
                model=self.model,
                prompt=prompt,
                temperature=self.temperature,
            )
            self.request_log.append(
                {"prompt": prompt, "response": raw, "model": self.model}
            )
            code = _extract_python_code(raw)
            if not code or "def solve" not in code:
                self.mutation_memory.append(
                    f"Risposta LLM non valida (iter {parent.generation}, cand {index})."
                )
                continue
            candidates.append(
                CandidateProgram(
                    name=f"llm_gen_{parent.generation}_{index}",
                    description=f"Patch generata da {self.model}",
                    code=code,
                )
            )
        return candidates


def ollama_available(base_url: str = OLLAMA_BASE_URL) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/api/tags", timeout=3) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _call_ollama(model: str, prompt: str, temperature: float) -> str:
    try:
        from litellm import completion
    except ImportError as exc:
        raise RuntimeError(
            "Serve litellm. Attiva il venv e installa: pip install litellm"
        ) from exc

    if not ollama_available():
        raise RuntimeError(
            "Ollama non raggiungibile su http://localhost:11434. "
            "Avvia Ollama Desktop oppure: ollama serve"
        )

    os.environ.setdefault("OLLAMA_API_BASE", OLLAMA_BASE_URL)

    response = completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        timeout=120,
    )
    return response.choices[0].message.content or ""


def _extract_python_code(text: str) -> str | None:
    blocks = re.findall(r"```(?:python)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if blocks:
        return blocks[-1].strip()
    if "def solve" in text:
        return text.strip()
    return None


def _failed_examples(code: str, train_data: list[tuple[Any, Any]]) -> list[str]:
    from common import CandidateProgram, HyperAgent, MetaAgent, TaskAgent

    agent = HyperAgent(
        task_agent=TaskAgent(
            CandidateProgram("tmp", "tmp", code)
        ),
        meta_agent=MetaAgent(base_candidates=[]),
    )
    lines = []
    for item, expected in train_data:
        try:
            pred = agent.solve(item)
        except Exception as exc:
            pred = f"ERROR: {exc}"
        if pred != expected:
            lines.append(f"- solve({item!r}) -> {pred!r}, atteso {expected!r}")
    return lines[:6]


def _build_prompt(
    *,
    task_description: str,
    parent_code: str,
    train_data: list[tuple[Any, Any]],
    failures: list[str],
    archive: list["ArchiveEntry"],
) -> str:
    best_score = max((e.train_score for e in archive), default=0.0)
    train_lines = "\n".join(f"  - solve{inp} == {out}" for inp, out in train_data[:6])
    fail_block = (
        "\n".join(failures)
        if failures
        else "  (nessun dettaglio, migliora comunque il codice)"
    )
    return f"""Sei un meta-agent che migliora codice Python per un task di programmazione.

TASK:
{task_description}

CODICE ATTUALE (da migliorare):
```python
{parent_code.strip()}
```

ESEMPI DI TRAINING (input -> output atteso):
{train_lines}

TEST FALLITI CON IL CODICE ATTUALE:
{fail_block}

Miglior score in archivio finora: {best_score:.2f}

Scrivi UNA nuova implementazione della funzione:

def solve(x):
    ...

Regole:
- Rispondi SOLO con un blocco ```python ... ```
- Non usare import, eval, exec, open, subprocess o accesso al filesystem.
- x e' una tupla (a, b) di numeri.
- La funzione deve restituire un numero.
"""

