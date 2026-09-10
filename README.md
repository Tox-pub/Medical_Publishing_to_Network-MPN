# MPN — Medical Publishing to Network

**MPN** stands for *Medical Publishing to Network*: it turns published medical
literature into a network. The full name introduces the software; `MPN` is used
everywhere after.

MPN builds and validates **MeSH co-occurrence concept networks** from the PubMed
literature, connecting chemical stressors to adverse outcomes through biological
intermediates in the shape of an Adverse Outcome Pathway.

It is a desktop application for Windows, Linux and macOS, with a command-line
pipeline behind it. The application is validated on Windows and Linux.

---

## Get it

**One file per system**, from
[Releases](https://github.com/Tox-pub/Medical_Publishing_to_Network-MPN/releases).

| System | Download | What to do |
| :--- | :--- | :--- |
| Windows | `MPN-<version>-win64.msi` | Double-click it. |
| Windows, without installing | `MPN-<version>-win64-portable.zip` | Extract, then double-click `MPN.bat`. |
| Linux | `MPN-<version>-linux-x86_64.tar.gz` | Extract, then run `./"MPN"`. |
| macOS | `MPN-<version>-macos-arm64.tar.gz` | Extract, then run `./"MPN"` from Terminal. |

**Each one carries its own Python.** Nothing needs installing first: no system
Python, no `python3-tk`, no administrator rights, and nothing written outside the
user's own profile.

Remove MPN with its uninstaller: **Tools → Uninstall** in the window,
**Settings → Apps** for the Windows installer, `Uninstall.bat` for the Windows
portable copy, and `./mpn-uninstall` on Linux and macOS. Deleting the program
folder alone leaves the databases and settings behind. They are kept outside the
program folder so that an upgrade does not repeat a 50 GB download.

On Windows the only program that executes is `python.exe`, signed by the Python
Software Foundation, and the installer is run by `msiexec.exe`, which is part of
Windows.

The macOS download is unsigned, because signing requires a paid Apple Developer
ID, so macOS quarantines it. The launcher clears the quarantine on first run,
with no password and nothing to pay; start that first run from Terminal. See
[INSTALL.md](INSTALL.md#macos).

Full instructions, including what to do when a download is blocked:
**[INSTALL.md](INSTALL.md)**

---

## First run

The application opens on **Data Setup**. The pipeline works from a local copy of
PubMed's annotation data, so nothing can be analysed until that copy exists.
Press **Build** to download and compile it.

Plan for about **50 GB downloaded once** and about **10 GB** kept afterwards. The
download resumes if interrupted, and the archive can be deleted once the
database is built. Choose the drive that holds it on the **Folders** tab.

Once the database exists, analysis runs offline.

---

## What it does

1. **Process** the MeSH vocabulary and build the stop-word set.
2. **Retrieve** an article cohort from a PubMed query, and expand it by citation.
3. **Build** the co-occurrence network, filter it to a consensus subgraph
   (GLF and simulated annealing), and score every term by mean relevancy.
4. **Validate** against a curated ground truth, with permutation nulls and
   bootstrap confidence intervals.
5. **Draw** the figures, including the flow between the strata assigned to the
   terms. On an Adverse Outcome Pathway project that flow runs from stressor to
   adverse outcome.

Each stage runs on its own, from the application or the command line:

```
mpn-pipeline --step network
mpn
mpn-uninstall --list
```

A curated reference corpus ships with the program (the OECD AOP 40 allergic
contact dermatitis set), so the figures can be reproduced before any retrieval.
Tick **Use bundled reference data** on the Search tab to use it.

---

## Documentation

| | |
| --- | --- |
| **[INSTALL.md](INSTALL.md)** | Installing, updating and removing, on all three platforms. |
| **[HELP.md](HELP.md)** | How the pipeline works, every setting, the outputs, and troubleshooting. |
| **[COMMAND-LINE.md](COMMAND-LINE.md)** | Running the pipeline from a shell, and working on the source. |
| **[packaging/README.md](packaging/README.md)** | Building the releases. For maintainers. |

---

## Citing this work

[HELP.md](HELP.md#citation) gives the citation for this software and for the
methods it implements. The bundled ground truth is derived from the OECD Adverse
Outcome Pathway programme's case study on skin sensitisation (AOP 40), which is
cited there as well.

## Licence

MIT — see [LICENSE](LICENSE).
