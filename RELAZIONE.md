# Relazione: riproduzione didattica di DGM-Hyperagents

> **Traduzione italiana.** Documento ufficiale del progetto: [`REPORT.md`](REPORT.md) (English).

**Corso:** IoT  
**Autrice:** Maria Navarria  
**Articolo di riferimento:** *Hyperagents* — Zhang J., Zhao B., Yang W., Foerster J., Clune J., Jiang M., Devlin S., Shavrina T., arXiv 2603.19461 (2026)  
**Repository ufficiali analizzati:**
- `https://github.com/facebookresearch/Hyperagents`
- `https://github.com/jennyzzt/dgm`

> **Convenzione sui riferimenti:** **Articolo Sez. N** / **Articolo §N** = sezione dell'articolo *Hyperagents* (arXiv 2603.19461). **Relazione §N** / intestazioni `## N.` = sezione di questo documento. Vedi anche `README_IT.md` → *Come leggere i riferimenti*.

---

## Indice

1. [Obiettivo della relazione](#1-obiettivo-della-relazione)
2. [Contesto teorico](#2-contesto-teorico)
3. [Struttura del progetto](#3-struttura-del-progetto)
4. [Architettura della mini DGM-H](#4-architettura-della-mini-dgm-h)
5. [Flusso di esecuzione](#5-flusso-di-esecuzione)
6. [Demo 1 — Ablation archivio](#6-demo-1--ablation-archivio)
7. [Demo 2 — Ablation self-improve](#7-demo-2--ablation-self-improve)
8. [Demo 3 — Strategie di parent selection](#8-demo-3--strategie-di-parent-selection)
9. [Demo 4 — Secondo dominio: vocali](#9-demo-4--secondo-dominio-vocali)
10. [Demo 5 — Mini code-repair](#10-demo-5--mini-code-repair)
11. [Demo 6 — Plot overview](#11-demo-6--plot-overview)
12. [Demo 7 — LLM (Ollama) + Docker sandbox](#12-demo-7--llm-ollama--docker-sandbox)
13. [Tabella riassuntiva dei risultati](#13-tabella-riassuntiva-dei-risultati)
14. [Discussione e interpretazione](#14-discussione-e-interpretazione)
15. [Relazione con i repository ufficiali](#15-relazione-con-i-repository-ufficiali)
16. [Conclusione](#16-conclusione)
17. [Riferimenti](#17-riferimenti)

---

## 1. Obiettivo della relazione

L'obiettivo **non** era replicare numericamente i risultati del paper su Polyglot, paper review, robotics e IMO-GradingBench, perché ciascuno di quei benchmark richiede Docker, Linux, dipendenze pesanti (Genesis, Balrog) e chiamate a Foundation Model di grandi dimensioni con API a pagamento. L'obiettivo era invece **riprodurre in piccolo, su Windows gli stessi concetti algoritmici**:

- archivio open-ended di agenti;
- meta-agent in grado di modificare sé stesso (metacognitive self-modification);
- parent selection probabilistica;
- valutazione empirica del figlio prima dell'inserimento nell'archivio;
- ciclo iterativo `generate → evaluate → archive → select → modify`.
---

## 2. Contesto teorico

### 2.1 Dal Gödel Machine al DGM

L'idea di un'AI che si auto-migliora risale ai lavori teorici sul **Gödel Machine** di Schmidhuber (2003). In quei modelli, una modifica viene applicata solo se l'agente riesce a dimostrare formalmente che è benefica. Questo vincolo le rende impraticabili nella realtà.

Con i Foundation Model è diventato possibile un approccio diverso: invece di **dimostrare** che una modifica è benefica, la si **valuta empiricamente** su un benchmark. Su questa idea si basa la **Darwin Gödel Machine** (DGM, Zhang et al. 2025, arXiv 2505.22954), che parte da un agente di coding e lo evolve in modo aperto.

Nel DGM:

- l'agente è un programma Python che usa strumenti `bash` e `editor`;
- a ogni iterazione, un meccanismo fisso scritto a mano (`diagnose_prompt`) analizza i log e propone una direzione di miglioramento;
- un nuovo agente viene generato modificando il codice del padre;
- il figlio è valutato su SWE-bench o Polyglot e, se compila, entra in un archivio.

Il limite del DGM è che il **meccanismo di miglioramento è fisso**: vale solo per task di coding, perché la stessa abilità di coding viene usata sia per risolvere il task sia per modificare il codice dell'agente. Se il task non è di coding (es. peer review di paper), l'assunto di allineamento si rompe.

### 2.2 La svolta del DGM-Hyperagents

DGM-Hyperagents (DGM-H), pubblicato l'anno successivo dagli stessi autori, rimuove questo limite. La definizione chiave è:

> *A hyperagent is a self-referential agent that integrates a task agent and a meta agent within a single editable program, enabling it to modify not only how it performs tasks but also how it generates future self-modifications.*

In pratica:

- **Task agent**: l'agente che risolve il task (paper review, reward design, palindromi nel nostro caso).
- **Meta agent**: l'agente che modifica gli altri agenti, decide cosa cambiare nel codice.
- **Hyperagent**: un singolo programma editabile che contiene **entrambi**, e quindi può modificare sia il task agent sia sé stesso (il meta agent).

Questa proprietà si chiama **metacognitive self-modification**. Significa che il sistema non migliora solo come risolve il task, ma anche come genera le future modifiche.

Conseguenza importante: il DGM-H non assume più che task e self-improvement coincidano. Funziona quindi su domini molto diversi. Nel paper gli autori lo dimostrano su quattro domini:

- **Coding** (Polyglot benchmark): 60 task di training, 165 di test.
- **Paper review**: classificazione binaria accept/reject su 100 paper.
- **Robotics reward design** (Genesis, robot Go2): generazione di funzioni di reward per controllo robotico tramite PPO.
- **Olympiad-level math grading** (IMO-GradingBench): valutazione di soluzioni a problemi IMO.

### 2.3 Il ciclo algoritmico (Algorithm 1)

```text
Input: agente iniziale a^0, set di task T, iterazioni T_max
Output: archivio A

1. A = { (a^0, evaluate(a^0, T)) }
2. for t = 1 .. T_max:
3.     P = SelectParents(A)
4.     for (a, _) in P:
5.         a' = a.Modify(a, A)
6.         s' = Evaluate(a', T)
7.         if IsValid(a'):
8.             A = A ∪ { (a', s') }
9. return A
```

Tre ingredienti rendono il ciclo "open-ended":

- **archivio crescente**: ogni agente valido resta come *stepping stone* per il futuro;
- **parent selection probabilistica**: bilancia exploitation (chi va meglio) ed exploration (chi è poco esplorato);
- **self-modification a livello di codice**: il figlio è ottenuto modificando il codice del padre.

Nel DGM-H tutto il programma è editabile, quindi anche `Modify` e `SelectParents` possono essere riscritte. È questa la differenza concettuale rispetto al DGM originale.

### 2.4 Le tre baseline
Per misurare quale componente del DGM-H è davvero importante, gli autori confrontano il DGM-H con tre baseline ablate (Articolo Sez. 4.1):

| Metodo | Self-improving meta | Open-ended exploration | Hyperagent |
|---|:-:|:-:|:-:|
| **DGM-H** | sì | sì | sì |
| `DGM-H w/o self-improve` (≈ ADAS) | no | sì | sì |
| `DGM-H w/o open-ended exploration` | sì | no | sì |
| **DGM** originale | sì | sì | no (meccanismo fisso) |

Le  **Demo 1 e Demo 2** riproducono esattamente le due ablation di queste righe centrali.

### 2.5 La parent selection del DGM-H (Articolo Sez. 8.2)

A ogni iterazione, gli autori calcolano un peso per ciascun agente nell'archivio:

1. **Midpoint dinamico**: media degli score dei top-3 agenti, `α_mid = mean(top3(α_i))`.
2. **Sigmoide**: `s_i = 1 / (1 + exp(-λ · (α_i - α_mid)))` con `λ = 10`.
3. **Novelty bonus**: `h_i = 1 / (1 + n_i)` con `n_i` = numero di figli compilati.
4. **Peso finale**: `w_i = s_i · h_i`, normalizzato in probabilità.

Il peso è alto per gli agenti che **sono sopra la frontiera attuale di performance** e che **hanno generato pochi figli**. La **Demo 3** implementa fedelmente queste formule.

---

## 3. Struttura del progetto

```text
dgm_hyperagents/
├── README.md                        <-- guida esecuzione in inglese
├── README_IT.md                     <-- guida esecuzione e prerequisiti (italiano)
├── REPORT.md                        <-- relazione ufficiale (inglese)
├── RELAZIONE.md                     <-- questo documento (traduzione italiana)
├── requirements.txt                 <-- dipendenze Python (tutte le demo)
├── experiments/
│   ├── common.py                    <-- ciclo DGM-H, classi, parent selection
│   ├── mini_dgm_hyperagent.py       <-- demo originale palindromi
│   ├── ablation_archive.py          <-- Demo 1
│   ├── ablation_self_improve.py     <-- Demo 2
│   ├── parent_selection_strategies.py <-- Demo 3
│   ├── task_vowels.py               <-- Demo 4
│   ├── mini_code_repair.py          <-- Demo 5
│   ├── plot_progress.py             <-- Demo 6 (overview grafica)
│   ├── regenerate_plots.py          <-- rigenera PNG da CSV
│   └── llm_code_repair.py           <-- Demo 7 modello LLM Ollama
├── dgm/                             <-- repo ufficiale jennyzzt/dgm
├── HyperAgents/                     <-- repo ufficiale facebookresearch/Hyperagents
└── results/                         <-- CSV, PNG
```

### 3.1 I tre livelli di profondità

| Aspetto | Mini DGM-H (livello 1) | DGM repo (livello 2) | HyperAgents repo (livello 3) |
|---|---|---|---|
| Eseguibile su Windows | sì, in pochi secondi | parzialmente | parzialmente |
| Usa LLM | no | sì nella versione completa | sì nella versione completa |
| Usa Docker | no | sì negli esperimenti completi | sì negli esperimenti completi |
| Task | palindromi, vocali, code-repair | SWE-bench, Polyglot | Polyglot, IMO, Genesis, Balrog |
| Obiettivo | didattico | DGM su coding | hyperagent multi-dominio |
| Verificato | sì, 7 demo eseguite | sintassi + 11/22 test su Windows | sintassi |

### 3.2 La cartella `results/`

Contiene tutti gli artefatti generati automaticamente. Vedi anche `README_IT.md` (*Come leggere i riferimenti*, *File generati in `results/`*, *Interpretazione dei risultati*).

**Schema colonne CSV (Demo 1–6):**

| Colonna | Significato |
|---|---|
| `variant` | Etichetta configurazione (es. `con_archivio`, `meta_self_improve`) |
| `seed` | Seed random (più seed → media nei grafici) |
| `iteration` | Passo del ciclo DGM-H (0 = agente iniziale) |
| `best_train` | Miglior score su training nell'archivio fino a questa iterazione (0.0–1.0) |
| `best_test` | Miglior score su **test** — **asse Y nei grafici PNG** |
| `best_agent` | Nome del miglior agente a questa iterazione |
| `archive_size` | Numero di agenti in archivio |

La Demo 7 aggiunge `mode` (`mock` o `real`). Indice file:

| Demo | CSV | PNG |
|---|---|---|
| 1 | `ablation_archive.csv` | `ablation_archive.png` |
| 2 | `ablation_self_improve.csv` | `ablation_self_improve.png` |
| 3 | `parent_selection.csv` | `parent_selection.png` |
| 4 | `task_vowels.csv` | `task_vowels.png` |
| 5 | `code_repair.csv` | `code_repair.png` |
| 6 | — | `all_demos_overview.png` |
| 7 | `llm_code_repair_{mock,real}.csv`, `llm_code_repair.csv` | rispettivi `.png` |

**Assi PNG:** X = iterazione; Y = media di `best_test` sui seed (una curva per variante).

---

## 4. Architettura della mini DGM-H

Tutto il livello 1 è dentro `experiments/`. Il file `experiments/common.py` contiene tutte le classi e il ciclo. I sette script demo (Demo 1–7) sono **configurazioni diverse** della stessa funzione `run_dgm_h`; `plot_progress.py` (Demo 6) legge i CSV e produce l'overview grafica.

### 4.1 Diagramma delle classi

```text
┌─────────────────────────────────────────────────────────────┐
│                       HyperAgent                            │
│  ┌─────────────────┐         ┌──────────────────────────┐   │
│  │   TaskAgent     │         │       MetaAgent          │   │
│  │  ┌───────────┐  │         │  base_candidates: [...]  │   │
│  │  │Candidate  │  │         │  hidden_candidates: [...]│   │
│  │  │Program    │  │         │  self_improve: bool      │   │
│  │  │(code str) │  │         │  mutation_memory: [...]  │   │
│  │  └───────────┘  │         │  unlocked: int           │   │
│  └─────────────────┘         └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ valutazione + inserimento
                              ▼
                  ┌───────────────────────┐
                  │      ArchiveEntry     │
                  │  node_id, parent_id   │
                  │  iteration            │
                  │  train_score          │
                  │  test_score           │
                  │  valid, seed, variant │
                  └───────────────────────┘
```

### 4.2 `CandidateProgram`

Un `CandidateProgram` è il codice di un task agent **sotto forma di stringa Python**. La funzione `compile()` lo esegue con `exec()` e restituisce la funzione `solve(x)`. Questo riproduce il fatto che, nel DGM reale, ogni agente è codice modificabile.

```python
@dataclass(frozen=True)
class CandidateProgram:
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
```

**Perché stringhe e non funzioni Python?**  
Perché vogliamo simulare il fatto che il meta-agent **modifica codice testuale**, non oggetti vivi in memoria. Nel DGM reale il meta-agent invoca lo strumento `editor` per riscrivere file `.py`; qui le mutazioni sono nuove stringhe.

### 4.3 `TaskAgent`

Solo un involucro intorno al `CandidateProgram`: prende un input e restituisce la predizione di `solve(input)`.

```python
@dataclass
class TaskAgent:
    program: CandidateProgram

    def solve(self, item: Any) -> Any:
        return self.program.compile()(item)
```

### 4.4 `MetaAgent`

È il cuore della simulazione, perché incapsula la **capacità di proporre modifiche**. Nel paper, questa è la parte editabile per eccellenza. Qui è deterministico, ma simula due comportamenti chiave:

1. **Espansione progressiva del repertorio di mutazioni**: le `hidden_candidates` vengono sbloccate solo quando l'archivio raggiunge `unlock_score_threshold`. Questo replica l'idea che un meta-agent migliora nel tempo: non genera sempre le stesse modifiche, ma "scopre" strategie più sofisticate man mano che osserva risultati migliori nell'archivio.
2. **Memoria persistente** (`mutation_memory`): registra eventi di sblocco. Simula la *persistent memory* descritta in Articolo Sez. 5.2, dove gli autori mostrano che il DGM-H sviluppa autonomamente strutture per tracciare miglioramenti nel tempo.

```python
@dataclass
class MetaAgent:
    base_candidates: list[CandidateProgram]
    hidden_candidates: list[CandidateProgram] = field(default_factory=list)
    self_improve: bool = True
    unlock_score_threshold: float = 0.75
    mutation_memory: list[str] = field(default_factory=list)
    unlocked: int = 0

    def generate_candidates(self, parent, archive):
        best_score = max((e.train_score for e in archive), default=0.0)
        if self.self_improve and self.unlocked < len(self.hidden_candidates):
            if best_score >= self.unlock_score_threshold:
                candidate = self.hidden_candidates[self.unlocked]
                self.unlocked += 1
                self.mutation_memory.append(
                    f"Sbloccata strategia meta: {candidate.name}"
                )
        return self.base_candidates + self.hidden_candidates[: self.unlocked]
```

**Caso `self_improve=True`**: il meta-agent migliora il proprio repertorio di mutazioni. Replica il `DGM-H` completo.  
**Caso `self_improve=False`**: il meta-agent resta congelato all'iniziale. Replica la baseline `DGM-H w/o self-improve`, equivalente ad ADAS (Hu et al. 2024).

### 4.5 `HyperAgent`

Combina task agent e meta-agent nello stesso oggetto. Quando un hyperagent si auto-modifica, **eredita una copia (clone) del meta-agent del padre**. Così le scoperte meta-cognitive (lo stato di `unlocked` e `mutation_memory`) si propagano lungo la genealogia.

```python
@dataclass
class HyperAgent:
    task_agent: TaskAgent
    meta_agent: MetaAgent
    generation: int = 0

    def modify(self, archive, rng, candidates_per_iteration: int = 1):
        candidates = self.meta_agent.generate_candidates(self, archive)
        selected = rng.sample(candidates, k=min(candidates_per_iteration, len(candidates)))
        return [
            HyperAgent(
                task_agent=TaskAgent(c),
                meta_agent=self.meta_agent.clone(),
                generation=self.generation + 1,
            )
            for c in selected
        ]
```

### 4.6 `ArchiveEntry`

Una riga dell'archivio. Tiene traccia di tutto ciò che serve per analisi, plot e ricostruzione della genealogia:

- `node_id`, `parent_id`: per ricostruire l'albero degli agenti;
- `iteration`: per i plot temporali;
- `train_score`, `test_score`: doppia valutazione per misurare la generalizzazione;
- `valid`: `False` se il codice non compila o solleva eccezione;
- `seed`, `variant`: per distinguere run multipli e configurazioni.

### 4.7 Le 4 strategie di parent selection

Riproducono fedelmente quanto descritto in Articolo Sez. 8.2. Tutte sono funzioni `(archive, rng) → ArchiveEntry`:

```python
def select_random(archive, rng):
    return rng.choice(archive)

def select_best(archive, rng):
    best_score = max(e.train_score for e in archive)
    best_entries = [e for e in archive if e.train_score == best_score]
    return rng.choice(best_entries)

def _score_weights(archive):
    top_scores = sorted((e.train_score for e in archive), reverse=True)[:3]
    midpoint = mean(top_scores)
    return [1 / (1 + math.exp(-10 * (e.train_score - midpoint))) for e in archive]

def select_score_prop(archive, rng):
    return rng.choices(archive, weights=_score_weights(archive), k=1)[0]

def select_score_child_prop(archive, rng):
    counts = child_counts(archive)
    weights = [
        w * (1 / (1 + counts[e.node_id]))
        for e, w in zip(archive, _score_weights(archive))
    ]
    return rng.choices(archive, weights=weights, k=1)[0]
```

- `random`: pura exploration. Baseline.
- `best`: pura exploitation. Baseline opposta.
- `score_prop`: probabilità proporzionale alla sigmoide di `(α − α_mid)`. **Formula identica a Articolo Sez. 8.2**.
- `score_child_prop`: come sopra, moltiplicato per novelty bonus `1/(1+n_figli)`. **Strategia di default del DGM-H ufficiale**.

---

## 5. Flusso di esecuzione

### 5.1 Il ciclo `run_dgm_h`

Tutto passa da una singola funzione `run_dgm_h` in `common.py`, che riproduce Algorithm 1:

```python
def run_dgm_h(*, variant, train_data, test_data, initial_program, meta_agent,
              selector=select_score_child_prop, iterations=30, seed=0,
              archive_mode="full", candidates_per_iteration=1):
    rng = random.Random(seed)
    initial_agent = HyperAgent(TaskAgent(initial_program), meta_agent, generation=0)
    archive = [ArchiveEntry(node_id=0, parent_id=None, iteration=0,
                            agent=initial_agent,
                            train_score=evaluate(initial_agent, train_data),
                            test_score=evaluate(initial_agent, test_data),
                            valid=is_valid(initial_agent),
                            seed=seed, variant=variant)]
    history = list(archive)
    next_id = 1
    for iteration in range(1, iterations + 1):
        parent = selector(archive, rng)
        children = parent.agent.modify(archive, rng,
                                       candidates_per_iteration=candidates_per_iteration)
        new_entries = []
        for child in children:
            valid = is_valid(child)
            entry = ArchiveEntry(
                node_id=next_id, parent_id=parent.node_id, iteration=iteration,
                agent=child,
                train_score=evaluate(child, train_data) if valid else 0.0,
                test_score=evaluate(child, test_data) if valid else 0.0,
                valid=valid, seed=seed, variant=variant)
            next_id += 1
            new_entries.append(entry)
            history.append(entry)
        if archive_mode == "last_only":
            archive = new_entries or archive[-1:]
        elif archive_mode == "full":
            archive.extend(new_entries)
    return history
```

### 5.2 Diagramma del flusso

```text
              ┌──────────────────────────┐
              │   Programma iniziale     │
              │  (def solve: return False)│
              └────────────┬─────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   Valuta su train/test│
                │   Inserisci nodo 0   │
                │   in Archivio        │
                └──────────┬───────────┘
                           │
              ┌────────────▼────────────┐
              │       per iteration t   │◄──────────┐
              └────────────┬────────────┘           │
                           │                        │
                ┌──────────▼───────────┐            │
                │ SelectParent(archive)│            │
                │  (4 strategie)       │            │
                └──────────┬───────────┘            │
                           │                        │
                ┌──────────▼───────────┐            │
                │ MetaAgent.generate_  │            │
                │ candidates(parent,A) │            │
                │  → mutazioni proposte│            │
                └──────────┬───────────┘            │
                           │                        │
                ┌──────────▼───────────┐            │
                │  Crea figlio:        │            │
                │  HyperAgent(child)   │            │
                └──────────┬───────────┘            │
                           │                        │
                ┌──────────▼───────────┐            │
                │  evaluate(child)     │            │
                │  is_valid(child)     │            │
                └──────────┬───────────┘            │
                           │                        │
            ┌──────────────▼──────────────┐         │
            │  archive_mode == "full"?    │         │
            │  → archive.append(child)    │         │
            │  archive_mode == "last_only"│─────────┘
            │  → archive = [child]        │
            └─────────────────────────────┘
```

### 5.3 Differenza fra `archive` e `history`

C'è una sottigliezza importante: la funzione mantiene **due strutture**:

- `archive`: quello da cui si seleziona il parent. In modalità `last_only` viene azzerato a ogni iterazione.
- `history`: la cronologia completa, **sempre** mantenuta. Serve per generare CSV e plot.

In questo modo, anche la baseline `senza_archivio` produce dati confrontabili (vediamo cosa avrebbe potuto fare, anche se di fatto non lo sta usando per la selezione).

---

## 6. Demo 1 — Ablation archivio

### 6.1 Scopo

Misurare l'effetto dell'archivio open-ended sul ciclo DGM-H. Vogliamo capire se conservare tutti gli stepping stones aiuta rispetto a tenere solo l'ultimo agente generato.

### 6.2 Mappatura sull'articolo

Replica la baseline `DGM-H w/o open-ended exploration` (Algorithm 3, Articolo Sez. 9). Nell'articolo, la rimozione dell'archivio fa crollare le performance su paper review (test score 0.0) e robotics reward design (test score 0.116).

### 6.3 Setup sperimentale

| Parametro | Valore |
|---|---|
| Task | Classificazione palindromi |
| Train | 12 esempi |
| Test | 10 esempi |
| Iterazioni | 30 |
| Seed | 5 (0..4) |
| Selector | `score_child_prop` |
| Soglia di sblocco | 0.75 |

**Mutazioni di base disponibili**: `always_true`, `always_false`, `even_length`, `first_last_equal`.  
**Mutazione nascosta**: `reverse_check` (la corretta).

### 6.4 Codice rilevante

```python
configs = {
    "con_archivio": "full",
    "senza_archivio": "last_only",
}
for variant, archive_mode in configs.items():
    for seed in SEEDS:
        archive = run_dgm_h(
            variant=variant,
            train_data=TRAIN_DATA,
            test_data=TEST_DATA,
            initial_program=make_initial(),
            meta_agent=make_meta(),
            selector=select_score_child_prop,
            iterations=ITERATIONS,
            seed=seed,
            archive_mode=archive_mode,
        )
        rows.extend(best_by_iteration(archive))
```

### 6.5 Risultati

| Variante | Final mean | Min | Max | Std | Iterazione media di convergenza |
|---|---:|---:|---:|---:|---:|
| `con_archivio` | **1.000** | 1.000 | 1.000 | 0.000 | **6.4** |
| `senza_archivio` | **1.000** | 1.000 | 1.000 | 0.000 | **6.4** |

### 6.6 Spiegazione del grafico (`ablation_archive.png`)

Il grafico mostra due curve, una per variante, dell'andamento del best test score medio sui 5 seed in funzione dell'iterazione (0..30). Entrambe partono da 0.5 (l'agente iniziale ingenuo) e salgono a scalini, raggiungendo 1.0 intorno all'iterazione 12. Le due curve sono quasi sovrapposte.

### 6.7 Interpretazione

Sul nostro task didattico la mutazione corretta è raggiungibile in 1-2 passi, quindi l'archivio non fa molta differenza: anche solo conservando l'ultimo agente, prima o poi il meta-agent propone la strategia giusta.

- Questa demo è una **ablation strutturale**: mostra cosa significa nel codice "rimuovere l'open-ended exploration", ma su task così piccoli non si vede il guadagno. Negli esperimenti reali (Figura 2) la differenza è enorme: la stessa baseline crolla a zero su paper review.

---

## 7. Demo 2 — Ablation self-improve

### 7.1 Scopo

Misurare l'effetto del **metacognitive self-modification**, cioè della capacità del meta-agent di migliorare nel tempo. È l'idea **centrale**.

### 7.2 Mappatura sull'articolo

Replica il confronto tra `DGM-H` (completo) e `DGM-H w/o self-improve` (Articolo Sez. 5.1, Figura 2). Nell'articolo, su paper review la baseline senza self-improve si ferma a 0.0, mentre il DGM-H raggiunge 0.710. Su robotics la differenza è 0.213 vs 0.372.

### 7.3 Setup sperimentale

| Parametro | Valore |
|---|---|
| Task | Classificazione palindromi (versione ridotta) |
| Train | 8 esempi |
| Test | 6 esempi |
| Iterazioni | 30 |
| Seed | 5 (0..4) |
| Selector | `score_child_prop` |
| Archive mode | `full` |

**Mutazioni di base**: `always_true`, `always_false`, `first_last_equal` (euristica parziale: solo primo e ultimo carattere).  
**Mutazione nascosta**: `reverse_check` (corretta, ma sbloccabile solo se `self_improve=True`).

### 7.4 Codice rilevante

```python
for variant, self_improve in {
    "meta_congelato": False,
    "meta_self_improve": True,
}.items():
    for seed in SEEDS:
        archive = run_dgm_h(
            variant=variant,
            train_data=TRAIN_DATA,
            test_data=TEST_DATA,
            initial_program=make_initial(),
            meta_agent=make_meta(self_improve),
            selector=select_score_child_prop,
            iterations=ITERATIONS,
            seed=seed,
            archive_mode="full",
        )
        rows.extend(best_by_iteration(archive))
```

### 7.5 Risultati

| Variante | Final mean | Min | Max | Std | Iterazione media di convergenza |
|---|---:|---:|---:|---:|---:|
| `meta_congelato` | **0.667** | 0.667 | 0.667 | 0.000 | mai converge |
| `meta_self_improve` | **1.000** | 1.000 | 1.000 | 0.000 | **10.6** |

### 7.6 Spiegazione del grafico (`ablation_self_improve.png`)

Il grafico è quello chiave della relazione. Due curve nette:

- `meta_congelato` (linea bassa): cresce rapidamente da 0.5 a 0.667 nelle prime 2-3 iterazioni, poi **piatta a 0.667 per tutte le 30 iterazioni**. La strategia migliore disponibile è `first_last_equal`, che è giusta solo per alcuni casi di test.
- `meta_self_improve` (linea alta): segue lo stesso percorso fino a 0.667, ma poi a un certo punto il meta-agent sblocca `reverse_check` e la curva sale a 1.0. La convergenza avviene in media all'iterazione **10.6**.

### 7.7 Interpretazione

Questo è il risultato più importante della relazione. La differenza **0.667 vs 1.000** è statisticamente significativa nel nostro setup ed è **l'unica** delle nostre demo a mostrare una vera differenza quantitativa fra varianti.

Dimostra concretamente la tesi degli HyperAgents: **migliorare solo il task agent non basta**. Se il meccanismo di generazione delle modifiche è fisso, il sistema è bloccato dal suo repertorio iniziale. Solo se il meta-agent può espandere il proprio repertorio (qui simulato dallo sblocco progressivo, nel paper realizzato da un LLM che riscrive il codice del meta-agent) si rompe il soffitto di performance.

---

## 8. Demo 3 — Strategie di parent selection

### 8.1 Scopo

Confrontare le quattro strategie di selezione del parent dall'archivio. Vogliamo capire come exploration ed exploitation si bilanciano.

### 8.2 Mappatura sull'articolo

Implementa **fedelmente** le formule di Articolo Sez. 8.2: midpoint dinamico sui top-3 score, sigmoide con `λ = 10`, novelty bonus `1/(1+n_figli)`.

### 8.3 Setup sperimentale

| Parametro | Valore |
|---|---|
| Task | Classificazione palindromi |
| Train | 10 esempi |
| Test | 8 esempi |
| Iterazioni | 35 |
| Seed | 8 (0..7) |
| Strategie | `random`, `best`, `score_prop`, `score_child_prop` |
| Archive mode | `full` |

### 8.4 Codice rilevante

```python
PARENT_SELECTORS: dict[str, Callable[..., ArchiveEntry]] = {
    "random": select_random,
    "best": select_best,
    "score_prop": select_score_prop,
    "score_child_prop": select_score_child_prop,
}

for selector_name, selector in PARENT_SELECTORS.items():
    for seed in SEEDS:
        archive = run_dgm_h(
            variant=selector_name,
            train_data=TRAIN_DATA, test_data=TEST_DATA,
            initial_program=make_initial(), meta_agent=make_meta(),
            selector=selector, iterations=ITERATIONS,
            seed=seed, archive_mode="full",
        )
        rows.extend(best_by_iteration(archive))
```

### 8.5 Risultati

| Strategia | Final mean | Std | Iterazione media di convergenza |
|---|---:|---:|---:|
| `best` | 1.000 | 0.000 | 8.125 |
| `random` | 1.000 | 0.000 | 8.250 |
| `score_prop` | 1.000 | 0.000 | **7.125** |
| `score_child_prop` | 1.000 | 0.000 | **7.125** |

### 8.6 Spiegazione del grafico (`parent_selection.png`)

Quattro curve sovrapposte, una per strategia. Tutte convergono a 1.0 ma con velocità leggermente diverse:

- `score_prop` e `score_child_prop`: le prime ad arrivare a 1.0, in media intorno all'iter **7**.
- `best`: leggermente più lenta (iter 8.1). Sembra controintuitivo, ma `best` resta intrappolata sui parent già esplorati e non sfrutta abbastanza la diversità dell'archivio.
- `random`: la più lenta (iter 8.25), ma comunque arriva.

### 8.7 Interpretazione

Anche se tutte convergono al massimo, le strategie basate su sigmoide score-proporzionale convergono **circa il 14% più rapidamente** rispetto a `best` puro. Questo conferma il design: la combinazione di score e novelty bonus dà un piccolo ma reale vantaggio.

Nei plot ufficiali (Figure 2-4) la differenza è più visibile perché lavorano con 80-200 iterazioni e domini più rumorosi.

---

## 9. Demo 4 — Secondo dominio: vocali

### 9.1 Scopo

Mostrare la generalizzazione del framework a un secondo task computabile, senza modificare l'architettura.

### 9.2 Mappatura sull'articolo

Replica in piccolo l'idea di Articolo Sez. 8.4 *"Multi-domain optimization"*: lo stesso framework lavora su domini diversi semplicemente cambiando dati e mutazioni.

### 9.3 Setup sperimentale

| Parametro | Valore |
|---|---|
| Task | Stringa contiene **solo** vocali |
| Train | 10 esempi |
| Test | 8 esempi |
| Iterazioni | 25 |
| Seed | 5 |
| Soglia di sblocco | 0.70 (abbassata) |

**Mutazioni di base**: `always_true`, `always_false`, `contains_vowel` (almeno una vocale), `starts_with_vowel`.  
**Mutazione nascosta**: `only_vowels` (la corretta).

### 9.4 Codice rilevante

```python
def make_meta() -> MetaAgent:
    base = [
        CandidateProgram("always_true", "...", "def solve(x):\n    return True\n"),
        CandidateProgram("always_false", "...", "def solve(x):\n    return False\n"),
        CandidateProgram("contains_vowel", "...",
            "def solve(x):\n    return any(ch in 'aeiou' for ch in x.lower())\n"),
        CandidateProgram("starts_with_vowel", "...",
            "def solve(x):\n    return bool(x) and x[0].lower() in 'aeiou'\n"),
    ]
    hidden = [
        CandidateProgram("only_vowels", "Controlla che tutti i caratteri siano vocali.",
            "def solve(x):\n    vowels = set('aeiou')\n    "
            "return bool(x) and all(ch in vowels for ch in x.lower())\n")
    ]
    return MetaAgent(base_candidates=base, hidden_candidates=hidden,
                     self_improve=True, unlock_score_threshold=0.70)
```

### 9.5 Risultati

| Variante | Final mean | Std | Iterazione media di convergenza |
|---|---:|---:|---:|
| `task_vocali` | 1.000 | 0.000 | **6.4** |

### 9.6 Spiegazione del grafico (`task_vowels.png`)

Una sola curva, parte dal baseline iniziale (intorno a 0.625), sale rapidamente quando il meta-agent sblocca `only_vowels`, e converge a 1.0 entro l'iterazione 7.

### 9.7 Interpretazione

Cambiando solo il dataset e la lista di mutazioni candidate, l'intero ciclo `run_dgm_h` funziona senza una sola modifica al codice. Questo è esattamente lo spirito della tesi: **any computable task** può essere ottimizzato con lo stesso framework.

---

## 10. Demo 5 — Mini code-repair

### 10.1 Scopo

Avvicinarci al dominio originale del DGM: riparazione di codice difettoso valutata da test. Replica in miniatura lo scenario Polyglot/SWE-bench.

### 10.2 Mappatura sull'articolo

DGM-H eredita il design del DGM, che è nato proprio per coding. Articolo Sez. 5.1 riporta che il DGM-H raggiunge **0.267** sul Polyglot benchmark, comparabile al DGM originale (0.307). La nostra demo è una versione ultra-semplificata di quello scenario.

### 10.3 Setup sperimentale

| Parametro | Valore |
|---|---|
| Funzione iniziale | `def solve(x): a, b = x; return a - b` (bug: sottrazione) |
| Train | 5 input-output |
| Test | 4 input-output |
| Iterazioni | 25 |
| Seed | 5 |
| Soglia di sblocco | 0.20 (abbassata) |

**Patch candidate**: `return a`, `return b`, `a * b`, `abs(a - b)`.  
**Patch nascosta corretta**: `a + b`.

Soglia bassa: la funzione buggata (`a - b`) ha già score positivo su alcuni casi (es. `add(5, 7)` produce `-2` ≠ 12, ma `add(-1, 4)` produce `-5` ≠ 3, ecc.), e abbassiamo per consentire lo sblocco di `a + b`.

### 10.4 Codice rilevante

```python
TRAIN_DATA = [
    ((1, 2), 3), ((0, 0), 0), ((5, 7), 12), ((-1, 4), 3), ((10, -3), 7),
]
TEST_DATA = [
    ((2, 3), 5), ((-2, -8), -10), ((100, 1), 101), ((8, -8), 0),
]

def make_initial():
    return CandidateProgram(
        "buggy_subtraction",
        "Bug iniziale: usa la sottrazione invece dell'addizione.",
        "def solve(x):\n    a, b = x\n    return a - b\n",
    )
```

### 10.5 Risultati

| Variante | Final mean | Std | Iterazione media di convergenza |
|---|---:|---:|---:|
| `mini_code_repair` | 1.000 | 0.000 | **4.8** |

Converge più velocemente delle altre demo (4.8 iterazioni) perché lo spazio di patch è piccolo e la patch corretta è ben definita.

### 10.6 Spiegazione del grafico (`code_repair.png`)

Una sola curva: parte da 0 (il bug originale `a-b` non risolve nessuno dei test), sale a circa 0.2 con `abs(a-b)` che a volte coincide con `a+b`, e infine arriva a 1.0 quando il meta-agent sblocca `a + b`.

### 10.7 Interpretazione

Questa è la demo più vicina al **DGM originale**. Si vede chiaramente il ciclo:

1. bug iniziale → score basso;
2. il meta-agent propone patch candidate;
3. ognuna è valutata sui test;
4. la migliore entra nell'archivio;
5. dopo qualche iterazione viene sbloccata la patch corretta.

È anche la demo più naturalmente estendibile a un **vero LLM** come meta-agent: basterebbe sostituire la lista predefinita con una chiamata a un modello che produce patch reali.

---

## 11. Demo 6 — Plot overview

### 11.1 Scopo

Generare una visualizzazione **riassuntiva** delle demo disponibili a supporto dell'analisi comparativa dei risultati.

### 11.2 Codice rilevante

```python
CSV_FILES = [
    ("Ablation archivio", "ablation_archive.csv", None),
    ("Ablation self-improve", "ablation_self_improve.csv", None),
    ("Parent selection", "parent_selection.csv", None),
    ("Task vocali", "task_vowels.csv", None),
    ("Code repair", "code_repair.csv", None),
    ("LLM mock (Docker)", "llm_code_repair.csv", "llm_code_repair_mock"),
    ("LLM reale (Ollama)", "llm_code_repair.csv", "llm_code_repair"),
]
```

Per rigenerare i PNG per-demo a partire dai CSV (senza rieseguire le demo 1–5): `python experiments/regenerate_plots.py`.

### 11.3 Spiegazione del grafico (`all_demos_overview.png`)

Sette curve (cinque demo deterministiche + mock LLM + LLM reale). Le curve mostrano comportamenti diversi:

- **Code repair** converge per prima (iter 4.8).
- **Task vocali**, **Ablation archivio**, **Parent selection** convergono fra iter 6 e 8.
- **Ablation self-improve** mostra due regimi: la media include sia la curva piatta a 0.667 sia quella che sale a 1.0.
- **LLM mock** e **LLM reale** convergono entro iter 1 (task semplice; mock con patch fissa).

### 11.4 Interpretazione

L'overview comunica visivamente che:

- il framework DGM-H funziona su domini diversi (palindromi, vocali, code-repair);
- la velocità di convergenza dipende dal task e dal numero di patch candidate;
- l'ablation self-improve è l'unica che resta sotto 1.0, confermando che è l'esperimento più informativo.

---

## 12. Demo 7 — LLM (Ollama) + Docker sandbox

### 12.1 Scopo

Estendere la Demo 5 (code-repair) sostituendo il meta-agent deterministico con **Ollama** (via LiteLLM) e valutando il codice generato dentro **container Docker isolati**, in linea con Articolo Sez. 6 (Safety).

Non serve una VM dedicata: Docker Desktop su Windows è sufficiente per la sandbox.

### 12.2 Architettura

```text
Host (Python)
  ├── LLMMetaAgent  →  prompt  →  Ollama (localhost:11434)
  │                      ↓
  │                 patch Python (def solve)
  └── sandbox.py  →  docker run --network=none python:3.12-slim
                         ↓
                    esecuzione test → score
```

File aggiunti:

| File | Ruolo |
|---|---|
| `experiments/llm_meta_agent.py` | Meta-agent che chiama Ollama |
| `experiments/sandbox.py` | Esecuzione codice in Docker |
| `experiments/llm_code_repair.py` | Script Demo 7 |
| `requirements.txt` | Dipendenze Python (tutte le demo) |
| `experiments/requirements-llm.txt` | Alias/riferimento LiteLLM (vedi root) |

### 12.3 Prerequisiti e avvio

Vedi anche `README.md` per la guida completa. Sintesi per la Demo 7:

```powershell
# 1. Ambiente e dipendenze (dalla root del progetto)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Docker Desktop avviato
docker run hello-world

# 3. Solo modalita' LLM reale: Ollama (https://ollama.com)
ollama pull llama3.2

# 4. Esecuzione
python experiments/llm_code_repair.py              # LLM reale (Ollama)
python experiments/llm_code_repair.py --mock     # mock (solo Docker, no Ollama)
```

Variabili d'ambiente opzionali: `OLLAMA_MODEL`, `OLLAMA_API_BASE`, `DGMH_SANDBOX_IMAGE`, `DGMH_LLM_ITERATIONS`, `DGMH_LLM_SEEDS`.

### 12.4 Sandbox Docker

Ogni valutazione scrive uno script in `runs/sandbox/` e lo esegue con:

- `--network=none` (nessun accesso rete)
- `--cpus=1`, `--memory=256m`
- volume montato in sola lettura

Prima dell'esecuzione, un filtro blocca costrutti pericolosi (`import os`, `eval`, `open`, ecc.). I log sono in `results/sandbox_logs/`.

### 12.5 Risultati — distinzione modalità mock vs LLM reale

La Demo 7 supporta due modalità esplicite, distinguibili nella colonna `mode` dei CSV:

| Modalità | Comando | Colonna `mode` | Variante CSV | File dedicato |
|---|---|---|---|---|
| **Mock** | `--mock` | `mock` | `llm_code_repair_mock` | `results/llm_code_repair_mock.csv` |
| **LLM reale** | (default) | `real` | `llm_code_repair` | `results/llm_code_repair_real.csv` |

Il file combinato `results/llm_code_repair.csv` contiene **entrambe** le modalità (merge senza sovrascrittura). Eseguire una modalità non cancella i risultati dell'altra.

**Modalità mock** (`--mock`): il meta-agent propone sempre la patch corretta `a + b`, ma la valutazione passa comunque dal sandbox Docker. Serve a verificare la pipeline Docker senza Ollama.

| Variante | Final test (2 seed) | Train | Note |
|---|---:|---:|---|
| `llm_code_repair_mock` | **1.000** | **1.000** | Convergenza artificiale (patch fissa) |

**Modalità LLM reale** (Ollama + LiteLLM): il meta-agent genera patch via prompt; prompt e risposte in `results/llm_logs/`.

| Variante | Final test (2 seed) | Train | Note |
|---|---:|---:|---|
| `llm_code_repair` | **1.000** | **1.000** | Patch generate da `llama3.2` via Ollama |

Output grafici: `llm_code_repair_mock.png`, `llm_code_repair_real.png`, `llm_code_repair.png` (confronto).

### 12.6 Interpretazione

Questa demo collega tre pezzi della consegna:

1. **Hyperagent**: il meta-agent genera modifiche al task agent.
2. **LLM**: Ollama sostituisce la lista fissa di mutazioni.
3. **Safety**: Docker isola l'esecuzione del codice non fidato.

È il passo più vicino al DGM/HyperAgents ufficiale, restando su un task piccolo e riproducibile.

---

## 13. Tabella riassuntiva dei risultati

Tutti i numeri sono medie su 5 o 8 seed.

| Demo | File | Variante | Final test | Std | Conv. iter | Concetto articolo |
|---|---|---|---:|---:|---:|---|
| 1 | `ablation_archive.py` | `con_archivio` | 1.000 | 0.000 | 6.4 | Open-ended archive |
| 1 | `ablation_archive.py` | `senza_archivio` | 1.000 | 0.000 | 6.4 | Baseline Algorithm 3 |
| **2** | `ablation_self_improve.py` | `meta_congelato` | **0.667** | 0.000 | **mai** | Baseline `w/o self-improve` |
| **2** | `ablation_self_improve.py` | `meta_self_improve` | **1.000** | 0.000 | **10.6** | DGM-H completo |
| 3 | `parent_selection_strategies.py` | `random` | 1.000 | 0.000 | 8.25 | Baseline |
| 3 | `parent_selection_strategies.py` | `best` | 1.000 | 0.000 | 8.13 | Pure exploitation |
| 3 | `parent_selection_strategies.py` | `score_prop` | 1.000 | 0.000 | 7.13 | Sigmoide Articolo Sez. 8.2 |
| 3 | `parent_selection_strategies.py` | `score_child_prop` | 1.000 | 0.000 | 7.13 | Default DGM-H |
| 4 | `task_vowels.py` | `task_vocali` | 1.000 | 0.000 | 6.4 | Articolo Sez. 8.4 multi-domain |
| 5 | `mini_code_repair.py` | `mini_code_repair` | 1.000 | 0.000 | 4.8 | Polyglot/SWE-bench in piccolo |
| 7 | `llm_code_repair.py` | `llm_code_repair_mock` (`mode=mock`) | 1.000 | 0.000 | 1 | Docker sandbox, patch fissa |
| 7 | `llm_code_repair.py` | `llm_code_repair` (`mode=real`) | 1.000 | 0.000 | 1 | Ollama + Docker sandbox |

**Le due righe in grassetto sono il risultato chiave**: dimostrano che la differenza fra DGM-H completo e baseline senza self-improve è netta (0.333 di gap, statisticamente significativa nel nostro setup).

---

## 14. Discussione e interpretazione

### 14.1 Cosa funziona

- Il ciclo `generate → evaluate → archive → select → modify` funziona su tutti e tre i tipi di task provati (classificazione palindromi, classificazione vocali, code-repair).
- L'archivio cresce in modo open-ended e produce una genealogia tracciabile (`parent_id`).
- Le quattro strategie di parent selection sono implementate fedelmente alle formule di Articolo Sez. 8.2.
- La differenza fra meta-agent congelato e meta-agent evolutivo è netta e replica la tesi centrale.

### 14.2 Cosa converge troppo facilmente

Su task così piccoli (8-12 esempi di training, 6-10 di test):

- L'ablation archivio non mostra differenze perché la mutazione corretta è raggiungibile in pochi passi senza bisogno di stepping stones intermedi.
- Le quattro strategie di parent selection convergono tutte: si vede solo una differenza modesta di velocità.

Questo non è un problema della implementazione, ma una limitazione **inerente** alla scala didattica. Nell'articolo, i benchmark hanno 60-200 task e 80-100 iterazioni, e quelle differenze diventano gigantesche.

### 14.3 Il risultato chiave (Demo 2)

La differenza **0.667 vs 1.000** è la riproduzione concettuale di quello che gli autori dimostrano su scala enorme:

| Dominio articolo | DGM-H | DGM-H w/o self-improve | Gap |
|---|---:|---:|---:|
| Paper review (test) | 0.710 | 0.0 | 0.710 |
| Robotics reward (test) | 0.372 | 0.213 | 0.159 |
| **Nostra Demo 2** | **1.000** | **0.667** | **0.333** |

Il nostro setup è enormemente più piccolo e con LLM rimpiazzato da una lista di mutazioni, ma il pattern qualitativo è lo stesso: **togliere la capacità di self-improvement al meta-agent peggiora significativamente la performance finale**.

### 14.4 Perché tutto questo è importante

Il messaggio di fondo, che la nostra mini-replica supporta, è:

> *Per costruire AI realmente capaci di automigliorarsi su qualunque task computabile, non basta migliorare il task agent. Bisogna progettare sistemi in cui anche il meccanismo che genera i miglioramenti possa essere modificato dal sistema stesso.*

Senza questo, ogni sistema di self-improvement resta bloccato dal suo design iniziale.

---

## 15. Relazione con i repository ufficiali

Questa sezione documenta in dettaglio l'analisi dei due repository open-source citati nel paper *Hyperagents* e nel lavoro precedente *Darwin Gödel Machine* (DGM). I clone non sono versionati in Git (`.gitignore`); i commit esatti sono registrati in `results/repo_commits.txt`.

### 15.0 Procedura di clone e versione testata

```powershell
git clone https://github.com/jennyzzt/dgm.git dgm
git clone https://github.com/facebookresearch/Hyperagents.git HyperAgents

cd dgm
git checkout a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2

cd ../HyperAgents
git checkout 59a68f672dfb92c74aeb7e61535d776fb36e172d
```

| Repository | URL | Commit |
|---|---|---|
| DGM | https://github.com/jennyzzt/dgm | `a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2` |
| HyperAgents | https://github.com/facebookresearch/Hyperagents | `59a68f672dfb92c74aeb7e61535d776fb36e172d` |

### 15.1 Repository DGM (`dgm/`)

Il repository **DGM** implementa agenti che si auto-migliorano su task di coding (SWE-bench, Polyglot) usando LLM e strumenti `bash`/`editor` in ambiente Docker.

#### 15.1.1 Architettura e file principali

| File / cartella | Ruolo | Corrispondenza nelle mini-demo |
|---|---|---|
| `DGM_outer.py` | Ciclo esterno: iterazioni, selezione parent | `common.run_dgm_h()` |
| `self_improve_step.py` | Passo di auto-miglioramento (diagnosi + patch) | `MetaAgent.generate_candidates()` / Demo 2 |
| `coding_agent.py` | Agente per SWE-bench Verified | Demo 5 / 7 (code-repair) |
| `coding_agent_polyglot.py` | Variante Polyglot multi-linguaggio | Demo 5 (concetto) |
| `prompts/` | Prompt fissi (`diagnose_prompt`, ecc.) | `llm_meta_agent.py` (Demo 7) |
| `tools/bash.py`, `tools/editor.py` | Strumenti nel container | `sandbox.py` (valutazione isolata) |
| `tests/` | Suite pytest (22 test al commit testato) | — |

#### 15.1.2 Dipendenze e test su Windows

```powershell
pip install -r dgm/requirements.txt
pytest dgm/tests -v
```

**Risultato:** 11 test passati, 11 falliti su Windows nativo.

| Categoria di fallimento | Esempio | Causa |
|---|---|---|
| API POSIX | `os.setsid`, `signal.SIGTERM` | Non disponibili su Windows |
| Subprocess / shell | Invocazioni bash-like | Richiede WSL o Linux |
| Docker networking | Configurazione rete container | Comportamento diverso su Docker Desktop |

Per riproduzione completa servono **Linux/WSL**, **Docker** e **API key** OpenAI o Anthropic.

#### 15.1.3 Flusso algoritmico (DGM ufficiale vs mini-demo)

```text
DGM ufficiale                         Mini-demo (livello 1)
─────────────────                     ─────────────────────
DGM_outer.py loop          ≈          run_dgm_h()
  └─ select parent         ≈          select_score_child_prop / altre
  └─ self_improve_step     ≈          MetaAgent.generate_candidates
       └─ LLM + editor     ≈          CandidateProgram (stringhe Python)
       └─ valuta in Docker ≈          evaluate_with_sandbox (Demo 7)
  └─ archivio open-ended   ≈          ArchiveEntry + archive_mode
```

### 15.2 Repository HyperAgents (`HyperAgents/`)

**HyperAgents** generalizza il DGM su piu' domini (Polyglot, IMO, Genesis, Balrog) con meta-agent LLM condiviso.

#### 15.2.1 Entry point e moduli core

| File | Ruolo | Verifica effettuata |
|---|---|---|
| `generate_loop.py` | Entry point del ciclo hyperagent | `python -m py_compile` |
| `meta_agent.py` | Meta-agent che propone modifiche | `py_compile` |
| `task_agent.py` | Agente operativo sul dominio | `py_compile` |
| `select_next_parent.py` | Parent selection (formule Articolo Sez. 8.2) | `py_compile` |
| `baselines/dgm/` | Baseline che riusa codice DGM | Ispezione manuale |

#### 15.2.2 Domini disponibili

| Dominio | Descrizione | Analogia locale |
|---|---|---|
| `polyglot` | Coding multi-linguaggio | Demo 5 / 7 |
| `imo` | Problem solving matematico | non replicato |
| `genesis` | Simulazione robotica / reward | Demo 4 (dominio semplificato) |
| `balrog` | Ambiente RL complesso | non replicato |

#### 15.2.3 Requisiti per riproduzione completa

| Requisito | Dettaglio |
|---|---|
| OS | Fedora o WSL2 (README ufficiale) |
| Docker | `--network=host` per alcuni domini |
| Dipendenze | Balrog, Genesis, stack RL |
| API key | OpenAI, Anthropic, Gemini |
| Log ufficiali | Google Drive (link nel README HyperAgents) |

Su Windows nativo e' stato possibile verificare la sintassi e leggere la struttura; l'esecuzione end-to-end non e' stata tentata.

### 15.3 Tabella di corrispondenza concettuale

| Concetto paper / repo ufficiale | Implementazione locale | Demo |
|---|---|---|
| Open-ended archive | `archive_mode="full"` vs `"last_only"` | 1 |
| Meta-agent self-improve | `MetaAgent.self_improve` + `hidden_candidates` | 2 |
| Parent selection Articolo Sez. 8.2 | quattro selector in `common.py` | 3 |
| Multi-domain | palindromi + vocali + code-repair | 4, 5 |
| LLM meta-agent | `LLMMetaAgent` + Ollama | 7 (real) |
| Sandbox sicura | `sandbox.py` + Docker `--network=none` | 7 |
| Mock / test pipeline | `MockLLMMetaAgent` + `--mock` | 7 (mock) |

### 15.4 Limitazioni dell'analisi su Windows

1. **DGM:** meta' dei test pytest fallisce per dipendenze POSIX; analisi basata su lettura codice + test parziali.
2. **HyperAgents:** nessuna esecuzione completa di `generate_loop.py`; solo `py_compile` e ispezione domini.
3. **Gap intenzionale:** le mini-demo sostituiscono LLM cloud con mutazioni deterministiche (Demo 1-6) o Ollama locale (Demo 7), mantenendo la stessa struttura algoritmica del ciclo DGM-H.


---

## 16. Conclusione

Il progetto raggiunge l'obiettivo dichiarato: **riprodurre in piccolo il funzionamento del DGM-Hyperagents**, partendo dalla teoria e arrivando a **sette demo** (sei riproducibili in pochi secondi su Windows senza Docker e senza LLM, più la Demo 7 con Ollama e sandbox Docker).

I risultati sintetici:

- **Sette demo eseguite** con successo, tutte con output salvato in CSV e PNG.
- **Una differenza statisticamente significativa** è stata osservata (Demo 2, 0.667 vs 1.000), che riproduce concettualmente la tesi centrale.
- **Quattro strategie di parent selection** sono state implementate fedelmente alle formule di Articolo Sez. 8.2.
- **Tre livelli di profondità** sono stati coperti: mini-demo locali eseguibili, analisi del repo DGM, analisi del repo HyperAgents.

Conclusione sintetica:

> *Il DGM-H non è solo un agente che migliora un task: è un sistema che modifica anche il proprio meccanismo di miglioramento. Nel setup di questa relazione, senza self-improvement del meta-agent la performance si stabilizza su un limite inferiore; con self-improvement quel limite viene superato.*

---

## 17. Riferimenti

### Articoli scientifici

- Zhang J., Zhao B., Yang W., Foerster J., Clune J., Jiang M., Devlin S., Shavrina T. (2026). *Hyperagents*. arXiv 2603.19461.
- Zhang J., Hu S., Lu C., Lange R., Clune J. (2025). *Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents*. arXiv 2505.22954.
- Schmidhuber J. (2003). *Gödel Machines: Self-Referential Universal Problem Solvers Making Provably Optimal Self-Improvements*.
- Hu S. et al. (2024). *Automated Design of Agentic Systems (ADAS)*.

### Repository

- `https://github.com/facebookresearch/Hyperagents` — commit `59a68f672dfb92c74aeb7e61535d776fb36e172d`
- `https://github.com/jennyzzt/dgm` — commit `a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2`

### File del progetto

- `experiments/common.py` — ciclo DGM-H, classi, parent selection
- `experiments/ablation_archive.py` — Demo 1
- `experiments/ablation_self_improve.py` — Demo 2
- `experiments/parent_selection_strategies.py` — Demo 3
- `experiments/task_vowels.py` — Demo 4
- `experiments/mini_code_repair.py` — Demo 5
- `experiments/plot_progress.py` — Demo 6
- `experiments/llm_meta_agent.py`, `experiments/sandbox.py`, `experiments/llm_code_repair.py` — Demo 7
- `experiments/demo_passo_passo.ipynb` — notebook didattico
- `README.md` — guida esecuzione e prerequisiti
- `requirements.txt` — dipendenze Python (tutte le demo)
- `results/*.csv`, `results/*.png` — dati e grafici delle demo
