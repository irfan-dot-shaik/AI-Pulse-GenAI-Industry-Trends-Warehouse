# =============================================================================
# conftest.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   This file is automatically loaded by pytest before running any tests.
#   It solves a critical problem: Python's import system.
#
# THE PROBLEM:
#   When you run 'pytest tests/' from the project root, pytest needs to
#   import your project modules like 'from config.settings import ...'
#
#   By default, Python only looks for modules in certain directories.
#   Without conftest.py, pytest cannot find 'config', 'ingestion', etc.
#   and will raise: ModuleNotFoundError: No module named 'config'
#
# THE SOLUTION:
#   conftest.py adds the project root to sys.path, which is Python's list
#   of directories to search when you use 'import' or 'from x import y'.
#
# CONCEPT — sys.path:
#   sys.path is a list of folder paths.
#   When Python sees 'import config', it searches each folder in sys.path.
#   Adding the project root means Python will find: AI.NEWS/config/__init__.py
#
# WHY NOT USE pytest.ini alone?
#   pytest.ini sets testpaths and options, but doesn't modify sys.path.
#   conftest.py is the pytest-native way to configure the Python environment.
#
# =============================================================================

import sys
from pathlib import Path

# Add the project root directory to Python's module search path.
# Path(__file__).parent = the folder containing conftest.py = project root
# str(...) converts Path object to string (sys.path expects strings)
project_root = str(Path(__file__).parent)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
