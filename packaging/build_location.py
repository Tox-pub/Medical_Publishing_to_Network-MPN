# -*- coding: utf-8 -*-
"""
build_location.py - the one place a build is allowed to write.

Every build script resolves its output directory here, so they cannot disagree.
The answer is enforced rather than preferred:

    D:\\mpn_build

If D: is not attached, the build STOPS rather than choosing somewhere else. The
obvious fallback is the project folder, which is cloud-synced, so a build there
would upload half a gigabyte of reproducible output.

--out overrides for one run and MESH_BUILD_OUT for a session. CI uses the
environment variable, because a runner has no D: and must write into its
workspace.
"""

import os
import sys

#: The only location a build writes to unless it is told otherwise.
BUILD_ROOT = r'D:\mpn_build'

_ENV = 'MESH_BUILD_OUT'


def _writable(path):
    """Can this actually be written to? Existing is not the same thing.

    D: on another machine may be a read-only optical drive or a disconnected
    network mapping, and a build that discovered that halfway through would
    leave a half-assembled tree behind.
    """
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, '.write_test')
        with open(probe, 'w') as fh:
            fh.write('')
        os.remove(probe)
        return True
    except OSError:
        return False


def resolve(explicit=None, purpose='build'):
    """Where to write, or exit saying why not.

    `explicit` is a --out the user passed; it is honoured without question,
    because naming a path is an answer, not a guess.
    """
    if explicit:
        if not _writable(explicit):
            sys.exit(f'--out is not writable: {explicit}')
        return os.path.abspath(explicit)

    env = os.environ.get(_ENV)
    if env:
        if not _writable(env):
            sys.exit(f'{_ENV} is not writable: {env}')
        return os.path.abspath(env)

    if _writable(BUILD_ROOT):
        return BUILD_ROOT

    sys.exit(
        f'\nThe {purpose} needs {BUILD_ROOT}, and it is not available.\n\n'
        f'  D: is where every artefact for this project is built. Attach it and\n'
        f'  run this again.\n\n'
        f'  Nothing was written.\n\n'
        f'  To build somewhere else on purpose:\n'
        f'      --out <path>            for this run\n'
        f'      set {_ENV}=<path>   for the session (CI uses this)\n')
