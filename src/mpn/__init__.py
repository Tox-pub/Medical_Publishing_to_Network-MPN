# -*- coding: utf-8 -*-
"""
mpn - desktop front-end for the mesh_aop pipeline.

A window over the same configuration and the same pipeline steps the
`mpn-pipeline` command exposes. Settings are read from and written back to
mesh_config.json, and each step runs in a child process so a long analysis
cannot block the interface.

Entry points
    mpn                 console script (see pyproject.toml)
    python -m mpn       equivalent
"""

__version__ = '3.2.10'
__all__ = ['app', 'runner', 'settings_schema']
