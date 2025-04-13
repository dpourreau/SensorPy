"""
Configuration file for pytest.

This file is automatically loaded by pytest and helps with test configuration.
It adds the project root directory to the Python path, allowing imports from the sensorpy directory.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
