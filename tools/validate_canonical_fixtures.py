import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conformance.fixtures import discover_fixtures, validate_fixture

if __name__ == "__main__":
    failures = []
    fixtures = discover_fixtures()
    if not fixtures:
        raise SystemExit("no canonical fixtures discovered")
    for fixture in fixtures:
        errors = validate_fixture(fixture)
        if errors:
            failures.append((fixture.fixture_id, errors))
        print(fixture.fixture_id)
    if failures:
        raise SystemExit(str(failures))
