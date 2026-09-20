# -*- coding: utf-8 -*-
"""
field_rules.py - what every setting is allowed to be, checked in one place.

Everything that can be checked without the databases is checked the moment a
run is asked for. A mistyped field then costs a second instead of the hours it
used to take to reach the step that reads it, and every mistake is reported at
once rather than one per attempt.

The window and the command line both call `problems()`, so they cannot
disagree about what is acceptable. Every line it returns has one shape:

    Citation generations: whole number, 1 to 5. Input: "abc".

Two kinds of mistake are deliberately NOT here, because nothing can know them
before the run: a stop-word term that matches no MeSH heading, and a target
node that is not in the network. Both need a vocabulary or a network that does
not exist yet, and both are reported where they are read.
"""

import os
import re

from . import vocabulary

PREFIX_RE = re.compile(r'^[A-Za-z0-9_-]{1,40}$')
DATE_RE = re.compile(r'^\d{4}(/\d{2}(/\d{2})?)?$')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
API_KEY_RE = re.compile(r'^[A-Za-z0-9]{20,64}$')

SORT_METRICS = ('F1', 'Linear')
FIGURE_FORMATS = ('jpeg', 'jpg', 'tif', 'tiff', 'png', 'svg', 'pdf')
CENTRALITIES = tuple(
    f'{p}{c}_centrality' for p in ('', 'MRS_')
    for c in ('pagerank', 'betweenness', 'eigenvector',
              'pagerank_subgraph', 'betweenness_subgraph',
              'eigenvector_subgraph'))
COLOUR_METRICS = CENTRALITIES + (
    'adjusted_node_weight', 'article_count', 'degree',
    'clustering_coefficient', 'major_topic_proportion',
    'article_count_rank_normalized', 'rank_norm_mean_cit',
    'rank_norm_median_cit', 'rank_norm_total_cit')

# The steps that write nothing named after a project, and so need no project
# name. Kept beside the prefix rule rather than in the CLI, so both agree.
SHARED_STEPS = ('baseline', 'process')
# The steps that send a query to PubMed, and so need something to search for.
RETRIEVING_STEPS = ('all', 'data_ops')


def _text(value):
    return '' if value is None else str(value).strip()


def split_list(value):
    """Entries of a semicolon-delimited field, with optional quotes removed.

    Semicolons rather than commas because MeSH headings contain commas as a
    matter of course - "Dermatitis, Allergic Contact" is one heading. Quotes
    around an entry are accepted and dropped: they read as natural punctuation
    for a list of names, and an entry kept with its quotes matches nothing.
    """
    out = []
    for part in _text(value).split(';'):
        part = part.strip()
        if len(part) >= 2 and part[0] == part[-1] and part[0] in '"\'':
            part = part[1:-1].strip()
        if part:
            out.append(part)
    return out


def _whole(value, low, high=None):
    """A whole number in range, or what it should have been.

    A decimal is refused rather than rounded: 5.7 generations is not a typo
    with an obvious intention, and silently using 5 would be a different run
    from the one that was asked for.

    `high=None` means there is no upper limit. Where a larger number only costs
    the person who typed it their own time - iterations, resamples - there is
    nothing to protect them from.
    """
    expected = (f'whole number, {low} or more' if high is None
                else f'whole number, {low} to {high}')
    text = _text(value)
    if not re.fullmatch(r'-?\d+', text):
        return expected
    number = int(text)
    if number < low or (high is not None and number > high):
        return expected
    return None


def _decimal(value, low, high=None, exclusive=False):
    text = _text(value)
    try:
        number = float(text)
    except (TypeError, ValueError):
        return _decimal_expected(low, high, exclusive)
    if exclusive:
        if number <= low or (high is not None and number >= high):
            return _decimal_expected(low, high, exclusive)
    elif number < low or (high is not None and number > high):
        return _decimal_expected(low, high, exclusive)
    return None


def _decimal_expected(low, high, exclusive):
    if high is None:
        return f'number above {low:g}' if exclusive else f'number, {low:g} or more'
    if exclusive:
        return f'number above {low:g} and below {high:g}'
    return f'number, {low:g} to {high:g}'


def _date(value):
    if not _text(value):
        return None                       # empty means the widest window
    return None if DATE_RE.match(_text(value)) else 'date as YYYY/MM/DD, or empty'


