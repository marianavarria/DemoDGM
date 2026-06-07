"""Rigenera i PNG per demo da CSV gia' presenti in results/."""

from __future__ import annotations

import os
import sys

_EXPERIMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _EXPERIMENTS_DIR not in sys.path:
    sys.path.insert(0, _EXPERIMENTS_DIR)

from common import plot_csv

ROOT = os.path.dirname(_EXPERIMENTS_DIR)
RESULTS = os.path.join(ROOT, "results")

PLOTS = [
    ("ablation_archive.csv", "ablation_archive.png", "Ablation: archivio completo vs ultimo agente"),
    (
        "ablation_self_improve.csv",
        "ablation_self_improve.png",
        "Ablation: meta-agent congelato vs self-improve",
    ),
    ("parent_selection.csv", "parent_selection.png", "Strategie di parent selection"),
    ("task_vowels.csv", "task_vowels.png", "Secondo dominio: stringhe di sole vocali"),
    ("code_repair.csv", "code_repair.png", "Mini code-repair"),
]


def main() -> None:
    for csv_name, png_name, title in PLOTS:
        csv_path = os.path.join(RESULTS, csv_name)
        png_path = os.path.join(RESULTS, png_name)
        if not os.path.exists(csv_path):
            print(f"SALTO (CSV mancante): {csv_name}")
            continue
        plot_csv(csv_path, png_path, title)
        print(f"Generato: {png_path}")


if __name__ == "__main__":
    main()
