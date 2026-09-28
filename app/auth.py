from datetime import datetime, timezone
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from urllib.parse import urlsplit
from sqlalchemy import func

from app import db
from app.models import User

auth = Blueprint("auth", __name__)


def _login_throttled(email):
    attempts = session.get("login_attempts", {})
    recent = [ts for ts in attempts.get(email, []) if datetime.now(timezone.utc).timestamp() - ts < 300]
    attempts[email] = recent
    session["login_attempts"] = attempts
    return len(recent) >= 8


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        name = request.form.get("display_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(name) < 2 or len(name) > 80 or "@" not in email or len(password) < 10:
            flash("Enter a name, valid email, and password with at least 10 characters.", "error")
        elif User.query.filter(func.lower(User.email) == email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(display_name=name, email=email, role="student")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Your student account is ready.", "success")
            return redirect(url_for("main.dashboard"))
    return render_template("auth/register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if _login_throttled(email):
            flash("Too many attempts. Wait five minutes, then try again.", "error")
        else:
            user = User.query.filter(func.lower(User.email) == email).first()
            if user and user.check_password(password):
                session.pop("login_attempts", None)
                login_user(user, remember=False)
                next_path = request.args.get("next", "")
                if next_path and urlsplit(next_path).netloc == "" and next_path.startswith("/"):
                    return redirect(next_path)
                return redirect(url_for("main.dashboard"))
            attempts = session.get("login_attempts", {})
            attempts.setdefault(email, []).append(datetime.now(timezone.utc).timestamp())
            session["login_attempts"] = attempts
            flash("Email or password was not recognized.", "error")
    return render_template("auth/login.html")


@auth.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("main.index"))
