"""
Demo 7: mini code-repair con meta-agent Ollama e valutazione in sandbox Docker.

Prerequisiti:
  1. Docker Desktop avviato (docker run hello-world)
  2. Modalita' LLM reale (default): Ollama su http://localhost:11434
     - installa da https://ollama.com
     - poi: ollama pull llama3.2
     - pip install litellm  (oppure: pip install -r requirements.txt)
  3. Modalita' mock (--mock): solo Docker, nessun Ollama ne' litellm

Variabili d'ambiente opzionali:
  OLLAMA_MODEL=ollama/llama3.2
  OLLAMA_API_BASE=http://localhost:11434
  DGMH_SANDBOX_IMAGE=python:3.12-slim
  DGMH_LLM_ITERATIONS=12
  DGMH_LLM_SEEDS=2

Uso:
  python experiments/llm_code_repair.py
  python experiments/llm_code_repair.py --mock    # senza Ollama (solo test sandbox)

Output:
  results/llm_code_repair_mock.csv | llm_code_repair_real.csv  (per modalita')
  results/llm_code_repair.csv       (combinato, colonna mode)
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Permette import da experiments/ quando lo script e' lanciato dalla root.
_EXPERIMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _EXPERIMENTS_DIR not in sys.path:
    sys.path.insert(0, _EXPERIMENTS_DIR)

from common import (
    CandidateProgram,
    best_by_iteration,
    merge_csv_variants,
    plot_csv,
    run_dgm_h,
    select_score_child_prop,
    write_csv,
)
from llm_meta_agent import LLMMetaAgent, ollama_available
from sandbox import docker_available, evaluate_with_sandbox

ROOT = os.path.dirname(_EXPERIMENTS_DIR)
RESULTS = os.path.join(ROOT, "results")
RUNS_DIR = os.path.join(ROOT, "runs")
LLM_LOGS = os.path.join(RESULTS, "llm_logs")

ITERATIONS = int(os.environ.get("DGMH_LLM_ITERATIONS", "12"))
SEEDS = range(int(os.environ.get("DGMH_LLM_SEEDS", "2")))

TRAIN_DATA = [
    ((1, 2), 3),
    ((0, 0), 0),
    ((5, 7), 12),
    ((-1, 4), 3),
    ((10, -3), 7),
]

TEST_DATA = [
    ((2, 3), 5),
    ((-2, -8), -10),
    ((100, 1), 101),
    ((8, -8), 0),
]

TASK_DESCRIPTION = (
    "Data una tupla (a, b) di numeri, la funzione solve(x) deve restituire la somma a + b."
)


def make_initial() -> CandidateProgram:
    return CandidateProgram(
        "buggy_subtraction",
        "Bug iniziale: usa la sottrazione invece dell'addizione.",
        "def solve(x):\n    a, b = x\n    return a - b\n",
    )


def make_llm_meta(mock: bool = False) -> LLMMetaAgent:
    if mock:
        return MockLLMMetaAgent(
            task_description=TASK_DESCRIPTION,
            train_data=TRAIN_DATA,
        )
    return LLMMetaAgent(
        model=os.environ.get("OLLAMA_MODEL", "ollama/llama3.2"),
        task_description=TASK_DESCRIPTION,
        train_data=TRAIN_DATA,
        num_candidates=1,
        temperature=0.2,
    )


class MockLLMMetaAgent(LLMMetaAgent):
    """Meta-agent fittizio per testare il ciclo senza Ollama."""

    def clone(self) -> "MockLLMMetaAgent":
        return MockLLMMetaAgent(
            model=self.model,
            task_description=self.task_description,
            train_data=list(self.train_data),
            num_candidates=self.num_candidates,
            temperature=self.temperature,
            mutation_memory=list(self.mutation_memory),
            request_log=list(self.request_log),
        )

    def generate_candidates(self, parent, archive):
        from common import CandidateProgram

        return [
            CandidateProgram(
                name=f"mock_gen_{parent.generation}",
                description="Patch mock: addizione corretta.",
                code="def solve(x):\n    a, b = x\n    return a + b\n",
            )
        ]


def check_prerequisites(mock: bool) -> None:
    errors = []
    if not docker_available():
        errors.append("Docker non disponibile. Avvia Docker Desktop.")
    if not mock and not ollama_available():
        errors.append(
            "Ollama non raggiungibile su http://localhost:11434. "
            "Installa Ollama, avvialo e esegui: ollama pull llama3.2"
        )
    if not mock:
        try:
            import litellm  # noqa: F401
        except ImportError:
            errors.append("Modulo litellm mancante. Esegui: pip install litellm")

    if errors:
        for message in errors:
            print(f"ERRORE: {message}")
        print("\nPer testare solo Docker+sandbox senza Ollama: python experiments/llm_code_repair.py --mock")
        raise SystemExit(1)


def annotate_rows(rows: list[dict], mode: str, variant: str) -> list[dict]:
    annotated = []
    for row in rows:
        enriched = dict(row)
        enriched["mode"] = mode
        enriched["variant"] = variant
        annotated.append(enriched)
    return annotated


def save_llm_logs(meta_agent: LLMMetaAgent, seed: int) -> None:
    os.makedirs(LLM_LOGS, exist_ok=True)
    path = os.path.join(LLM_LOGS, f"seed_{seed}_requests.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(meta_agent.request_log, file, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo LLM + Docker sandbox")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Usa patch fissa senza chiamare Ollama (utile per testare Docker).",
    )
    args = parser.parse_args()

    check_prerequisites(mock=args.mock)
    os.makedirs(RUNS_DIR, exist_ok=True)
    sandbox_workdir = os.path.join(RUNS_DIR, "sandbox")

    mode = "mock" if args.mock else "real"
    variant = "llm_code_repair_mock" if args.mock else "llm_code_repair"
    mode_label = "Mock (patch fissa, no Ollama)" if args.mock else "LLM reale (Ollama)"

    print("=== Demo 7: LLM (Ollama) + Docker sandbox ===")
    print(f"Modalita': {mode_label}")
    print(f"Docker: OK | Ollama: {'mock' if args.mock else 'OK'}")
    print(f"Modello: {os.environ.get('OLLAMA_MODEL', 'ollama/llama3.2')}")
    print(f"Iterazioni: {ITERATIONS}, seed: {list(SEEDS)}")

    # Verifica rapida sandbox con codice corretto
    sanity = evaluate_with_sandbox(
        "def solve(x):\n    a, b = x\n    return a + b\n",
        TRAIN_DATA[:2],
        sandbox_workdir,
        run_id="sanity_check",
    )
    print(f"Sanity check sandbox (addizione corretta su 2 esempi): {sanity:.2f}")

    rows = []
    for seed in SEEDS:
        meta = make_llm_meta(mock=args.mock)
        print(f"\n--- Seed {seed} ---")
        archive = run_dgm_h(
            variant=variant,
            train_data=TRAIN_DATA,
            test_data=TEST_DATA,
            initial_program=make_initial(),
            meta_agent=meta,
            selector=select_score_child_prop,
            iterations=ITERATIONS,
            seed=seed,
            archive_mode="full",
            candidates_per_iteration=1,
            use_sandbox=True,
            sandbox_workdir=sandbox_workdir,
        )
        rows.extend(annotate_rows(best_by_iteration(archive), mode, variant))
        save_llm_logs(meta, seed)
        best = max(archive, key=lambda e: e.train_score)
        print(
            f"Seed {seed} completato: best={best.name}, "
            f"train={best.train_score:.2f}, test={best.test_score:.2f}"
        )

    mode_csv_path = os.path.join(RESULTS, f"llm_code_repair_{mode}.csv")
    combined_csv_path = os.path.join(RESULTS, "llm_code_repair.csv")
    mode_png_path = os.path.join(RESULTS, f"llm_code_repair_{mode}.png")
    combined_png_path = os.path.join(RESULTS, "llm_code_repair.png")

    write_csv(mode_csv_path, rows)
    merge_csv_variants(combined_csv_path, rows)
    plot_csv(
        mode_csv_path,
        mode_png_path,
        f"Code-repair Demo 7 — modalita' {mode}",
    )
    plot_csv(
        combined_csv_path,
        combined_png_path,
        "Code-repair Demo 7 — confronto mock vs LLM reale",
    )
    print(f"\nSalvati: {mode_csv_path}")
    print(f"Salvati: {combined_csv_path}")
    print(f"Salvati: {mode_png_path}")
    print(f"Salvati: {combined_png_path}")
    print(f"Log LLM: {LLM_LOGS}/")
    print(f"Log sandbox: {os.path.join(RESULTS, 'sandbox_logs')}/")


if __name__ == "__main__":
    main()
