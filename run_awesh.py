#!/usr/bin/env python3
"""
Direct runner for awesh - bypasses console script issues
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path so awesh can be imported as a package
parent_path = Path(__file__).parent
sys.path.insert(0, str(parent_path))

# Import and run awesh
from awesh.main import cli_main

if __name__ == "__main__":
    cli_main()
