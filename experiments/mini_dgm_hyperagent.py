"""
Mini DGM / DGM-H didattico
---------------------------------
Obiettivo: mostrare il ciclo generate -> evaluate -> archive -> select -> modify.

Task: classificare stringhe come palindrome oppure non palindrome.
- TaskAgent: contiene la funzione solve(s)
- MetaAgent: genera nuove versioni del TaskAgent
- HyperAgent: contiene TaskAgent + MetaAgent nello stesso oggetto modificabile
- Archive: conserva tutti gli agenti validi con score e descrizione

Esecuzione:
    python mini_dgm_hyperagent.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Tuple, Dict, Any
import random
import textwrap
import csv


Dataset = List[Tuple[str, bool]]


TRAIN_DATA: Dataset = [
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
TEST_DATA: Dataset = [
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


@dataclass
class CandidateProgram:
    """Rappresenta una possibile strategia dell'agente."""

    name: str
    description: str
    code: str

    def compile(self) -> Callable[[str], bool]:
        """Compila il codice testuale in una funzione Python solve(s)."""
        namespace: Dict[str, Any] = {}
        exec(self.code, {}, namespace)
        solve = namespace.get("solve")
        if not callable(solve):
            raise ValueError("Il programma non definisce una funzione solve(s).")
        return solve


@dataclass
class TaskAgent:
    """Agente che risolve il task."""

    program: CandidateProgram

    def solve(self, s: str) -> bool:
        fn = self.program.compile()
        return bool(fn(s))


@dataclass
class MetaAgent:
    """Agente che genera modifiche. Qui è deterministico/didattico, non usa LLM."""

    mutation_memory: List[str] = field(default_factory=list)

    def generate_candidates(self, parent: "HyperAgent", archive: List["ArchiveEntry"]) -> List[CandidateProgram]:
        """
        Genera varianti candidate. In una DGM reale questa parte sarebbe svolta da un LLM
        che modifica codice del repository. Qui usiamo un insieme di mutazioni semplici.
        """
        candidates = [
            CandidateProgram(
                name="always_true",
                description="Risponde sempre True.",
                code="""
def solve(s):
    return True
""",
            ),
            CandidateProgram(
                name="always_false",
                description="Risponde sempre False.",
                code="""
def solve(s):
    return False
""",
            ),
            CandidateProgram(
                name="even_length",
                description="Predice palindromo se la lunghezza è pari.",
                code="""
def solve(s):
    return len(s) % 2 == 0
""",
            ),
            CandidateProgram(
                name="first_last_equal",
                description="Predice palindromo se primo e ultimo carattere coincidono.",
                code="""
def solve(s):
    if not s:
        return True
    return s[0] == s[-1]
""",
            ),
            CandidateProgram(
                name="reverse_check",
                description="Controlla se la stringa è uguale alla sua inversa.",
                code="""
def solve(s):
    normalized = s.strip().lower()
    return normalized == normalized[::-1]
""",
            ),
        ]

        # Simula un miglioramento meta-cognitivo: se l'archivio mostra fallimenti,
        # il meta-agent aggiunge memoria su quali strategie evitare.
        best_score = max((entry.train_score for entry in archive), default=0.0)
        if best_score < 1.0:
            self.mutation_memory.append("Serve una regola strutturale, non una costante.")

        return candidates


@dataclass
class HyperAgent:
    """Contiene task agent e meta agent in un unico programma modificabile."""

    task_agent: TaskAgent
    meta_agent: MetaAgent
    generation: int = 0

    def solve(self, s: str) -> bool:
        return self.task_agent.solve(s)

    def modify(self, archive: List["ArchiveEntry"]) -> List["HyperAgent"]:
        children = []
        candidates = self.meta_agent.generate_candidates(self, archive)
        for candidate in candidates:
            child = HyperAgent(
                task_agent=TaskAgent(candidate),
                meta_agent=MetaAgent(mutation_memory=list(self.meta_agent.mutation_memory)),
                generation=self.generation + 1,
            )
            children.append(child)
        return children


@dataclass
class ArchiveEntry:
    agent: HyperAgent
    train_score: float
    test_score: float
    valid: bool
    parent_name: str | None

    @property
    def name(self) -> str:
        return self.agent.task_agent.program.name

    @property
    def description(self) -> str:
        return self.agent.task_agent.program.description


