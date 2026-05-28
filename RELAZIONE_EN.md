# Report: didactic reproduction of DGM-Hyperagents

This report documents a compact, reproducible implementation inspired by the paper *DGM-Hyperagents* and aligned with two official repositories:

- HyperAgents: `https://github.com/facebookresearch/Hyperagents`
- DGM: `https://github.com/jennyzzt/dgm`

The goal is to reproduce the core algorithmic ideas in a lightweight setting that runs quickly on Windows.

---

## Table of contents

1. Objective  
2. Theoretical context  
3. Project structure  
4. Mini DGM-H architecture  
5. Execution flow  
6. Demo 1 — Archive ablation  
7. Demo 2 — Self-improve ablation  
8. Demo 3 — Parent selection strategies  
9. Demo 4 — Second domain: vowels  
10. Demo 5 — Mini code-repair  
11. Demo 6 — Plot overview  
12. Demo 7 — LLM (Ollama) + Docker sandbox  
13. Results summary table  
14. Discussion and interpretation  
15. Relationship with official repositories   
16. Conclusion  
17. References

---

## 1. Objective

The objective is to provide a faithful **didactic mini-version** of DGM-Hyperagents that demonstrates:

- the iterative loop `generate -> evaluate -> archive -> select -> modify`;
- open-ended archive growth (genealogical stepping stones);
- the effect of self-improving meta-agents;
- parent-selection strategies inspired by Section 8.2 of the paper.

The project includes:

1. a local mini-implementation under `experiments/`, executable in seconds;
2. structural validation of the official DGM repository;
3. structural validation of the official HyperAgents repository.

---

## 2. Theoretical context

### 2.1 From Gödel Machine to DGM

The original DGM introduces a self-improving coding agent. The outer mechanism evaluates produced code and updates future behavior through a fixed diagnosis/improvement prompt loop.

### 2.2 The DGM-Hyperagents shift

DGM-H extends this idea: the **agent itself is an editable hyperagent**, where not only task-solving logic but also parts of the optimization process can evolve.

### 2.3 Algorithmic cycle (paper Algorithm 1)

Core cycle:

1. generate candidates from current parent(s);
2. evaluate candidates on train/test;
3. archive valid nodes;
4. select next parent;
5. modify and iterate.

### 2.4 The three paper baselines

- `DGM-H w/o self-improve`
- `DGM-H w/o open-ended exploration`
- strategy comparisons for parent selection

### 2.5 Parent selection in DGM-H (Sec. 8.2)

Implemented ideas:

1. Dynamic midpoint on top-3 scores;
2. Sigmoid weighting (`lambda = 10`);
3. Novelty bonus `1 / (1 + n_children)`;
4. normalized final probabilities.

---

## 3. Project structure

The repository contains:

- `experiments/`: mini framework and all demos
- `results/`: generated CSV and PNG artifacts
- `dgm/`: official DGM repo clone (analyzed/tested)
- `HyperAgents/`: official HyperAgents repo clone (analyzed)
- `RELAZIONE.md`: Italian report
- `RELAZIONE_EN.md`: this English report

### 3.1 Three depth levels

1. Local didactic implementation (fully runnable);
2. DGM repository inspection + partial tests on Windows;
3. HyperAgents repository inspection + syntax checks.

### 3.2 `results/` folder

Generated artifacts:

- CSV per demo (progress across iterations/seeds)
- PNG per demo (best-test progression plots)
- textual logs for repository checks and environment status

---

## 4. Mini DGM-H architecture

The mini-framework is implemented in `experiments/common.py`.

### 4.1 Main classes

- `CandidateProgram`: Python code as string + compile/execute wrapper
- `TaskAgent`: prediction interface over `solve(x)`
- `MetaAgent`: candidate generation, unlock logic, mutation memory
- `HyperAgent`: task + meta composition with inherited meta state
- `ArchiveEntry`: genealogy and metrics (`node_id`, `parent_id`, scores, validity)

### 4.2 `CandidateProgram`

Represents editable code. Compilation is done dynamically and evaluated through controlled benchmark datasets.

### 4.3 `TaskAgent`

Thin wrapper around candidate logic, exposing prediction behavior.

### 4.4 `MetaAgent`

