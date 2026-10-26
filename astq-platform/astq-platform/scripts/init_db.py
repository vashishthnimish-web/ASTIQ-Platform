"""Create tables and seed the suite registry:  python scripts/init_db.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db


def main() -> None:
    app = create_app()
    with app.app_context():
        db.create_all()
        from scripts.seed_suites import seed

        created = seed()
        print(f"Database ready at {app.config['SQLALCHEMY_DATABASE_URI']} ({created} suites added)")


if __name__ == "__main__":
    main()
