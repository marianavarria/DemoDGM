"""Demo 6: genera un grafico riassuntivo da tutti i CSV delle mini-demo."""

from __future__ import annotations

import os
from statistics import mean

import matplotlib.pyplot as plt

from common import read_csv


ROOT = os.path.dirname(os.path.dirname(__file__))
RESULTS = os.path.join(ROOT, "results")

CSV_FILES = [
    ("Ablation archivio", "ablation_archive.csv", None),
    ("Ablation self-improve", "ablation_self_improve.csv", None),
    ("Parent selection", "parent_selection.csv", None),
    ("Task vocali", "task_vowels.csv", None),
    ("Code repair", "code_repair.csv", None),
    ("LLM mock (Docker)", "llm_code_repair.csv", "llm_code_repair_mock"),
    ("LLM reale (Ollama)", "llm_code_repair.csv", "llm_code_repair"),
]


def main() -> None:
    plt.figure(figsize=(10, 6))

    for label, filename, variant_filter in CSV_FILES:
        path = os.path.join(RESULTS, filename)
        if not os.path.exists(path):
            print(f"CSV mancante, salto: {path}")
            continue

        rows = read_csv(path)
        if variant_filter is not None:
            rows = [row for row in rows if row.get("variant") == variant_filter]
            if not rows:
                print(f"Variante assente in {path}: {variant_filter}")
                continue
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
