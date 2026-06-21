import sys

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QStatusBar, QFormLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal

from constants import APP_FULL_NAME, APP_NAME, APP_VERSION, APP_TAGLINE, ROLE_NAMES
from ui.style_helpers import styled_widget, apply_card_shadow
from services import (
    UserService,
    CourseService,
    AuditService,
    StatsService,
    LearningService,
    ReportService,
    MaterialService,
    DepartmentService,
)
from ui.dashboards import AdminDashboardWidget, DepartmentHeadDashboardWidget
from ui.employee import EmployeeLearningWidget


class LoginWindow(QMainWindow):
    login_success = pyqtSignal()

    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.setWindowTitle(f"{APP_FULL_NAME} — Вход")
        self.setFixedSize(920, 520)
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        brand_panel = styled_widget(QWidget(), "loginBrandPanel")
        brand_panel.setObjectName("loginBrandPanel")
        brand_layout = QVBoxLayout(brand_panel)
        brand_layout.setContentsMargins(40, 48, 40, 48)
        brand_layout.addStretch()

        brand_title = QLabel(APP_NAME)
        brand_title.setProperty("class", "brandTitle")
        brand_layout.addWidget(brand_title)

        brand_sub = QLabel(APP_TAGLINE)
        brand_sub.setProperty("class", "brandSubtitle")
        brand_sub.setWordWrap(True)
        brand_layout.addWidget(brand_sub)

        brand_tag = QLabel("Обучение · Контроль · Развитие")
        brand_tag.setProperty("class", "brandSubtitle")
        brand_layout.addWidget(brand_tag)
        brand_layout.addStretch()

        form_panel = styled_widget(QWidget(), "loginFormPanel")
        form_panel.setObjectName("loginFormPanel")
        form_outer = QVBoxLayout(form_panel)
        form_outer.setContentsMargins(56, 48, 56, 48)
        form_outer.addStretch()

        form_card = styled_widget(QWidget(), "loginCard")
        apply_card_shadow(form_card, blur=28, offset_y=6, alpha=30)
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(28, 28, 28, 28)

        heading = QLabel("Вход в систему")
        heading.setProperty("class", "loginHeading")
        form_layout.addWidget(heading)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@company.ru")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self._attempt_login)

        field_form = QFormLayout()
        field_form.setSpacing(12)
        field_form.addRow("Email", self.email_input)
        field_form.addRow("Пароль", self.password_input)
        form_layout.addLayout(field_form)

        self.login_btn = QPushButton("Войти")
        self.login_btn.setProperty("class", "primary")
        self.login_btn.setMinimumHeight(42)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._attempt_login)
        form_layout.addWidget(self.login_btn)

        form_outer.addWidget(form_card, 0, Qt.AlignmentFlag.AlignHCenter)
        form_outer.addStretch()

        layout.addWidget(brand_panel, 42)
        layout.addWidget(form_panel, 58)

    def _attempt_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        if not email or not password:
            QMessageBox.warning(self, "Ошибка", "Введите email и пароль")
            return
        if self.auth_manager.authenticate(email, password):
            self.login_success.emit()
            self.close()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный email или пароль")


class MainWindow(QMainWindow):
    def __init__(self, auth_manager, db_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.current_user = auth_manager.get_current_user()

        if not self.current_user:
            QMessageBox.critical(self, "Ошибка", "Пользователь не найден")
            sys.exit(1)

        self.setWindowTitle(f"{APP_FULL_NAME} — {self.current_user.full_name}")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)
        self._init_ui()

    def _init_ui(self):
        self._create_status_bar()
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._create_dashboard(), 1)
        self.setCentralWidget(central)

    def _create_header(self):
        header = styled_widget(QWidget(), "topHeader")
        header.setObjectName("topHeader")
        header.setFixedHeight(56)
        row = QHBoxLayout(header)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        row.addStretch()

        user_label = QLabel(
            f"{self.current_user.full_name}  ·  "
            f"{ROLE_NAMES.get(self.current_user.role_id, '')}"
        )
        user_label.setProperty("class", "headerUser")
        user_label.style().unpolish(user_label)
        user_label.style().polish(user_label)
        row.addWidget(user_label)

        logout_btn = QPushButton("Выход")
        logout_btn.setProperty("class", "headerBtn")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        row.addWidget(logout_btn)

        about_btn = QPushButton("О программе")
        about_btn.setProperty("class", "headerBtn")
        about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        about_btn.clicked.connect(self._show_about)
        row.addWidget(about_btn)
        return header

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        dept = (
            self.current_user.department.name
            if self.current_user.department
            else "—"
        )
        self.status_bar.showMessage(
            f"{self.current_user.position} | {dept}"
        )

    def _create_dashboard(self):
        user_service = UserService(self.db_manager)
        course_service = CourseService(self.db_manager)
        audit_service = AuditService(self.db_manager)
        stats_service = StatsService(self.db_manager)
        report_service = ReportService(self.db_manager, stats_service)
        material_service = MaterialService(self.db_manager)
        department_service = DepartmentService(self.db_manager)
        header = self._create_header()
        if self.current_user.is_role('main_admin'):
            return AdminDashboardWidget(
                self.current_user,
                self.db_manager,
                user_service,
                course_service,
                audit_service,
                stats_service,
                report_service,
                material_service,
                department_service,
                header_widget=header,
            )
        if self.current_user.is_role('department_head'):
            return DepartmentHeadDashboardWidget(
                self.current_user,
                self.db_manager,
                user_service,
                course_service,
                audit_service,
                stats_service,
                report_service,
                material_service,
                header_widget=header,
            )
        return EmployeeLearningWidget(
            self.current_user,
            self.db_manager,
            course_service,
            LearningService(self.db_manager),
            material_service,
            header_widget=header,
        )

    def _logout(self):
        if QMessageBox.question(self, 'Выход', 'Вы уверены?') == QMessageBox.StandardButton.Yes:
            self.auth_manager.logout()
            self.close()

    def _show_about(self):
        QMessageBox.about(
            self,
            "О программе",
            f"{APP_FULL_NAME} v{APP_VERSION}\n"
            f"{APP_TAGLINE}\n\n"
            f"Пользователь: {self.current_user.full_name}",
        )
