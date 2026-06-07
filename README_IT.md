# DGM-Hyperagents — mini-demo didattiche

Riproduzione in piccolo dei concetti algoritmici di **DGM-Hyperagents** (Zhang et al., arXiv 2603.19461), con sette demo eseguibili su Windows e analisi dei repository ufficiali.

Relazione ufficiale: [`REPORT.md`](REPORT.md) (inglese) · traduzione italiana: [`RELAZIONE.md`](RELAZIONE.md).

English README: [`README.md`](README.md)

---

## Contesto teorico

Questo repository implementa una **mini DGM-H** (Darwin Gödel Machine — Hyperagents): un ciclo evolutivo in cui un **meta-agent** propone modifiche al **task agent**, che viene valutato e inserito in un **archivio open-ended**. A ogni iterazione si seleziona un parent, si generano figli e si ripete.

```text
generate → evaluate → archive → select parent → modify
```

| Demo | Concetto del paper (Sez.) | Cosa verifica |
|---|---|---|
| 1 | Archivio open-ended vs baseline (Alg. 3) | Archivio completo vs solo ultimo agente |
| 2 | Self-improvement del meta-agent (§5.1) | Meta-agent congelato vs meta-agent evolutivo |
| 3 | Parent selection (§8.2) | `random`, `best`, `score_prop`, `score_child_prop` |
| 4 | Multi-domain (§8.4) | Stesso framework su un secondo task (vocali) |
| 5 | Code-repair / Polyglot (§5.1) | Riparazione codice senza LLM |
| 6 | — | Overview grafica di tutte le demo |
| 7 | LLM + safety sandbox (§6) | Ollama + valutazione in Docker (`mock` vs `real`) |

Spiegazione estesa, formule e risultati numerici: [`REPORT.md`](REPORT.md) (§2–§16). Repository ufficiali analizzati: §15.

---

## Prerequisiti

| Componente | Demo 1–6 | Demo 7 (mock) | Demo 7 (LLM reale) |
|---|---|---|---|
| **Python** ≥ 3.10 | sì | sì | sì |
| **matplotlib** | sì (grafici) | sì | sì |
| **Docker Desktop** | no | sì | sì |
| **Ollama** | no | no | sì |
| **litellm** | no | no | sì |

### Repository ufficiali (analisi, opzionale)

I clone non sono inclusi nel repository Git (vedi `.gitignore`). Per l’analisi descritta in REPORT §15:

```powershell
git clone https://github.com/jennyzzt/dgm.git dgm
git clone https://github.com/facebookresearch/Hyperagents.git HyperAgents
cd dgm && git checkout a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2
cd ../HyperAgents && git checkout 59a68f672dfb92c74aeb7e61535d776fb36e172d
```

Commit registrati in [`results/repo_commits.txt`](results/repo_commits.txt).

---

## Configurazione dell’ambiente

Dalla root del progetto (`dgm_hyperagents/`):

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

**Demo 7 — prerequisiti aggiuntivi:**

```bash
docker run hello-world          # obbligatorio per Demo 7 (mock e reale)
ollama pull llama3.2            # solo modalità LLM reale (senza --mock)
```

### Variabili d’ambiente (Demo 7)

| Variabile | Default | Descrizione |
|---|---|---|
| `OLLAMA_MODEL` | `ollama/llama3.2` | Modello LiteLLM |
| `OLLAMA_API_BASE` | `http://localhost:11434` | Endpoint Ollama |
| `DGMH_SANDBOX_IMAGE` | `python:3.12-slim` | Immagine Docker per la sandbox |
| `DGMH_LLM_ITERATIONS` | `12` | Iterazioni del ciclo DGM-H |
| `DGMH_LLM_SEEDS` | `2` | Numero di seed (0 … N−1) |

---

## Esecuzione completa (dall’inizio alla fine)

Dopo il setup sopra, dalla **root** del progetto (con venv attivo):

```bash
# Demo 1–5: solo Python + matplotlib (pochi secondi ciascuna)
python experiments/ablation_archive.py
python experiments/ablation_self_improve.py
python experiments/parent_selection_strategies.py
python experiments/task_vowels.py
python experiments/mini_code_repair.py

# Demo 7: richiede Docker Desktop avviato
python experiments/llm_code_repair.py --mock    # test pipeline Docker (no Ollama)
python experiments/llm_code_repair.py           # LLM reale (Ollama + litellm)

# Demo 6: overview (dopo tutti i CSV)
python experiments/plot_progress.py
```

**Solo Demo 1–6 (senza Docker):** eseguire le prime cinque righe + `plot_progress.py`.  
**Solo rigenerare i PNG** dai CSV già presenti: `python experiments/regenerate_plots.py` poi `plot_progress.py`.

Output atteso: CSV e PNG in `results/` (vedi sezione seguente per il dettaglio per demo).

---

## Esecuzione delle demo (dettaglio)

Tutti i comandi vanno lanciati **dalla root** del progetto. Output in `results/` (CSV + PNG).

### Demo 1 — Ablation archivio

Confronta archivio completo vs solo ultimo agente (palindromi).

```powershell
python experiments/ablation_archive.py
```

