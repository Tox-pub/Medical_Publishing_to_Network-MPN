# -*- coding: utf-8 -*-
"""
guides.py - the written instructions the program leaves next to its files.

Two moments in this pipeline leave someone holding a file and no context: the
run that pauses for AOP annotation, and the master database that took a night to
build. Both are places where the explanation is given once, on a console that is
closed by the time it matters - the annotation pause can sit for days, and nobody
reads a build log a month later when the database will not open.

So the instructions are written to disk beside the file they describe, named so
they are the obvious thing to open. The annotation guide is a page - it has a
list of strata and a table of what to do next, and it opens in a browser where
that reads as a document rather than as a wall of fixed-width text. The
database guide stays plain text: it is short, and it is read by someone whose
program will not start.

This module holds that text and nothing else. Its only imports are strata and
mdhtml, both of which are standard-library-only, so it stays cheap enough to
call from the GUI, the CLI, or a bare interpreter.
"""

import os

from .strata import (COLUMN, DEFAULT_ORDER, DEFAULT_ORDER_TEXT, PLACEHOLDER,
                     UNASSIGNED, parse_order)

ANNOTATION_GUIDE_NAME = 'HOW TO ANNOTATE - read me.html'
ANNOTATION_GUIDE_NAME_FALLBACK = 'HOW TO ANNOTATE - read me.txt'
MASTER_DB_GUIDE_NAME = 'HOW TO REBUILD THIS DATABASE - read me.txt'

# Both names, so callers looking for an existing guide find one written by an
# older version - or by a run where the renderer failed - and do not write a
# second copy alongside it.
ANNOTATION_GUIDE_NAMES = (ANNOTATION_GUIDE_NAME, ANNOTATION_GUIDE_NAME_FALLBACK)


def annotation_guide_markdown(annotation_path, strata_order=''):
    """What to do with a run-annotations file, for the file's own folder.

    Written as Markdown and rendered to HTML beside the file. The document has
    a structure worth keeping - a list of strata, a table of what each column
    is - and plain text in a folder is something people skim past.
    """
    order = parse_order(strata_order) or list(DEFAULT_ORDER)
    listed = '\n'.join(f'{i}. {name}' for i, name in enumerate(order, 1))
    is_default = order == list(DEFAULT_ORDER)
    example = '' if not is_default else (
        '\nThese seven are the default because MPN was built for adverse '
        'outcome pathways, and they are the levels of one: a stressor acts at '
        'the molecular level, which propagates through cell, tissue and organ '
        'to an adverse outcome. They are an example, not a requirement. Replace '
        'them with organ systems, exposure routes, study designs, or whatever '
        'grouping the research question uses.\n')

    return f"""\
# The run is paused for annotation

Nothing has gone wrong. The pipeline built and scored the network, then stopped
on purpose: the next step needs a judgement the program cannot make.

## What is needed

Every MeSH term in the final network is assigned to a **stratum**: one of the
groups chosen to divide the network. Which groups to use, and which term belongs
in which, is a decision for the annotator. The program does not check the scheme
against anything.

## The file to edit

`{annotation_path}`

One row per MeSH term. Fill in the `{COLUMN}` column. The file is a
semicolon-delimited CSV; open it in Excel, LibreOffice or a text editor.

**Keep the semicolons.** MeSH headings contain commas as a matter of course
("Dermatitis, Allergic Contact"), which is why this file does not use commas as
separators. When a spreadsheet offers to save as "CSV (comma delimited)",
decline and keep the original format.

## The strata this project expects

{listed}
{example}
Any name entered is valid. A stratum missing from the list above still appears
in the figures, added at the end of the order. Spelling and capitalisation are
taken literally, so `Molecular` and `molecular` are two different strata, which
is usually a typo.

To change the order the figures use, set **Strata order** in Settings. That
setting controls order only; it never restricts what may be entered here.

### Terms without a stratum

Two values mark a term with no stratum, and they mean different things:

| Value | Meaning |
| :--- | :--- |
| `{PLACEHOLDER}` | Not yet reviewed. Every row starts here. |
| `{UNASSIGNED}` | Reviewed, and belongs to none of the groups. |

The distinction serves the annotator, not the program. It separates terms
already decided from terms not yet reached, which makes it practical to work
through a long file over several sittings.

**The figures treat both as one.** Both stay in the network and in every
topological figure, and both are left out of the figures that show strata. An
unfinished file therefore draws the same picture as a finished one in which
those terms were judged not to belong. Check the counts in the run log before
drawing conclusions from a sparse figure.

## Before starting, if another project has been annotated

The master annotations library remembers the stratum given to every MeSH term,
so no term is annotated twice. That saves work when two projects share a scheme
and **misleads when they do not**: a term labelled `Molecular` in an AOP project
arrives pre-filled as `Molecular` in a project organised by organ system.

The library is shared by every project and merging into it is permanent. When
this project uses a different scheme from the previous one, read the file
through by hand before running the figures, rather than trusting what is already
in the column.

## When finished

Save the file, then run the figures step:

| Where | Action |
| :--- | :--- |
| In MPN | Run → Step 4 — Figures |
| In a terminal | `python -m mesh_aop.cli --step viz` |

Nothing before that step is recomputed, so this is quick. Edit the file and
re-run the figures as often as needed.

## To skip annotation

Turn off **Pause for strata annotation** on the Search tab of Settings. The run
then completes unattended with every term left `{UNASSIGNED}`. The network, the
scores, the benchmark and the topological figures all remain valid; only the
figures that show strata lose their meaning, because no grouping is left in
them to show.

---

Written automatically when the run paused. Safe to delete.
"""


