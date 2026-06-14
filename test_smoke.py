"""Smoke tests for LearnMate Core — run: python test_smoke.py"""
import sys
import traceback

FAILURES = []


def _db():
    from database import DatabaseManager

    db = DatabaseManager()
    db.ensure_demo_users()
    return db


def check(name, fn):
    try:
        fn()
        print(f"  OK  {name}")
    except Exception as exc:
        FAILURES.append((name, exc))
        print(f"FAIL  {name}: {exc}")
        traceback.print_exc()


def test_imports():
    import constants  # noqa: F401
    import database  # noqa: F401
    import models  # noqa: F401
    import utils  # noqa: F401
    import quiz_parser  # noqa: F401
    from ui.theme import application_stylesheet  # noqa: F401
    from ui.dashboards import AdminDashboardWidget, DepartmentHeadDashboardWidget
    from ui.employee import EmployeeLearningWidget
    from ui.windows import LoginWindow, MainWindow
    assert len(application_stylesheet()) > 100


def test_auth_all_roles():
    from database import DatabaseManager
    from services import AuthManager

    db = _db()
    auth = AuthManager(db)
    accounts = [
        ("n.makanina@rami-clinic.ru", "admin123", "main_admin"),
        ("i.ivanov@rami-clinic.ru", "manager123", "department_head"),
        ("a.petrova@rami-clinic.ru", "employee123", "employee"),
    ]
    for email, password, role in accounts:
        assert auth.authenticate(email, password), f"login failed: {email}"
        user = auth.get_current_user()
        assert user is not None
        assert user.is_role(role), f"wrong role for {email}"
        auth.logout()


def test_stats_and_reports():
    from database import DatabaseManager
    from services import AuthManager, StatsService, ReportService

    db = _db()
    auth = AuthManager(db)
    auth.authenticate("n.makanina@rami-clinic.ru", "admin123")
    admin = auth.get_current_user()
    stats = StatsService(db)
    report = ReportService(db, stats)

    with db.session_scope() as session:
        summary = stats.get_admin_summary(session)
        assert "learning_count" in summary
        stats.get_department_rows(session)
        stats.get_course_stats(session)
        stats.get_employee_stats(session)
        stats.get_problem_employees(session)

    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "report.csv")
        report.export_admin_report(admin.id, path)
        assert os.path.isfile(path)
        assert os.path.getsize(path) > 0


def test_dept_head_stats():
    from database import DatabaseManager
    from services import AuthManager, StatsService

    db = _db()
    auth = AuthManager(db)
    auth.authenticate("i.ivanov@rami-clinic.ru", "manager123")
    dept_id = auth.get_current_user().department_id
    stats = StatsService(db)

    with db.session_scope() as session:
        stats.get_department_summary(session, dept_id)
        stats.get_course_stats(session, department_id=dept_id)
        stats.get_employee_stats(session, department_id=dept_id)


def test_create_department():
    from database import DatabaseManager
    from services import AuthManager, DepartmentService
    from models import Department

    db = _db()
    auth = AuthManager(db)
    auth.authenticate("n.makanina@rami-clinic.ru", "admin123")
    admin = auth.get_current_user()
    dept_service = DepartmentService(db)

    dept_id = dept_service.create_department(
        admin.id,
        "Тестовое подразделение smoke",
        "Создано автотестом",
    )
    assert dept_id

    with db.session_scope() as session:
        dept = session.query(Department).filter(Department.id == dept_id).first()
        assert dept is not None
        assert dept.name == "Тестовое подразделение smoke"


def test_courses_list():
    from database import DatabaseManager
    from services import AuthManager, CourseService

    db = _db()
    auth = AuthManager(db)
    auth.authenticate("n.makanina@rami-clinic.ru", "admin123")
    admin = auth.get_current_user()
    courses = CourseService(db).list_courses(admin.id)
    assert isinstance(courses, list)


def test_learning_service():
    from database import DatabaseManager
    from services import AuthManager, LearningService

    db = _db()
    auth = AuthManager(db)
    auth.authenticate("a.petrova@rami-clinic.ru", "employee123")
    emp = auth.get_current_user()
    learning = LearningService(db)

    with db.session_scope() as session:
        learning.get_today_tasks(emp.id, db=session)
        learning.get_recommendations(emp.id, db=session)
        learning.get_learning_history(emp.id, db=session)


def test_ui_widgets():
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    from ui.theme import application_stylesheet, FONT_FAMILY
    from PyQt6.QtGui import QFont

    app.setStyle("Fusion")
    app.setStyleSheet(application_stylesheet())
    app.setFont(QFont(FONT_FAMILY, 10))

    from database import DatabaseManager
    from services import (
        AuthManager, UserService, CourseService, AuditService,
        StatsService, ReportService, MaterialService, LearningService,
    )
    from ui.windows import MainWindow

    db = _db()
    auth = AuthManager(db)

    for email, password in [
        ("n.makanina@rami-clinic.ru", "admin123"),
        ("i.ivanov@rami-clinic.ru", "manager123"),
        ("a.petrova@rami-clinic.ru", "employee123"),
    ]:
        auth.authenticate(email, password)
        win = MainWindow(auth, db)
        win.close()
        auth.logout()


def test_quiz_parser():
    from quiz_parser import parse_quiz_text, parse_quiz_file
    import tempfile
    from pathlib import Path

    questions = parse_quiz_text(
        "Вопрос: Тест?\nA) Да\nB) Нет\nОтвет: A\n"
    )
    assert len(questions) == 1
    assert questions[0]["correct_index"] == 0

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
        tmp.write("Вопрос: 2+2?\nA) 3\nB) 4\nОтвет: B\n")
        path = Path(tmp.name)
    try:
        parsed = parse_quiz_file(path)
        assert len(parsed) == 1
    finally:
        path.unlink(missing_ok=True)


def main():
    print("LearnMate Core smoke tests\n")
    check("imports", test_imports)
    check("auth all roles", test_auth_all_roles)
    check("admin stats & export", test_stats_and_reports)
    check("dept head stats", test_dept_head_stats)
    check("create department", test_create_department)
    check("courses list", test_courses_list)
    check("learning service", test_learning_service)
    check("quiz parser", test_quiz_parser)
    check("UI widgets (all roles)", test_ui_widgets)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} test(s)")
        for name, exc in FAILURES:
            print(f"  - {name}: {exc}")
        sys.exit(1)
    print("All smoke tests passed.")


if __name__ == "__main__":
    main()
