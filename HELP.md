# MPN — Help and reference

**MPN** is *Medical Publishing to Network*. The full name introduces the
software; `MPN` is used everywhere thereafter.

This document is how the pipeline works, what every setting does, and what it
produces.

MPN is a desktop **application** with a command-line pipeline behind
it. Everything described here can be done from either. The application is
validated on **Windows** and **Linux**.

To install it, see [INSTALL.md](INSTALL.md). To drive the pipeline from a shell
instead, or to work on the source, see
[COMMAND-LINE.md](COMMAND-LINE.md).


## Overview

MPN is a computational pipeline and desktop application that constructs, filters and analyses knowledge graphs of adverse outcome pathways and biological flows. By leveraging the NCBI Entrez API and the complete offline NLM PubMed Baseline, the pipeline extracts primary literature associated with specific Medical Subject Headings (**MeSH**), maps multi-generational citation topologies, and calculates semantic co-occurrence networks.

The system connects **Stressors** (e.g., chemicals) to **Adverse Outcomes** (e.g., diseases) through biological intermediates. It utilizes Global Likelihood Filter (GLF) and Simulated Annealing (SA) to optimize subgraph density, Louvain heuristics for community detection, and Mean Relevancy Scoring (MRS) to rank nodes and edges based on their impact within the global corpus of literature.

---

### Terms used throughout

| Term | Means |
| :--- | :--- |
| **GLF** — Global Likelihood Filter | One of the two edge filters whose agreement forms the consensus network. An ensemble method that scores an edge against a null model accounting for correlations between edges. From Dianati (2016); the name is his. |
| **MLF** — Marginal Likelihood Filter | The faster filter from the same paper, scoring each edge against the marginal distribution of edge weights. Used here for the per-edge p-values recorded on the full graph. |
| **SA** — Simulated Annealing | The second optimiser. It searches the same space as GLF from a different starting point and by a different rule, so agreement between them means more than either alone. |
| **ARS** — Article Relevance Score | Per **article**. How much network-term weight an article carries, normalised by how many network terms it has and by how common each is. Computed for every weighting, in `*_mean_relevancy.db` as `score_*` columns. |
| **MRS** — Mean Relevancy Score | Per **term**. The mean ARS of the articles a term appears in — how strongly the literature that mentions a term supports the network built around it. Written back onto each node as `MRS_*`. |
| **P0** | The article set the initial PubMed query returned, before any citation expansion. |
| **Gn** | Articles reached after *n* citation hops from P0. |
| **Consensus network** | The edges GLF and SA both kept, reduced to the largest connected component. |
| **Subgraph centrality** | A centrality recomputed on the consensus network rather than the whole corpus graph, so it measures importance within the curated concept space. |

### How articles and terms are scored

Two numbers do most of the work. Both come out of the same bipartite structure:
articles on one side, MeSH terms on the other, an edge wherever an article is
indexed with a term.

**ARS — Article Relevance Score.** Per article. The network's node weights are
projected down onto articles across that bipartite graph:

```
ARS(a) = (1/sqrt(k_a)) * SUM over terms t in a and in the network of
                          w(t) / sqrt(df(t))
```

* `w(t)` is the node weight of term `t` — whichever centrality or weighting is
  being scored.
* `df(t)` is how many articles in the corpus carry `t`, so a term cannot count
  for more simply by being common. This is the same intuition as IDF.
* `k_a` is how many network terms the article carries, so a long, broadly
  indexed article cannot outrank a focused one on breadth alone.

Both damping terms are square roots, which is the symmetric normalisation of a
bipartite projection: divide each side by the square root of its own degree.
One `score_*` column is written per weighting, so the alternatives can be
compared rather than assumed.

**MRS — Mean Relevancy Score.** Per term, and computed from ARS: the mean ARS
of the articles that carry that term. Where the node weight asks "how central is
this term in the graph", MRS asks "how strongly does the literature mentioning
it support the network built around it". Averaging over a term's articles is
what makes it frequency-neutral — a common term is diluted by its own many
low-scoring articles — which is why no further frequency correction is applied
on top. Written back onto each node as `MRS_*`.

