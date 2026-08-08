#!/usr/bin/env python3
from pathlib import Path
import runpy
import sys

script = Path(__file__).with_name('apply_stable_admin_interactions_v2.py')
sys.argv[0] = str(script)
runpy.run_path(str(script), run_name='__main__')