def _writable(path):
    """Can this folder be used? Creating it is part of the answer."""
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, '.write_test')
        with open(probe, 'w'):
            pass
        os.remove(probe)
        return True
    except OSError:
        return False


def problems(config, step='all'):
    """Every setting that would stop or spoil this run, as finished lines.

    `config` is a MeshConfig, so values arrive resolved: a date written TODAY
    is checked as the date it becomes, which is what the pipeline will use.
    """
    found = []

    def report(label, expected, value):
        shown = '' if value is None else str(value)
        found.append(f'{label}: {expected}. Input: "{shown}".')

    def check(label, section, key, test):
        value = config.get(section, key)
        expected = test(value)
        if expected:
            report(label, expected, value)
        return expected is None

    params = config.params
    flags = params.get('control_flags', {})
    reference = bool(flags.get('use_reference_data'))

    # -- Search ---------------------------------------------------------
    # The reference corpus supplies its own name, term and dates, so none of
    # them is the user's to get wrong while it is ticked.
    if not reference:
        prefix = _text(flags.get('custom_file_prefix'))
        if step not in SHARED_STEPS or prefix:
            if not PREFIX_RE.match(prefix):
                report('Project prefix',
                       'letters, digits, hyphen or underscore, up to 40 characters',
                       prefix)
        if step in RETRIEVING_STEPS and not _text(
                config.get('search_parameters', 'search_term')):
            report('Search term', 'a PubMed query', '')

    check('Citation generations', 'search_parameters', 'generations_n',
          lambda v: _whole(v, 1, 5))
    start_ok = check('Start date', 'search_parameters', 'start_date', _date)
    end_ok = check('End date', 'search_parameters', 'end_date', _date)
    if start_ok and end_ok:
        start = _text(config.get('search_parameters', 'start_date'))
        end = _text(config.get('search_parameters', 'end_date'))
        if start and end and start > end:
            report('Start date', f'a date on or before the end date, {end}', start)

    # -- Folders --------------------------------------------------------
    for key, label in (('data_dir', 'Data folder'),
                       ('results_dir', 'Results folder'),
                       ('input_dir', 'Input folder'),
                       ('output_dir', 'Output folder'),
                       ('etl_workspace_dir', 'Database build workspace')):
        folder = _text(params.get('directories', {}).get(key))
        if folder and not _writable(folder):
            report(label, 'a folder that can be created and written to', folder)

    # -- Stop words -----------------------------------------------------
    # TREE_NAMES is keyed by letter; TREES is (letter, name) pairs, and testing
    # membership against the pairs said every valid letter was unknown.
    letters = _text(params.get('stop_words', {}).get('excluded_trees'))
    unknown = [c for c in re.split(r'[;,\s]+', letters.upper()) if c
               and c not in vocabulary.TREE_NAMES]
    if unknown:
        report('Excluded MeSH trees',
               'letters of the sixteen MeSH trees (A to N, V, Z)',
               ', '.join(unknown))

    # -- Credentials ----------------------------------------------------
    email = _text(params.get('credentials', {}).get('entrez_email'))
    if email and not EMAIL_RE.match(email):
        report('NCBI e-mail', 'an e-mail address, or empty', email)
    key_text = _text(params.get('credentials', {}).get('entrez_api_key'))
    if key_text and not API_KEY_RE.match(key_text):
        report('NCBI API key', 'the key from your NCBI account, or empty', key_text)

    # -- Analysis -------------------------------------------------------
    check('Random seed', 'analysis_parameters', 'random_seed',
          lambda v: _whole(v, 0))
    check('Context start date', 'analysis_parameters', 'context_start_date', _date)
    check('Context end date', 'analysis_parameters', 'context_end_date', _date)
    check('Betweenness samples', 'analysis_parameters', 'betweenness_k_samples',
          lambda v: _whole(v, 1, 100000))
    check('Eigenvector iterations', 'analysis_parameters', 'eigenvector_max_iter',
          lambda v: _whole(v, 1, 100000))
    check('Eigenvector tolerance', 'analysis_parameters', 'eigenvector_tol',
          lambda v: _decimal(v, 0, 1, exclusive=True))

    # -- Network --------------------------------------------------------
    check('Lambda', 'network_parameters', 'lambda_val',
          lambda v: _decimal(v, 0, exclusive=True))
    weights = (params.get('network_parameters', {})
               .get('node_weight_factors', {}) or {})
    total, weights_ok = 0.0, True
    for key, label in (('centrality', 'Centrality weight'),
                       ('article_rank', 'Article rank weight'),
                       ('rank_median_cit', 'Median citations weight'),
                       ('rank_total_cit', 'Total citations weight')):
        expected = _decimal(weights.get(key), 0, 1)
        if expected:
            report(label, expected, weights.get(key))
            weights_ok = False
        else:
            total += float(_text(weights.get(key)))
    if weights_ok and abs(total - 1.0) > 1e-6:
        report('Node weight factors', 'four values totalling 1.00', f'{total:g}')

    # -- Consensus ------------------------------------------------------
    check('Target edge count', 'simulation_parameters', 'target_num_edges',
          lambda v: _whole(v, 10))
    # No upper limit on either search. A larger number costs the person who
    # typed it their own time and nobody else's.
    check('GLF iterations', 'simulation_parameters', 'glf_iterations',
          lambda v: _whole(v, 1000))
    check('SA iterations', 'simulation_parameters', 'sa_iterations',
          lambda v: _whole(v, 1000))
    check('SA start temperature', 'simulation_parameters', 'sa_temp_start',
          lambda v: _decimal(v, 0, exclusive=True))
    check('SA cooling rate', 'simulation_parameters', 'sa_cooling_rate',
          lambda v: _decimal(v, 0, 1, exclusive=True))

    # -- Secondary ------------------------------------------------------
    check('Export limit', 'secondary_analysis', 'export_limit',
          lambda v: _whole(v, 1))
    check('ARS weight', 'secondary_analysis', 'linear_weight_ars',
          lambda v: _decimal(v, 0, 1))
    metric = _text(config.get('secondary_analysis', 'sort_metric'))
    if metric and metric.lower() not in [m.lower() for m in SORT_METRICS]:
        report('Sort metric', 'F1 or Linear', metric)
    for entry in split_list(config.get('secondary_analysis', 'target_edges')):
        if ' - ' not in entry:
            report('Target edges', 'pairs written as NodeA - NodeB', entry)
            break
    if params.get('secondary_analysis', {}).get('compare_networks') and not split_list(
            config.get('secondary_analysis', 'comparison_networks')):
        report('Networks to compare', 'at least one network file', '')

    # -- Benchmark ------------------------------------------------------
    ground_truth = _text(config.get('benchmark', 'ground_truth_csv'))
    if ground_truth and not os.path.isfile(ground_truth):
        report('Ground truth file', 'a file that exists, or empty to search for one',
               ground_truth)
    check('Validation bootstraps', 'benchmark', 'validation_report_n_boot',
          lambda v: _whole(v, 1))
    check('Background pool', 'benchmark', 'background_pool_size',
          lambda v: _whole(v, 100))
    check('Minimum articles per node', 'benchmark', 'min_articles_per_node',
          lambda v: _whole(v, 1))
    check('Bootstrap resamples', 'benchmark', 'n_boot', lambda v: _whole(v, 1))
    check('Permutations', 'benchmark', 'n_perm', lambda v: _whole(v, 1))
    weight_key = _text(config.get('benchmark', 'network_validation_weight_key'))
    if weight_key and weight_key not in CENTRALITIES:
        report('Validation weight', 'one of the centralities offered', weight_key)

    # -- Figures --------------------------------------------------------
    check('Figure resolution', 'viz_parameters', 'figure_dpi',
          lambda v: _whole(v, 72, 1200))
    formats = [f.lower() for f in re.split(r'[;,\s]+',
                                           _text(config.get('viz_parameters',
                                                            'figure_formats')))
               if f]
    bad = [f for f in formats if f not in FIGURE_FORMATS]
    if bad:
        report('Figure formats', 'jpeg, tif, png, svg or pdf', ', '.join(bad))
    colour = _text(config.get('viz_parameters', 'network_color_metric'))
    if colour and colour not in COLOUR_METRICS:
        report('Network colour metric', 'one of the metrics offered', colour)

    return found
