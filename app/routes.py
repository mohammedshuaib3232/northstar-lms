from datetime import date
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Announcement, Assignment, Course, Material, Submission
from app.storage import download_response, save_upload

bp = Blueprint("main", __name__)


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@bp.route("/")
def index():
    courses = Course.query.order_by(Course.title).limit(6).all()
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
    return render_template("index.html", courses=courses, announcements=announcements)


@bp.route("/dashboard")
@login_required
def dashboard():
    courses = Course.query.order_by(Course.title).all()
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    submissions = Submission.query.filter_by(student_id=current_user.id).order_by(Submission.submitted_at.desc()).all()
    return render_template("dashboard.html", courses=courses, announcements=announcements, submissions=submissions)


@bp.route("/courses/<int:course_id>")
def course_detail(course_id):
    course = db.get_or_404(Course, course_id)
    return render_template("course.html", course=course)


@bp.route("/materials/<int:material_id>/download")
@login_required
def material_download(material_id):
    material = db.get_or_404(Material, material_id)
    return download_response(material.storage_key, material.original_name)


@bp.route("/assignments/<int:assignment_id>/submit", methods=["POST"])
@login_required
def submit_assignment(assignment_id):
    if current_user.is_admin:
        abort(403)
    assignment = db.get_or_404(Assignment, assignment_id)
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        flash("Choose a file to submit.", "error")
    else:
        try:
            key, original, _ = save_upload(uploaded, f"submissions/{assignment_id}/{current_user.id}")
            submission = Submission(assignment_id=assignment.id, student_id=current_user.id, storage_key=key, original_name=original)
            db.session.add(submission)
            db.session.commit()
            flash("Assignment submitted.", "success")
        except ValueError as exc:
            flash(str(exc), "error")
    return redirect(url_for("main.course_detail", course_id=assignment.course_id))


@bp.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin/index.html", courses=Course.query.order_by(Course.created_at.desc()).all(), submissions=Submission.query.order_by(Submission.submitted_at.desc()).limit(30).all())


@bp.route("/admin/courses", methods=["POST"])
@admin_required
def create_course():
    title = request.form.get("title", "").strip()
    code = request.form.get("code", "").strip().upper()
    if len(title) < 3 or not code or Course.query.filter_by(code=code).first():
        flash("Provide a course title and a unique course code.", "error")
    else:
        course = Course(title=title, code=code, description=request.form.get("description", "").strip(), instructor=current_user.display_name)
        db.session.add(course)
        db.session.commit()
        flash("Course created.", "success")
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/courses/<int:course_id>/materials", methods=["POST"])
@admin_required
def add_material(course_id):
    course = db.get_or_404(Course, course_id)
    title = request.form.get("title", "").strip()
    uploaded = request.files.get("file")
    if not title or not uploaded or not uploaded.filename:
        flash("Provide a title and choose a file.", "error")
    else:
        try:
            key, original, content_type = save_upload(uploaded, f"materials/{course.id}")
            db.session.add(Material(course_id=course.id, title=title, original_name=original, storage_key=key, content_type=content_type))
            db.session.commit()
            flash("Learning material uploaded.", "success")
        except ValueError as exc:
            flash(str(exc), "error")
    return redirect(url_for("main.course_detail", course_id=course.id))


@bp.route("/admin/courses/<int:course_id>/assignments", methods=["POST"])
@admin_required
def create_assignment(course_id):
    course = db.get_or_404(Course, course_id)
    title = request.form.get("title", "").strip()
    instructions = request.form.get("instructions", "").strip()
    due = request.form.get("due_date", "").strip()
    if not title or not instructions:
        flash("Assignment title and instructions are required.", "error")
    else:
        try:
            parsed_due = date.fromisoformat(due) if due else None
        except ValueError:
            flash("Enter a valid due date.", "error")
            return redirect(url_for("main.course_detail", course_id=course.id))
        db.session.add(Assignment(course_id=course.id, title=title, instructions=instructions, due_date=parsed_due))
        db.session.commit()
        flash("Assignment published.", "success")
    return redirect(url_for("main.course_detail", course_id=course.id))


@bp.route("/admin/announcements", methods=["POST"])
@admin_required
def create_announcement():
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    if not title or not body:
        flash("Announcement title and message are required.", "error")
    else:
        db.session.add(Announcement(title=title, body=body, author_id=current_user.id))
        db.session.commit()
        flash("Announcement posted.", "success")
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/submissions/<int:submission_id>/download")
@admin_required
def download_submission(submission_id):
    submission = db.get_or_404(Submission, submission_id)
    return download_response(submission.storage_key, submission.original_name)
