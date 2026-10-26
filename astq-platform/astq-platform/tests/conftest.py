import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    """Fresh app + temp SQLite DB + temp artifact dir; runs are left QUEUED by default."""
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
        "ARTIFACTS_DIR": str(tmp_path / "artifacts"),
        "RUN_DISPATCH": "none",
        "CSRF_ENABLED": True,
        "RUN_TIMEOUT_SECONDS": 60,
    })
    yield application
    from app.extensions import db

    with application.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()
