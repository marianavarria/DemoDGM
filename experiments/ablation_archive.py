"""Demo 1: ablation con archivio completo vs solo ultimo agente."""

from __future__ import annotations

import os

from common import (
    CandidateProgram,
    MetaAgent,
    best_by_iteration,
    plot_csv,
    run_dgm_h,
    select_score_child_prop,
    write_csv,
)


ROOT = os.path.dirname(os.path.dirname(__file__))
RESULTS = os.path.join(ROOT, "results")
ITERATIONS = 30
SEEDS = range(5)

TRAIN_DATA = [
    ("anna", True),
    ("otto", True),
    ("radar", True),
    ("casa", False),
    ("python", False),
    ("abc", False),
    ("level", True),
    ("banana", False),
    ("abca", False),
    ("abda", False),
    ("axya", False),
    ("racecar", True),
]

TEST_DATA = [
    ("kayak", True),
    ("madam", True),
    ("chatgpt", False),
    ("robot", False),
    ("noon", True),
    ("openai", False),
    ("abcda", False),
    ("abxba", True),
    ("acxca", True),
    ("axcya", False),
]


def make_initial() -> CandidateProgram:
    return CandidateProgram(
        "initial_false",
        "Agente iniziale ingenuo: risponde sempre False.",
        "def solve(x):\n    return False\n",
    )


def make_meta() -> MetaAgent:
    base = [
        CandidateProgram("always_true", "Risponde sempre True.", "def solve(x):\n    return True\n"),
        CandidateProgram("always_false", "Risponde sempre False.", "def solve(x):\n    return False\n"),
        CandidateProgram(
            "even_length",
            "Predice palindromo se la lunghezza e' pari.",
            "def solve(x):\n    return len(x) % 2 == 0\n",
        ),
        CandidateProgram(
            "first_last_equal",
            "Controlla solo primo e ultimo carattere.",
            "def solve(x):\n    return True if not x else x[0] == x[-1]\n",
        ),
    ]
    hidden = [
        CandidateProgram(
            "reverse_check",
            "Strategia strutturale corretta per i palindromi.",
            "def solve(x):\n    s = x.strip().lower()\n    return s == s[::-1]\n",
        )
    ]
    return MetaAgent(base_candidates=base, hidden_candidates=hidden, self_improve=True)


def main() -> None:
    rows = []
    configs = {
        "con_archivio": "full",
        "senza_archivio": "last_only",
    }
    for variant, archive_mode in configs.items():
        for seed in SEEDS:
            archive = run_dgm_h(
                variant=variant,
                train_data=TRAIN_DATA,
                test_data=TEST_DATA,
                initial_program=make_initial(),
                meta_agent=make_meta(),
                selector=select_score_child_prop,
                iterations=ITERATIONS,
                seed=seed,
                archive_mode=archive_mode,
            )
            rows.extend(best_by_iteration(archive))

    csv_path = os.path.join(RESULTS, "ablation_archive.csv")
    png_path = os.path.join(RESULTS, "ablation_archive.png")
    write_csv(csv_path, rows)
    plot_csv(csv_path, png_path, "Ablation: archivio completo vs ultimo agente")
    print(f"Salvati: {csv_path} e {png_path}")


if __name__ == "__main__":
    main()
