import os
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "local-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///lms.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", str(Path(app.instance_path) / "uploads")),
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH", 50 * 1024 * 1024)),
        STORAGE_BACKEND=os.getenv("STORAGE_BACKEND", "local"),
        S3_BUCKET=os.getenv("S3_BUCKET", ""),
        AWS_REGION=os.getenv("AWS_REGION", "ap-south-1"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
        REMEMBER_COOKIE_HTTPONLY=True,
    )
    if test_config:
        app.config.update(test_config)
    if os.getenv("APP_ENV", "development") == "production" and app.config["SECRET_KEY"] == "local-only-change-me":
        raise RuntimeError("Set a strong SECRET_KEY before starting in production.")
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    csrf.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes import bp
    app.register_blueprint(bp)
    from app.auth import auth
    app.register_blueprint(auth)

    @app.cli.command("init-db")
    def init_db():
        """Create application tables."""
        db.create_all()
        print("Database tables created.")

    @app.cli.command("create-admin")
    def create_admin():
        """Create an administrator without a public admin signup route."""
        import getpass
        from app.models import User

        email = os.getenv("ADMIN_EMAIL") or input("Admin email: ").strip().lower()
        password = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Admin password (12+ characters): ")
        if len(password) < 12:
            raise SystemExit("Admin password must be at least 12 characters.")
        if User.query.filter_by(email=email).first():
            raise SystemExit("That email already exists.")
        user = User(email=email, display_name=email.split("@", 1)[0], role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Administrator created: {email}")

    return app
