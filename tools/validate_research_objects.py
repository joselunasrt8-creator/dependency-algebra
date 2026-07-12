import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conformance.research_objects.registry import discover_handlers, _HANDLERS

if __name__ == "__main__":
    discover_handlers()
    if not _HANDLERS:
        raise SystemExit("no research objects registered")
    for research_object_id in sorted(_HANDLERS):
        print(research_object_id)
