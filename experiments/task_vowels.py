"""Demo 4: secondo dominio semplice, classificazione di stringhe di sole vocali."""

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

TRAIN_DATA = [
    ("aei", True),
    ("oua", True),
    ("aaa", True),
    ("io", True),
    ("abc", False),
    ("robot", False),
    ("cloud", False),
    ("python", False),
    ("a1e", False),
    ("ae!", False),
]

TEST_DATA = [
    ("aeiou", True),
    ("oo", True),
    ("uai", True),
    ("data", False),
    ("agent", False),
    ("ml", False),
    ("aei2", False),
    ("i-o", False),
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
        CandidateProgram(
            "contains_vowel",
            "Controlla se esiste almeno una vocale.",
            "def solve(x):\n    return any(ch in 'aeiou' for ch in x.lower())\n",
        ),
        CandidateProgram(
            "starts_with_vowel",
            "Controlla solo il primo carattere.",
            "def solve(x):\n    return bool(x) and x[0].lower() in 'aeiou'\n",
        ),
    ]
    hidden = [
        CandidateProgram(
            "only_vowels",
            "Controlla che tutti i caratteri siano vocali.",
            "def solve(x):\n    vowels = set('aeiou')\n    return bool(x) and all(ch in vowels for ch in x.lower())\n",
        )
    ]
    return MetaAgent(
        base_candidates=base,
        hidden_candidates=hidden,
        self_improve=True,
        unlock_score_threshold=0.70,
    )


def main() -> None:
    rows = []
    for seed in SEEDS:
        archive = run_dgm_h(
            variant="task_vocali",
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

    csv_path = os.path.join(RESULTS, "task_vowels.csv")
    png_path = os.path.join(RESULTS, "task_vowels.png")
    write_csv(csv_path, rows)
    plot_csv(csv_path, png_path, "Secondo dominio: stringhe di sole vocali")
    print(f"Salvati: {csv_path} e {png_path}")


if __name__ == "__main__":
    main()
