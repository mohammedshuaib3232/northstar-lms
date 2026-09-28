from app.models import Course


def test_homepage_and_student_registration(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Make room for" in response.data

    response = client.post(
        "/register",
        data={
            "display_name": "A Student",
            "email": "student@example.test",
            "password": "a strong password",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome back, A Student" in response.data


def test_admin_can_create_course_and_student_can_view(app, client):
    client.post(
        "/login",
        data={"email": "admin@example.test", "password": "correct horse battery staple"},
    )
    response = client.post(
        "/admin/courses",
        data={
            "title": "Cloud Foundations",
            "code": "CLD-101",
            "description": "A practical introduction.",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        course = Course.query.filter_by(code="CLD-101").one()
        course_url = f"/courses/{course.id}"

    client.post("/logout")
    client.post(
        "/register",
        data={
            "display_name": "Learner",
            "email": "learner@example.test",
            "password": "long student pass",
        },
    )
    response = client.get(course_url)
    assert response.status_code == 200
    assert b"Cloud Foundations" in response.data


def test_student_cannot_access_admin(client):
    client.post(
        "/register",
        data={
            "display_name": "Learner",
            "email": "learner@example.test",
            "password": "long student pass",
        },
    )
    assert client.get("/admin").status_code == 403


def test_login_rejects_wrong_password(client):
    client.post(
        "/register",
        data={
            "display_name": "Learner",
            "email": "learner@example.test",
            "password": "long student pass",
        },
    )
    client.post("/logout")
    response = client.post(
        "/login",
        data={"email": "learner@example.test", "password": "incorrect"},
        follow_redirects=True,
    )
    assert b"Email or password was not recognized" in response.data
