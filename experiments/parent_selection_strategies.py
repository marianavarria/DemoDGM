"""Demo 3: confronto tra strategie di parent selection."""

from __future__ import annotations

import os

from common import (
    CandidateProgram,
    MetaAgent,
    PARENT_SELECTORS,
    best_by_iteration,
    plot_csv,
    run_dgm_h,
    write_csv,
)


ROOT = os.path.dirname(os.path.dirname(__file__))
RESULTS = os.path.join(ROOT, "results")
ITERATIONS = 35
SEEDS = range(8)

TRAIN_DATA = [
    ("anna", True),
    ("otto", True),
    ("radar", True),
    ("level", True),
    ("racecar", True),
    ("casa", False),
    ("python", False),
    ("banana", False),
    ("abca", False),
    ("axya", False),
]

TEST_DATA = [
    ("kayak", True),
    ("madam", True),
    ("noon", True),
    ("chatgpt", False),
    ("openai", False),
    ("abcda", False),
    ("abxba", True),
    ("axcya", False),
]


def make_initial() -> CandidateProgram:
    return CandidateProgram(
        "initial_false",
        "Baseline costante.",
        "def solve(x):\n    return False\n",
    )


def make_meta() -> MetaAgent:
    base = [
        CandidateProgram("always_true", "Costante True.", "def solve(x):\n    return True\n"),
        CandidateProgram("always_false", "Costante False.", "def solve(x):\n    return False\n"),
        CandidateProgram("even_length", "Lunghezza pari.", "def solve(x):\n    return len(x) % 2 == 0\n"),
        CandidateProgram(
            "first_last_equal",
            "Primo e ultimo carattere uguali.",
            "def solve(x):\n    return True if not x else x[0] == x[-1]\n",
        ),
    ]
    hidden = [
        CandidateProgram(
            "reverse_check",
            "Controllo completo con stringa invertita.",
            "def solve(x):\n    s = x.strip().lower()\n    return s == s[::-1]\n",
        )
    ]
    return MetaAgent(base_candidates=base, hidden_candidates=hidden, self_improve=True)


def main() -> None:
    rows = []
    for selector_name, selector in PARENT_SELECTORS.items():
        for seed in SEEDS:
            archive = run_dgm_h(
                variant=selector_name,
                train_data=TRAIN_DATA,
                test_data=TEST_DATA,
                initial_program=make_initial(),
                meta_agent=make_meta(),
                selector=selector,
                iterations=ITERATIONS,
                seed=seed,
                archive_mode="full",
            )
            rows.extend(best_by_iteration(archive))

    csv_path = os.path.join(RESULTS, "parent_selection.csv")
    png_path = os.path.join(RESULTS, "parent_selection.png")
    write_csv(csv_path, rows)
    plot_csv(csv_path, png_path, "Strategie di parent selection")
    print(f"Salvati: {csv_path} e {png_path}")


if __name__ == "__main__":
    main()
