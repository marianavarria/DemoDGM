"""
Utility condivise per le mini-demo DGM-H.

Il modulo implementa un ciclo didattico generate -> evaluate -> archive -> select
senza LLM. Le mutazioni sono programmi Python predefiniti, cosi' gli esperimenti
sono riproducibili su Windows senza Docker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import csv
import math
import os
import random
from statistics import mean, stdev
from typing import Any, Callable, Iterable


Dataset = list[tuple[Any, Any]]


@dataclass(frozen=True)
class CandidateProgram:
    """Rappresenta una possibile variante del task agent."""

    name: str
    description: str
    code: str

    def compile(self) -> Callable[[Any], Any]:
        namespace: dict[str, Any] = {}
        exec(self.code, {}, namespace)
        solve = namespace.get("solve")
        if not callable(solve):
            raise ValueError("Il programma non definisce solve(x).")
        return solve


@dataclass
class TaskAgent:
    """Agente operativo valutato sul task."""

    program: CandidateProgram

    def solve(self, item: Any) -> Any:
        return self.program.compile()(item)


@dataclass
class MetaAgent:
    """
    Meta-agent deterministico.

    Se self_improve=True, sblocca progressivamente strategie piu' forti: e' una
    simulazione minima della modifica del meccanismo di miglioramento.
    """

    base_candidates: list[CandidateProgram]
    hidden_candidates: list[CandidateProgram] = field(default_factory=list)
    self_improve: bool = True
    unlock_score_threshold: float = 0.75
    mutation_memory: list[str] = field(default_factory=list)
    unlocked: int = 0

    def clone(self) -> "MetaAgent":
        return MetaAgent(
            base_candidates=list(self.base_candidates),
            hidden_candidates=list(self.hidden_candidates),
            self_improve=self.self_improve,
            unlock_score_threshold=self.unlock_score_threshold,
            mutation_memory=list(self.mutation_memory),
            unlocked=self.unlocked,
        )

    def generate_candidates(
        self,
        parent: "HyperAgent",
        archive: list["ArchiveEntry"],
    ) -> list[CandidateProgram]:
        best_score = max((entry.train_score for entry in archive), default=0.0)
        if self.self_improve and self.unlocked < len(self.hidden_candidates):
            if best_score >= self.unlock_score_threshold:
                candidate = self.hidden_candidates[self.unlocked]
                self.unlocked += 1
                self.mutation_memory.append(
                    f"Sbloccata strategia meta: {candidate.name}"
                )

        return self.base_candidates + self.hidden_candidates[: self.unlocked]


@dataclass
class HyperAgent:
    """Task agent e meta-agent nello stesso oggetto modificabile."""

    task_agent: TaskAgent
    meta_agent: MetaAgent
    generation: int = 0

    def solve(self, item: Any) -> Any:
        return self.task_agent.solve(item)

    def modify(
        self,
        archive: list["ArchiveEntry"],
        rng: random.Random,
        candidates_per_iteration: int = 1,
    ) -> list["HyperAgent"]:
        candidates = self.meta_agent.generate_candidates(self, archive)
        selected = rng.sample(
            candidates,
            k=min(candidates_per_iteration, len(candidates)),
        )
        return [
            HyperAgent(
                task_agent=TaskAgent(candidate),
                meta_agent=self.meta_agent.clone(),
                generation=self.generation + 1,
            )
            for candidate in selected
        ]


@dataclass
class ArchiveEntry:
    node_id: int
    parent_id: int | None
    iteration: int
    agent: HyperAgent
    train_score: float
    test_score: float
    valid: bool
    seed: int
    variant: str

    @property
    def name(self) -> str:
        return self.agent.task_agent.program.name


def evaluate(
    agent: HyperAgent,
    data: Dataset,
    *,
    use_sandbox: bool = False,
    sandbox_workdir: str | None = None,
    run_id: str | None = None,
) -> float:
    if use_sandbox:
        from sandbox import evaluate_with_sandbox

        if not sandbox_workdir:
            raise ValueError("sandbox_workdir richiesto quando use_sandbox=True")
        return evaluate_with_sandbox(
            agent.task_agent.program.code,
            data,
            sandbox_workdir,
            run_id=run_id,
        )

    correct = 0
    for item, expected in data:
        try:
            prediction = agent.solve(item)
        except Exception:
            prediction = None
        if prediction == expected:
            correct += 1
    return correct / len(data)


def is_valid(agent: HyperAgent) -> bool:
    try:
        agent.task_agent.program.compile()
        return True
    except Exception:
        return False


def child_counts(archive: list[ArchiveEntry]) -> dict[int, int]:
    counts = {entry.node_id: 0 for entry in archive}
    for entry in archive:
        if entry.parent_id is not None and entry.parent_id in counts:
            counts[entry.parent_id] += 1
    return counts


def select_random(archive: list[ArchiveEntry], rng: random.Random) -> ArchiveEntry:
    return rng.choice(archive)


def select_best(archive: list[ArchiveEntry], rng: random.Random) -> ArchiveEntry:
    best_score = max(entry.train_score for entry in archive)
    best_entries = [entry for entry in archive if entry.train_score == best_score]
    return rng.choice(best_entries)


def _score_weights(archive: list[ArchiveEntry]) -> list[float]:
    top_scores = sorted((entry.train_score for entry in archive), reverse=True)[:3]
    midpoint = mean(top_scores)
    weights = []
    for entry in archive:
        weights.append(1 / (1 + math.exp(-10 * (entry.train_score - midpoint))))
    return weights


def select_score_prop(
    archive: list[ArchiveEntry],
    rng: random.Random,
) -> ArchiveEntry:
    weights = _score_weights(archive)
    return rng.choices(archive, weights=weights, k=1)[0]


def select_score_child_prop(
    archive: list[ArchiveEntry],
    rng: random.Random,
) -> ArchiveEntry:
    counts = child_counts(archive)
    score_weights = _score_weights(archive)
    weights = [
        score_weight * (1 / (1 + counts[entry.node_id]))
        for entry, score_weight in zip(archive, score_weights)
    ]
    return rng.choices(archive, weights=weights, k=1)[0]


PARENT_SELECTORS: dict[str, Callable[[list[ArchiveEntry], random.Random], ArchiveEntry]] = {
    "random": select_random,
    "best": select_best,
    "score_prop": select_score_prop,
    "score_child_prop": select_score_child_prop,
}


def run_dgm_h(
    *,
    variant: str,
    train_data: Dataset,
    test_data: Dataset,
    initial_program: CandidateProgram,
    meta_agent: MetaAgent,
    selector: Callable[[list[ArchiveEntry], random.Random], ArchiveEntry] = select_score_child_prop,
    iterations: int = 30,
    seed: int = 0,
    archive_mode: str = "full",
    candidates_per_iteration: int = 1,
    use_sandbox: bool = False,
    sandbox_workdir: str | None = None,
) -> list[ArchiveEntry]:
    rng = random.Random(seed)
    initial_agent = HyperAgent(TaskAgent(initial_program), meta_agent, generation=0)
    archive = [
        ArchiveEntry(
            node_id=0,
            parent_id=None,
            iteration=0,
            agent=initial_agent,
            train_score=evaluate(
                initial_agent,
                train_data,
                use_sandbox=use_sandbox,
                sandbox_workdir=sandbox_workdir,
                run_id=f"{variant}_s{seed}_init_train",
            ),
            test_score=evaluate(
                initial_agent,
                test_data,
                use_sandbox=use_sandbox,
                sandbox_workdir=sandbox_workdir,
                run_id=f"{variant}_s{seed}_init_test",
            ),
            valid=is_valid(initial_agent),
            seed=seed,
            variant=variant,
        )
    ]
    history = list(archive)

    next_id = 1
    for iteration in range(1, iterations + 1):
        parent = selector(archive, rng)
        children = parent.agent.modify(
            archive,
            rng,
            candidates_per_iteration=candidates_per_iteration,
        )
        new_entries: list[ArchiveEntry] = []
        for child in children:
            valid = is_valid(child)
            entry = ArchiveEntry(
                node_id=next_id,
                parent_id=parent.node_id,
                iteration=iteration,
                agent=child,
                train_score=evaluate(
                    child,
                    train_data,
                    use_sandbox=use_sandbox,
                    sandbox_workdir=sandbox_workdir,
                    run_id=f"{variant}_s{seed}_i{iteration}_n{next_id}_train",
                )
                if valid
                else 0.0,
                test_score=evaluate(
                    child,
                    test_data,
                    use_sandbox=use_sandbox,
                    sandbox_workdir=sandbox_workdir,
                    run_id=f"{variant}_s{seed}_i{iteration}_n{next_id}_test",
                )
                if valid
                else 0.0,
                valid=valid,
                seed=seed,
                variant=variant,
            )
            next_id += 1
            new_entries.append(entry)
            history.append(entry)

        if archive_mode == "last_only":
            archive = new_entries or archive[-1:]
        elif archive_mode == "full":
            archive.extend(new_entries)
        else:
            raise ValueError(f"archive_mode non supportato: {archive_mode}")

    return history


def best_by_iteration(archive: list[ArchiveEntry]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    best_train = -1.0
    best_test = -1.0
    best_name = ""
    for iteration in sorted({entry.iteration for entry in archive}):
        entries = [entry for entry in archive if entry.iteration == iteration]
        current_best = max(entries, key=lambda entry: entry.train_score)
        if current_best.train_score >= best_train:
            best_train = current_best.train_score
            best_test = current_best.test_score
            best_name = current_best.name
        rows.append(
            {
                "variant": current_best.variant,
                "seed": current_best.seed,
                "iteration": iteration,
                "best_train": best_train,
                "best_test": best_test,
                "best_agent": best_name,
                "archive_size": len(
                    [entry for entry in archive if entry.iteration <= iteration]
                ),
            }
        )
    return rows


def write_csv(path: str, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        raise ValueError("Nessuna riga da salvare.")
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def summarize_csv(path: str) -> list[dict[str, Any]]:
    rows = read_csv(path)
    grouped: dict[str, list[float]] = {}
    for row in rows:
        grouped.setdefault(row["variant"], []).append(float(row["best_test"]))
    summary = []
    for variant, scores in sorted(grouped.items()):
        summary.append(
            {
                "variant": variant,
                "mean_best_test": mean(scores),
                "max_best_test": max(scores),
                "std_best_test": stdev(scores) if len(scores) > 1 else 0.0,
            }
        )
    return summary


def plot_csv(
    csv_path: str,
    png_path: str,
    title: str,
    ylabel: str = "Best test score",
) -> None:
    import matplotlib.pyplot as plt

    rows = read_csv(csv_path)
    grouped: dict[str, dict[int, list[float]]] = {}
    for row in rows:
        grouped.setdefault(row["variant"], {}).setdefault(
            int(row["iteration"]),
            [],
        ).append(float(row["best_test"]))

    plt.figure(figsize=(8, 5))
    for variant, by_iteration in sorted(grouped.items()):
        xs = sorted(by_iteration)
        ys = [mean(by_iteration[x]) for x in xs]
        plt.plot(xs, ys, marker="o", linewidth=2, label=variant)

    plt.title(title)
    plt.xlabel("Iterazione")
    plt.ylabel(ylabel)
    plt.ylim(0, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    plt.savefig(png_path, dpi=160)
    plt.close()