- **Output:** `results/ablation_archive.csv`, `results/ablation_archive.png`
- **Varianti CSV:** `con_archivio`, `senza_archivio`
- **Dipendenze:** stdlib + matplotlib

### Demo 2 — Ablation self-improve

Meta-agent congelato vs meta-agent che sblocca mutazioni nascoste.

```powershell
python experiments/ablation_self_improve.py
```

- **Output:** `results/ablation_self_improve.csv`, `results/ablation_self_improve.png`
- **Varianti CSV:** `meta_congelato`, `meta_self_improve`
- **Dipendenze:** stdlib + matplotlib

### Demo 3 — Parent selection

Confronto delle quattro strategie di Sez. 8.2 del paper.

```powershell
python experiments/parent_selection_strategies.py
```

- **Output:** `results/parent_selection.csv`, `results/parent_selection.png`
- **Varianti CSV:** `random`, `best`, `score_prop`, `score_child_prop`
- **Dipendenze:** stdlib + matplotlib

### Demo 4 — Task vocali

Secondo dominio: classificazione stringhe di sole vocali.

```powershell
python experiments/task_vowels.py
```

- **Output:** `results/task_vowels.csv`, `results/task_vowels.png`
- **Varianti CSV:** `task_vocali`
- **Dipendenze:** stdlib + matplotlib

### Demo 5 — Mini code-repair

Code-repair deterministico (`a - b` → `a + b`), senza LLM né Docker.

```powershell
python experiments/mini_code_repair.py
```

- **Output:** `results/code_repair.csv`, `results/code_repair.png`
- **Varianti CSV:** `mini_code_repair`
- **Dipendenze:** stdlib + matplotlib

### Demo 6 — Overview grafica

Grafico riassuntivo da tutti i CSV esistenti.

```powershell
python experiments/plot_progress.py
```

- **Output:** `results/all_demos_overview.png`
- **Dipendenze:** matplotlib
- **Nota:** eseguire dopo le altre demo per avere tutti i CSV.
- **Rigenerare PNG da CSV esistenti** (senza rieseguire le demo): `python experiments/regenerate_plots.py`

### Demo 7 — LLM (Ollama) + Docker sandbox

Stesso task della Demo 5, con meta-agent Ollama e valutazione in container isolato.

**Modalità mock** (patch fissa, nessuna chiamata Ollama — utile per testare Docker):

```powershell
python experiments/llm_code_repair.py --mock
```

**Modalità LLM reale** (Ollama + LiteLLM):

```powershell
python experiments/llm_code_repair.py
```

| Modalità | Flag | Colonna `mode` | Variante CSV | File dedicato |
|---|---|---|---|---|
| Mock | `--mock` | `mock` | `llm_code_repair_mock` | `results/llm_code_repair_mock.csv` |
| LLM reale | (nessuno) | `real` | `llm_code_repair` | `results/llm_code_repair_real.csv` |

File combinato (entrambe le modalità, se presenti): `results/llm_code_repair.csv`  
Grafici: `results/llm_code_repair_mock.png`, `results/llm_code_repair_real.png`, `results/llm_code_repair.png`  
Log: `results/llm_logs/`, `results/sandbox_logs/`, `runs/sandbox/`

---

## Artefatti extra

| Script | Comando | Output |
|---|---|---|
| Demo originale palindromi | `python experiments/mini_dgm_hyperagent.py` | `results/mini_dgm_archive.csv` |
| Notebook didattico | `jupyter notebook experiments/demo_passo_passo.ipynb` | — |

---

## Struttura del progetto

```text
dgm_hyperagents/
├── README.md                 ← versione inglese
├── README_IT.md              ← questo file
├── REPORT.md                 ← relazione ufficiale (inglese)
├── RELAZIONE.md              ← traduzione italiana
├── requirements.txt          ← dipendenze Python (tutte le demo)
├── experiments/              ← codice eseguibile
│   ├── common.py             ← ciclo DGM-H condiviso
│   ├── ablation_archive.py   ← Demo 1
│   ├── ablation_self_improve.py ← Demo 2
│   ├── parent_selection_strategies.py ← Demo 3
│   ├── task_vowels.py        ← Demo 4
│   ├── mini_code_repair.py   ← Demo 5
│   ├── plot_progress.py      ← Demo 6
│   ├── regenerate_plots.py   ← rigenera PNG da CSV
│   ├── llm_code_repair.py    ← Demo 7
│   └── demo_passo_passo.ipynb
├── results/                  ← CSV e PNG generati
├── dgm/                      ← clone repo ufficiale (gitignored)
└── HyperAgents/              ← clone repo ufficiale (gitignored)
```

---

## Repository ufficiali analizzati

| Repository | URL | Commit testato |
|---|---|---|
| DGM | https://github.com/jennyzzt/dgm | `a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2` |
| HyperAgents | https://github.com/facebookresearch/Hyperagents | `59a68f672dfb92c74aeb7e61535d776fb36e172d` |

Dettaglio dell’analisi: REPORT §15.

---

## Riferimenti

- Zhang J. et al. (2026). *Hyperagents*. arXiv 2603.19461.
- Zhang J. et al. (2025). *Darwin Gödel Machine*. arXiv 2505.22954.
