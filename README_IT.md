# DGM-Hyperagents — mini-demo didattiche

Riproduzione in piccolo dei concetti algoritmici di **DGM-Hyperagents** (Zhang et al., arXiv 2603.19461), con sette demo eseguibili su Windows e analisi dei repository ufficiali.

Relazione ufficiale: [`REPORT.md`](REPORT.md) (inglese) · traduzione italiana: [`RELAZIONE.md`](RELAZIONE.md).

English README: [`README.md`](README.md)

---

## Come leggere i riferimenti

| Prefisso | Significato |
|---|---|
| **Articolo** / **Articolo Sez.** / **Articolo §** | Sezione dell'articolo [*Hyperagents*](https://arxiv.org/abs/2603.19461) (Zhang et al., arXiv 2603.19461) |
| **Relazione** / **Relazione §** | Capitolo di [`RELAZIONE.md`](RELAZIONE.md) (questo repository) |
| `experiments/…` | Codice eseguibile nel repository |

Esempio: *Articolo Sez. 8.2* = parent selection nell'articolo; *Relazione §8* = documentazione della Demo 3 nel nostro report.

---

## Obiettivo del progetto

L'obiettivo **non** è replicare numericamente i benchmark del paper (Polyglot, paper review, robotics, IMO-GradingBench), che richiedono Linux, dipendenze pesanti e API LLM a pagamento. L'obiettivo è **riprodurre in piccolo, su Windows, le stesse idee algoritmiche** del DGM-Hyperagents:

- **archivio** open-ended di agenti (stepping stones);
- **meta-agent** in grado di modificare sé stesso (*metacognitive self-modification*);
- **parent selection** probabilistica (Articolo Sez. 8.2);
- **valutazione empirica** di ogni figlio prima dell'inserimento in archivio;
- ciclo iterativo: `generate → evaluate → archive → select parent → modify`.

Ogni demo è un esperimento controllato su uno di questi meccanismi. Teoria, formule e analisi per demo: [`RELAZIONE.md`](RELAZIONE.md) (Relazione §2–§16) · [`REPORT.md`](REPORT.md) (inglese).

---

## Contesto teorico

Questo repository implementa una **mini DGM-H** (Darwin Gödel Machine — Hyperagents): un ciclo evolutivo in cui un **meta-agent** propone modifiche al **task agent**, che viene valutato e inserito in un **archivio open-ended**. A ogni iterazione si seleziona un parent, si generano figli e si ripete.

```text
generate → evaluate → archive → select parent → modify
```

| Demo | Articolo (Hyperagents) | Relazione | Cosa verifica |
|---|---|---|---|
| 1 | Archivio open-ended vs baseline (Alg. 3) | §6 | Archivio completo vs solo ultimo agente |
| 2 | Meta self-improve (Articolo Sez. 4.1, Articolo §5.1) | §7 | Meta-agent congelato vs meta-agent evolutivo |
| 3 | Parent selection (Articolo Sez. 8.2) | §8 | `random`, `best`, `score_prop`, `score_child_prop` |
| 4 | Multi-domain (Articolo Sez. 8.4) | §9 | Stesso framework su un secondo task (vocali) |
| 5 | Code-repair / Polyglot (Articolo §5.1) | §10 | Riparazione codice senza LLM |
| 6 | — (sintesi) | §11 | Overview grafica di tutte le demo |
| 7 | LLM + safety sandbox (Articolo Sez. 6) | §12 | Ollama + valutazione in Docker (`mock` vs `real`) |

### Meccanismi DGM / HyperAgents nel codice

| Concetto paper | Implementazione | Dove |
|---|---|---|
| Hyperagent (task + meta agent) | `HyperAgent`, `MetaAgent`, `TaskAgent` | `experiments/common.py` |
| Ciclo Algorithm 1 | `run_dgm_h()` | `experiments/common.py` |
| Archivio open-ended | `archive_mode="full"` vs `"last_only"` | Demo 1 |
| Meta self-improve | `MetaAgent.self_improve` + mutazioni nascoste | Demo 2 |
| Parent selection (Articolo Sez. 8.2) | `random`, `best`, `score_prop`, `score_child_prop` | Demo 3 |
| Multi-domain | stesso ciclo, `train_data` / task diversi | Demo 4–5 |
| Meta-agent LLM + sandbox | `LLMMetaAgent` + `sandbox.py` (Docker) | Demo 7 |