Supports:

- base mutations (always available);
- hidden mutations unlocked after threshold;
- persistent memory (`mutation_memory`) for unlock events.

### 4.5 `HyperAgent`

Combines task and meta components. Child agents inherit cloned meta-agent state, enabling evolutionary propagation of discovered capabilities.

### 4.6 `ArchiveEntry`

Stores genealogy and reproducibility metadata:

- IDs and parent links
- iteration index
- train/test scores
- validity
- seed and variant

### 4.7 Parent selection strategies

Implemented in the mini framework:

- `random`
- `best`
- `score_prop`
- `score_child_prop` (paper default)

---

## 5. Execution flow

### 5.1 `run_dgm_h` cycle

A single function orchestrates:

- parent selection
- candidate generation
- child creation
- evaluation
- archive/history updates

### 5.2 Flow summary

`initialize -> iterate (select/generate/modify/evaluate/archive) -> export CSV/plots`

### 5.3 `archive` vs `history`

- `archive`: pool used for parent selection
- `history`: full chronological record used for metrics/plots

---

## 6. Demo 1 — Archive ablation

Script: `experiments/ablation_archive.py`  
Question: what changes if open-ended archive usage is reduced?

Result (5 seeds): both variants reach full score in this small task.

- `con_archivio`: best test `1.000`, mean convergence `6.4`
- `senza_archivio`: best test `1.000`, mean convergence `6.4`

Interpretation: this task scale is too small to highlight archive benefits clearly.

---

## 7. Demo 2 — Self-improve ablation

Script: `experiments/ablation_self_improve.py`  
Question: does self-improve matter?

Result:

- `meta_congelato`: best test `0.667`, never reaches full convergence
- `meta_self_improve`: best test `1.000`, mean convergence `10.6`

This is the clearest conceptual replication of the paper thesis in this project setup.

---

## 8. Demo 3 — Parent selection strategies

Script: `experiments/parent_selection_strategies.py`

Compared strategies:

- `random`
- `best`
- `score_prop`
- `score_child_prop`

All reach best test `1.000`, but speed differs:

- `score_prop`: `7.125`
- `score_child_prop`: `7.125`
- `best`: `8.125`
- `random`: `8.250`

Score-proportional strategies are faster in this setup.

---

## 9. Demo 4 — Second domain: vowels

Script: `experiments/task_vowels.py`  
Goal: verify domain transfer with same framework.

Result:

- `task_vocali`: best test `1.000`, mean convergence `6.4`

Only dataset and mutation definitions change; the framework remains identical.

---

## 10. Demo 5 — Mini code-repair

Script: `experiments/mini_code_repair.py`

Task: repair a buggy function (`a - b`) toward correct addition (`a + b`) through mutation search.

Result:

- `mini_code_repair`: best test `1.000`, mean convergence `4.8`

---

## 11. Demo 6 — Plot overview

Script: `experiments/plot_progress.py`

Builds a combined visualization over all core demos, confirming:

- similar convergence profiles for easy tasks;
- clear divergence in Demo 2 (self-improve ablation).

---

## 12. Demo 7 — LLM (Ollama) + Docker sandbox

Main files:

- `experiments/llm_meta_agent.py`
- `experiments/sandbox.py`
- `experiments/llm_code_repair.py`
- `experiments/requirements-llm.txt`

### 12.1 Goal

Add an LLM-driven variant while preserving safer execution through Docker sandboxing.

### 12.2 Sandbox properties

Containerized execution with restricted resources and no network:

- `--network=none`
- constrained CPU/memory
- blocked dangerous constructs before execution

### 12.3 Mock result

With `--mock` mode (Docker path verified):

- `llm_code_repair_mock`: best train `1.000`, best test `1.000`

Outputs:

- `results/llm_code_repair.csv`
- `results/llm_code_repair.png`

### 12.4 Result interpretation

This demo validates three aligned aspects of the project:

1. **Hyperagent behavior**: the meta component still proposes task-agent code updates.
2. **LLM integration**: Ollama replaces a fixed mutation list with generated patches.
3. **Safety-aware execution**: candidate code is evaluated in an isolated Docker sandbox.

