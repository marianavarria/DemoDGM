"""Demo 2: ablation del meta-agent con e senza self-improve."""

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
    ("radar", True),
    ("level", True),
    ("casa", False),
    ("python", False),
    ("abc", False),
    ("abca", False),
    ("racecar", True),
]

TEST_DATA = [
    ("kayak", True),
    ("madam", True),
    ("robot", False),
    ("abcda", False),
    ("abxba", True),
    ("axcya", False),
]


def make_initial() -> CandidateProgram:
    return CandidateProgram(
        "initial_false",
        "Agente iniziale ingenuo.",
        "def solve(x):\n    return False\n",
    )


def make_meta(self_improve: bool) -> MetaAgent:
    base = [
        CandidateProgram("always_true", "Risponde sempre True.", "def solve(x):\n    return True\n"),
        CandidateProgram("always_false", "Risponde sempre False.", "def solve(x):\n    return False\n"),
        CandidateProgram(
            "first_last_equal",
            "Euristica parziale: primo e ultimo carattere.",
            "def solve(x):\n    return True if not x else x[0] == x[-1]\n",
        ),
    ]
    hidden = [
        CandidateProgram(
            "reverse_check",
            "Mutazione sbloccata dal meta-agent evolutivo.",
            "def solve(x):\n    s = x.strip().lower()\n    return s == s[::-1]\n",
        )
    ]
    return MetaAgent(
        base_candidates=base,
        hidden_candidates=hidden,
        self_improve=self_improve,
    )


def main() -> None:
    rows = []
    for variant, self_improve in {
        "meta_congelato": False,
        "meta_self_improve": True,
    }.items():
        for seed in SEEDS:
            archive = run_dgm_h(
                variant=variant,
                train_data=TRAIN_DATA,
                test_data=TEST_DATA,
                initial_program=make_initial(),
                meta_agent=make_meta(self_improve),
                selector=select_score_child_prop,
                iterations=ITERATIONS,
                seed=seed,
                archive_mode="full",
            )
            rows.extend(best_by_iteration(archive))

    csv_path = os.path.join(RESULTS, "ablation_self_improve.csv")
    png_path = os.path.join(RESULTS, "ablation_self_improve.png")
    write_csv(csv_path, rows)
    plot_csv(csv_path, png_path, "Ablation: meta-agent congelato vs self-improve")
    print(f"Salvati: {csv_path} e {png_path}")


if __name__ == "__main__":
    main()
