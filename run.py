#!/usr/bin/env python3
"""
FAI 4-Way Formation Skydiving Suite Launcher

Usage:
    python3 run.py              # Startet das Debriefing & Scoring Tool (Standard)
    python3 run.py --3d [CODE]  # Startet den 3D Formation Explorer (z.B. python3 run.py --3d 12)
"""

import sys
import os

# Ensure src/ is in python search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--3d", "-3d", "--formation", "-f"):
        import formation_tool
        sys.argv.pop(1)
        formation_tool.main()
    else:
        import scoring
        scoring.main()

if __name__ == "__main__":
    main()
