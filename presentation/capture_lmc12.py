"""Capture LearnMate Core LMC/v1.2 — widgets only (faster, no MainWindow)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

OUTPUT_DIR = Path(__file__).resolve().parent / "screenshots-lmc12"


def setup():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    from ui.theme import application_stylesheet, FONT_FAMILY

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(application_stylesheet())
    app.setFont(QFont(FONT_FAMILY, 10))
    return app


def polish(w):
    from PyQt6.QtWidgets import QWidget

    w.style().unpolish(w)
    w.style().polish(w)
    for c in w.findChildren(QWidget):
        c.style().unpolish(c)
        c.style().polish(c)


def grab(app, widget, name, w, h):
    widget.resize(w, h)
    widget.show()
    polish(widget)
    for _ in range(15):
        app.processEvents()
    (OUTPUT_DIR / name).parent.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(OUTPUT_DIR / name), "PNG")
    print("saved", name)
    widget.close()


def main():
    from database import DatabaseManager
    from services import (
        AuthManager, UserService, CourseService, AuditService,
        StatsService, ReportService, MaterialService, LearningService,
    )
    from ui.windows import LoginWindow
    from ui.dashboards import AdminDashboardWidget
    from ui.employee import EmployeeLearningWidget
    from ui.dialogs import AddCourseDialog, AssignCourseDialog

    app = setup()
    db = DatabaseManager()
    db.init_test_data()
    db.ensure_demo_users()
    auth = AuthManager(db)

    login = LoginWindow(auth)
    login.email_input.setText("n.makanina@rami-clinic.ru")
    grab(app, login, "01_login.png", 920, 520)

    if not auth.authenticate("n.makanina@rami-clinic.ru", "admin123"):
        raise RuntimeError("Admin login failed")
    user = auth.get_current_user()
    us, cs, aus, ss = UserService(db), CourseService(db), AuditService(db), StatsService(db)
    rs, ms = ReportService(db, ss), __import__("services.material_service", fromlist=["MaterialService"]).MaterialService(db)

    admin = AdminDashboardWidget(user, db, us, cs, aus, ss, rs, ms)
    grab(app, admin, "02_admin_dashboard.png", 1280, 800)

    dlg = AddCourseDialog(db, user, cs)
    dlg.title_input.setText("Адаптация нового сотрудника")
    grab(app, dlg, "03_create_course.png", 520, 560)

    with db.session_scope() as s:
        from models import Course
        c = s.query(Course).filter(Course.is_active.is_(True)).first()
        cid = c.id if c else 1
    grab(app, AssignCourseDialog(db, user, cs, cid), "04_assign_course.png", 520, 480)

    auth.logout()
    if not auth.authenticate("a.petrova@rami-clinic.ru", "employee123"):
        raise RuntimeError("Employee login failed")
    emp = auth.get_current_user()
    ls = LearningService(db)
    employee = EmployeeLearningWidget(emp, db, cs, ls, ms)
    grab(app, employee, "05_employee_dashboard.png", 1280, 800)
    print("done")


if __name__ == "__main__":
    main()
