"""Demo 6: genera un grafico riassuntivo da tutti i CSV delle mini-demo."""

from __future__ import annotations

import os
from statistics import mean

import matplotlib.pyplot as plt

from common import read_csv


ROOT = os.path.dirname(os.path.dirname(__file__))
RESULTS = os.path.join(ROOT, "results")

CSV_FILES = [
    ("Ablation archivio", "ablation_archive.csv"),
    ("Ablation self-improve", "ablation_self_improve.csv"),
    ("Parent selection", "parent_selection.csv"),
    ("Task vocali", "task_vowels.csv"),
    ("Code repair", "code_repair.csv"),
    ("LLM + Docker", "llm_code_repair.csv"),
]


def main() -> None:
    plt.figure(figsize=(10, 6))

    for label, filename in CSV_FILES:
        path = os.path.join(RESULTS, filename)
        if not os.path.exists(path):
            print(f"CSV mancante, salto: {path}")
            continue

        rows = read_csv(path)
        by_iteration: dict[int, list[float]] = {}
        for row in rows:
            by_iteration.setdefault(int(row["iteration"]), []).append(
                float(row["best_test"])
            )
        xs = sorted(by_iteration)
        ys = [mean(by_iteration[x]) for x in xs]
        plt.plot(xs, ys, linewidth=2, label=label)

    plt.title("Overview mini-demo DGM-H")
    plt.xlabel("Iterazione")
    plt.ylabel("Best test score medio")
    plt.ylim(0, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    output_path = os.path.join(RESULTS, "all_demos_overview.png")
    plt.savefig(output_path, dpi=160)
    plt.close()
    print(f"Salvato: {output_path}")


if __name__ == "__main__":
    main()
