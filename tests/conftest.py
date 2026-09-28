import pytest

from app import create_app, db
from app.models import User


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}", "UPLOAD_FOLDER": str(tmp_path / "uploads"), "SECRET_KEY": "test-secret"})
    with app.app_context():
        db.create_all()
        admin = User(email="admin@example.test", display_name="Admin", role="admin")
        admin.set_password("correct horse battery staple")
        db.session.add(admin)
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
