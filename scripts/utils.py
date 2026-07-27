"""
Shared utilities for competitive programming scripts.
"""
import os

# Enable ANSI escape codes on Windows 10+ terminals
try:
    os.system('')
except Exception:
    pass

GREEN  = '\033[0;32m'
RED    = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE   = '\033[0;34m'
RESET  = '\033[0m'