def evaluate(agent: HyperAgent, data: Dataset) -> float:
    """Valuta un agente su un dataset."""
    correct = 0
    for x, expected in data:
        try:
            pred = agent.solve(x)
        except Exception:
            pred = None
        if pred == expected:
            correct += 1
    return correct / len(data)


def is_valid(agent: HyperAgent) -> bool:
    """Controlla che il programma sia eseguibile."""
    try:
        agent.task_agent.program.compile()
        return True
    except Exception:
        return False


def select_parent(archive: List[ArchiveEntry]) -> HyperAgent:
    """
    Selezione parent semplificata.
    Favorisce agenti con score alto, ma lascia una piccola probabilità agli altri.
    """
    weights = [entry.train_score + 0.05 for entry in archive]
    return random.choices([entry.agent for entry in archive], weights=weights, k=1)[0]


def run_dgm_h(iterations: int = 4, seed: int = 42) -> List[ArchiveEntry]:
    random.seed(seed)

    initial_program = CandidateProgram(
        name="initial_agent",
        description="Agente iniziale ingenuo: risponde sempre False.",
        code="""
def solve(s):
    return False
""",
    )

    initial_agent = HyperAgent(
        task_agent=TaskAgent(initial_program),
        meta_agent=MetaAgent(),
        generation=0,
    )

    archive: List[ArchiveEntry] = []
    archive.append(
        ArchiveEntry(
            agent=initial_agent,
            train_score=evaluate(initial_agent, TRAIN_DATA),
            test_score=evaluate(initial_agent, TEST_DATA),
            valid=is_valid(initial_agent),
            parent_name=None,
        )
    )

    for iteration in range(1, iterations + 1):
        parent = select_parent(archive)
        children = parent.modify(archive)

        for child in children:
            valid = is_valid(child)
            entry = ArchiveEntry(
                agent=child,
                train_score=evaluate(child, TRAIN_DATA) if valid else 0.0,
                test_score=evaluate(child, TEST_DATA) if valid else 0.0,
                valid=valid,
                parent_name=parent.task_agent.program.name,
            )
            archive.append(entry)

        best = max(archive, key=lambda e: e.train_score)
        print(f"Iterazione {iteration}: best={best.name}, train={best.train_score:.2f}, test={best.test_score:.2f}")

    return archive


def print_report(archive: List[ArchiveEntry]) -> None:
    print("\n=== ARCHIVIO FINALE ===")
    print(f"{'Nome':<18} {'Parent':<18} {'Train':<8} {'Test':<8} Descrizione")
    print("-" * 90)
    for entry in archive:
        print(
            f"{entry.name:<18} "
            f"{str(entry.parent_name):<18} "
            f"{entry.train_score:<8.2f} "
            f"{entry.test_score:<8.2f} "
            f"{entry.description}"
        )

    best = max(archive, key=lambda e: e.train_score)
    print("\n=== MIGLIOR AGENTE ===")
    print(f"Nome: {best.name}")
    print(f"Train score: {best.train_score:.2f}")
    print(f"Test score: {best.test_score:.2f}")
    print("Codice:")
    print(textwrap.dedent(best.agent.task_agent.program.code).strip())
    print("\nMemoria meta-agent:")
    for item in best.agent.meta_agent.mutation_memory:
        print(f"- {item}")
def save_archive_to_csv(
    archive: List[ArchiveEntry],
    output_path: str = "results/mini_dgm_archive.csv"
) -> None:
    """
    Salva l'archivio finale in un file CSV.
    """

    with open(output_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "name",
            "parent",
            "generation",
            "train_score",
            "test_score",
            "valid",
            "description",
        ])

        for entry in archive:
            writer.writerow([
                entry.name,
                entry.parent_name,
                entry.agent.generation,
                entry.train_score,
                entry.test_score,
                entry.valid,
                entry.description,
            ])

if __name__ == "__main__":
    archive = run_dgm_h(iterations=4)
    print_report(archive)
    save_archive_to_csv(archive)
    print("\nCSV salvato in: results/mini_dgm_archive.csv")