def master_db_guide_text(db_path, data_dir='', workspace_dir=''):
    """How the master annotation database is built, kept beside the database."""
    where = os.path.dirname(db_path) or data_dir
    return f"""\
================================================================================
THE MASTER ANNOTATION DATABASE
MPN - what this file is, and how to rebuild it
================================================================================

    {db_path}

WHAT IT IS
    A local copy of PubMed's MeSH annotations: for every article, its publication
    date and its subject headings. Every other step reads it. It is built once
    and reused by every run.

DO NOT DELETE IT WITHOUT CAUSE
    Building it downloads about 50 GB from the NLM and compiles it into a
    database of about 10 GB. That takes several hours and, on a slow connection,
    most of a day. It is by far the longest operation in the program.

    The downloaded archives, by contrast, ARE safe to delete once the database
    exists. The Data Setup screen has a button for that.

HOW TO REBUILD IT
    In MPN:
        Database -> Data setup, then press Build next to "Master annotation
        database". If a damaged database is present, tick the option to delete
        it first.

    In a terminal:
        python -m mesh_aop.cli --step baseline --build-database

        Add --skip-baseline-download to compile from archives already on disk,
        --with-updates to include the daily files published since the baseline,
        and --rebuild-corrupt to delete an unreadable database before starting.

IF IT WILL NOT OPEN
    A build interrupted by a power cut, a full disk or a machine that hibernated
    can leave the database unreadable. The program checks it before every run
    and reports damage plainly instead of failing halfway through a long step.

    Run Tools -> Check and repair files in MPN. It reports what is damaged,
    offers to remove it, and names the step to resume from. Only the master
    database has to be rebuilt from scratch; everything else is derived and
    regenerates in minutes.

    A full disk is the usual cause. The build needs room for the archives, the
    database, and a working copy of the database at the same time. If this drive
    is short of space, set a different workspace under Settings -> Folders ->
    "Database build workspace"{f' (currently {workspace_dir})' if workspace_dir else ''}.

WHAT ELSE LIVES HERE
    {where}

    Downloaded PubMed archives, the per-project PMID databases, and this file.
    Everything here can be rebuilt; none of it is analysis output. Results are
    stored elsewhere, so clearing this folder never destroys an analysis, only
    the time needed to download it all again.

================================================================================
Written automatically by MPN. Safe to delete; it will come back.
================================================================================
"""


def _write(path, text):
    """Write a guide, returning its path, or None if it could not be written.

    A guide is a courtesy. Failing to write one must never interrupt whatever
    the program was actually doing.
    """
    try:
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)
        return path
    except OSError:
        return None


def write_annotation_guide(annotation_path, config=None, strata_order=''):
    """Drop the annotation instructions beside the file to be annotated.

    Written as HTML so the browser opens it. If rendering fails for any reason
    the Markdown goes out under a .txt name instead - it is readable either
    way, and a guide that does not appear is worse than an unstyled one.
    """
    folder = os.path.dirname(os.path.abspath(annotation_path))
    body = annotation_guide_markdown(os.path.abspath(annotation_path),
                                     strata_order=strata_order)
    try:
        from . import mdhtml
        page = mdhtml.render_page(body, 'How to annotate - MPN')
    except Exception:                                              # noqa: BLE001
        return _write(os.path.join(folder, ANNOTATION_GUIDE_NAME_FALLBACK), body)
    return _write(os.path.join(folder, ANNOTATION_GUIDE_NAME), page)


def write_master_db_guide(db_path, workspace_dir=''):
    """Drop the rebuild instructions beside the master database.

    Written next to where the database belongs, whether or not it exists yet -
    someone looking at an empty data folder and wondering what goes in it is
    exactly the person this is for.
    """
    folder = os.path.dirname(os.path.abspath(db_path))
    return _write(os.path.join(folder, MASTER_DB_GUIDE_NAME),
                  master_db_guide_text(os.path.abspath(db_path),
                                       workspace_dir=workspace_dir))
