"""Insert missing suite definitions:  python scripts/seed_suites.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def seed() -> int:
    from app.services.suite_service import seed_suites

    return seed_suites()


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        print(f"{seed()} suites added")