Spiegazione estesa: [`RELAZIONE.md`](RELAZIONE.md) Relazione §2–§5. Repository ufficiali: Relazione §15.

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

I clone non sono inclusi nel repository Git (vedi `.gitignore`). Per l’analisi descritta in Relazione §15:

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

## Catalogo demo (obiettivo, varianti, output, interpretazione)

Tutti i comandi vanno lanciati **dalla root**. Ogni demo scrive CSV + PNG in `results/` (schema in [File generati in `results/`](#file-generati-in-results)).

### Demo 1 — Ablation archivio

| | |
|---|---|
| **Obiettivo** | Misurare se l'archivio open-ended completo aiuta rispetto a tenere solo l'ultimo agente. |
| **Articolo (Hyperagents)** | Baseline `DGM-H w/o open-ended exploration` (Algorithm 3, Articolo Sez. 9). |
| **Relazione** | [Relazione §6](RELAZIONE.md#6-demo-1--ablation-archivio) |
| **Varianti** | `con_archivio` (`archive_mode="full"`) vs `senza_archivio` (`archive_mode="last_only"`). Stesso selettore (`score_child_prop`), 30 iterazioni, 5 seed. |
| **Task** | Classificazione palindromi (12 train / 10 test). |

```powershell
python experiments/ablation_archive.py
```

- **Output:** `results/ablation_archive.csv`, `results/ablation_archive.png`
- **Leggere il grafico:** X = iterazione, Y = media `best_test` sui seed (0–1). Due curve, una per variante.
- **Risultato atteso:** Entrambe le varianti raggiungono **1.0** (circa iterazione 12); curve sovrapposte. Su questo task piccolo l'archivio non cambia l'esito — a differenza dei benchmark grandi dell'articolo. Vedi [Relazione §6](RELAZIONE.md#6-demo-1--ablation-archivio).

### Demo 2 — Ablation self-improve

| | |
|---|---|
| **Obiettivo** | Misurare la **metacognitive self-modification**: il meta-agent può sbloccare mutazioni migliori nel tempo? |
| **Articolo (Hyperagents)** | Baseline `DGM-H w/o self-improve` (Articolo Sez. 4.1, Articolo §5.1) — **idea centrale dell'articolo**. |
| **Relazione** | [Relazione §7](RELAZIONE.md#7-demo-2--ablation-self-improve) |
| **Varianti** | `meta_congelato` (meta-agent bloccato) vs `meta_self_improve` (meta-agent evolutivo, sblocca `reverse_check`). |
| **Task** | Palindromi (come Demo 1). |

```powershell
python experiments/ablation_self_improve.py
```

- **Output:** `results/ablation_self_improve.csv`, `results/ablation_self_improve.png`
- **Leggere il grafico:** `meta_self_improve` sale a **1.0**; `meta_congelato` si ferma circa **0.67**.
- **Risultato atteso:** **Differenza quantitativa chiave** del progetto (gap 0.333). Replica il pattern dell'articolo. Vedi [Relazione §7](RELAZIONE.md#7-demo-2--ablation-self-improve).

### Demo 3 — Strategie di parent selection

| | |
|---|---|
| **Obiettivo** | Confrontare quattro strategie di parent selection del paper DGM-H. |
| **Articolo (Hyperagents)** | Articolo Sez. 8.2 (pesi sigmoide + novelty bonus). |
| **Relazione** | [Relazione §8](RELAZIONE.md#8-demo-3--strategie-di-parent-selection) |
| **Varianti** | `random`, `best` (solo exploitation), `score_prop` (solo sigmoide), `score_child_prop` (sigmoide × novelty — default DGM-H). |
| **Task** | Palindromi. |

```powershell
python experiments/parent_selection_strategies.py
```

- **Output:** `results/parent_selection.csv`, `results/parent_selection.png`
- **Leggere il grafico:** Quattro curve; tutte dovrebbero arrivare a **1.0**. `score_prop` / `score_child_prop` spesso convergono leggermente prima.
- **Risultato atteso:** Su task piccolo tutte le strategie riescono; differenze soprattutto di velocità. Vedi [Relazione §8](RELAZIONE.md#8-demo-3--strategie-di-parent-selection).

### Demo 4 — Secondo dominio (vocali)

| | |
|---|---|
| **Obiettivo** | Stesso ciclo DGM-H su un **task diverso** (multi-domain, Articolo Sez. 8.4). |
| **Articolo (Hyperagents)** | Articolo Sez. 8.4 — framework indipendente dal dominio. |
| **Relazione** | [Relazione §9](RELAZIONE.md#9-demo-4--secondo-dominio-vocali) |
| **Varianti** | `task_vocali` (variante unica). |
| **Task** | Classificare stringhe di sole vocali (`a,e,i,o,u`). |

```powershell
python experiments/task_vowels.py
```

- **Output:** `results/task_vowels.csv`, `results/task_vowels.png`
- **Leggere il grafico:** Curva unica; salita a scalini fino a **1.0**.
- **Risultato atteso:** Il framework generalizza oltre i palindromi. Vedi [Relazione §9](RELAZIONE.md#9-demo-4--secondo-dominio-vocali).

### Demo 5 — Mini code-repair

| | |
|---|---|
| **Obiettivo** | Miniatura del **code-repair / Polyglot**: correggere `a - b` → `a + b` senza LLM. |
| **Articolo (Hyperagents)** | Articolo §5.1 (evoluzione agente di coding); collegamento al DGM su SWE-bench/Polyglot. |
| **Relazione** | [Relazione §10](RELAZIONE.md#10-demo-5--mini-code-repair) |
| **Varianti** | `mini_code_repair` (meta-agent deterministico). |
| **Task** | Somma di tuple: `solve((a,b))` deve restituire `a + b`. |

```powershell
python experiments/mini_code_repair.py
```

- **Output:** `results/code_repair.csv`, `results/code_repair.png`
- **Leggere il grafico:** Parte da **0.0** (sottrazione errata), poi sale a **1.0** con la patch corretta.
- **Risultato atteso:** Score 1.0 dopo poche iterazioni. Vedi [Relazione §10](RELAZIONE.md#10-demo-5--mini-code-repair).

### Demo 6 — Overview grafica

| | |
|---|---|
| **Obiettivo** | Grafico unico con le curve di apprendimento di tutte le demo. |
| **Articolo (Hyperagents)** | — (sintesi, non ablation separata). |
| **Relazione** | [Relazione §11](RELAZIONE.md#11-demo-6--plot-overview) |
| **Input** | CSV delle Demo 1–5 e 7. |

```powershell
python experiments/plot_progress.py
```

- **Output:** solo `results/all_demos_overview.png`
- **Leggere il grafico:** Sette curve; Y = media `best_test`. La curva Demo 2 sta tra 0.67 e 1.0 perché media entrambe le varianti.
- **Rigenerare PNG per-demo** senza rieseguire: `python experiments/regenerate_plots.py`
- Vedi [Relazione §11](RELAZIONE.md#11-demo-6--plot-overview).

### Demo 7 — LLM (Ollama) + Docker sandbox

| | |
|---|---|
| **Obiettivo** | Stesso task della Demo 5, meta-agent **Ollama** (LiteLLM) e codice in **sandbox Docker** isolata (Articolo Sez. 6 Safety). |
| **Articolo (Hyperagents)** | Meta-agent LLM HyperAgents + esecuzione sicura. |
| **Relazione** | [Relazione §12](RELAZIONE.md#12-demo-7--llm-ollama--docker-sandbox) |
| **Modalità** | **Mock** (`--mock`): patch fissa, testa solo Docker. **Reale** (default): patch generate da Ollama. |

**Mock** (senza Ollama):

```powershell
python experiments/llm_code_repair.py --mock
```

**LLM reale** (Ollama + LiteLLM):

```powershell
python experiments/llm_code_repair.py
```

| Modalità | Flag | Colonna `mode` | Variante CSV | File dedicato |
|---|---|---|---|---|
| Mock | `--mock` | `mock` | `llm_code_repair_mock` | `results/llm_code_repair_mock.csv` |
| LLM reale | (nessuno) | `real` | `llm_code_repair` | `results/llm_code_repair_real.csv` |

- **Output:** CSV/PNG per modalità + combinati `results/llm_code_repair.csv` / `.png`
- **Log (locali, gitignored):** `results/llm_logs/`, `results/sandbox_logs/`, `runs/sandbox/`
- **Leggere il grafico:** Entrambe le modalità raggiungono **1.0** rapidamente su questo task semplice.
- Vedi [Relazione §12](RELAZIONE.md#12-demo-7--llm-ollama--docker-sandbox).

---

## File generati in `results/`

### Indice file di output

| Demo | CSV | PNG | Note |
|---|---|---|---|
| 1 | `ablation_archive.csv` | `ablation_archive.png` | 2 varianti |
| 2 | `ablation_self_improve.csv` | `ablation_self_improve.png` | 2 varianti |
| 3 | `parent_selection.csv` | `parent_selection.png` | 4 varianti |
| 4 | `task_vowels.csv` | `task_vowels.png` | 1 variante |
| 5 | `code_repair.csv` | `code_repair.png` | 1 variante |
| 6 | — | `all_demos_overview.png` | legge altri CSV |
| 7 mock | `llm_code_repair_mock.csv` | `llm_code_repair_mock.png` | `mode=mock` |
| 7 reale | `llm_code_repair_real.csv` | `llm_code_repair_real.png` | `mode=real` |
| 7 combinato | `llm_code_repair.csv` | `llm_code_repair.png` | entrambe le modalità |
| extra | `mini_dgm_archive.csv` | — | demo palindromi originale |
| meta | `repo_commits.txt` | — | commit repo ufficiali |

### Schema colonne CSV (Demo 1–6)

| Colonna | Significato |
|---|---|
| `variant` | Etichetta configurazione (es. `con_archivio`, `meta_self_improve`) |
| `seed` | Seed per riproducibilità (più seed → media nei grafici) |
| `iteration` | Passo del ciclo DGM-H (0 = solo agente iniziale) |
| `best_train` | Miglior score training in archivio fino a questa iterazione (0.0–1.0) |
| `best_test` | Miglior score **test** — **metrica principale nei grafici** |
| `best_agent` | Nome del miglior agente a questa iterazione |
| `archive_size` | Numero di agenti in archivio |

La Demo 7 aggiunge la colonna `mode` (`mock` o `real`).

### Come leggere i grafici PNG

| Elemento | Significato |
|---|---|
| **Asse X (Iterazione)** | Passo evolutivo del ciclo DGM-H |
| **Asse Y (Best test score)** | Media di `best_test` sui seed per quella variante |
| **Una curva per variante** | Ogni linea è una configurazione o strategia confrontata |
| **Score 1.0** | L'agente risolve correttamente tutti gli esempi di test |
| **Plateau sotto 1.0** | Ricerca bloccata senza la mutazione necessaria (vedi Demo 2 meta congelato) |

Per i numeri grezzi: aprire il `.csv` corrispondente e filtrare per `variant` e `seed`.

---

## Interpretazione dei risultati

### Tabella riassuntiva (run committati)

| Demo | Varianti chiave | Test finale | Messaggio principale |
|---|---|---:|---|
| 1 | `con_archivio` / `senza_archivio` | 1.000 / 1.000 | Ablation archivio: nessun gap su task piccolo |
| **2** | `meta_congelato` / `meta_self_improve` | **0.667** / **1.000** | **Self-improve essenziale** — risultato principale |
| 3 | quattro selettori | 1.000 ciascuno | Tutti funzionano; piccole differenze di velocità |
| 4 | `task_vocali` | 1.000 | Multi-domain OK |
| 5 | `mini_code_repair` | 1.000 | Code-repair senza LLM |
| 7 | mock / reale | 1.000 / 1.000 | Pipeline Docker + (opz.) Ollama funzionante |

### Linee guida

1. **Priorità alla Demo 2** — unica con gap chiaro tra varianti; valida la tesi centrale del paper a scala didattica.
2. **Demo 1 e 3** — riproduzioni strutturali delle baseline; convergenza a 1.0 su task piccoli è attesa e **non** contraddice il paper.
3. **Demo 7 mock vs reale** — `mock` verifica Docker; `reale` verifica Ollama. Entrambi a 1.0 = pipeline OK, non misura qualità LLM su task difficili.
4. **Overview Demo 6** — la curva self-improve media le due varianti (~0.83); per il dettaglio usare il PNG dedicato della Demo 2.

Discussione completa: [`RELAZIONE.md`](RELAZIONE.md) Relazione §13–§14.

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

Dettaglio dell’analisi: [Relazione §15](RELAZIONE.md#15-relazione-con-i-repository-ufficiali).

---

## Riferimenti

- Zhang J. et al. (2026). *Hyperagents*. arXiv 2603.19461.
- Zhang J. et al. (2025). *Darwin Gödel Machine*. arXiv 2505.22954.
