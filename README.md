# DGM-Hyperagents — Educational Mini-Demos

A small-scale reproduction of the algorithmic concepts from **DGM-Hyperagents** (Zhang et al., arXiv 2603.19461), with seven runnable demos on Windows and analysis of the official repositories.

Official report: [`REPORT.md`](REPORT.md) (English) · Italian translation: [`RELAZIONE.md`](RELAZIONE.md).

Italian README: [`README_IT.md`](README_IT.md)

---

## Theoretical background

This repository implements a **mini DGM-H** (Darwin Gödel Machine — Hyperagents): an evolutionary loop where a **meta-agent** proposes changes to a **task agent**, which is evaluated and stored in an **open-ended archive**. Each iteration selects a parent, generates children, and repeats.

```text
generate → evaluate → archive → select parent → modify
```

| Demo | Paper concept (Sec.) | What it verifies |
|---|---|---|
| 1 | Open-ended archive vs baseline (Alg. 3) | Full archive vs last agent only |
| 2 | Meta-agent self-improvement (§5.1) | Frozen meta-agent vs evolving meta-agent |
| 3 | Parent selection (§8.2) | `random`, `best`, `score_prop`, `score_child_prop` |
| 4 | Multi-domain (§8.4) | Same framework on a second task (vowels) |
| 5 | Code-repair / Polyglot (§5.1) | Code repair without LLM |
| 6 | — | Graphical overview of all demos |
| 7 | LLM + safety sandbox (§6) | Ollama + Docker evaluation (`mock` vs `real`) |

Extended explanation, formulas, and numeric results: [`REPORT.md`](REPORT.md) (§2–§16). Official repositories: §15.

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

Clones are not included in the Git repository (see `.gitignore`). For the analysis described in REPORT §15:

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

## Running the demos (details)

Run all commands **from the project root**. Output in `results/` (CSV + PNG).

### Demo 1 — Archive ablation

Compares full archive vs last agent only (palindromes).

```powershell
python experiments/ablation_archive.py
```

- **Output:** `results/ablation_archive.csv`, `results/ablation_archive.png`
- **CSV variants:** `con_archivio`, `senza_archivio`
- **Dependencies:** stdlib + matplotlib

### Demo 2 — Self-improve ablation

Frozen meta-agent vs meta-agent that unlocks hidden mutations.

```powershell
python experiments/ablation_self_improve.py
```

- **Output:** `results/ablation_self_improve.csv`, `results/ablation_self_improve.png`
- **CSV variants:** `meta_congelato`, `meta_self_improve`
- **Dependencies:** stdlib + matplotlib

### Demo 3 — Parent selection

Compares the four strategies from Sec. 8.2 of the paper.

```powershell
python experiments/parent_selection_strategies.py
```

- **Output:** `results/parent_selection.csv`, `results/parent_selection.png`
- **CSV variants:** `random`, `best`, `score_prop`, `score_child_prop`
- **Dependencies:** stdlib + matplotlib

### Demo 4 — Vowel task

Second domain: classify strings of vowels only.

```powershell
python experiments/task_vowels.py
```

- **Output:** `results/task_vowels.csv`, `results/task_vowels.png`
- **CSV variants:** `task_vocali`
- **Dependencies:** stdlib + matplotlib

### Demo 5 — Mini code-repair

Deterministic code repair (`a - b` → `a + b`), no LLM or Docker.

```powershell
python experiments/mini_code_repair.py
```

- **Output:** `results/code_repair.csv`, `results/code_repair.png`
- **CSV variants:** `mini_code_repair`
- **Dependencies:** stdlib + matplotlib

### Demo 6 — Plot overview

Summary chart from all existing CSV files.

```powershell
python experiments/plot_progress.py
```

- **Output:** `results/all_demos_overview.png`
- **Dependencies:** matplotlib
- **Note:** run after the other demos to have all CSV files.
- **Regenerate PNGs from existing CSVs** (without re-running demos): `python experiments/regenerate_plots.py`

### Demo 7 — LLM (Ollama) + Docker sandbox

Same task as Demo 5, with Ollama meta-agent and evaluation in an isolated container.

**Mock mode** (fixed patch, no Ollama calls — useful to test Docker):

```powershell
python experiments/llm_code_repair.py --mock
```

**Real LLM mode** (Ollama + LiteLLM):

```powershell
python experiments/llm_code_repair.py
```

| Mode | Flag | `mode` column | CSV variant | Dedicated file |
|---|---|---|---|---|
| Mock | `--mock` | `mock` | `llm_code_repair_mock` | `results/llm_code_repair_mock.csv` |
| Real LLM | (none) | `real` | `llm_code_repair` | `results/llm_code_repair_real.csv` |

Combined file (both modes, when present): `results/llm_code_repair.csv`  
Plots: `results/llm_code_repair_mock.png`, `results/llm_code_repair_real.png`, `results/llm_code_repair.png`  
Logs: `results/llm_logs/`, `results/sandbox_logs/`, `runs/sandbox/`

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

Analysis details: REPORT §15.

---

## References

- Zhang J. et al. (2026). *Hyperagents*. arXiv 2603.19461.
- Zhang J. et al. (2025). *Darwin Gödel Machine*. arXiv 2505.22954.