Even in mock mode, the full evaluation path is containerized, so the reported score reflects the actual sandboxed execution flow rather than a direct in-process shortcut.

---

## 13. Results summary table

| Demo | Script | Variant | Best test | Std | Mean convergence iter | Note |
|---|---|---|---:|---:|---:|---|
| 1 | `ablation_archive.py` | `con_archivio` | 1.000 | 0.000 | 6.4 | Open-ended archive |
| 1 | `ablation_archive.py` | `senza_archivio` | 1.000 | 0.000 | 6.4 | Algorithm-3-like baseline |
| 2 | `ablation_self_improve.py` | `meta_congelato` | 0.667 | 0.000 | never | w/o self-improve |
| 2 | `ablation_self_improve.py` | `meta_self_improve` | 1.000 | 0.000 | 10.6 | full DGM-H behavior |
| 3 | `parent_selection_strategies.py` | `random` | 1.000 | 0.000 | 8.25 | baseline |
| 3 | `parent_selection_strategies.py` | `best` | 1.000 | 0.000 | 8.13 | exploitation |
| 3 | `parent_selection_strategies.py` | `score_prop` | 1.000 | 0.000 | 7.13 | sigmoid weighting |
| 3 | `parent_selection_strategies.py` | `score_child_prop` | 1.000 | 0.000 | 7.13 | paper-like default |
| 4 | `task_vowels.py` | `task_vocali` | 1.000 | 0.000 | 6.4 | second domain |
| 5 | `mini_code_repair.py` | `mini_code_repair` | 1.000 | 0.000 | 4.8 | code repair |
| 7 | `llm_code_repair.py` | `llm_code_repair_mock` | 1.000 | 0.000 | — | Ollama + Docker |

---

## 14. Discussion and interpretation

### 14.1 What works

- Full cycle works across classification and code-repair tasks.
- Archive supports traceable genealogies.
- Parent-selection strategies are implemented as intended.
- Self-improving meta-agent unlock logic reproduces the key conceptual effect.

### 14.2 What converges too easily

With small datasets, multiple strategies eventually solve the task, which reduces visible differences across archive ablations and selector comparisons.

### 14.3 Key finding (Demo 2)

`0.667 vs 1.000` (frozen vs self-improving meta-agent) is the main local evidence consistent with the paper claims: without meta-level adaptation, performance saturates early.

### 14.4 Why this matters

If self-improvement mechanisms are frozen, systems inherit fixed design limits. Meta-level adaptability is central.

---

## 15. Relationship with official repositories

### 15.1 DGM repository (`dgm/`)

- tested commit: `a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2`
- requirements installed
- tests on Windows: `11 passed, 11 failed`
- failures mainly from POSIX-specific features (e.g., `os.setsid`)

### 15.2 HyperAgents repository (`HyperAgents/`)

- tested commit: `59a68f672dfb92c74aeb7e61535d776fb36e172d`
- core files syntax-checked (`py_compile`)
- domains found: `polyglot`, `imo`, `genesis`, `balrog`

Full official reproduction still needs Linux/WSL/Fedora setup, heavy dependencies, and API keys.

---

## 16. Conclusion

The project achieves its objective: a reproducible DGM-Hyperagents-inspired system that demonstrates the central mechanics and reproduces the conceptual difference between frozen and self-improving meta-agents.

Main outcomes:

- seven demos overall (including the LLM/sandbox extension);
- reproducible CSV/PNG outputs;
- faithful implementation of core parent-selection formulas;
- clear evidence for the importance of self-improvement (Demo 2).

---

## 17. References

### Papers and repositories

- HyperAgents: `https://github.com/facebookresearch/Hyperagents`
- DGM: `https://github.com/jennyzzt/dgm`

### Project files

- `experiments/common.py`
- `experiments/ablation_archive.py`
- `experiments/ablation_self_improve.py`
- `experiments/parent_selection_strategies.py`
- `experiments/task_vowels.py`
- `experiments/mini_code_repair.py`
- `experiments/plot_progress.py`
- `experiments/llm_meta_agent.py`
- `experiments/sandbox.py`
- `experiments/llm_code_repair.py`
- `experiments/demo_passo_passo.ipynb`
- `results/*.csv`, `results/*.png`
