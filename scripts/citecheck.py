#!/usr/bin/env python3
"""Standalone script to check citations in a paper."""

import sys
from pathlib import Path

# Add parent directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from citecheck.cli import main

if __name__ == "__main__":
    main()
