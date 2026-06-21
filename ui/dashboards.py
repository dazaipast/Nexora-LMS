from sqlalchemy.orm import joinedload
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QDialog,
)

from constants import (
    ROLE_NAMES,
    APP_FULL_NAME,
    MAIN_ADMIN_ROLE_ID,
    DEPT_HEAD_ROLE_ID,
    EMPLOYEE_ROLE_ID,
    STAT_VALUE_STYLE,
    STAT_COLORS,
    DEPT_STATS_HEADERS,
    COURSE_STATS_HEADERS,
    ADMIN_COURSE_STATS_HEADERS,
    EMPLOYEE_STATS_HEADERS,
    DEPT_EMPLOYEE_STATS_HEADERS,
    PROBLEM_EMPLOYEE_HEADERS,
)
from sqlalchemy import func

from models import User, CourseMaterial
from utils import (
    format_percent,
)
from ui.mixins import StatCardMixin, QuickActionsMixin, AuditPanelMixin, CoursesPanelMixin
from ui.table_helpers import (
    configure_readonly_table,
    fill_courses_table,
    fill_users_table,
    fill_employees_table,
    fill_department_stats_table,
    fill_course_stats_table,
    fill_employee_stats_table,
    fill_problem_employees_table,
    get_selected_user_id,
)
from ui.sidebar import SidebarNav, SidebarTabProxy
from ui.widgets import create_section_panel, create_stat_grid, create_section_header
from ui.style_helpers import styled_widget
from ui.dialogs import (
    AddUserDialog,
    AddDepartmentDialog,
    ChangeDepartmentDialog,
    confirm_deactivate_user,
)

