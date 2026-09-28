from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="student")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    code = db.Column(db.String(24), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    instructor = db.Column(db.String(100), nullable=False, default="Course team")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    materials = db.relationship("Material", backref="course", cascade="all, delete-orphan")
    assignments = db.relationship("Assignment", backref="course", cascade="all, delete-orphan")


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False, index=True)
    title = db.Column(db.String(140), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(500), nullable=False, unique=True)
    content_type = db.Column(db.String(120), nullable=False, default="application/octet-stream")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False, index=True)
    title = db.Column(db.String(140), nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    submissions = db.relationship("Submission", backref="assignment", cascade="all, delete-orphan")


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    storage_key = db.Column(db.String(500), nullable=False, unique=True)
    original_name = db.Column(db.String(255), nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    student = db.relationship("User")


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    author = db.relationship("User")
