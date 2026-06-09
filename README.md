# DGM-Hyperagents — Educational Mini-Demos

A small-scale reproduction of the algorithmic concepts from **DGM-Hyperagents** (Zhang et al., arXiv 2603.19461), with seven runnable demos on Windows and analysis of the official repositories.

Official report: [`REPORT.md`](REPORT.md) (English) · Italian translation: [`RELAZIONE.md`](RELAZIONE.md).

Italian README: [`README_IT.md`](README_IT.md)

---

## How to read references

| Prefix | Meaning |
|---|---|
| **Paper** / **Paper Sec.** / **Paper §** | Section of the article [*Hyperagents*](https://arxiv.org/abs/2603.19461) (Zhang et al., arXiv 2603.19461) |
| **Report** / **Report §** | Chapter of [`REPORT.md`](REPORT.md) (this repository) |
| `experiments/…` | Runnable code in this repository |

Example: *Paper Sec. 8.2* = parent selection in the article; *Report §8* = our Demo 3 documentation.

---

## Project objective

The goal is **not** to numerically replicate the paper's benchmarks (Polyglot, paper review, robotics, IMO-GradingBench), which require Linux, heavy dependencies, and paid LLM APIs. The goal is to **reproduce on a small scale, on Windows, the same algorithmic ideas** of DGM-Hyperagents:

- open-ended **archive** of agents (stepping stones);
- **meta-agent** that can modify itself (*metacognitive self-modification*);
- probabilistic **parent selection** (Paper Sec. 8.2);
- **empirical evaluation** of each child before archive insertion;
- iterative cycle: `generate → evaluate → archive → select parent → modify`.

Each demo is a controlled experiment on one of these mechanisms. Full theory, formulas, and per-demo analysis: [`REPORT.md`](REPORT.md) (Report §2–§16).

---

## Theoretical background

This repository implements a **mini DGM-H** (Darwin Gödel Machine — Hyperagents): an evolutionary loop where a **meta-agent** proposes changes to a **task agent**, which is evaluated and stored in an **open-ended archive**. Each iteration selects a parent, generates children, and repeats.

```text
generate → evaluate → archive → select parent → modify
```

| Demo | Paper (Hyperagents) | Report | What it verifies |
|---|---|---|---|
| 1 | Open-ended archive vs baseline (Alg. 3) | §6 | Full archive vs last agent only |
| 2 | Meta self-improve (Paper Sec. 4.1, Paper §5.1) | §7 | Frozen meta-agent vs evolving meta-agent |
| 3 | Parent selection (Paper Sec. 8.2) | §8 | `random`, `best`, `score_prop`, `score_child_prop` |
| 4 | Multi-domain (Paper Sec. 8.4) | §9 | Same framework on a second task (vowels) |
| 5 | Code-repair / Polyglot (Paper §5.1) | §10 | Code repair without LLM |
| 6 | — (synthesis) | §11 | Graphical overview of all demos |
| 7 | LLM + safety sandbox (Paper Sec. 6) | §12 | Ollama + Docker evaluation (`mock` vs `real`) |

### DGM / HyperAgents mechanisms used in code

| Paper concept | Implementation | Where |
|---|---|---|
| Hyperagent (task + meta agent) | `HyperAgent`, `MetaAgent`, `TaskAgent` | `experiments/common.py` |
| Algorithm 1 loop | `run_dgm_h()` | `experiments/common.py` |
| Open-ended archive | `archive_mode="full"` vs `"last_only"` | Demo 1 |
| Meta self-improve | `MetaAgent.self_improve` + hidden mutations | Demo 2 |
| Parent selection (Paper Sec. 8.2) | `random`, `best`, `score_prop`, `score_child_prop` | Demo 3 |
| Multi-domain | same loop, different `train_data` / task | Demos 4–5 |
| LLM meta-agent + sandbox | `LLMMetaAgent` + `sandbox.py` (Docker) | Demo 7 |

Extended explanation: [`REPORT.md`](REPORT.md) Report §2–§5. Official repositories: Report §15.

---

## Prerequisites

| Component | Demo 1–6 | Demo 7 (mock) | Demo 7 (real LLM) |
|---|---|---|---|
| **Python** ≥ 3.10 | yes | yes | yes |
| **matplotlib** | yes (plots) | yes | yes |
| **Docker Desktop** | no | yes | yes |
| **Ollama** | no | no | yes |
| **litellm** | no | no | yes |

### Official repositories (optional analysis)

Clones are not included in the Git repository (see `.gitignore`). For the analysis described in Report §15:

```powershell
git clone https://github.com/jennyzzt/dgm.git dgm
git clone https://github.com/facebookresearch/Hyperagents.git HyperAgents
cd dgm && git checkout a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2
cd ../HyperAgents && git checkout 59a68f672dfb92c74aeb7e61535d776fb36e172d
```

Commits recorded in [`results/repo_commits.txt`](results/repo_commits.txt).

---

## Environment setup

From the project root (`dgm_hyperagents/`):

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Demo 7 — additional prerequisites:**

```bash
docker run hello-world          # required for Demo 7 (mock and real)
ollama pull llama3.2            # real LLM mode only (without --mock)
```

### Environment variables (Demo 7)

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `ollama/llama3.2` | LiteLLM model |
| `OLLAMA_API_BASE` | `http://localhost:11434` | Ollama endpoint |
| `DGMH_SANDBOX_IMAGE` | `python:3.12-slim` | Docker image for the sandbox |
| `DGMH_LLM_ITERATIONS` | `12` | DGM-H loop iterations |
| `DGMH_LLM_SEEDS` | `2` | Number of seeds (0 … N−1) |

---

## Full run (start to finish)

After the setup above, from the project **root** (with venv active):

```bash
# Demos 1–5: Python + matplotlib only (a few seconds each)
python experiments/ablation_archive.py
python experiments/ablation_self_improve.py
python experiments/parent_selection_strategies.py
python experiments/task_vowels.py
python experiments/mini_code_repair.py

# Demo 7: requires Docker Desktop running
python experiments/llm_code_repair.py --mock    # test Docker pipeline (no Ollama)
python experiments/llm_code_repair.py           # real LLM (Ollama + litellm)

# Demo 6: overview (after all CSV files exist)
python experiments/plot_progress.py
```

**Demos 1–6 only (no Docker):** run the first five commands + `plot_progress.py`.  
**Regenerate PNGs only** from existing CSVs: `python experiments/regenerate_plots.py` then `plot_progress.py`.

Expected output: CSV and PNG files in `results/` (see per-demo details below).

---

## Demo catalog (objective, variants, outputs, interpretation)

Run all commands **from the project root**. Each demo writes CSV + PNG under `results/` (schema in [Generated files](#generated-files-in-results)).

### Demo 1 — Archive ablation

| | |
|---|---|
| **Objective** | Measure whether keeping the full open-ended archive helps vs keeping only the last agent. |
| **Paper (Hyperagents)** | Baseline `DGM-H w/o open-ended exploration` (Algorithm 3, Paper Sec. 9). |
| **Report** | [Report §6](REPORT.md#6-demo-1--archive-ablation) |
| **Variants** | `con_archivio` (`archive_mode="full"`) vs `senza_archivio` (`archive_mode="last_only"`). Same parent selector (`score_child_prop`), 30 iterations, 5 seeds. |
| **Task** | Palindrome classification (train 12 / test 10 examples). |

```powershell
python experiments/ablation_archive.py
```

- **Output:** `results/ablation_archive.csv`, `results/ablation_archive.png`
- **Read the graph:** X = iteration, Y = mean `best_test` over seeds (0–1). Two curves, one per variant.
- **Expected result:** Both variants reach score **1.0** (around iteration 12); curves overlap. On this small task the archive does not change the outcome — unlike the paper's large benchmarks where removing the archive collapses performance. See [Report §6](REPORT.md#6-demo-1--archive-ablation).

### Demo 2 — Self-improve ablation

| | |
|---|---|
| **Objective** | Measure **metacognitive self-modification**: can the meta-agent unlock better mutations over time? |
| **Paper (Hyperagents)** | Baseline `DGM-H w/o self-improve` (Paper Sec. 4.1, Paper §5.1) — **central idea of the article**. |
| **Report** | [Report §7](REPORT.md#7-demo-2--self-improve-ablation) |
| **Variants** | `meta_congelato` (meta-agent frozen, only base mutations) vs `meta_self_improve` (meta-agent evolves and unlocks `reverse_check`). |
| **Task** | Palindromes (same as Demo 1). |

```powershell
python experiments/ablation_self_improve.py
```

- **Output:** `results/ablation_self_improve.csv`, `results/ablation_self_improve.png`
- **Read the graph:** `meta_self_improve` rises to **1.0**; `meta_congelato` plateaus near **0.67**.
- **Expected result:** This is the **key quantitative difference** in the project (gap 0.333). It mirrors the paper's pattern: without self-improve, performance stays limited. See [Report §7](REPORT.md#7-demo-2--self-improve-ablation).

### Demo 3 — Parent selection strategies

| | |
|---|---|
| **Objective** | Compare four parent-selection strategies from the DGM-H paper. |
| **Paper (Hyperagents)** | Paper Sec. 8.2 (sigmoid weights + novelty bonus). |
| **Report** | [Report §8](REPORT.md#8-demo-3--parent-selection-strategies) |
| **Variants** | `random`, `best` (pure exploitation), `score_prop` (sigmoid only), `score_child_prop` (sigmoid × novelty — DGM-H default). |
| **Task** | Palindromes. |

```powershell
python experiments/parent_selection_strategies.py
```

- **Output:** `results/parent_selection.csv`, `results/parent_selection.png`
- **Read the graph:** Four curves; all should reach **1.0**. `score_prop` / `score_child_prop` often converge slightly earlier than `random` / `best`.
- **Expected result:** On this small task all strategies succeed; differences are mainly convergence speed, not final score. See [Report §8](REPORT.md#8-demo-3--parent-selection-strategies).

### Demo 4 — Second domain (vowels)

| | |
|---|---|
| **Objective** | Show the same DGM-H loop on a **different task** (multi-domain, Paper Sec. 8.4). |
| **Paper (Hyperagents)** | Paper Sec. 8.4 — framework is domain-agnostic. |
| **Report** | [Report §9](REPORT.md#9-demo-4--second-domain-vowels) |
| **Variants** | `task_vocali` (single variant). |
| **Task** | Classify strings made of vowels only (`a,e,i,o,u`). |

```powershell
python experiments/task_vowels.py
```

- **Output:** `results/task_vowels.csv`, `results/task_vowels.png`
- **Read the graph:** Single curve; step-wise rise to **1.0**.
- **Expected result:** Confirms the framework generalizes beyond palindromes. See [Report §9](REPORT.md#9-demo-4--second-domain-vowels).

### Demo 5 — Mini code-repair

| | |
|---|---|
| **Objective** | Miniature of **coding / Polyglot** self-repair: fix `a - b` → `a + b` without an LLM. |
| **Paper (Hyperagents)** | Paper §5.1 (coding agent evolution); connects to DGM on SWE-bench/Polyglot. |
| **Report** | [Report §10](REPORT.md#10-demo-5--mini-code-repair) |
| **Variants** | `mini_code_repair` (deterministic meta-agent proposes patches). |
| **Task** | Tuple addition: `solve((a,b))` must return `a + b`. |

```powershell
python experiments/mini_code_repair.py
```

- **Output:** `results/code_repair.csv`, `results/code_repair.png`
- **Read the graph:** Starts at **0.0** (buggy subtraction fails all tests), then climbs to **1.0** when the correct addition patch is found.
- **Expected result:** Score 1.0 after a few iterations. See [Report §10](REPORT.md#10-demo-5--mini-code-repair).

### Demo 6 — Plot overview

| | |
|---|---|
| **Objective** | Single chart comparing learning curves of all demos. |
| **Paper (Hyperagents)** | — (synthesis, not a separate ablation). |
| **Report** | [Report §11](REPORT.md#11-demo-6--plot-overview) |
| **Input** | Existing CSV files from Demos 1–5 and 7. |

```powershell
python experiments/plot_progress.py
```

- **Output:** `results/all_demos_overview.png` only (no new CSV).
- **Read the graph:** Seven curves (5 deterministic demos + LLM mock + LLM real). Y = mean `best_test` per iteration. Demo 2 average sits between 0.67 and 1.0 because it averages both variants.
- **Regenerate per-demo PNGs** without re-running demos: `python experiments/regenerate_plots.py`
- See [Report §11](REPORT.md#11-demo-6--plot-overview).

### Demo 7 — LLM (Ollama) + Docker sandbox

| | |
|---|---|
| **Objective** | Same task as Demo 5, but meta-agent is **Ollama** (LiteLLM) and code runs in an **isolated Docker sandbox** (Paper Sec. 6 Safety). |
| **Paper (Hyperagents)** | HyperAgents LLM meta-agent + safe execution environment. |
| **Report** | [Report §12](REPORT.md#12-demo-7--llm-ollama--docker-sandbox) |
| **Modes** | **Mock** (`--mock`): fixed correct patch, tests Docker only. **Real** (default): Ollama generates patches. |

**Mock** (no Ollama):

```powershell
python experiments/llm_code_repair.py --mock
```

**Real LLM** (Ollama + LiteLLM):

```powershell
python experiments/llm_code_repair.py
```

| Mode | Flag | `mode` column | CSV variant | Dedicated file |
|---|---|---|---|---|
| Mock | `--mock` | `mock` | `llm_code_repair_mock` | `results/llm_code_repair_mock.csv` |
| Real LLM | (none) | `real` | `llm_code_repair` | `results/llm_code_repair_real.csv` |

- **Output:** mode-specific CSV/PNG + combined `results/llm_code_repair.csv` / `.png`
- **Logs (local, gitignored):** `results/llm_logs/`, `results/sandbox_logs/`, `runs/sandbox/`
- **Read the graph:** Both modes reach **1.0** quickly on this simple task; mock uses a fixed patch, real uses `llama3.2` via Ollama.
- See [Report §12](REPORT.md#12-demo-7--llm-ollama--docker-sandbox).

---

## Generated files in `results/`

### Output file index

| Demo | CSV | PNG | Notes |
|---|---|---|---|
| 1 | `ablation_archive.csv` | `ablation_archive.png` | 2 variants |
| 2 | `ablation_self_improve.csv` | `ablation_self_improve.png` | 2 variants |
| 3 | `parent_selection.csv` | `parent_selection.png` | 4 variants |
| 4 | `task_vowels.csv` | `task_vowels.png` | 1 variant |
| 5 | `code_repair.csv` | `code_repair.png` | 1 variant |
| 6 | — | `all_demos_overview.png` | reads other CSVs |
| 7 mock | `llm_code_repair_mock.csv` | `llm_code_repair_mock.png` | `mode=mock` |
| 7 real | `llm_code_repair_real.csv` | `llm_code_repair_real.png` | `mode=real` |
| 7 combined | `llm_code_repair.csv` | `llm_code_repair.png` | both modes merged |
| extra | `mini_dgm_archive.csv` | — | original palindrome demo |
| meta | `repo_commits.txt` | — | pinned official repo commits |

### CSV column schema (Demos 1–6)

| Column | Meaning |
|---|---|
| `variant` | Configuration label (e.g. `con_archivio`, `meta_self_improve`, `random`) |
| `seed` | Random seed for reproducibility (multiple seeds → average in plots) |
| `iteration` | DGM-H loop step (0 = initial agent only) |
| `best_train` | Best training score in archive up to this iteration (0.0–1.0) |
| `best_test` | Best **test** score in archive up to this iteration (0.0–1.0) — **primary metric in graphs** |
| `best_agent` | Name of the best agent at this iteration |
| `archive_size` | Number of agents stored in the archive |

Demo 7 adds column `mode` (`mock` or `real`).

### How to read the PNG graphs

| Element | Meaning |
|---|---|
| **X-axis (Iterazione / Iteration)** | Evolution step of the DGM-H loop |
| **Y-axis (Best test score)** | Mean of `best_test` over seeds for that variant (per-demo PNGs), or across variants filtered by label (overview) |
| **One curve per variant** | Each line is a configuration or strategy being compared |
| **Score 1.0** | Agent solves all test examples correctly |
| **Flat plateau below 1.0** | Search stuck without the needed mutation (see Demo 2 frozen meta-agent) |

To inspect raw numbers: open the matching `.csv` and filter by `variant` and `seed`.

---

## Interpreting results

### Summary table (committed runs)

| Demo | Key variants | Final test | Main takeaway |
|---|---|---:|---|
| 1 | `con_archivio` / `senza_archivio` | 1.000 / 1.000 | Archive ablation: no gap on small task |
| **2** | `meta_congelato` / `meta_self_improve` | **0.667** / **1.000** | **Self-improve is essential** — main result |
| 3 | four selectors | 1.000 each | All work; minor speed differences |
| 4 | `task_vocali` | 1.000 | Multi-domain OK |
| 5 | `mini_code_repair` | 1.000 | Code-repair without LLM |
| 7 | mock / real | 1.000 / 1.000 | Docker + (optional) Ollama pipeline works |

### Reading guidelines

1. **Prioritize Demo 2** — the only demo with a clear performance gap between variants; it validates the paper's central claim at didactic scale.
2. **Demos 1 and 3** — structural reproductions of paper baselines; convergence to 1.0 on tiny tasks is expected and does **not** contradict the paper (large benchmarks show large gaps).
3. **Demo 7 mock vs real** — `mock` verifies Docker sandbox; `real` verifies Ollama integration. Both reaching 1.0 means the pipeline works; it does not measure LLM quality on hard coding tasks.
4. **Demo 6 overview** — the `Ablation self-improve` curve averages frozen + self-improve variants (~0.83); read Demo 2's dedicated PNG for the split.

Full discussion: [`REPORT.md`](REPORT.md) Report §13–§14.

---

## Extra artifacts

| Script | Command | Output |
|---|---|---|
| Original palindrome demo | `python experiments/mini_dgm_hyperagent.py` | `results/mini_dgm_archive.csv` |
| Tutorial notebook | `jupyter notebook experiments/demo_passo_passo.ipynb` | — |

---

## Project structure

```text
dgm_hyperagents/
├── README.md                 ← this file (English)
├── README_IT.md              ← Italian version
├── REPORT.md                 ← official report (English)
├── RELAZIONE.md              ← Italian translation
├── requirements.txt          ← Python dependencies (all demos)
├── experiments/              ← runnable code
│   ├── common.py             ← shared DGM-H loop
│   ├── ablation_archive.py   ← Demo 1
│   ├── ablation_self_improve.py ← Demo 2
│   ├── parent_selection_strategies.py ← Demo 3
│   ├── task_vowels.py        ← Demo 4
│   ├── mini_code_repair.py   ← Demo 5
│   ├── plot_progress.py      ← Demo 6
│   ├── regenerate_plots.py   ← regenerate PNGs from CSV
│   ├── llm_code_repair.py    ← Demo 7
│   └── demo_passo_passo.ipynb
├── results/                  ← generated CSV and PNG
├── dgm/                      ← official repo clone (gitignored)
└── HyperAgents/              ← official repo clone (gitignored)
```

---

## Official repositories analyzed

| Repository | URL | Tested commit |
|---|---|---|
| DGM | https://github.com/jennyzzt/dgm | `a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2` |
| HyperAgents | https://github.com/facebookresearch/Hyperagents | `59a68f672dfb92c74aeb7e61535d776fb36e172d` |

Analysis details: [Report §15](REPORT.md#15-relationship-with-official-repositories).

---

## References

- Zhang J. et al. (2026). *Hyperagents*. arXiv 2603.19461.
- Zhang J. et al. (2025). *Darwin Gödel Machine*. arXiv 2505.22954.
