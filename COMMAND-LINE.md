# MPN (Medical Publishing to Network) — Command-Line Guide

This document is how to run the pipeline from a shell, and how to work on the
source. It ships with the source package.

**The desktop application does not require it.** MPN is a desktop
application, and everything the pipeline does can be driven from its window. To
install the application, see [INSTALL.md](INSTALL.md); for the manual, see
[HELP.md](HELP.md), which is also what **Help → MPN Manual** opens.

This document covers scripting runs, working on the code, and running on a
machine with no desktop.

**Every setting named here is the same setting the application shows.** The
config keys below (`search_parameters.search_term`, `benchmark.primary_node`,
and so on) are the dotted paths into `mesh_config.json`; the application writes
the same file. The parameter glossary in [HELP.md](HELP.md) documents what each
one means, once, for both.

---

## Contents

- [Running the pipeline from a downloaded build](#running-the-pipeline-from-a-downloaded-build)
- [Setting up a development environment](#setting-up-a-development-environment)
- [Execution Guide](#execution-guide)
- [Repository Structure](#repository-structure)
- [Jupyter Notebook Interface](#jupyter-notebook-interface)
- [Programmatic API Usage](#programmatic-api-usage)
- [Where to find everything else](#where-to-find-everything-else)

## Running the pipeline from a downloaded build

Every downloadable build carries its own Python. The command line requires no
system Python, no virtual environment and no `pip install`. Nothing in the
section after this one applies to a downloaded build; it covers installing from
source.

Each build provides a launcher named `mpn-pipeline`, placed beside the
application in the program folder. It accepts every flag listed under
[CLI Flags](#cli-flags) and passes them through unchanged.

### Windows

Extract the portable zip, or install the `.msi`. Open a shell in the program
folder and run:

```powershell
mpn-pipeline.bat --step viz
mpn-pipeline.bat --step all --interactive
```

From another directory, give the full path in quotes — the folder name contains
a space:

```powershell
& "C:\path\to\MPN\mpn-pipeline.bat" --step viz
```

**If the launcher does not run**, call the module directly. The command is
identical in effect; the launcher adds nothing but the path lookup:

```powershell
& "C:\path\to\MPN\python\python.exe" -m mesh_aop.cli --step viz
```

That second form also applies where policy blocks `.bat` execution, since it
invokes the bundled interpreter rather than a script.

### Linux and macOS

Extract the tarball, change into the extracted folder, and run:

```bash
./mpn-pipeline --step viz
./mpn-pipeline --step all --interactive
```

The first invocation unpacks the bundled wheels, which takes about a minute and
requires no network. Subsequent invocations start immediately.

**If the launcher reports "Permission denied"**, the executable bit was lost in
transit — extracting on Windows or copying through a FAT32 or exFAT volume does
this. Restore it:

```bash
chmod +x mpn-pipeline "MPN" mpn-uninstall python/bin/python3.12
```

**If the launcher still does not run**, call the module directly. Run the
launcher once first, or the bundled libraries will not have been unpacked:

```bash
PYTHONPATH="$PWD/app/src" ./python/bin/python3.12 -m mesh_aop.cli --step viz
```

### Startup time

The pipeline loads NumPy, SciPy, pandas, scikit-learn, statsmodels and
matplotlib before it does anything. About 400 MB is read at every start, so
each invocation carries a fixed cost before the requested work begins.

Measured on one build, running the same command three ways:

| Location | First run | Subsequent runs |
| :--- | ---: | ---: |
| Internal disk | 39s | 4s |
| External drive | 142s | 139s |

The first run on an internal disk is slow because nothing is cached yet; after
that the operating system holds the libraries in memory and startup drops to
about four seconds.

**Install to an internal disk.** An external drive gains nothing from caching —
Windows applies a removal-safe policy to it by default — so every invocation
re-reads the full 400 MB and the cost never falls. A command that should take
four seconds takes over two minutes, which reads as a frozen program rather
than a slow one. Running from a USB stick is the usual cause.

---

## Setting up a development environment

Installing the **application** is covered in [INSTALL.md](INSTALL.md) — that is
the right document for anyone who simply wants to run it, and none of the below
is needed. What follows is for working on the source.

### Requirements

* **Python 3.11–3.13** (`requires-python = ">=3.11,<3.14"`).
* **Memory** — 16 GB is the ideal minimum; 32 GB or more for the database
  build and for networks past one citation generation. It will run on less.
* **Storage** — about 80 GB free. The NLM baseline archives are about 50 GB
  and the SQLite master database built from them is about 10 GB. Once that
  database is built and verified, `data/raw/pubmed_baseline/` can be deleted to
  reclaim the archive space, unless daily updates will be applied later — those
  re-read the archives.

### Install from source

This installs the pipeline and the application from source. To install a
downloaded build instead, see [INSTALL.md](INSTALL.md); the application window is
described under [The MPN Window](HELP.md#the-mpn-window).

The commands assume **PowerShell** on Windows or **bash** on Linux and macOS.
Adjust the paths and the activation command for another shell.

```bash
git clone https://github.com/Tox-pub/Medical_Publishing_to_Network-MPN.git
cd Medical_Publishing_to_Network-MPN
python -m venv ~/mesh_env
~/mesh_env/bin/python -m pip install -e .
```

On **Windows**, create the environment at a short path such as
`C:\Users\<name>\mesh_env` — not inside a deeply nested or cloud-synced folder.
Several dependencies ship very long filenames that overflow the 260-character
`MAX_PATH` limit and abort the install part-way through. See
[Troubleshooting](HELP.md#troubleshooting).

Verify the entry points resolve:

```bash
mpn-pipeline --version
mpn-check-env
```

`mpn-check-env` also reports missing OS-level rendering libraries.

---

## Execution Guide

The pipeline is entirely modular and controlled via a terminal interface. Configuration is handled by an interactive command-line wizard, allowing users to modify runtime parameters safely without touching source code.

> **Invocation by platform.** The examples below use the `mpn-pipeline` command, which works on **macOS/Linux** and on Windows after activating the virtual environment. On **Windows**, where activation or pip's `.exe` launcher is blocked, use the equivalent module form with the environment's Python by full path; it behaves identically:
> ```powershell
> & "$env:USERPROFILE\mesh_env\Scripts\python.exe" -m mesh_aop.cli --step all --interactive
> ```
> i.e. replace `mpn-pipeline` with `& "$env:USERPROFILE\mesh_env\Scripts\python.exe" -m mesh_aop.cli` in any command.
>
> Settings are read from the per-user settings file (`%LOCALAPPDATA%\MPN\mesh_config.json` on Windows, `~/.local/share/MPN/mesh_config.json` on Linux, `~/Library/Application Support/MPN/mesh_config.json` on macOS) unless `--config` names another, so the working directory does not matter.

### CLI Flags

| Flag | Description |
|------|-------------|
| `--step <name>` | Which pipeline segment to run: `all`, `baseline`, `process`, `data_ops`, `network`, `secondary`, `viz` or `benchmark`. Defaults to `all`. |
| `--interactive` | Launches the interactive wizard before execution. |
| `--config <path>` | Path to a settings JSON. Defaults to the per-user settings file described above. |
| `--sync-annotations <ask/yes/no>` | After a pause for annotation, whether to merge the run's strata into the master annotations library. Defaults to `ask`. |
| `--refresh-mesh-support` | Re-downloads the MeSH descriptor file and rebuilds the stop-word vocabulary from it. |
| `--build-database` | Runs Step 0 first: downloads the PubMed baseline and compiles the master annotation database. |
| `--skip-baseline-download` | With `--build-database`, compiles from archives already on disk. |
| `--with-updates` | With `--build-database`, also fetches the daily update files published since the baseline. |
| `--rebuild-corrupt` | With `--build-database`, deletes an unreadable master database before rebuilding it. |
| `--max-workers <N>` | Parser processes for the database build. Defaults to a value chosen from available RAM. |
| `--check-files` | Checks every file the project depends on, reports anything damaged, and exits. |
| `--repair-files` | With `--check-files`, deletes the damaged files so the next run rebuilds them. |
| `--deep-check` | With `--check-files`, runs SQLite's full integrity check. Thorough, and slow on a large database. |
| `--readme` | Opens `README.md` in the system's default viewer. |
| `-v` / `--version` | Prints the installed package version and exits. |

### Running the Complete Pipeline

To construct a network from the ground up, execute the `all` step. The `--interactive` flag invokes the wizard.

```bash
mpn-pipeline --step all --interactive

```

### Running Individual Modules

If upstream dependencies are already built, specific modules can be executed in isolation.

* **Step 0 only:** `mpn-pipeline --step baseline --build-database` (Master database download and compilation)
* **Step 0 & 1:** `mpn-pipeline --step process --interactive` (Database Compilation & MeSH processing)
* **Step 2:** `mpn-pipeline --step data_ops --interactive` (Entrez API Collection)
* **Step 3:** `mpn-pipeline --step network --interactive` (Topology & Filtering)
* **Step 3.5:** `mpn-pipeline --step secondary --interactive` (Targeted Export Analysis)
* **Step 4:** `mpn-pipeline --step viz --interactive` (Biological Figure Generation)
* **Step 5:** `mpn-pipeline --step benchmark` (Ground-Truth Validation & Performance Benchmarking)

---

## Repository Structure

The package assumes and enforces the following directory architecture.

```text
Medical_Publishing_to_Network-MPN/
│
├── data/                               # Data storage
│   ├── raw/                            # Inputs for a run
│   │   ├── aop_annotations_master.csv  # Ships w/ repo: AOP strata dictionary (pre-seeded; grows each run)
│   │   ├── desc2025.xml                # Auto-downloaded from NLM if missing (or place manually); not in repo
│   │   ├── ground_truth_pmids.template.csv # Ships w/ repo: copy and fill for a project's benchmark set
│   │   ├── ground_truth_pmids.csv      # Optional, placed by hand: a project's benchmark set (see "Ground Truth")
│   │   ├── master_mesh_database.db     # Auto-generated: offline PubMed corpus (Step 0)
│   │   ├── pubmed_baseline/            # Auto-downloaded: NLM Baseline XMLs (~50 GB, Step 0)
│   │   └── pubmed_updates/             # Auto-downloaded: NLM Daily Update XMLs (optional)
│   ├── processed/                      # Auto-generated: pipeline databases and JSONs (starts empty)
│   ├── reference_raw/                  # Ships w/ repo: bundled reference inputs
│   │   └── oecd_resolved_citations.csv # OECD AOP-40 citation->PMID table (the bundled ground-truth source)
│   └── reference_processed/            # Ships w/ repo: curated OECD ground-truth set + bundled reference network
│
├── results/                            # Output artifacts (auto-generated)
│   ├── figures/                        # High-resolution pipeline plots (.png, .tif, .html)
│   ├── benchmark/                      # All --step benchmark outputs
│   │   ├── inputs/                     # The ground truth the run used
│   │   ├── ranking/                    # Article-ranking benchmark
│   │   ├── ranking_validation/         # Node-weighting and projection comparison
│   │   └── network_validation/         # Node/edge convergent validation
│   ├── logs/                           # System logs and failed fetch records
│   ├── *_run_annotations.csv           # Run-specific strata annotation templates
│   ├── *_Top_Network_Articles.csv      # Secondary analysis exports
│   └── *_export.xlsx                   # Exported full network tables
│
├── src/
│   ├── mpn/                            # The desktop application: window, settings form, runner
│   ├── mesh_aop/                       # Core Python package modules
│   │   ├── __init__.py
│   │   ├── baseline_manager.py         # Multi-core MapReduce ETL for the Master Database
│   │   ├── benchmark.py                # Ground-truth validation & performance benchmarking
│   │   ├── check_env.py                # System environment & dependency verification
│   │   ├── cli.py                      # Orchestrator and CLI entry point
│   │   ├── config_parser.py            # Two-tier configuration engine
│   │   ├── data_ops.py                 # SQLite and NCBI Entrez querying
│   │   ├── gt_network_validation.py    # Node/edge convergent ground-truth validation
│   │   ├── mesh_data_processor.py      # Unified XML extraction and stop-word generation
│   │   ├── mesh_stop_words.py          # Auto-generated MeSH stop-word set
│   │   ├── vocabulary.py               # Which MeSH trees an analysis may see
│   │   ├── strata.py                   # The annotation scheme and its order
│   │   ├── mdhtml.py                   # Renders the shipped documents as HTML
│   │   ├── network.py                  # NetworkX assembly, filtering, and centrality
│   │   ├── node2vec_embedding.py       # Node2Vec embedding used by the dendrogram figure
│   │   ├── relevance.py                # Mean Relevancy Scoring (Semantic Re-ranking)
│   │   ├── secondary_analysis.py       # Metadata hydration and targeted graph querying
│   │   ├── stats.py                    # GLF/SA mathematical models and graph statistics
│   │   ├── validation_report.py        # Consolidated node-weighting + projection evaluation
│   │   ├── viz.py                      # Matplotlib, Seaborn, and Plotly graphics
│   │   └── wizard.py                   # Interactive configuration module
│   └── mesh_aop_notebooks/             # Jupyter notebook equivalents of each module
│       └── *.ipynb                     # One notebook per module for interactive exploration
│
├── packaging/                          # Release build scripts, launchers and the WiX source
├── tests/                              # Test suites (python tests/run_all.py)
│
├── environment.yml                     # Mamba/Conda cross-platform dependency resolution
├── pyproject.toml                      # Package specification and entry points
├── CITATION.cff                        # Machine-readable citation
├── LICENSE                             # MIT License
├── THIRD-PARTY-NOTICES.md              # Licences of the bundled components
├── README.md                           # Project overview
├── INSTALL.md                          # Installing downloaded builds
├── HELP.md                             # The manual
└── COMMAND-LINE.md                     # This document


```

---

## Jupyter Notebook Interface

Every module in `src/mesh_aop/` has a corresponding Jupyter notebook in `src/mesh_aop_notebooks/`. Each notebook holds its module's source in a single code cell, regenerated from the module by `packaging/sync_notebooks.py`. They are intended for:

* **Interactive exploration** — step through the pipeline one cell at a time and inspect intermediate data structures.
* **Prototyping** — experiment with individual functions (e.g., tweak GLF parameters and re-run only the filtering step) without triggering the full CLI orchestration.
* **Debugging** — isolate a specific module and inspect its inputs and outputs in a notebook environment.

The folder carries its own `environment.yml` and `pyproject.toml`, so it can be used on its own.

---

## Programmatic API Usage

The package exposes a clean Python API through its `__init__.py`. All pipeline functions can be imported and called directly without using the CLI, which is useful for embedding the analysis within a larger workflow or Jupyter-based research pipeline.

```python
from mesh_aop import (
    MeshConfig,
    process_raw_mesh_data,
    run_initial_data_collection,
    run_network_construction,
    run_consensus_filtering_and_lcc,
    run_community_detection,
    run_mean_relevancy_scoring,
    get_top_network_articles,
    plot_sankey_alluvial,
)

# Load settings (factory defaults overlaid by the local mesh_config.json)
config = MeshConfig(config_path="mesh_config.json")

# Step 1 – Extract MeSH terms from XML
process_raw_mesh_data(
    xml_file=config.files['mesh_xml'],
    output_csv=config.files['mesh_terms_csv'],
    output_py=config.files['mesh_stopwords_py'],
)

# Step 2 – Collect articles from NCBI Entrez
run_initial_data_collection(
    search_term_param=config.get('search_parameters', 'search_term'),
    start_date_str=config.get('search_parameters', 'start_date'),
    end_date_str=config.get('search_parameters', 'end_date'),
    generations_n_param=config.get('search_parameters', 'generations_n'),
    db_path=config.files['pmids_db'],
    entrez_email=config.get('credentials', 'entrez_email'),
    entrez_api_key=config.get('credentials', 'entrez_api_key'),
)

# Step 3 – Build and filter the network
run_network_construction(db_path_param=config.files['cleaned_db'],
                         output_json_path=config.files['full_network'], ...)
run_consensus_filtering_and_lcc(...)
run_community_detection(network_file_path=config.files['consensus_lcc'], ...)
run_mean_relevancy_scoring(...)
```

The full list of exported symbols is defined in `src/mesh_aop/__init__.py`.

---

## Where to find everything else

This document covers only how to drive the pipeline from a shell. Everything
about what the pipeline does, and what each setting means, is in
[HELP.md](HELP.md):

| Looking for | See |
| :--- | :--- |
| What every setting does | [Settings Reference](HELP.md#settings-reference) |
| How ARS and MRS are calculated | [How articles and terms are scored](HELP.md#how-articles-and-terms-are-scored) |
| Prerequisites and disk budget | [Data Acquisition & Prerequisites](HELP.md#data-acquisition--prerequisites) |
| Assigning strata | [The Annotation Workflow (Strata)](HELP.md#the-annotation-workflow-strata) |
| What the run produces | [Output Artifacts](HELP.md#output-artifacts) |
| Ground truth and benchmarking | [Ground Truth](HELP.md#ground-truth), [Validation & Benchmarking](HELP.md#validation--benchmarking) |
| Damaged files | [When Files Go Wrong](HELP.md#when-files-go-wrong) |
| Citing this program | [Citation](HELP.md#citation) |
