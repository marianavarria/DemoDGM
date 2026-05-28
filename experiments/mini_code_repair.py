"""Demo 5: mini code-repair, una versione ridotta dello scenario DGM originale."""

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
ITERATIONS = 25
SEEDS = range(5)

# Ogni input e' la tupla di argomenti per una funzione add(a, b).
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


def make_initial() -> CandidateProgram:
    return CandidateProgram(
        "buggy_subtraction",
        "Bug iniziale: usa la sottrazione invece dell'addizione.",
        "def solve(x):\n    a, b = x\n    return a - b\n",
    )


def make_meta() -> MetaAgent:
    base = [
        CandidateProgram(
            "return_first",
            "Patch sbagliata: restituisce solo il primo argomento.",
            "def solve(x):\n    a, b = x\n    return a\n",
        ),
        CandidateProgram(
            "return_second",
            "Patch sbagliata: restituisce solo il secondo argomento.",
            "def solve(x):\n    a, b = x\n    return b\n",
        ),
        CandidateProgram(
            "multiply",
            "Patch sbagliata: moltiplicazione.",
            "def solve(x):\n    a, b = x\n    return a * b\n",
        ),
        CandidateProgram(
            "abs_difference",
            "Patch parziale: distanza assoluta.",
            "def solve(x):\n    a, b = x\n    return abs(a - b)\n",
        ),
    ]
    hidden = [
        CandidateProgram(
            "correct_addition",
            "Patch corretta: addizione.",
            "def solve(x):\n    a, b = x\n    return a + b\n",
        )
    ]
    return MetaAgent(
        base_candidates=base,
        hidden_candidates=hidden,
        self_improve=True,
        unlock_score_threshold=0.20,
    )


def main() -> None:
    rows = []
    for seed in SEEDS:
        archive = run_dgm_h(
            variant="mini_code_repair",
            train_data=TRAIN_DATA,
            test_data=TEST_DATA,
            initial_program=make_initial(),
            meta_agent=make_meta(),
            selector=select_score_child_prop,
            iterations=ITERATIONS,
            seed=seed,
            archive_mode="full",
        )
        rows.extend(best_by_iteration(archive))

    csv_path = os.path.join(RESULTS, "code_repair.csv")
    png_path = os.path.join(RESULTS, "code_repair.png")
    write_csv(csv_path, rows)
    plot_csv(csv_path, png_path, "Mini code-repair")
    print(f"Salvati: {csv_path} e {png_path}")


if __name__ == "__main__":
    main()