**Which one is better** is not assumed. The benchmark scores all of them against
the project's ground truth and reports the comparison, so the answer comes from
the data rather than from this document. See
[Validation & Benchmarking](#validation--benchmarking).

**On GLF specifically.** The filter this pipeline runs is the Global Likelihood Filter of:

> Dianati, N. (2016). *Unwinding the hairball graph: Pruning algorithms for weighted complex networks.* Physical Review E, **93**, 012304. <https://doi.org/10.1103/PhysRevE.93.012304>


## Table of Contents

- [Data Acquisition & Prerequisites](#data-acquisition--prerequisites)
  - [1. The MeSH XML File (automatic)](#1-the-mesh-xml-file-automatic)
  - [2. Internet Connectivity & Disk Budget](#2-internet-connectivity--disk-budget)
- [The MPN Window](#the-mpn-window)
  - [Data setup](#data-setup)
  - [Settings](#settings)
  - [Before a run starts](#before-a-run-starts)
  - [Results](#results)
  - [Menus](#menus)
- [Controlling a Run](#controlling-a-run)
  - [Pause](#pause)
  - [Abort](#abort)
- [Settings Reference](#settings-reference)
  - [1. Control Flags & Directories](#1-control-flags--directories)
  - [2. Master Database Status (Step 0 ETL)](#2-master-database-status-step-0-etl)
  - [3. Stop Words — which MeSH terms the analysis may see](#3-stop-words--which-mesh-terms-the-analysis-may-see)
  - [4. NCBI Credentials](#4-ncbi-credentials)
  - [5. Search Parameters](#5-search-parameters)
  - [6. Analysis Parameters](#6-analysis-parameters)
  - [7. Network & Simulation Parameters](#7-network--simulation-parameters)
  - [8. Secondary Analysis Parameters](#8-secondary-analysis-parameters)
  - [9. Benchmark Parameters](#9-benchmark-parameters)
- [The Annotation Workflow (Strata)](#the-annotation-workflow-strata)
  - [How to annotate a network](#how-to-annotate-a-network)
  - [What "syncing to the master library" does](#what-syncing-to-the-master-library-does)
- [Output Artifacts](#output-artifacts)
  - [Data & Network Artifacts (`data/processed/`)](#data--network-artifacts-dataprocessed)
  - [Analytical Exports (`results/`)](#analytical-exports-results)
- [When Files Go Wrong](#when-files-go-wrong)
  - [Tools → Check and repair files](#tools--check-and-repair-files)
  - [The master annotation database](#the-master-annotation-database)
- [The Run Ledger and PRISMA-Style Flow Overview](#the-run-ledger-and-prisma-style-flow-overview)
  - [`*_run_ledger.csv` — the counts](#runledgercsv--the-counts)
  - [`*_prisma_flow_report.txt` and `figures/*_prisma_flow.*` — the overview](#prismaflowreporttxt-and-figuresprismaflow--the-overview)
- [Validation & Benchmarking](#validation--benchmarking)
  - [Ground Truth](#ground-truth)
  - [What It Reports](#what-it-reports)
  - [Outputs](#outputs)
  - [Node/Edge Convergent Validation](#nodeedge-convergent-validation)
- [User-Provided Files — Quick Reference](#user-provided-files--quick-reference)
- [Troubleshooting](#troubleshooting)
  - [Windows `MAX_PATH` / "No such file or directory" during install](#windows-maxpath--no-such-file-or-directory-during-install)
  - ["Activate.ps1 cannot be loaded ... running scripts is disabled"](#activateps1-cannot-be-loaded--running-scripts-is-disabled)
  - ["Access is denied" running `mpn-pipeline` / `mpn-check-env`](#access-is-denied-running-mpn-pipeline--mpn-check-env)
  - [`community` / `python-louvain` Namespace Collision](#community--python-louvain-namespace-collision)
  - [RAM Exhaustion on Large Networks](#ram-exhaustion-on-large-networks)
  - [SQLite Lock Errors on Network-Attached Storage](#sqlite-lock-errors-on-network-attached-storage)
  - [Convergence Warnings for Eigenvector Centrality](#convergence-warnings-for-eigenvector-centrality)
- [Repository Structure](#repository-structure)
- [Citation](#citation)
  - [Also cite the methods this rests on](#also-cite-the-methods-this-rests-on)
- [License](#license)

## Data Acquisition & Prerequisites

### 1. The MeSH XML File (automatic)

The pipeline reads the MeSH vocabulary from the NLM's **MeSH XML** descriptor file.

* **Automatic download (default):** The file does **not** need to be fetched by hand. When Step 1 builds the MeSH support files, it checks `data/raw/` for the current descriptor XML and, if it is missing or a newer annual release has appeared, downloads the latest `descYYYY.xml` straight from NLM into `data/raw/` (verifying it is the genuine ~300 MB file, not an error page). The year advances automatically — `desc2025.xml` today, `desc2026.xml` once NLM publishes it.
* **Manual placement (optional):** Download `descYYYY.xml` from the [NLM MeSH Data Distribution page](https://nlmpubs.nlm.nih.gov/projects/mesh/) and place it in `data/raw/`. An existing local copy is always reused.

### 2. Internet Connectivity & Disk Budget

Internet access is required only for the steps that talk to NCBI; everything else runs against the local databases:

| Pipeline step | Internet? | When |
|---|---|---|
| Step 0 — Master DB build (baseline FTP) | **Yes** | First run only; again only to refresh to a newer yearly baseline or apply daily updates |
| Step 1 — MeSH support-file build | Only if XML absent | Downloads `descYYYY.xml` from NLM when it is missing or superseded |
| Step 2 — Article collection (Entrez + citation links) | **Yes** | **Every** time a new query's citation database is built |
| Step 3.5 — Secondary metadata hydration | **Yes** | Whenever top articles are exported or `--step secondary` runs |
| Steps 3, 4, benchmark | No | Run against the local databases |

These baseline and daily-update archives are the official NLM/NCBI PubMed releases, distributed at the [NCBI PubMed Data Distribution page](https://pubmed.ncbi.nlm.nih.gov/download/).

**Disk budget.** Set aside **about 80 GB free** to build the master database the first time. The pipeline downloads the full set of NLM baseline `.xml.gz` archives (**about 50 GB**) and expands them into the **about 10 GB** SQLite master database, with working headroom during extraction. This one-time bulk download plus local SQLite lookups is dramatically faster and more reliable than issuing millions of live Entrez queries per run. Once the master database is built and verified, the **`pubmed_baseline/` archives can be deleted** to reclaim that space, provided `master_mesh_database.db` is kept and daily-update ingestion will not be run, since it re-reads those archives.

**Daily updates (optional).** Between annual baselines, NLM publishes daily update archives (`pubmed_updates/`). Applying them keeps the master corpus current with the newest PMIDs, but re-runs the multi-core ETL and requires the update archives to be present. A fresh yearly baseline supersedes accumulated daily updates, so for most analyses the annual baseline **alone** is sufficient — enable daily updates only when very recent publications are required.

---

## The MPN Window

### Data setup

Lists what is on disk **at the paths the pipeline actually uses** — the configured data folder, and the current project prefix. Each row shows Present/Missing, its size, and the actions available:

| Row | What it is |
| :--- | :--- |
| Master annotation database | Built from the archive. Required for every run. Hours to rebuild. |
| PubMed baseline archive | The yearly snapshot, about 50 GB. Only needed to build the database. |
| PubMed daily updates | Records published since the baseline snapshot. |
| MeSH descriptor file | Defines the stop-word vocabulary. Fetched automatically. |
| Retrieved PMIDs / Citation database / Relevance database | Per-project, named with the project prefix. |

**Also fetch the daily update files when building** is a checkbox on this screen, so its state is visible without starting a build.

#### Databases accumulate when the project prefix changes

Every search writes its own PMID, citation and relevance databases, named for
the project prefix that produced them. Changing the prefix starts a new set and
leaves the old one where it is — nothing removes them, and each set is
gigabytes.

The Database screen reports them as **Databases from other projects**, grouped
by prefix with a total, and its **Delete** button removes them all. Two things
that button does not touch: the databases of the current project, and the
master annotation database.

**What it costs.** Networks, figures, workbooks and reports already produced
are not affected. What is lost is the ability to repeat one of those earlier
runs *exactly* without retrieving its corpus from PubMed again, which is the
slow part of a run. Keep a project's databases if that analysis may need to be
reproduced end to end; delete them if the prefixes were only used for trials.

The two rows beneath, **Raw data folder** and **Working files folder**, give the
totals for each tree, so it is clear where the space has actually gone.

Every Build, Rebuild, Download and Delete here requires typing **`REBUILD` or `DELETE`** before it proceeds. These actions either destroy something that took hours to produce or start something that will take hours to finish, and a yes/no box is one mis-aimed click. Deleting a database also removes its `-wal`, `-shm` and health sidecars — a stale write-ahead log left beside a rebuilt database is worse than useless, because SQLite will try to replay it.

### Settings

Ten tabs: **Search**, **Folders**, **Stop words**, **Credentials**, **Analysis**, **Network**, **Consensus**, **Secondary**, **Benchmark** and **Figures**.

Click any control and the description pane at the foot of the window shows what it does, its default, and anything worth knowing before changing it. The Search, Secondary and Benchmark tabs each carry a standing note above that pane covering the tab as a whole.

The **Run** button beside the step list runs whichever step is selected. On the Secondary, Benchmark and Figures tabs it reads **Run secondary analysis**, **Run benchmark** and **Run figures**, and selecting one of those tabs sets the step list to match.

### Before a run starts

Pressing **Run** checks whether this prefix has already produced output for the steps about to execute. If it has, a dialog lists exactly what would be replaced, with sizes, and offers to change the prefix instead. **If the prefix has not been used for those steps, nothing is asked** — a fresh project never meets a dialog it has no reason to read.

### Results

Opens on the **run overview**: the PRISMA-style account of the whole search, in a scrollable, selectable box — records retrieved per citation generation, what the MeSH screen excluded and why, what each optimiser kept, what the consensus and the largest connected component discarded, and what was finally included. Buttons open the full report and the flow diagram; the file listing sits underneath.

### Menus

- **Run** — any single step.
- **Database** — the Data setup screen.
- **Results** — the run overview.
- **Tools** — Annotate strata levels, Show the annotation guide (both greyed until a run has produced something to annotate), Check and repair files, Uninstall.
- **Help** — this manual, the installation notes, the read-me, the reference-figure provenance, and the annotation instructions.

---

## Controlling a Run

### Pause

**Pause** asks the run to stop at its next safe point — between pipeline stages, and between batches inside the long retrieval loops. It is not instant, and the window says so: on a long step it can take a few minutes, and the status line reads *Pausing* until the run actually reports back, at which point it changes to *Paused at a safe point*. **Resume** lets it continue from exactly where it stopped.

Pausing is cooperative rather than a process suspend, which on a managed
machine can silently fail and which would in any case freeze the run in the
middle of a multi-gigabyte database transaction.

Time spent paused is excluded from the elapsed clock, so reported durations remain honest.

### Abort

**Abort run** stops the step for good; its work is lost. The confirmation says how long the run has been going, because that is the fact that changes the decision. Completed steps are kept — a later run resumes from the last one that finished rather than starting over.

If the run reaches a checkpoint before the process is killed, it exits tidily and reports *Stopped at a safe point*, meaning nothing was left half-written.

From a terminal, the same controls are files: create `pause.flag` in the directory named by `MESH_CONTROL_DIR` to pause, delete it to resume, create `abort.flag` to stop.

---

## Settings Reference

Every setting the application shows, tab by tab, with what it does and what changing it costs. The same values are the keys in `mesh_config.json`, so this section serves the command line too.

### 1. Control Flags & Directories

* **Use Bundled Reference Data (demonstration only):** Analyses the finished network that ships with the program instead of building one from a new search. See [Using the bundled reference data](#using-the-bundled-reference-data) below for what it does and does not change.
* **Pause for strata annotation:** Off by default, so the pipeline runs uninterrupted from start to finish and no term is placed in a stratum. When on, the pipeline pauses after Step 3 so the network can be annotated by hand before the strata figures are drawn. See [The Annotation Workflow (Strata)](#the-annotation-workflow-strata).
* **Custom Prefix:** The naming convention prepended to all output files (e.g., `DAC_Mesh`).

#### Using the bundled reference data

> **Cite the ground truth when using it.** The curated PMID set behind the bundled corpus is a resolution of the bibliography of:
>
> OECD (2014), *The Adverse Outcome Pathway for Skin Sensitisation Initiated by Covalent Binding to Proteins*, OECD Series on Testing and Assessment No. 168, OECD Publishing, Paris. <https://doi.org/10.1787/9789264221444-en>
>
> It is AOP 40 ([AOP-Wiki.org](https://aopwiki.org/aops/40)). The set is a resolution of that bibliography, not an independent selection, so the document is what a methods section should cite.


**This is for demonstration, not for research.** A first real run means a long PubMed download and a full rebuild before a single figure appears. Ticking this box instead analyses a network that already exists — the allergic contact dermatitis network published with this software, already built and scored — so the figures, the workflow report and the benchmark come out in minutes. Use it to judge whether the outputs meet the project's needs, and to learn where everything lands on disk, before committing to a new retrieval.

What it **cannot** do is change the corpus. The articles behind that network are fixed, the retrieval that produced them is not repeated and cannot be varied, and any finding in it is already published. For new findings, untick the box and run a new search.

| | |
| :--- | :--- |
| **Set automatically, and greyed out** | Search term, both date windows, citation depth, random seed, benchmark primary node — anything else would label the figures with a query that did not make them. |
| **Still editable** | Figure resolution and formats, which figures are drawn, folders, credentials and the project prefix. |
| **Does not run** | Retrieval (there is nothing to fetch) and network construction (it ships built). Secondary analysis and the benchmark both run: they generate the relevance and citation data they need. |
| **Saved settings** | Untouched. Unticking the box restores the previous search term and dates. |
| **File naming** | Outputs are prefixed `Reference_` so they cannot be confused with a project's own outputs. |

The reference networks are **copied into the networks folder** the first time the box is ticked, and everything downstream reads them from there. They can be opened, edited or deleted like any other result. Copies already in that folder are left alone, so edits survive later runs; deleting one restores the pristine original from the program folder.

### 2. Master Database Status (Step 0 ETL)

The wizard probes the local master SQLite database for corruption, completion status and age, including whether a newer yearly baseline is available.

* **Compile PubMed Baseline / Daily Updates:** Initiates a multi-core MapReduce extraction of the NLM XMLs into the local cache.

### 3. Stop Words — which MeSH terms the analysis may see

MeSH is organised into sixteen top-level trees. By default the pipeline keeps four of them and treats every term in the other twelve as a **stop word** — a term that can never become a node. Geographicals, publication types, occupations and named groups are noise in a mechanistic question, and dropping them is most of what makes the resulting network readable.

They are not noise in every question. Research geography needs Geographicals; a workforce study needs Disciplines and Occupations. So the trees are selectable.

**A ticked box excludes that tree.** The four left unticked by default are the ones a biological strata analysis is built from:

| Kept by default | Excluded by default |
| :--- | :--- |
| `A` Anatomy | `B` Organisms, `E` Techniques and Equipment, `F` Psychiatry and Psychology, |
| `C` Diseases | `H` Disciplines and Occupations, `I` Anthropology and Social Phenomena, |
| `D` Chemicals and Drugs | `J` Technology and Agriculture, `K` Humanities, `L` Information Science, |
| `G` Phenomena and Processes | `M` Named Groups, `N` Health Care, `V` Publication Characteristics, `Z` Geographicals |

This is not a display filter. A term excluded here is absent from the network, the scores and the benchmark alike, so runs that are to be compared must use the same trees.

* **Male and Female — check tags.** The seventeenth box in the same list. `Male` and `Female` are *check tags*: they belong to no tree, so no tree box can reach them. They are indexed on a large share of clinical articles, which makes them two of the highest-degree nodes in any network that keeps them — connected to nearly everything, and therefore distinguishing nothing. Ticked by default; untick it when sex is part of the question.
* **Also exclude these terms.** Individual headings to drop on top of the trees, semicolon-delimited: `Humans; Adult; Middle Aged`. Semicolons, not commas — `Dermatitis, Allergic Contact` split on its comma would exclude two headings that do not exist. Spelling must match the MeSH heading exactly; a term matching nothing is ignored, so check the run log's count if in doubt.
* **Rebuild the stop-word list.** A button, on this tab and on the Database page beside the MeSH descriptor file. It re-reads the descriptor file and builds the term list again, which takes a few minutes. It is not needed to change the trees or the terms above: which tree each term belongs to is recorded when the list is first built, so a different selection applies to the next run straight from that record. It is needed when the MeSH release year changes, or when the run log reports that the term list predates that record.

**A change here alters a network only when the network is built again.** The terms that survived are part of the saved network, so re-running the figures alone redraws what is already there. Run the network step, or a full run, for a new vocabulary to take effect.

Every run prints the vocabulary it used — trees kept, trees excluded, how the sexes were treated, and anything entered by hand. A network is only interpretable next to the vocabulary it was built from, and that is not recoverable from the network afterwards.

### 4. NCBI Credentials

* **Entrez Email & API Key:** Registration with NCBI allows for 10 API requests per second. Without a key, requests are hard-limited to 3 per second, roughly tripling Step 2 processing time. Sign in or create a free account at the [NCBI/NLM account portal](https://account.ncbi.nlm.nih.gov/) to obtain a key (found under *Account Settings → API Key Management*).

### 5. Search Parameters

* **MeSH Search Term:** The PubMed query used to retrieve the base (P0) cohort. This string is sent **verbatim** to NCBI as the P0 `esearch` query, so any valid PubMed syntax is accepted — MeSH tags (`[Mesh]`, `[Majr]`), field tags (`[tiab]`, `[au]`), quoted phrases, and the boolean operators `AND` / `OR` / `NOT` with parentheses for grouping. Examples:
  * Single MeSH heading — `Dermatitis, Allergic Contact [Mesh]`
  * MeSH plus a free-text phrase — `"Dermatitis, Allergic Contact"[Mesh] OR "skin sensitization"[tiab]`
  * Boolean combination — `(Dermatitis, Allergic Contact[Mesh]) AND (Haptens[Mesh])`

  Any query that works in PubMed works here. The field is passed to Entrez
  unchanged, so the syntax is PubMed's — see the
  [PubMed User Guide](https://pubmed.ncbi.nlm.nih.gov/help/) for how to build
  one, and the [MeSH Browser](https://meshb.nlm.nih.gov/) to confirm a heading
  exists. Two things are specific to this pipeline:
  * A MeSH heading must be spelled exactly as MeSH spells it. A misspelling does
    not fail — it degrades silently to a free-text search.
  * The benchmark's `primary_node` is taken from this term. For a
    compound or free-text query rather than a single MeSH heading, set
    `benchmark.primary_node` explicitly so the naive-query baseline resolves to
    a real node.
* **Start / End Date:** Constrains the temporal boundaries of the initial P0 PubMed search.
* **Citation Generations:** Controls the depth of the citation scrape. The value counts *levels including P0*, matching the wizard label (`P0=1, P0+G1=2, ...`).
  * `1`: Only the base parental generation (P0) articles.
  * `2`: P0 articles + all articles they cite + all articles that cite them (G1).
  * `3`: The above + a further citation hop (G2), and so on.
  * *Warning:* Values $\ge 2$ result in exponential data growth.
* **Update MeSH Support Files:** If `True`, forces re-extraction of the MeSH term list and stop-word set from the XML file even if cached outputs already exist. Changing which MeSH trees are excluded does *not* need this — see [Stop Words](#3-stop-words--which-mesh-terms-the-analysis-may-see).



### 6. Analysis Parameters

* **Calculate Full Centrality (Boolean):** Controls **how betweenness is computed, not whether centrality is computed at all**. If `True`, betweenness is calculated **exactly** over every node pair. If `False` (Default), it is **estimated** from a sample of `betweenness_k_samples` source nodes, which is dramatically faster and bounds memory on large graphs.
  * Eigenvector and PageRank centrality are computed **either way** and are unaffected by this flag, so Article Relevance Scores (ARS) and Mean Relevancy Scores (MRS) are produced normally in both modes. The only difference is that WHOLE-GRAPH betweenness — and therefore the betweenness-weighted ARS/MRS — is a sampled estimate rather than an exact value. Report this in the methods when it is left `False`.
* **Betweenness K-Samples:** Heuristic sampling limit for Centrality calculation. Lower values increase speed but reduce precision.
* **Context Start / End Date:** Temporal constraints applied exclusively to Step 3 Mean Relevancy Scoring, allowing the simulation of historical network states.
* **Random Seed:** Integer seed passed to NetworkX and scikit-learn for reproducible t-SNE projections and community detection. Default: `42`.
* **Eigenvector Max Iterations / Tolerance:** Power-iteration convergence controls for Eigenvector centrality. Increase `eigenvector_max_iter` (default `1000`) if convergence warnings appear on very large or sparse graphs.

### 7. Network & Simulation Parameters

* **Lambda Value:** The distance-decay factor for generational node weighting: a node's generation weight is $W = e^{-\lambda d}$, where $d$ is the citation-generation distance from the P0 seed set ($d = 0$ for P0, $1$ for G1, …). Larger $\lambda$ penalizes distant generations more steeply.
* **Node Weight Factors:** A four-component dictionary combined into a single per-node `adjusted_node_weight` attribute recorded on the final network. It is a **user-tunable node-importance metric, not a driver of the GLF/SA filtering** — consensus filtering is driven by edge co-occurrence strength, independent of these factors. The attribute is reported on the final graph (and offered as one of the candidate weightings in the validation step), so it is available as a base metric for downstream analysis. The four keys and their defaults are:

  | Key | Default | Role |
  |-----|---------|------|
  | `centrality` | `0.45` | Combined betweenness + eigenvector centrality contribution |
  | `article_rank` | `0.15` | PageRank-style article influence |
  | `rank_median_cit` | `0.20` | Median incoming citations across linked articles |
  | `rank_total_cit` | `0.20` | Total incoming citation volume |

  The four values must sum to `1.0`.

* **Target Edges (`target_num_edges`):** The target subgraph size handed to the GLF and SA optimizers. Each selects a subgraph of about this many edges; their intersection (the consensus, reduced to its LCC) is typically somewhat smaller. *(Distinct from the `target_edges` in Secondary Analysis.)*
* **GLF / SA Iterations:** Monte Carlo search and thermal cooling steps for the optimization heuristics.
* **SA Temperature Start:** The initial thermal energy of the Simulated Annealing system (default `5000.0`). Higher values allow larger disruptive jumps early in the search.
* **SA Cooling Rate:** The multiplicative decay applied to temperature each iteration (default `0.999995`). Values closer to `1.0` cool more slowly and explore more widely at the cost of run time.

### 8. Secondary Analysis Parameters

Executes highly targeted queries against the finalized network to extract specific publications for manual review.

> **Target nodes and edges do not run as part of a full pipeline run.** Each one hydrates hundreds of records from NCBI, which would add a long tail to every run, so they run only on request: choose **secondary — targeted queries & exports** from the step list and press Run. Everything they need is on disk once a full run has finished, so this can be done days later as long as the project prefix is the same. The Secondary tab in the application carries the same note. (Export Top Articles is not affected — that one *does* run in a full pipeline.)

**Where to get the names to type.** A target must be a MeSH heading that is in the network, spelled exactly as the network spells it — `Dermatitis, Allergic Contact`, not `allergic contact dermatitis`. Two places give the real list:

* The **network JSON** in the networks folder is the easiest way to see the candidates. Open it in **Cytoscape** (*File → Import → Network from File*) to draw the whole graph; click any node or edge and its exact id appears in the table below, ready to copy. Gephi and the `networkx` library read these files too. The **Open network folder** button on the Results screen opens that folder.
* The **network Excel export** in the results folder (written by *Export network to Excel* on the same tab) has one row per node and per edge, so it can be sorted by centrality and the names copied out.

**How an article is matched.** `relevance.py` records, for every article, which of the network's nodes appear among the MeSH headings it was indexed with (base headings — `Skin/drug effects` is stored as `Skin`). A target node returns the articles carrying that heading; a target edge returns the articles carrying **both**. Matching is on the **whole heading**, so `Skin` returns articles indexed under Skin and never those under `Skin Diseases`, `Skin Absorption` or `Skin Tests`. A name that is not in the network finds nothing, so each entry is checked before the query runs and the nearest matches are offered.

* **Export Top Articles:** If `True` (default), always exports the highest-scoring network-wide articles at the end of Step 3 without requiring `--step secondary`.
* **Export Limit:** Maximum number of articles returned per query (default `500`).
* **Exclude Review Articles:** Filters out broad review articles to isolate primary literature.
* **Target Nodes:** The articles behind specific nodes. **Must be semicolon-separated** (e.g., `Skin; T-Lymphocytes`).
* **Target Edges (`target_edges`):** The articles behind a specific relationship — those indexed under both headings. Separate the two node names with a **space-padded hyphen** (` - `), and separate multiple edge queries with semicolons: `NodeA - NodeB; NodeC - NodeD`. *(Distinct from the numeric `target_num_edges`)*
* **Sort Metric (`sort_metric`):** Selects the ranking engine — `Linear` (compensatory weighted average) or `F1` (penalizing harmonic mean). Default `F1`.

  **1. Linear (Weighted Additive Model)**

  * **Mechanism:** Calculates the arithmetic weighted average of the normalized Article Relevance Score (ARS) and the normalized citation rate.
  * **Behavior:** Compensatory. A high score in one metric can offset a low score in the other, governed by the user-defined `linear_weight_ars`.
  * **Formula:** $(ARS \times w) + (Cit \times (1 - w))$

  **2. F1 (Harmonic Mean)**

  * **Mechanism:** Calculates the strict harmonic mean of the normalized ARS and the normalized citation rate.
  * **Behavior:** Penalizing. The final output skews heavily toward the lower of the two input values. An article must possess both high topological relevance and high community impact to achieve a high score.
  * **Formula:** $2 \times \frac{ARS \times Cit}{ARS + Cit}$
* **ARS Weight (`linear_weight_ars`):** Weight given to the normalized ARS in the `Linear` metric (0–1.0); the remaining `1 − w` weights the normalized **citation rate** (citations per year, which corrects the age bias that otherwise favors older papers purely for having accumulated citations longer). Default `0.5`.
* **Compare Multiple Networks (`compare_networks`):** Off by default. When enabled, secondary analysis runs a **node-overlap comparison** across the saved networks listed in **Networks to Compare** (`comparison_networks`) — a comma-separated, quote-wrapped list such as `"Ex_Graph_1.json","Ex_Graph_2.graphml"`. Bare names are resolved against the processed data folder (or `data/reference_processed/` when `Use Reference Data` is on); explicit paths and non-JSON formats (`.graphml`, `.gml`, `.gexf`, …) are also accepted. Missing files trigger a warning naming where the pipeline looked. It writes a membership matrix, a pairwise intersection/Jaccard table, and an overlap figure to `results/`.

### 9. Benchmark Parameters

Controls the optional `--step benchmark` evaluation (see the **Validation & Benchmarking** section below). Configured under the `benchmark` block of `mesh_config.json`.

* **`ground_truth_csv`:** Ground-truth PMID set. Leave **empty** (default) to auto-detect a recognized filename in `data/raw/`; set it to pin a specific filename or path. When `Use Reference Data` is on, the bundled OECD set is used automatically. See **Ground Truth** below for the required structure and the template.
* **`negative_control_csv`:** Optional *unrelated* ground-truth set used as a specificity check (it should score near random). Same location, resolution, and structure as `ground_truth_csv` (drop it in `data/raw/` or give a path). Empty (default) disables the control.
* **`primary_node`:** The base disease/seed node used to separate "naive" articles (those carrying the primary node) from topology-exclusive hits. Defaults to the search term's MeSH node.
* **`n_boot` / `n_perm`:** Bootstrap resamples and permutation iterations behind the confidence intervals and the random-ranking null. Default `25` each. Each bootstrap resample re-ranks the full article pool, so runtime scales linearly with both this value and the size of that pool. Measured on a ~9-million-article pool:

  | `n_boot` / `n_perm` | Approx. runtime |
  | --- | --- |
  | `25` *(default)* | ~15 min |
  | `50` | ~30 min |
  | `100` | ~1 hour |
  | `200` | ~2 hours |

  Increasing the count tightens the bootstrap confidence intervals and stabilizes the permutation p-value, but runtime grows proportionally; decreasing it runs faster at the cost of noisier, less reliable estimates. The default (`25`) is a practical balance. Interval precision is ultimately bounded by the number of ground-truth positives rather than by `n_boot`, so values well beyond `200` give diminishing returns.
* **`run_ground_truth_analysis` (Boolean):** Master switch for the whole step. **If unset it follows `Use Reference Data`** — on when running against the bundled reference corpus (which the bundled ground truth describes), off when running on a project's own data (where that ground truth would not apply). Set it explicitly to override. The interactive wizard prompts for it first in this section.
  The six subgraph centralities are computed whenever the network is built, so every weighting is available whether or not this flag is set. Whole-corpus centrality measures importance across the entire literature, where generic high-degree MeSH terms dominate; subgraph centrality measures it within the curated concept space. Having both makes centrality **scope** and centrality **type** independent choices rather than confounded ones. Subgraph betweenness is exact on an ordinary network and falls back to sampled sources on a very large one, which the run log states when it happens. The `n_seeds` baseline is a uniform weight of 1 per node, and therefore the one scope-invariant control.
* **`run_network_validation` (Boolean):** If `True` (default), also runs the node/edge convergent validation described under **Validation & Benchmarking**. Set `False` to run only the article ranking benchmark.
* **`run_projection_comparison` (Boolean):** If `True` (default), also runs the article-scoring **projection comparison** — with the node seed fixed, it scores the alternative ways of turning node weights into an article score (normalised ARS, unnormalised sum, MRS-weighted, bipartite-reinforced, BM25, uniform, random, naive query) by BEDROC across three frames with positives-only bootstrap CIs, writing `{prefix}_projection_comparison.csv` and a figure to `results/validation/`. Set `False` to skip it.
* **`network_validation_weight_key`:** Node attribute used as the "network weight" when correlating a node's ground-truth prominence against its importance. Default `MRS_pagerank_centrality`; set to `MRS_betweenness_centrality` to compare against the betweenness weighting instead. The wizard also offers any raw or MRS centrality (betweenness / pagerank / eigenvector, whole-graph or subgraph).
* **`min_articles_per_node`:** Minimum number of ground-truth articles a term must appear in to become a node of the ground-truth co-occurrence network (default `2`, which suppresses singleton noise).
* **`background_pool_size`:** Number of randomly sampled articles used to estimate corpus base rates and to build the permutation nulls (default `50000`). Larger is more precise but slower.

---

## The Annotation Workflow (Strata)

The pipeline can find the statistical relationships between MeSH terms. It cannot decide what those terms *mean* to the research question — whether `Apoptosis` is a cellular event, a mechanism of interest, or beside the point. That judgement belongs to the researcher, and supplying it is what makes the strata figures worth drawing.

A **stratum** is one group in whatever scheme the project uses. The program has no opinion about the scheme. It ships with the seven levels of an adverse outcome pathway because that is what it was built for, and they serve as a worked example below, but organ systems, exposure routes, study designs, evidence tiers or anything else are equally valid. Set the names and their order under **Strata order** on the Search tab.

Annotation files are **semicolon-delimited**. MeSH headings contain commas as a matter of course — `Dermatitis, Allergic Contact` is one heading — so a comma-delimited CSV corrupts them.

### How to annotate a network

1. **Enable pausing.** Set `Pause for strata annotation` to `True` on the Search tab.
2. **Run the pipeline.** Steps 0 through 3 run normally and the scheme-independent figures (distributions, convergence trajectories) are drawn. It then pauses: the node set is final, but nothing that depends on the strata has been drawn yet.
3. **Open the run template.** In `results/`, open `[PREFIX]_run_annotations.csv`. Instructions are written beside it as `HOW TO ANNOTATE - read me.html`, which opens in a web browser.
4. **Assign the strata.** The file lists every surviving node, pre-filled from the master library where it knows the term. Replace each `Unassigned` with a stratum name. *(Unsure about a term? Its scope note and hierarchy in the [NLM MeSH Browser](https://meshb.nlm.nih.gov/) are the best guide.)*

   Any name entered is valid. A name not listed in **Strata order** is still plotted — it is placed at the end of the order and reported in the run log, never dropped. Spelling and capitalisation are taken literally, so `Molecular` and `molecular` are two strata, which is usually a typo.

   Two values mean "no stratum", and they are not the same thing:

   | Value | What it means |
   | :--- | :--- |
   | `Unassigned` | Not yet reviewed. Every row starts here. |
   | `Uncategorized` | Reviewed, and belongs to none of the groups. |

   The difference serves the annotator, not the program: it separates terms already decided from terms not yet reached, which makes it practical to work through a long file over several sittings. The merge prompt counts the two separately.

   **The figures treat the two as one.** Both stay in the network and in every topological figure, and both are left out of the figures that show the strata — a stratum is a group to draw, and neither of these is one. So an unfinished file draws the same picture as a finished one where those terms did not belong; check the counts before reading much into a sparse figure.

5. **Save the file**, keeping it semicolon-delimited.
6. **Resume.** Run the figures step. The pipeline asks whether to merge the annotations into the master library, then draws the remaining figures.

#### The AOP seven, as an example

These are the defaults, and what a toxicology project would use:

| Stratum | What belongs in it | Example |
| :--- | :--- | :--- |
| `Stressor` | External stimuli that initiate a biological reaction | `UV Rays` |
| `Molecular` | Gene, protein or receptor level events | `Receptors, Antigen` |
| `Cellular` | Cellular level events | `Chemotaxis`, `Apoptosis` |
| `Tissue` | Events localised to a subsection of tissue | `Necrosis`, `Skin Absorption` |
| `Organ` | Organ level names or events | `Liver`, `Skin` |
| `Adverse Outcome` | High-level disease outcomes | `Drug Hypersensitivity` |
| `Uncategorized` | Terms that sit in none of the above | — |

Their **order** is what makes Figure 5 readable: an alluvial flow drawn left to right from stressor to adverse outcome traces a pathway. Order cannot be inferred from names, which is why it is a setting rather than something the program guesses.

### What "syncing to the master library" does

When the run resumes, the pipeline offers to write the run's annotations back to the **master library** (`data/raw/aop_annotations_master.csv`). Saying yes merges every `term → stratum` assignment from this run into it:

* The assignments become **persistent**. Every future run pre-fills these terms automatically, so no MeSH heading is annotated twice, and the curated strata can be re-exported from the master file at any time.
* The library ships **partially pre-seeded**: terms relevant to the bundled Dermatitis, Allergic Contact (DAC / AOP 40) query are already annotated from prior curation. Most MeSH terms are not, and appear as `Unassigned` in the template. Anything left `Unassigned` — or a run completed unattended — is treated as `Uncategorized`.

> **When projects use different schemes, check the file by hand.** The library is shared by every project and the merge is permanent. A term labelled `Molecular` in an AOP project arrives pre-filled as `Molecular` in a project organised by organ system, where it is wrong. Read the template through after Step 3 rather than trusting what is already in the column, and answer **No** to the merge when the schemes differ.

---

## Output Artifacts

Upon successful completion of the pipeline, the following critical files are generated:

### Data & Network Artifacts (`data/processed/`)

* `master_mesh_database.db`: A persistent offline cache of all PubMed IDs and MeSH annotations.
* `*_pmids.db`: What retrieval downloaded — every PMID reached, which citation generation it came from, and its `cited_by` list.
* `*_cleaned_pmids.db`: **Belongs to one search, not to the installation.** It is a copy of `*_pmids.db` with the citation generations at or beyond the configured generation depth deleted, then annotated with MeSH headings from the master database. Because it depends on the search term, the date window and the generation depth, it is rebuilt per project prefix rather than shared — it is *not* a derivation of the master MeSH database and does not belong in the Databases screen.

  It is created automatically in **Step 2 (Retrieval & Database Operations)** of a full run, and it is a hard prerequisite of network construction, secondary analysis and the benchmark. If it is deleted, the next full run rebuilds it from `*_pmids.db` without re-downloading anything.

  The **bundled reference corpus ships without one**, because nothing was retrieved. Secondary analysis still runs against it: it fetches the citation data for the shortlist it is about to rank from the iCite API and caches it in a cleaned database of the same shape, so the second query reads from disk. Generating what it needs is what the demonstration is for.
* `mesh_terms.csv`: The MeSH vocabulary extracted from the XML in Step 1.
* `*_full_network_data.json`: The raw, unfiltered NetworkX graphical representation.
* `*_glf_optimal_subgraph.json` / `*_sa_optimal_subgraph.json`: The two independent optimizer solutions whose intersection forms the consensus subgraph.
* `*_optimization_history.json`: The GLF/SA score trajectory (feeds the optimization-trajectory figure).
* `*_consensus_lcc_network.json`: The optimized graph containing the intersection of the GLF and SA algorithms, reduced to its Largest Connected Component (LCC).
* `*_final_network_with_relevance.json`: The fully annotated terminal graph, populated with semantic Mean Relevancy Scores (MRS) and Louvain Community classifications.
* `*_mean_relevancy.db`: The per-article Mean Relevancy Scoring database — the `score_*` columns behind ARS/MRS and the secondary/benchmark steps.

### Analytical Exports (`results/`)

* `*_export.xlsx`: A tabular summary of the final nodes and edges.
* `*_Top_Network_Articles.csv`: The highest-scoring primary literature driving the network's structure.
* `*_run_annotations.csv`: The per-run biological-strata template edited during the annotation pause.
* `*_run_ledger.csv`: Every count the run produced, at every stage — records per citation generation, MeSH annotations screened, what each optimiser kept, what the consensus and the LCC discarded. Semicolon-delimited (MeSH headings contain commas), one ledger per file prefix, with the timestamp each figure was recorded. See **The Run Ledger & PRISMA Report** below.
* `*_prisma_flow_report.txt` and `figures/*_prisma_flow.*`: A PRISMA-style flow of records through the pipeline, in text and as a figure — the overview of the whole search, suitable for a methods section or a supplementary figure.
* `*_network_overlap_membership.csv` / `*_network_overlap_matrix.csv` / `*_Network_Overlap.png`: node-overlap comparison across the networks named in **Networks to Compare** — produced only when **Compare Multiple Networks** is enabled.
* **Benchmark & validation outputs** (all under `results/benchmark/`): the `--step benchmark` step asks several different questions of the same network, so its folder is grouped by question rather than left as one pile of files:

  | Folder | What is in it |
  | --- | --- |
  | `inputs/` | The ground truth the run actually used, kept under the project prefix (`*_ground_truth.*`, and `*_negative_control.*` when one is configured). A benchmark number cannot be read without knowing what it was scored against, and the original can be anywhere on disk — this copy is the one the results belong to. |
  | `ranking/` | The article-ranking benchmark: `*_benchmark_results.json`, `*_benchmark_quarantined_pmids.csv`, and `figures/*_benchmark_enrichment.png`. |
  | `ranking_validation/` | Every node weighting scored across the evaluation frames: `*_validation_report.xlsx` / `.html`, `*_projection_comparison.csv`, and `figures/`. |
  | `network_validation/` | The node/edge convergent validation — is the network's vocabulary and wiring reproduced? `*_gt_network_validation.xlsx`, `*_gt_cooccurrence_network.json`, and `figures/*_GT_*.png`. |

  See the **Validation & Benchmarking** section below for what each file contains.
* `logs/`: run logs and failed-fetch records.
* **Figures (`results/figures/`)**:
* **Figure 1 — Edge weight distribution.** How often each pair of MeSH terms appears in the same article, before and after consensus filtering. Shows that filtering removed the long tail rather than the signal.
* **Figure 2 — Optimisation trajectory.** GLF and SA traced over their search for the consensus subgraph.
* **Figure 3 — Community composition.** Stacked bars showing which strata make up each Louvain community, showing whether the communities follow the strata scheme. Needs the strata assigned; with everything left `Unassigned` it draws one bar.
* **Figure 4 — t-SNE projection.** The graph distance matrix in two dimensions, each node coloured by its Louvain community.
* **Figure 5 — Alluvial flow between strata.** An interactive Sankey tracing flow between the strata in the order set by **Strata order**. On an AOP project that reads stressor through to adverse outcome. Written as `.html`, labelled and unlabelled, plus the connection table behind it. Needs at least two strata; skipped otherwise.
* **Figure 6 — Node2Vec dendrogram.** Ward clustering of Node2Vec embeddings, leaves coloured by stratum.
* **Figure 7 — Network graph.** The consensus network drawn, every term labelled, nodes coloured by a metric chosen on the Figures tab.

Each figure has its own switch on the **Figures** tab; unticking one costs nothing but that figure.



---

## When Files Go Wrong

A run that is interrupted — a machine that hibernated, a disk that filled, a sync client caught mid-write — can leave a file that looks complete and is not. It has the right name and a plausible size, and it fails much later, inside a step that had no way to know its input was rubbish.

**Before a long run, turn hibernation off.** An ordinary sleep, where the screen blanks and the machine stays powered, does not interrupt a run. Hibernation writes memory to disk and stops the process, which can leave a database half-written. On Windows set *Settings → System → Power → Hibernate* to Never; on Linux, `systemd-inhibit` or the equivalent in the desktop's power settings.

### Tools → Check and repair files

Opens every artefact the pipeline depends on and reports its condition:

| Status | Meaning |
| :--- | :--- |
| **ok** | Opens and reads cleanly |
| *(blank)* | Not built yet — normal, and not a problem |
| **EMPTY** | Present but zero bytes: a write that never started |
| **CORRUPT** | Opening or parsing it fails outright |
| **SUSPECT** | Opens, but the contents do not add up |
| **ORPHAN** | A temporary or part-file no finished run would leave |

Definitely-broken files are pre-ticked; merely suspect ones are listed unticked. The dialog warns before removing anything that costs hours to rebuild, and afterwards names the step to resume from. Sidecar files go with their parent — a stale SQLite write-ahead log left beside a rebuilt database is worse than useless, because SQLite will try to replay it.

Nothing listed is analysis output. Every one of these files is machinery the pipeline rebuilds; results are never touched.

From a terminal:

```bash
python -m mesh_aop.cli --check-files
```

Add `--repair-files` to delete what is broken, and `--deep-check` for SQLite's full integrity check (thorough, and slow on a large database).

### The master annotation database

This one is treated differently because it is the only artefact whose replacement costs a night rather than a coffee break — roughly 50 GB downloaded and several hours compiled.

- After a successful build, a **health record** (`master_mesh_database.db.health.json`) stores its size, modification time and row count. Later damage is then detectable in seconds instead of by re-scanning eight gigabytes.
- Before any step that reads it, the pipeline runs a **pre-flight check**: open it, structural `quick_check`, confirm the table has rows, compare against the health record. A corrupt database stops the run *before* it spends hours on work that depends on it; a merely suspect one warns and continues.
- **Rebuild instructions are written beside the database itself**, as `HOW TO REBUILD THIS DATABASE - read me.txt`. A build log is not where anyone looks a month later when the file will not open.

---

## The Run Ledger and PRISMA-Style Flow Overview

Every run writes two provenance artefacts into `results/`, without being asked and regardless of which `--step` was run.

### `*_run_ledger.csv` — the counts

Every stage of a run produces counts: how many articles the search returned, how many survived each filter, how many nodes and edges the network ended with. The ledger records them all, so a number can be looked up afterwards instead of re-running the stage that produced it. It is a semicolon-delimited table — semicolons because MeSH headings contain commas as a matter of course (*Dermatitis, Allergic Contact*) — with five columns:

| Column | Meaning |
| :--- | :--- |
| `stage` | `run`, `identification`, `screening`, `pruning`, `included`, `unipartite` — in pipeline order |
| `metric` | What was counted |
| `value` | The count, or the setting |
| `recorded` | When that row was written |
| `note` | A plain-language gloss, so the file reads without this manual |

There is **one ledger per file prefix**, and recording **merges**: re-running the network step rewrites the `pruning` and `included` rows and leaves `identification` alone. That is why every row carries its own timestamp — a ledger whose stages were written weeks apart is legible rather than misleading, and the text report calls the mixed dates out explicitly when they differ.

Counts come from whichever source is most trustworthy, in this order: the stage that just ran hands back its own numbers; failing that, the ledger reuses what it recorded last time; failing that, it reads the artefacts on disk. The middle step matters — a resumed run would otherwise re-parse a several-hundred-megabyte network JSON to recover a number it had already written down.

### `*_prisma_flow_report.txt` and `figures/*_prisma_flow.*` — the overview

The same counts, laid out as a PRISMA 2020-style flow: **Identification → Screening → Pruning → Included**, with what was excluded at each step, and why, set beside it. The pipeline has genuinely the same shape as a systematic review — a seeded PubMed search expanded over citation generations, an annotation screen, two optimisers pruning the graph, and a largest connected component that everything downstream reports on — so it is drawn the same way.

The figure is written at the dpi and in the formats set under **Figures** in the settings (default 300 dpi, JPEG + TIFF). A stage the run never reached is left out rather than drawn as zero: *not run* and *found nothing* are different claims, and a reader cannot tell them apart from a box of zeroes.

---

## Validation & Benchmarking

The `--step benchmark` module evaluates how well the network's per-article relevance scores recover an external, curated set of "ground-truth" PMIDs (e.g. the bibliography of an authoritative OECD Adverse Outcome Pathway document). It is designed for the realistic situation here — a few dozen known-relevant papers hidden in a multi-million article candidate pool — and follows three principles: **validate the ground truth first, use metrics robust to incomplete relevance judgments, and quantify uncertainty against baselines.**

```bash
mpn-pipeline --step benchmark
```

### Ground Truth

The benchmark scores a network against a set of articles already believed to be
relevant. That set is the ground truth, and everything the benchmark reports
is relative to it.

**What makes a good one.** A few dozen PMIDs is enough; a hundred is comfortable.
What matters is that they are:

* **Indexed in PubMed with MeSH headings.** An article with no MeSH indexing is
  unreachable by a MeSH co-occurrence network by construction, so including one
  depresses every metric for a reason that has nothing to do with ranking
  quality. Book chapters, guidance documents and unindexed reports belong in a
  separate exclusions list, not in the positive set.
* **Chosen independently of this pipeline.** A set assembled by looking at what
  the network already ranks highly measures nothing.
* **Within the context window.** Articles outside the Analysis-tab date range
  are never scored, so they cap achievable recall.

#### Providing a ground truth

1. **Enable it.** Set `benchmark.run_ground_truth_analysis = true` — on the
   **Benchmark** tab, *Run ground-truth analysis*.
2. **Provide the file.** Put it in the **raw data folder** (the Folders tab
   shows where that is) under any of these names, and it is picked up
   automatically:

   ```text
   <project prefix>_ground_truth.csv          (or .txt / .tsv / .xlsx)
   ground_truth_pmids.csv        ground_truth.csv
   ground_truth_pmids.txt        ground_truth.txt
   oecd_resolved_citations.csv
   ```

   The prefixed name is looked for first, so each project can keep its own set
   side by side. Any other name works when entered in *Ground truth file*.

**Required structure.** A template ships at
[`data/raw/ground_truth_pmids.template.csv`](data/raw/ground_truth_pmids.template.csv).
The only hard requirement is a **`PMID` column**:

| Column | Required? | Notes |
|---|---|---|
| `PMID` | **Yes** | One PubMed ID per row. `pmids`, `pubmed_id` and `id` are accepted as aliases. Digits only — `19033392`, not `19033392.0`. |
| `Reference` (or any second column) | Optional | The citation as free text. When present it enables a publication-year check that flags citation-to-PMID mis-resolution. |

**Accepted shapes**, detected automatically: an `.xlsx` workbook with a `PMID`
column; a CSV or TSV with a `PMID` column and an optional reference column; a
semicolon-delimited `Raw_Reference;PMID` file; a single column of PMIDs with or
without a header; or a plain `.txt` list with one PMID per line.

If nothing is found, the run stops and prints every location it searched.

**Negative control (optional).** *Negative control CSV* takes an unrelated set,
which should score near random, as a specificity check. Same locations, names
and structure as above. Empty disables it.

#### The bundled example

The reference corpus ships with a worked example of all of the above: **96
curated positives** in `oecd_ground_truth_curated.xlsx`, with **22 excluded
citations** listed separately in `oecd_ground_truth_exclusions.xlsx`, each with
the reason it was excluded. Looking at those two files together is the quickest
way to see what a usable ground truth looks like — including what belongs in the
exclusions rather than the positives.

They were resolved from the reference list of:

> OECD (2014), *The Adverse Outcome Pathway for Skin Sensitisation Initiated by
> Covalent Binding to Proteins*, OECD Series on Testing and Assessment No. 168,
> OECD Publishing, Paris.
> <https://doi.org/10.1787/9789264221444-en> ·
> [AOP 40 on AOP-Wiki](https://aopwiki.org/aops/40)

Cite that document, not this program, as the origin of the set — it is a PMID
resolution of a published bibliography, not an independent selection. For a
different set of positives, cite its source instead.

### What It Reports

1. **Ground-truth validation.** PMIDs are digit-normalized (fixing the common `19033392.0` float-coercion mismatch), de-duplicated, and split into resolved vs. unresolved (`NOT_FOUND`). Each resolved PMID is sanity-checked for plausibility: an *absolute ceiling* test rejects PMIDs too large to exist yet, and a *chronological* test flags post-1990 papers whose PMID is implausibly large for the cited year (a hallmark of citation→PMID mis-resolution). **Flagged rows are quarantined to a review CSV — never deleted automatically.** When a reference/citation column is present the year check is active; for bare PMID lists only the absolute-ceiling test applies.
2. **Coverage vs. ranking (kept separate).** *Retrievability ceiling* — how many ground-truth PMIDs are even present in the candidate pool — is reported independently of *ranking quality*, so a low score is correctly attributed to either missing coverage or poor ranking rather than conflated.
3. **Ranking metrics suited to extreme imbalance and incomplete judgments.** The
   primary metrics depend only on where the known positives rank, and never
   assume an unjudged article is a negative:

   | Metric | One line |
   | :--- | :--- |
   | **Recall@K** | Of the ground truth, the fraction that appears in the top K. |
   | **MAP** | Mean average precision — rewards putting positives early, not merely somewhere. |
   | **R-precision** | Precision at K = the number of positives, so it needs no arbitrary cut-off. |
   | **NDCG** | Discounted gain: a positive at rank 5 counts for more than one at rank 500. |
   | **Enrichment Factor** | How many times more positives appear in the top 1 % or 5 % than chance would give. |
   | **BEDROC** | Early recognition, weighted so the very top of the list dominates. The headline number. |

   ROC-AUC and PR-AUC are reported but demoted to secondary diagnostics: at a
   prevalence near 10⁻⁵, ROC-AUC flatters almost anything, and PR-AUC is biased
   low because it treats every unjudged article as a negative.
4. **Uncertainty and baselines.** Every headline metric carries a **bootstrap confidence interval**, and a **permutation null** reports lift-over-random with an empirical p-value. A structural baseline (number of bridged network nodes) and an optional **negative-control** ground-truth set (which should score near random) guard against the network merely surfacing generically popular papers.

### Outputs

Written to `results/benchmark/`:

* `*_benchmark_results.json` — all metrics, confidence intervals, lift, and coverage figures, with the run's seed and configuration for reproducibility.
* `*_benchmark_quarantined_pmids.csv` — ground-truth rows flagged as implausible, for manual adjudication.
* `*_benchmark_enrichment.png` — cumulative recall (enrichment) curve: ground-truth recovery vs. fraction of the pool screened.
* `validation/*_validation_report.xlsx` / `.html` + figures — the consolidated **node-weighting** comparison across four framings (corpus / within-query / outside / hybrid) with BEDROC and paired bootstraps (from `run_network_validation`).
* `validation/*_projection_comparison.csv` + figure — the article-scoring **projection** comparison, by BEDROC across three frames (from `run_projection_comparison`). It scores the alternative ways of turning node weights into an article score against each other:

  | Projection | What it does |
  | :--- | :--- |
  | **Normalised ARS** | The bipartite projection described above — the one the pipeline uses. |
  | **Unnormalised sum** | The same sum without the degree damping, so breadth is rewarded. |
  | **MRS-weighted** | Weights terms by MRS rather than by raw node weight. |
  | **Bipartite-reinforced** | Lets article and term scores reinforce each other over further iterations. |
  | **BM25** | The standard information-retrieval ranking function, treating an article's MeSH headings as its text and the network's terms as the query. A well-understood external baseline. |
  | **Uniform** | Every network term weighted 1 — measures how much the weighting is contributing at all. |
  | **Random** | The floor. |
  | **Naive query** | Rank by the single primary node, as a plain PubMed search would. |

> **Note on incomplete judgments:** the non-ground-truth articles are *unjudged*, not confirmed negatives. This is why recall- and rank-based metrics (which only need positive positions) are the headline numbers, while precision/PR-AUC are interpreted with caution. For the most rigorous citation→PMID verification, cross-check publication years online via NCBI Entrez (not enabled by default, as it requires network access).

### Node/Edge Convergent Validation

`--step benchmark` also runs a **structural** check (`gt_network_validation.py`) that asks a different question from the article ranking above: *is the network's own vocabulary and wiring independently reproduced by the ground-truth literature?* A network could rank articles well simply by naming popular terms — recovering its **edges** from an independent corpus is far harder to achieve by chance.

The ground-truth articles' MeSH terms are pulled from the master database and filtered through the **same node-eligibility stop-word list used to build the network**, so stop-listed headings (check tags, organisms, geographics) can never appear as spurious "near misses" — they were never eligible to be nodes in the first place. An audit sheet records exactly which stop terms were removed and asserts that none leaked into the node or miss lists.

Both levels are calibrated against a **permutation null of random article draws of the same size** — essential, because two corpora about the same topic will overlap somewhat by construction, so raw overlap alone is not evidence:

* **Node level** — how many network nodes are attested in the ground truth, their enrichment over corpus base rates, and the Spearman correlation between a node's ground-truth prominence and its network weight.
* **Edge level** — how many of the network's edges reappear as ground-truth co-occurrences.
* **Misses** — ground-truth-frequent eligible terms that are *not* network nodes, which localize where the network under-covers the domain.
* **Node-weighting comparison** — scores every available node weighting (each `MRS_*`, each raw centrality, `adjusted_node_weight`) against external ground-truth prominence, to test whether the MRS transformation adds node-importance information **over** the centrality it is built from. Because an MRS is derived from its centrality the two are collinear, so a plain comparison of their correlations is not sufficient; the table therefore reports a **partial correlation controlling for the raw centrality** and a **paired bootstrap CI on the difference**. A difference interval spanning zero means the transformation is not distinguishable from the centrality underneath it. Three criteria are reported side by side: correlation with GT article frequency, correlation with **enrichment** (base-rate corrected, which removes any residual frequency component and is therefore the stricter test), and an AUC for ranking attested nodes above unattested ones across *all* nodes.

It runs *before* the ranking benchmark (it takes minutes rather than tens of minutes), so a long benchmark never blocks the structural result. Disable it with `benchmark.run_network_validation = false`.

**Outputs** (to `results/benchmark/`):

* `*_gt_network_validation.xlsx` — sheets: `summary`, `stopword_audit`, `network_nodes`, `GT_terms`, `GT_misses`, `network_edge_validation`, `node_weighting_comparison`
* `*_gt_cooccurrence_network.json` — the ground-truth co-occurrence graph in **Cytoscape.js** format, every node and edge annotated with its overlap status (`shared` vs `GT_only_miss`, `recovered` vs `GT_only`), enrichment, and counts
* `*_GT_Node_Validation.png`, `*_GT_Cooccurrence_Network.png`, `*_GT_Permutation_Nulls.png`

---

## User-Provided Files — Quick Reference

Everything a user supplies, where it goes, and how the pipeline picks it up. Most inputs are automatic or optional: only the MeSH XML (auto-downloaded) is **always** needed, plus a ground-truth list **only if** a project's own data is benchmarked.

| File | Where it goes | How it's picked up | Format / structure |
|---|---|---|---|
| **MeSH descriptor XML** | `data/raw/descYYYY.xml` | Auto-downloaded from NLM if missing (§1); or place manually | Unmodified NLM MeSH descriptor XML |
| **Ground-truth PMIDs** (benchmark) | `data/raw/` (own data), or a path | Auto-detected by name, or `benchmark.ground_truth_csv`; requires `run_ground_truth_analysis = true` | `PMID` column required — see **Ground Truth** below |
| **Negative-control PMIDs** (optional) | `data/raw/`, or a path | `benchmark.negative_control_csv` (filename or path) | Same structure as ground truth |
| **Comparison networks** (optional) | `data/processed/`, or a path | `comparison_networks` list when `compare_networks` is on | Pipeline network JSON (Cytoscape) or a networkx-readable graph — **reuse `*_consensus_lcc_network.json` outputs; do not hand-author** |
| **Strata annotations** | `results/*_run_annotations.csv` (generated) | Edited by hand during the Step-3 pause | Semicolon-delimited; one stratum name per term |
| **Entrez credentials** | wizard, or environment variables | `MESH_ENTREZ_EMAIL` / `MESH_ENTREZ_API_KEY`, or the wizard | Email + NCBI API key |

**Templates** for user-created files ship next to where they belong (e.g. [`data/raw/ground_truth_pmids.template.csv`](data/raw/ground_truth_pmids.template.csv)) — copy, rename, and fill. Everything else in `data/processed/`, the network JSONs, the relevance databases, and all figures is **generated** — never hand-authored.

---

## Troubleshooting

### Windows `MAX_PATH` / "No such file or directory" during install

Symptom: `pip install -e .` aborts with `OSError: [Errno 2] No such file or directory: '...\statsmodels\tsa\vector_ar\tests\JMulTi_results\...txt'` and a hint about *"Windows Long Path support"*.

Cause: the Windows 260-character path limit. A deeply nested project location (especially under `OneDrive - <Org>\Documents\...`) plus a venv plus `statsmodels`' long test filenames exceeds 260 characters, so the file write fails and pip rolls back the whole install.

Fix (no admin needed): create the venv at a **short path outside** the project, then install from the repo root — only the deep dependency files need the short location; the editable package links back to the source:

```powershell
py -3.12 -m venv "$env:USERPROFILE\mesh_env"     # e.g. C:\Users\<name>\mesh_env
& "$env:USERPROFILE\mesh_env\Scripts\python.exe" -m pip install -e .
```

(Alternative, with administrator rights: enable long paths via `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1` and reboot.)

### "Activate.ps1 cannot be loaded ... running scripts is disabled"

Symptom: activating the virtual environment fails with `running scripts is disabled on this system` (a `PSSecurityException` / `UnauthorizedAccess`).

Cause: Windows PowerShell's **execution policy** (often `Restricted` by default) blocks the `Activate.ps1` script. This only blocks the activation *script* — `python.exe` itself is unaffected. `mpn-check-env` detects this and prints the same guidance.

Fix — enable local scripts once (no admin needed; works in all future windows):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
& "$env:USERPROFILE\mesh_env\Scripts\Activate.ps1"
```

If a corporate policy blocks even `CurrentUser`, set it per-window instead: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force`. Or skip activation entirely and call the venv Python by full path (needs no policy change):

```powershell
& "$env:USERPROFILE\mesh_env\Scripts\python.exe" -m mesh_aop.cli --step all --interactive
```

### "Access is denied" running `mpn-pipeline` / `mpn-check-env`

Symptom: the console-script launchers fail with *Access is denied* / `ApplicationFailedException`, even though `python.exe` itself works.

Cause: corporate security/EDR software on managed machines often blocks freshly-created, unsigned `.exe` launcher stubs that pip generates in the venv's `Scripts` folder.

Fix: invoke the tools as modules, which bypasses the launcher exes entirely:

```powershell
python -m mesh_aop.cli --step all --interactive
python -m mesh_aop.check_env --auto
```

### `community` / `python-louvain` Namespace Collision

The `python-louvain` package installs itself under the name `community`, which conflicts with an unrelated package also named `community` on PyPI. If `ImportError: cannot import name 'community_louvain' from 'community'` appears, run:

```bash
pip uninstall community python-louvain -y
pip install python-louvain
```

The `mpn-check-env --auto` script detects and resolves this automatically.

### RAM Exhaustion on Large Networks

Networks with `generations_n >= 2` can load several million records into RAM during centrality calculation. If the process is killed by the OS:

1. Set `calculate_full_centrality: false` in `mesh_config.json` so betweenness is estimated from a node sample rather than computed exactly.
2. Reduce `betweenness_k_samples` (default `1000`) to lower the heuristic sampling budget.
3. Reduce `target_num_edges` so GLF/SA operate on a smaller subgraph.

Setting `calculate_full_centrality: false` does **not** disable centrality or prevent MRS from being calculated — eigenvector and PageRank are computed regardless, and only betweenness becomes a sampled estimate (see the Analysis Parameters section above).

### SQLite Lock Errors on Network-Attached Storage

The `baseline_manager` uses a verified safe-transfer architecture specifically to handle write failures on NAS and cloud-synced directories (OneDrive, Dropbox, etc.). If lock errors persist, ensure no other process (e.g., a cloud-sync agent) has the `.db` file open, then re-run `mpn-pipeline --step process`.

### Convergence Warnings for Eigenvector Centrality

On sparse or disconnected graphs, the power-iteration solver may not converge within the default 1000 iterations. Increase `eigenvector_max_iter` in `mesh_config.json` or lower `eigenvector_tol` to relax the stopping criterion.

---

## Repository Structure

The layout of the source tree, and what each module does, is described in [COMMAND-LINE.md](COMMAND-LINE.md#repository-structure).

---

## Citation

Cite this software, or a network it produced, in published work as:

```
Sax, J. (2026). MPN (Medical Publishing to Network): MeSH co-occurrence concept networks for Adverse Outcome Pathways (Version 3.2.10) [Computer software]. https://github.com/Tox-pub/Medical_Publishing_to_Network-MPN
```

Archived release: [10.5281/zenodo.18662959](https://doi.org/10.5281/zenodo.18662959)
A machine-readable version ships as `CITATION.cff`, and **Help → Cite this Program** shows the same text with BibTeX.

### Also cite the methods this rests on

These are other people's work, implemented here. A methods section describing the filtering or the ground truth without citing them is incomplete.

* **Edge filtering (GLF)** — Dianati, N. (2016). Unwinding the hairball graph: Pruning algorithms for weighted complex networks. Physical Review E, 93, 012304. https://doi.org/10.1103/PhysRevE.93.012304
  The Global Likelihood Filter this pipeline runs as one of its two optimisers. The same paper introduces the Marginal Likelihood Filter (MLF), used here for per-edge p-values.

* **Ground-truth set (reference corpus)** — OECD (2014). The Adverse Outcome Pathway for Skin Sensitisation Initiated by Covalent Binding to Proteins. OECD Series on Testing and Assessment No. 168. OECD Publishing, Paris. https://doi.org/10.1787/9789264221444-en
  AOP 40. The curated positive set the bundled reference corpus is validated against comes from the references of this document.

* **Community detection** — Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. Journal of Statistical Mechanics: Theory and Experiment, 2008(10), P10008.
  The Louvain method, used to partition the consensus network.

* **Early-recognition metric** — Truchon, J.-F., & Bayly, C. I. (2007). Evaluating virtual screening methods: Good and bad metrics for the "early recognition" problem. Journal of Chemical Information and Modeling, 47(2), 488-508.
  BEDROC, the benchmark's headline ranking metric.

* **Article citation counts** — Hutchins, B. I., Baker, K. L., Davis, M. T., et al. (2019). The NIH Open Citation Collection: A public access, broad coverage resource. PLOS Biology, 17(10), e3000385.
  The iCite API, which supplies the citation side of the Article Impact Score.

## License

MIT License. Copyright (c) 2026 Tox-pub.

Free to use, modify and redistribute, including commercially, provided the copyright notice and licence text are kept. Provided without warranty of any kind. The full text ships as `LICENSE`, and the bundled CPython, Tcl/Tk and Python libraries carry their own licences, listed in `THIRD-PARTY-NOTICES.md`.

In the application: **Help → License**.