class AdminDashboardWidget(
    StatCardMixin, CoursesPanelMixin, AuditPanelMixin, QuickActionsMixin, QWidget
):
    def __init__(
        self,
        actor_user,
        db_manager,
        user_service,
        course_service,
        audit_service,
        stats_service,
        report_service,
        material_service,
        department_service,
        header_widget=None,
    ):
        super().__init__()
        self.actor_user = actor_user
        self.db_manager = db_manager
        self.user_service = user_service
        self.course_service = course_service
        self.audit_service = audit_service
        self.stats_service = stats_service
        self.report_service = report_service
        self.material_service = material_service
        self.department_service = department_service
        self._header_widget = header_widget
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        styled_widget(self, "pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = SidebarNav(
            [
                ("Обзор", self._create_overview_tab()),
                ("Статистика", self._create_statistics_tab()),
                ("Пользователи", self._create_users_tab()),
                ("Курсы", self._create_courses_tab()),
                ("Журнал", self._create_audit_tab()),
            ],
            brand=APP_FULL_NAME,
            subtitle="Администрирование",
            header_widget=self._header_widget,
        )
        self.tabs = SidebarTabProxy(self.sidebar)
        layout.addWidget(self.sidebar)
    
    def _create_overview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 4, 0, 0)

        layout.addWidget(self._create_quick_actions_group([
            ("Создать подразделение", self._quick_add_department),
            ("Создать курс", self._quick_create_course),
            ("Добавить руководителя", self._quick_add_manager),
            ("Экспорт CSV", self._quick_export_report),
            ("Проблемные зоны", self._quick_problem_zones),
        ]))

        self.learning_count = QLabel("0")
        self.learning_count.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[0]))
        self.total_employees = QLabel("0")
        self.total_employees.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[1]))
        self.managers_count = QLabel("0")
        self.managers_count.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[2]))
        self.active_courses = QLabel("0")
        self.active_courses.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[3]))
        self.avg_progress = QLabel("0%")
        self.avg_progress.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[0]))
        self.pass_rate = QLabel("0%")
        self.pass_rate.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[1]))

        layout.addLayout(create_stat_grid([
            self._create_stat_card(
                "Обучается", self.learning_count,
                "Сотрудники с хотя бы одним назначенным курсом",
            ),
            self._create_stat_card(
                "Сотрудников", self.total_employees,
                "Все активные сотрудники клиники",
            ),
            self._create_stat_card(
                "Руководителей", self.managers_count,
                "Активные руководители подразделений",
            ),
            self._create_stat_card(
                "Активных курсов", self.active_courses,
                "Курсы, доступные для назначения сотрудникам",
            ),
            self._create_stat_card(
                "Средний прогресс", self.avg_progress,
                "Средний процент прохождения по всем назначениям",
            ),
            self._create_stat_card(
                "Успеваемость", self.pass_rate,
                "Доля назначений, где прогресс ≥ порога сдачи",
            ),
        ]))

        dept_panel, dept_layout = create_section_panel()
        dept_header = QHBoxLayout()
        dept_header.addWidget(create_section_header("Подразделения"))
        dept_header.addStretch()
        add_dept_btn = QPushButton("Добавить подразделение")
        add_dept_btn.clicked.connect(self._open_add_department_dialog)
        dept_header.addWidget(add_dept_btn)
        dept_layout.addLayout(dept_header)
        self.depts_table = QTableWidget()
        configure_readonly_table(self.depts_table, DEPT_STATS_HEADERS)
        self.depts_table.setMinimumHeight(220)
        dept_layout.addWidget(self.depts_table)
        layout.addWidget(dept_panel)

        layout.addStretch()
        return tab

    def _quick_add_department(self):
        self._switch_to_tab("Обзор")
        self._open_add_department_dialog()

    def _quick_create_course(self):
        self._switch_to_tab("Курсы")
        self._open_create_course_dialog()

    def _quick_add_manager(self):
        self._switch_to_tab("Пользователи")
        self._open_add_user_dialog(DEPT_HEAD_ROLE_ID)

    def _quick_export_report(self):
        self._export_csv_report(
            lambda path: self.report_service.export_admin_report(self.actor_user.id, path),
            "nexora_otchet_klinika.csv",
        )

    def _quick_problem_zones(self):
        self._switch_to_tab("Статистика")

    def _create_statistics_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        export_row = QHBoxLayout()
        export_btn = QPushButton("Экспорт CSV")
        export_btn.clicked.connect(self._quick_export_report)
        export_row.addWidget(export_btn)
        export_row.addStretch()
        layout.addLayout(export_row)

        courses_group = QGroupBox("Статистика по курсам")
        courses_layout = QVBoxLayout()
        self.admin_course_stats_table = QTableWidget()
        configure_readonly_table(self.admin_course_stats_table, ADMIN_COURSE_STATS_HEADERS)
        courses_layout.addWidget(self.admin_course_stats_table)
        courses_group.setLayout(courses_layout)
        layout.addWidget(courses_group)

        employees_group = QGroupBox("Рейтинг сотрудников")
        employees_layout = QVBoxLayout()
        self.admin_employee_stats_table = QTableWidget()
        configure_readonly_table(self.admin_employee_stats_table, EMPLOYEE_STATS_HEADERS)
        employees_layout.addWidget(self.admin_employee_stats_table)
        employees_group.setLayout(employees_layout)
        layout.addWidget(employees_group)

        problems_group = QGroupBox("Нужна помощь (прогресс ниже 65%)")
        problems_layout = QVBoxLayout()
        self.problem_employees_table = QTableWidget()
        configure_readonly_table(self.problem_employees_table, PROBLEM_EMPLOYEE_HEADERS)
        problems_layout.addWidget(self.problem_employees_table)
        problems_group.setLayout(problems_layout)
        layout.addWidget(problems_group)
        return tab
    
    def _create_users_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        actions = QHBoxLayout()
        add_employee_btn = QPushButton("Добавить сотрудника")
        add_employee_btn.clicked.connect(
            lambda: self._open_add_user_dialog(EMPLOYEE_ROLE_ID)
        )
        add_manager_btn = QPushButton("Добавить руководителя")
        add_manager_btn.clicked.connect(
            lambda: self._open_add_user_dialog(DEPT_HEAD_ROLE_ID)
        )
        add_admin_btn = QPushButton("Добавить администратора")
        add_admin_btn.clicked.connect(
            lambda: self._open_add_user_dialog(MAIN_ADMIN_ROLE_ID)
        )
        actions.addWidget(add_employee_btn)
        actions.addWidget(add_manager_btn)
        actions.addWidget(add_admin_btn)
        change_dept_btn = QPushButton("Изменить отдел")
        change_dept_btn.clicked.connect(self._open_change_department_dialog)
        deactivate_btn = QPushButton("Удалить")
        deactivate_btn.clicked.connect(self._deactivate_selected_user)
        actions.addWidget(change_dept_btn)
        actions.addWidget(deactivate_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.users_table = QTableWidget()
        configure_readonly_table(
            self.users_table,
            ["ФИО", "Должность", "Отдел", "Роль", "Email", "Статус"],
        )
        layout.addWidget(self.users_table)
        return tab

    def _open_change_department_dialog(self):
        user_id = get_selected_user_id(self.users_table)
        if not user_id:
            QMessageBox.information(self, "Изменить отдел", "Выберите пользователя в таблице")
            return
        try:
            dialog = ChangeDepartmentDialog(
                self.db_manager,
                self.actor_user,
                self.user_service,
                user_id,
                parent=self,
            )
        except PermissionError as exc:
            QMessageBox.warning(self, "Доступ запрещён", str(exc))
            return
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Готово", "Отдел пользователя успешно изменён")
            self._load_data()

    def _deactivate_selected_user(self):
        user_id = get_selected_user_id(self.users_table)
        if not user_id:
            QMessageBox.information(self, "Удаление", "Выберите пользователя в таблице")
            return
        row = self.users_table.currentRow()
        user_name = self.users_table.item(row, 0).text()
        role_id = self.users_table.item(row, 3).data(Qt.ItemDataRole.UserRole)
        is_employee = role_id == EMPLOYEE_ROLE_ID
        is_department_head = role_id == DEPT_HEAD_ROLE_ID
        if not confirm_deactivate_user(
            self,
            user_name,
            is_employee=is_employee or is_department_head,
        ):
            return
        try:
            self.user_service.deactivate_user(self.actor_user.id, user_id)
            done_msg = (
                "Пользователь полностью удалён"
                if is_employee or is_department_head
                else "Пользователь удалён"
            )
            QMessageBox.information(self, "Готово", done_msg)
            self._load_data()
        except PermissionError as exc:
            QMessageBox.warning(self, "Доступ запрещён", str(exc))
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить пользователя: {exc}")

    def _open_add_department_dialog(self):
        dialog = AddDepartmentDialog(
            self.db_manager,
            self.actor_user,
            self.department_service,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Готово", "Подразделение успешно создано")
            self._load_data()

    def _open_add_user_dialog(self, role_id):
        dialog = AddUserDialog(
            self.db_manager,
            self.actor_user,
            self.user_service,
            preset_role_id=role_id,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Готово", "Пользователь успешно создан")
            self._load_data()
    
    def _create_courses_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self._add_courses_toolbar(layout)
        self.courses_table = self._create_courses_table()
        layout.addWidget(self.courses_table)
        return tab

    def _load_data(self):
        with self.db_manager.session_scope() as db:
            summary = self.stats_service.get_admin_summary(db)
            self.learning_count.setText(str(summary["learning_count"]))
            self.total_employees.setText(str(summary["employees"]))
            self.managers_count.setText(str(summary["managers"]))
            self.active_courses.setText(str(summary["active_courses"]))
            self.avg_progress.setText(format_percent(summary["avg_progress"]))
            self.pass_rate.setText(format_percent(summary["pass_rate"]))

            fill_department_stats_table(
                self.depts_table,
                self.stats_service.get_department_rows(db),
            )
            fill_course_stats_table(
                self.admin_course_stats_table,
                self.stats_service.get_course_stats(db),
                include_department=True,
            )
            employee_stats = self.stats_service.get_employee_stats(db)
            fill_employee_stats_table(
                self.admin_employee_stats_table,
                employee_stats,
                include_department=True,
            )
            fill_problem_employees_table(
                self.problem_employees_table,
                [row for row in employee_stats if row["needs_help"]],
            )

            users = (
                db.query(User)
                .options(joinedload(User.department), joinedload(User.role))
                .order_by(User.full_name)
                .all()
            )
            fill_users_table(self.users_table, users)
            courses = self.course_service.list_courses(self.actor_user.id, db=db)
            fill_courses_table(
                self.courses_table,
                courses,
                self._material_counts(db, courses),
            )
            self._refresh_audit_widgets(db)

    @staticmethod
    def _material_counts(db, courses):
        if not courses:
            return {}
        course_ids = [course.id for course in courses]
        rows = (
            db.query(CourseMaterial.course_id, func.count(CourseMaterial.id))
            .filter(CourseMaterial.course_id.in_(course_ids))
            .group_by(CourseMaterial.course_id)
            .all()
        )
        return {course_id: count for course_id, count in rows}

class DepartmentHeadDashboardWidget(
    StatCardMixin, CoursesPanelMixin, AuditPanelMixin, QuickActionsMixin, QWidget
):
    course_created_message = "Курс успешно создан для вашего отдела"

    def __init__(
        self,
        actor_user,
        db_manager,
        user_service,
        course_service,
        audit_service,
        stats_service,
        report_service,
        material_service,
        header_widget=None,
    ):
        super().__init__()
        self.actor_user = actor_user
        self.db_manager = db_manager
        self.user_service = user_service
        self.course_service = course_service
        self.audit_service = audit_service
        self.stats_service = stats_service
        self.report_service = report_service
        self.material_service = material_service
        self.course_fixed_department_id = actor_user.department_id
        self._header_widget = header_widget
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        styled_widget(self, "pageRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = SidebarNav(
            [
                ("Обзор", self._create_overview_tab()),
                ("Статистика", self._create_statistics_tab()),
                ("Журнал", self._create_audit_tab()),
            ],
            brand=APP_FULL_NAME,
            subtitle="Руководитель отдела",
            header_widget=self._header_widget,
        )
        self.tabs = SidebarTabProxy(self.sidebar)
        layout.addWidget(self.sidebar)

    def _create_overview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 4, 0, 0)

        layout.addWidget(self._create_quick_actions_group([
            ("Создать курс", self._quick_create_course),
            ("Назначить обучение", self._quick_assign_course),
            ("Статистика отдела", self._quick_department_stats),
            ("Экспорт CSV", self._quick_export_department_report),
        ]))

        self.emp_count = QLabel("0")
        self.emp_count.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[0]))
        self.learning_count = QLabel("0")
        self.learning_count.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[1]))
        self.course_count = QLabel("0")
        self.course_count.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[2]))
        self.avg_prog = QLabel("0%")
        self.avg_prog.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[3]))
        self.pass_rate = QLabel("0%")
        self.pass_rate.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[0]))
        self.need_help_count = QLabel("0")
        self.need_help_count.setStyleSheet(STAT_VALUE_STYLE.format(color=STAT_COLORS[1]))

        layout.addLayout(create_stat_grid([
            self._create_stat_card(
                "Сотрудников", self.emp_count,
                "Активные сотрудники вашего отдела",
            ),
            self._create_stat_card(
                "Обучается", self.learning_count,
                "Сотрудники с назначенными курсами",
            ),
            self._create_stat_card(
                "Курсов", self.course_count,
                "Активные курсы, созданные для отдела",
            ),
            self._create_stat_card(
                "Средний прогресс", self.avg_prog,
                "Средний % прохождения курсов в отделе",
            ),
            self._create_stat_card(
                "Успеваемость", self.pass_rate,
                "Доля назначений с прогрессом ≥ порога сдачи",
            ),
            self._create_stat_card(
                "Нужна помощь", self.need_help_count,
                "Сотрудники со средним прогрессом ниже 65%",
            ),
        ]))

        course_panel, course_layout = create_section_panel()
        self.dept_course_stats_table = QTableWidget()
        configure_readonly_table(self.dept_course_stats_table, COURSE_STATS_HEADERS)
        self.dept_course_stats_table.setMinimumHeight(140)
        course_layout.addWidget(self.dept_course_stats_table)
        layout.addWidget(course_panel)

        emp_panel, emp_layout = create_section_panel()
        actions = QHBoxLayout()
        add_employee_btn = QPushButton("Добавить сотрудника")
        add_employee_btn.setProperty("class", "actionBtn")
        add_employee_btn.style().unpolish(add_employee_btn)
        add_employee_btn.style().polish(add_employee_btn)
        add_employee_btn.clicked.connect(self._open_add_employee_dialog)
        deactivate_btn = QPushButton("Удалить")
        deactivate_btn.setProperty("class", "actionBtn")
        deactivate_btn.style().unpolish(deactivate_btn)
        deactivate_btn.style().polish(deactivate_btn)
        deactivate_btn.clicked.connect(self._deactivate_selected_employee)
        actions.addWidget(add_employee_btn)
        actions.addWidget(deactivate_btn)
        actions.addStretch()
        emp_layout.addLayout(actions)

        self.employees_table = QTableWidget()
        configure_readonly_table(self.employees_table, DEPT_EMPLOYEE_STATS_HEADERS)
        self.employees_table.setMinimumHeight(180)
        emp_layout.addWidget(self.employees_table)
        layout.addWidget(emp_panel)

        courses_panel, courses_layout = create_section_panel()
        self._add_courses_toolbar(courses_layout)
        self.courses_table = self._create_courses_table()
        self.courses_table.setMinimumHeight(180)
        courses_layout.addWidget(self.courses_table)
        layout.addWidget(courses_panel)

        layout.addStretch()
        return tab

    def _quick_create_course(self):
        self._open_create_course_dialog()

    def _quick_assign_course(self):
        self._open_assign_course_dialog()

    def _quick_department_stats(self):
        self._switch_to_tab("Статистика")

    def _quick_export_department_report(self):
        dept_name = "otdel"
        if self.actor_user.department:
            dept_name = self.actor_user.department.name.replace(" ", "_").lower()[:30]
        self._export_csv_report(
            lambda path: self.report_service.export_department_report(
                self.actor_user.id, path
            ),
            f"nexora_otchet_{dept_name}.csv",
        )

    def _create_statistics_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        export_row = QHBoxLayout()
        export_btn = QPushButton("Экспорт CSV")
        export_btn.clicked.connect(self._quick_export_department_report)
        export_row.addWidget(export_btn)
        export_row.addStretch()
        layout.addLayout(export_row)

        ranking_group = QGroupBox("Рейтинг сотрудников отдела")
        ranking_layout = QVBoxLayout()
        self.dept_employee_stats_table = QTableWidget()
        configure_readonly_table(self.dept_employee_stats_table, DEPT_EMPLOYEE_STATS_HEADERS)
        ranking_layout.addWidget(self.dept_employee_stats_table)
        ranking_group.setLayout(ranking_layout)
        layout.addWidget(ranking_group)

        courses_group = QGroupBox("Детальная статистика по курсам")
        courses_layout = QVBoxLayout()
        self.dept_stats_course_table = QTableWidget()
        configure_readonly_table(self.dept_stats_course_table, COURSE_STATS_HEADERS)
        courses_layout.addWidget(self.dept_stats_course_table)
        courses_group.setLayout(courses_layout)
        layout.addWidget(courses_group)

        problems_group = QGroupBox("Сотрудники, которым нужна помощь")
        problems_layout = QVBoxLayout()
        self.dept_problem_table = QTableWidget()
        configure_readonly_table(
            self.dept_problem_table,
            ["ФИО", "Должность", "Прогресс", "Оценка", "Курсов"],
        )
        problems_layout.addWidget(self.dept_problem_table)
        problems_group.setLayout(problems_layout)
        layout.addWidget(problems_group)
        return tab

    def _open_add_employee_dialog(self):
        dialog = AddUserDialog(
            self.db_manager,
            self.actor_user,
            self.user_service,
            preset_role_id=EMPLOYEE_ROLE_ID,
            fixed_department_id=self.actor_user.department_id,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Готово", "Сотрудник успешно добавлен в ваш отдел")
            self._load_data()

    def _deactivate_selected_employee(self):
        user_id = get_selected_user_id(self.employees_table)
        if not user_id:
            QMessageBox.information(self, "Удаление", "Выберите сотрудника в таблице")
            return
        row = self.employees_table.currentRow()
        user_name = self.employees_table.item(row, 0).text()
        if not confirm_deactivate_user(self, user_name, is_employee=True):
            return
        try:
            self.user_service.deactivate_user(self.actor_user.id, user_id)
            QMessageBox.information(self, "Готово", "Сотрудник полностью удалён")
            self._load_data()
        except PermissionError as exc:
            QMessageBox.warning(self, "Доступ запрещён", str(exc))
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить сотрудника: {exc}")

    def _load_data(self):
        with self.db_manager.session_scope() as db:
            dept_id = self.actor_user.department_id
            if not dept_id:
                return

            employee_stats = self.stats_service.get_employee_stats(db, department_id=dept_id)
            summary = self.stats_service.get_department_summary(
                db, dept_id, employee_stats=employee_stats
            )
            self.emp_count.setText(str(summary["employees"]))
            self.learning_count.setText(str(summary["learning_count"]))
            self.course_count.setText(str(summary["active_courses"]))
            self.avg_prog.setText(format_percent(summary["avg_progress"]))
            self.pass_rate.setText(format_percent(summary["pass_rate"]))
            self.need_help_count.setText(str(summary["need_help_count"]))

            employees = (
                db.query(User)
                .filter(
                    User.department_id == dept_id,
                    User.role_id == EMPLOYEE_ROLE_ID,
                    User.is_active.is_(True),
                )
                .order_by(User.full_name)
                .all()
            )
            fill_employees_table(
                self.employees_table, employees, {}, employee_stats=employee_stats
            )

            course_stats = self.stats_service.get_course_stats(db, department_id=dept_id)
            fill_course_stats_table(self.dept_course_stats_table, course_stats)
            fill_course_stats_table(self.dept_stats_course_table, course_stats)
            fill_employee_stats_table(self.dept_employee_stats_table, employee_stats)

            problem_rows = [row for row in employee_stats if row["needs_help"]]
            self.dept_problem_table.setRowCount(len(problem_rows))
            for row_index, row in enumerate(problem_rows):
                self.dept_problem_table.setItem(row_index, 0, QTableWidgetItem(row["full_name"]))
                self.dept_problem_table.setItem(row_index, 1, QTableWidgetItem(row["position"]))
                self.dept_problem_table.setItem(
                    row_index, 2, QTableWidgetItem(format_percent(row["progress"]))
                )
                self.dept_problem_table.setItem(row_index, 3, QTableWidgetItem(row["performance"]))
                self.dept_problem_table.setItem(
                    row_index, 4, QTableWidgetItem(str(row["assigned_courses"]))
                )

            courses = self.course_service.list_courses(self.actor_user.id, db=db)
            fill_courses_table(
                self.courses_table,
                courses,
                AdminDashboardWidget._material_counts(db, courses),
            )
            self._refresh_audit_widgets(db)


