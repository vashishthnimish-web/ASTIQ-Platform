"""Enable or disable a registered suite:

    python scripts/set_suite_enabled.py performance_baseline on
    python scripts/set_suite_enabled.py performance_baseline off
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db
from app.services.suite_service import get_suite


def main(argv) -> int:
    if len(argv) != 3 or argv[2] not in ("on", "off"):
        print(__doc__)
        return 2
    app = create_app()
    with app.app_context():
        suite = get_suite(argv[1])
        if suite is None:
            print(f"Unknown suite '{argv[1]}'")
            return 1
        suite.enabled = argv[2] == "on"
        db.session.commit()
        print(f"{suite.suite_key}: enabled={suite.enabled}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
