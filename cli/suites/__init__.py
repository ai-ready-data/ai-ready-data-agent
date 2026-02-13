"""Test suite definitions — auto-discovered from YAML files in definitions/.

On import, scans agent/suites/definitions/ for *.yaml suite files and registers
them via the loader.
"""

from agent.suites.loader import load_all_definitions

load_all_definitions()
