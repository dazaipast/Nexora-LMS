from sqlalchemy.orm import joinedload
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QListWidget, QProgressBar, QSizePolicy,
)
from PyQt6.QtCore import Qt

from constants import HISTORY_HEADERS
from models import User, UserCourse, Course
from utils import format_percent, course_pass_status, split_employee_progress, course_type_label
from ui.table_helpers import (
    configure_readonly_table,
    fill_text_list,
    fill_history_table,
    get_selected_course_id,
)
from ui.dialogs import (
    open_course_passing_dialog,
    show_course_details,
    open_course_materials_dialog,
)
from ui.sidebar import SidebarNav, SidebarTabProxy
from ui.widgets import create_section_panel
from ui.style_helpers import styled_widget

EMPLOYEE_COURSE_HEADERS = ["Название", "Тип", "Прогресс", "Срок (дн.)", "Порог %", "Статус"]


class EmployeeLearningWidget(QWidget):
    def __init__(
        self,
        actor_user,
        db_manager,
        course_service,
        learning_service,
        material_service,
        header_widget=None,
    ):
        super().__init__()
        self.actor_user = actor_user
        self.db_manager = db_manager
        self.course_service = course_service
        self.learning_service = learning_service
        self.material_service = material_service
        self._header_widget = header_widget
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        styled_widget(self, "pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = SidebarNav(
            [
                ("Главная", self._create_main_page()),
                ("История", self._create_history_page()),
            ],
            brand="LearnMate Core",
            subtitle="Моё обучение",
            header_widget=self._header_widget,
        )
        self.tabs = SidebarTabProxy(self.sidebar)
        self.sidebar.page_selected.connect(self._on_page_selected)
        self.sidebar.page_title.setVisible(False)
        layout.addWidget(self.sidebar)

    def _on_page_selected(self, index):
        self.sidebar.page_title.setVisible(index != 0)

    def _make_header_button(self, label, callback):
        button = QPushButton(label)
        button.setProperty("class", "headerBtn")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.style().unpolish(button)
        button.style().polish(button)
        button.clicked.connect(callback)
        return button

    def _create_main_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 4, 0, 0)

        self.welcome_label = QLabel()
        self.welcome_label.setProperty("class", "welcomeHeading")
        layout.addWidget(self.welcome_label)

        self.dept_label = QLabel()
        self.dept_label.setProperty("class", "pageSubtitle")
        layout.addWidget(self.dept_label)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        top_row.setContentsMargins(0, 0, 0, 0)

        prog_panel, prog_layout = create_section_panel()
        prog_title = QLabel("Ваш прогресс")
        styled_widget(prog_title, "sectionTitle")
        prog_layout.addWidget(prog_title)
        self.adapt_progress = QProgressBar()
        self.adapt_progress.setMaximum(100)
        self.adapt_progress.setFormat("Адаптация: %p%")
        self.know_progress = QProgressBar()
        self.know_progress.setMaximum(100)
        self.know_progress.setFormat("Общие знания: %p%")
        self.skill_progress = QProgressBar()
        self.skill_progress.setMaximum(100)
        self.skill_progress.setFormat("Проф. навыки: %p%")
        prog_layout.addWidget(self.adapt_progress)
        prog_layout.addWidget(self.know_progress)
        prog_layout.addWidget(self.skill_progress)
        prog_layout.addStretch()

        rec_panel, rec_layout = create_section_panel()
        rec_title = QLabel("Рекомендации")
        styled_widget(rec_title, "sectionTitle")
        rec_layout.addWidget(rec_title)
        self.recommendations_list = QListWidget()
        self.recommendations_list.setProperty("class", "flatList")
        self.recommendations_list.style().unpolish(self.recommendations_list)
        self.recommendations_list.style().polish(self.recommendations_list)
        rec_layout.addWidget(self.recommendations_list, 1)

        today_panel, today_layout = create_section_panel()
        today_title = QLabel("Сегодня вам")
        styled_widget(today_title, "sectionTitle")
        today_layout.addWidget(today_title)
        self.today_list = QListWidget()
        self.today_list.setProperty("class", "flatList")
        self.today_list.style().unpolish(self.today_list)
        self.today_list.style().polish(self.today_list)
        today_layout.addWidget(self.today_list, 1)

        courses_panel, courses_layout = create_section_panel()
        courses_title = QLabel("Мои курсы")
        styled_widget(courses_title, "sectionTitle")
        courses_layout.addWidget(courses_title)
        course_actions = QHBoxLayout()
        course_actions.setSpacing(10)
        course_actions.addWidget(self._make_header_button("Пройти", self._open_pass_course_dialog))
        course_actions.addWidget(self._make_header_button("Просмотр", self._open_view_course_dialog))
        course_actions.addWidget(self._make_header_button("Материалы", self._open_course_materials_dialog))
        course_actions.addStretch()
        courses_layout.addLayout(course_actions)
        self.courses_table = QTableWidget()
        configure_readonly_table(self.courses_table, EMPLOYEE_COURSE_HEADERS)
        self.courses_table.doubleClicked.connect(self._open_pass_course_dialog)
        courses_layout.addWidget(self.courses_table, 1)

        for panel in (prog_panel, rec_panel, today_panel):
            panel.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred,
            )
            panel.setMinimumHeight(180)
            top_row.addWidget(panel, 1)

        courses_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        courses_panel.setMinimumHeight(240)

        layout.addLayout(top_row)
        layout.addWidget(courses_panel, 1)
        return page

    def _create_history_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)

        history_panel, history_layout = create_section_panel()
        self.history_table = QTableWidget()
        configure_readonly_table(self.history_table, HISTORY_HEADERS)
        history_layout.addWidget(self.history_table)
        layout.addWidget(history_panel)
        return page

    def _open_pass_course_dialog(self):
        course_id = get_selected_course_id(self.courses_table)
        if not course_id:
            QMessageBox.information(self, "Прохождение", "Выберите курс в таблице")
            return
        open_course_passing_dialog(
            self.actor_user,
            self.course_service,
            course_id,
            self,
            material_service=self.material_service,
            on_success=self._load_data,
        )

    def _open_view_course_dialog(self):
        course_id = get_selected_course_id(self.courses_table)
        if not course_id:
            QMessageBox.information(self, "Просмотр", "Выберите курс в таблице")
            return
        show_course_details(
            self.actor_user,
            self.course_service,
            course_id,
            self,
            material_service=self.material_service,
        )

    def _open_course_materials_dialog(self):
        course_id = get_selected_course_id(self.courses_table)
        if not course_id:
            QMessageBox.information(self, "Материалы", "Выберите курс в таблице")
            return
        open_course_materials_dialog(
            self,
            self.actor_user,
            self.material_service,
            course_id,
        )

    def _load_data(self):
        with self.db_manager.session_scope() as db:
            user = (
                db.query(User)
                .options(joinedload(User.department))
                .filter(User.id == self.actor_user.id)
                .first()
            )
            if user:
                first_name = user.full_name.split(maxsplit=1)[0]
                self.welcome_label.setText(f"Добрый день, {first_name}!")
                self.dept_label.setText(
                    f"{user.position}  ·  "
                    f"{user.department.name if user.department else '—'}"
                )

            user_courses = (
                db.query(UserCourse)
                .options(joinedload(UserCourse.course))
                .join(Course, UserCourse.course_id == Course.id)
                .filter(
                    UserCourse.user_id == self.actor_user.id,
                    Course.is_active.is_(True),
                )
                .all()
            )

            active_courses = [
                uc for uc in user_courses if uc.course and uc.course.is_active
            ]
            self.courses_table.setRowCount(len(active_courses))
            for row, uc in enumerate(active_courses):
                title_item = QTableWidgetItem(uc.course.title)
                title_item.setData(Qt.ItemDataRole.UserRole, uc.course.id)
                status = course_pass_status(uc.progress, uc.course.pass_threshold)
                self.courses_table.setItem(row, 0, title_item)
                self.courses_table.setItem(
                    row, 1,
                    QTableWidgetItem(course_type_label(getattr(uc.course, "course_type", None))),
                )
                self.courses_table.setItem(row, 2, QTableWidgetItem(format_percent(uc.progress)))
                self.courses_table.setItem(row, 3, QTableWidgetItem(str(uc.course.deadline_days)))
                self.courses_table.setItem(row, 4, QTableWidgetItem(str(uc.course.pass_threshold)))
                self.courses_table.setItem(row, 5, QTableWidgetItem(status))

            if active_courses:
                adapt, know, skill = split_employee_progress(active_courses)
            else:
                adapt = know = skill = 0
            self.adapt_progress.setValue(adapt)
            self.know_progress.setValue(know)
            self.skill_progress.setValue(skill)

            fill_text_list(
                self.today_list,
                self.learning_service.get_today_tasks(self.actor_user.id, db=db),
            )
            fill_text_list(
                self.recommendations_list,
                self.learning_service.get_recommendations(self.actor_user.id, db=db),
            )
            fill_history_table(
                self.history_table,
                self.learning_service.get_learning_history(self.actor_user.id, db=db),
            )
