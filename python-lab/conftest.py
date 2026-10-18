"""Puts every weekNN/ folder on the import path so later weeks can import earlier ones."""
import sys
from pathlib import Path

for folder in sorted(Path(__file__).parent.glob("week*")):
    sys.path.insert(0, str(folder))
