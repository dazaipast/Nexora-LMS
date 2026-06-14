from types import SimpleNamespace

from sqlalchemy.orm import joinedload
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QSpinBox, QListWidget, QListWidgetItem,
    QDialogButtonBox, QMessageBox, QTableWidget, QPushButton, QProgressBar,
    QFileDialog, QScrollArea, QWidget, QRadioButton, QButtonGroup,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices

from constants import (
    ROLE_NAMES,
    MAIN_ADMIN_ROLE_ID,
    DEPT_HEAD_ROLE_ID,
    EMPLOYEE_ROLE_ID,
    MIN_PASSWORD_LENGTH,
    DEFAULT_DEADLINE_DAYS,
    DEFAULT_PASS_THRESHOLD,
    DEFAULT_MODULES_PER_COURSE,
    MIN_MODULES_PER_COURSE,
    MAX_MODULES_PER_COURSE,
    ALLOWED_MATERIAL_EXTENSIONS,
    MODULE_MATERIALS_HEADERS,
    MAX_MATERIAL_SIZE_BYTES,
    COURSE_TYPES,
    DEFAULT_COURSE_TYPE,
)
from models import Department, User, Course
from utils import (
    load_departments_for_actor,
    build_module_content,
    format_file_size,
    course_type_label,
)

from ui.table_helpers import (
    get_selected_course_id,
    get_selected_material_id,
    get_selected_module_index,
    populate_department_combo,
    configure_readonly_table,
    fill_module_materials_table,
)

class ChangeDepartmentDialog(QDialog):
    def __init__(self, db_manager, actor_user, user_service, target_user_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.actor_user = actor_user
        self.user_service = user_service
        self.target_user_id = target_user_id

        self.setWindowTitle("Изменить отдел")
        self.setMinimumWidth(420)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.user_label = QLabel()
        form.addRow("Пользователь:", self.user_label)

        self.role_label = QLabel()
        form.addRow("Роль:", self.role_label)

        self.current_dept_label = QLabel()
        form.addRow("Текущий отдел:", self.current_dept_label)

        self.department_combo = QComboBox()
        form.addRow("Новый отдел:", self.department_combo)

        layout.addLayout(form)

        hint = QLabel(
            "При смене отдела незавершённые курсы будут отменены, "
            "а курсы нового отдела — назначены автоматически."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        with self.db_manager.session_scope() as db:
            target = (
                db.query(User)
                .options(joinedload(User.department), joinedload(User.role))
                .filter(User.id == self.target_user_id)
                .first()
            )
            if not target:
                raise ValueError("Пользователь не найден")
            if not self.user_service.can_change_department(self.actor_user, target):
                raise PermissionError("Недостаточно прав для смены отдела")

            self.user_label.setText(target.full_name)
            self.role_label.setText(target.role.name if target.role else "")
            self.current_dept_label.setText(target.department.name if target.department else "—")

            departments = db.query(Department).order_by(Department.name).all()
            for dept in departments:
                if dept.id != target.department_id:
                    self.department_combo.addItem(dept.name, dept.id)

        if self.department_combo.count() == 0:
            raise ValueError("Нет других отделов для перевода")

    def _on_save(self):
        new_department_id = self.department_combo.currentData()
        try:
            self.user_service.change_department(
                self.actor_user.id,
                self.target_user_id,
                new_department_id,
            )
            self.accept()
        except PermissionError as exc:
            QMessageBox.warning(self, "Доступ запрещён", str(exc))
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось изменить отдел: {exc}")


def confirm_deactivate_user(parent, user_name, is_employee=False):
    if is_employee:
        message = (
            f"Удалить сотрудника «{user_name}»?\n\n"
            "Запись будет полностью удалена из системы вместе с назначениями курсов. "
            "Это действие нельзя отменить."
        )
    else:
        message = (
            f"Удалить пользователя «{user_name}»?\n\n"
            "Аккаунт будет деактивирован и не сможет войти в систему."
        )
    return (
        QMessageBox.question(
            parent,
            "Удаление пользователя",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        == QMessageBox.StandardButton.Yes
    )


def confirm_deactivate_course(parent, course_title):
    return (
        QMessageBox.question(
            parent,
            "Удаление курса",
            f"Удалить курс «{course_title}»?\n\n"
            "Курс будет деактивирован и исчезнет из списков обучения.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        == QMessageBox.StandardButton.Yes
    )


def deactivate_selected_course(parent, actor_user, course_service, table, on_success):
    course_id = get_selected_course_id(table)
    if not course_id:
        QMessageBox.information(parent, "Удаление", "Выберите курс в таблице")
        return
    row = table.currentRow()
    course_title = table.item(row, 0).text()
    if not confirm_deactivate_course(parent, course_title):
        return
    try:
        course_service.deactivate_course(actor_user.id, course_id)
        QMessageBox.information(parent, "Готово", "Курс удалён")
        on_success()
    except PermissionError as exc:
        QMessageBox.warning(parent, "Доступ запрещён", str(exc))
    except ValueError as exc:
        QMessageBox.warning(parent, "Ошибка", str(exc))
    except Exception as exc:
        QMessageBox.critical(parent, "Ошибка", f"Не удалось удалить курс: {exc}")


class AddUserDialog(QDialog):
    def __init__(
        self,
        db_manager,
        actor_user,
        user_service,
        preset_role_id=None,
        fixed_department_id=None,
        parent=None,
    ):
        super().__init__(parent)
        self.db_manager = db_manager
        self.actor_user = actor_user
        self.user_service = user_service
        self.preset_role_id = preset_role_id
        self.fixed_department_id = fixed_department_id
        self.created_user_id = None

        titles = {
            EMPLOYEE_ROLE_ID: "Добавить сотрудника",
            DEPT_HEAD_ROLE_ID: "Добавить руководителя",
            MAIN_ADMIN_ROLE_ID: "Добавить администратора",
        }
        self.setWindowTitle(titles.get(preset_role_id, "Добавить пользователя"))
        self.setMinimumWidth(420)
        self._init_ui()
        self._load_departments()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Иванов Иван Иванович")
        form.addRow("ФИО:", self.full_name_input)

        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("Должность")
        form.addRow("Должность:", self.position_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@rami-clinic.ru")
        form.addRow("Email:", self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText(f"Минимум {MIN_PASSWORD_LENGTH} символов")
        form.addRow("Пароль:", self.password_input)

        self.department_combo = QComboBox()
        form.addRow("Отдел:", self.department_combo)

        self.role_combo = QComboBox()
        if self.actor_user.is_role('main_admin'):
            for role_id, label in (
                (EMPLOYEE_ROLE_ID, ROLE_NAMES[EMPLOYEE_ROLE_ID]),
                (DEPT_HEAD_ROLE_ID, ROLE_NAMES[DEPT_HEAD_ROLE_ID]),
                (MAIN_ADMIN_ROLE_ID, ROLE_NAMES[MAIN_ADMIN_ROLE_ID]),
            ):
                self.role_combo.addItem(label, role_id)
        elif self.actor_user.is_role('department_head'):
            self.role_combo.addItem(ROLE_NAMES[EMPLOYEE_ROLE_ID], EMPLOYEE_ROLE_ID)

        if self.preset_role_id is not None:
            index = self.role_combo.findData(self.preset_role_id)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
        if self.preset_role_id is not None or self.actor_user.is_role('department_head'):
            self.role_combo.setEnabled(False)
        form.addRow("Роль:", self.role_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Создать")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_departments(self):
        with self.db_manager.session_scope() as db:
            departments = load_departments_for_actor(
                db, self.actor_user, self.fixed_department_id
            )
        populate_department_combo(
            self.department_combo, departments, self.actor_user, self.fixed_department_id
        )

    def _on_save(self):
        role_id = self.role_combo.currentData()
        department_id = self.department_combo.currentData()
        try:
            self.created_user_id = self.user_service.create_user(
                actor_id=self.actor_user.id,
                full_name=self.full_name_input.text(),
                email=self.email_input.text(),
                password=self.password_input.text(),
                position=self.position_input.text(),
                department_id=department_id,
                role_id=role_id,
            )
            self.accept()
        except PermissionError as exc:
            QMessageBox.warning(self, "Доступ запрещён", str(exc))
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать пользователя: {exc}")


class AddDepartmentDialog(QDialog):
    def __init__(self, db_manager, actor_user, department_service, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.actor_user = actor_user
        self.department_service = department_service

        self.setWindowTitle("Создать подразделение")
        self.setMinimumWidth(460)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: Контакт-центр")
        form.addRow("Название:", self.name_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Краткое описание подразделения (необязательно)")
        self.description_input.setMaximumHeight(100)
        form.addRow("Описание:", self.description_input)

        layout.addLayout(form)

        hint = QLabel(
            "После сохранения подразделение появится в общем списке и станет "
            "доступным при создании пользователей и курсов."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_save(self):
        try:
            self.department_service.create_department(
                self.actor_user.id,
                self.name_input.text(),
                self.description_input.toPlainText(),
            )
            self.accept()
        except PermissionError as exc:
            QMessageBox.warning(self, "Доступ запрещён", str(exc))
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать подразделение: {exc}")


class AddCourseDialog(QDialog):
    def __init__(self, db_manager, actor_user, course_service, fixed_department_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.actor_user = actor_user
        self.course_service = course_service
        self.fixed_department_id = fixed_department_id
        self.created_course_id = None

        self.setWindowTitle("Создать курс")
        self.setMinimumWidth(480)
        self._init_ui()
        self._load_departments()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Например: Адаптация оператора КЦ")
        form.addRow("Название:", self.title_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Описание курса, цели обучения...")
        self.description_input.setMaximumHeight(120)
        form.addRow("Описание:", self.description_input)

        self.department_combo = QComboBox()
        form.addRow("Отдел:", self.department_combo)

        self.deadline_input = QSpinBox()
        self.deadline_input.setRange(1, 365)
        self.deadline_input.setValue(DEFAULT_DEADLINE_DAYS)
        self.deadline_input.setSuffix(" дн.")
        form.addRow("Срок прохождения:", self.deadline_input)

        self.threshold_input = QSpinBox()
        self.threshold_input.setRange(1, 100)
        self.threshold_input.setValue(DEFAULT_PASS_THRESHOLD)
        self.threshold_input.setSuffix(" %")
        form.addRow("Порог сдачи:", self.threshold_input)

        self.modules_input = QSpinBox()
        self.modules_input.setRange(MIN_MODULES_PER_COURSE, MAX_MODULES_PER_COURSE)
        self.modules_input.setValue(DEFAULT_MODULES_PER_COURSE)
        self.modules_input.setSuffix(" этап.")
        form.addRow("Количество этапов:", self.modules_input)

        self.type_combo = QComboBox()
        for type_code, info in COURSE_TYPES.items():
            self.type_combo.addItem(info["label"], type_code)
        default_index = self.type_combo.findData(DEFAULT_COURSE_TYPE)
        if default_index >= 0:
            self.type_combo.setCurrentIndex(default_index)
        form.addRow("Тип курса:", self.type_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Создать")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_departments(self):
        with self.db_manager.session_scope() as db:
            departments = load_departments_for_actor(
                db, self.actor_user, self.fixed_department_id
            )
        populate_department_combo(
            self.department_combo, departments, self.actor_user, self.fixed_department_id
        )

    def _on_save(self):
        try:
            self.created_course_id = self.course_service.create_course(
                actor_id=self.actor_user.id,
                title=self.title_input.text(),
                description=self.description_input.toPlainText(),
                department_id=self.department_combo.currentData(),
                deadline_days=self.deadline_input.value(),
                pass_threshold=self.threshold_input.value(),
                module_count=self.modules_input.value(),
                course_type=self.type_combo.currentData(),
            )
            self.accept()
        except PermissionError as exc:
            QMessageBox.warning(self, "Доступ запрещён", str(exc))
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать курс: {exc}")


class AssignCourseDialog(QDialog):
    def __init__(self, db_manager, actor_user, course_service, course_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.actor_user = actor_user
        self.course_service = course_service
        self.course_id = course_id
        self._already_assigned = set()

        self.setWindowTitle("Назначить обучение")
        self.setMinimumSize(480, 420)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.course_label = QLabel()
        self.course_label.setWordWrap(True)
        layout.addWidget(self.course_label)

        hint = QLabel("Отметьте сотрудников, которым нужно назначить курс:")
        layout.addWidget(hint)

        self.employees_list = QListWidget()
        layout.addWidget(self.employees_list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Назначить")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        with self.db_manager.session_scope() as db:
            course = (
                db.query(Course)
                .options(joinedload(Course.department))
                .filter(Course.id == self.course_id)
                .first()
            )
            if not course:
                raise ValueError("Курс не найден")
            dept_name = course.department.name if course.department else "—"
            self.course_label.setText(
                f"Курс: {course.title}\nОтдел: {dept_name} | "
                f"Срок: {course.deadline_days} дн. | Порог: {course.pass_threshold}%"
            )

        employees = self.course_service.get_assignable_employees(
            self.actor_user.id, self.course_id
        )
        self.employees_list.clear()
        if not employees:
            self.employees_list.addItem("Нет доступных сотрудников для назначения")
            return

        show_department = self.actor_user.is_role('main_admin')
        for employee in employees:
            label = employee["full_name"]
            if show_department:
                label += f" — {employee['department_name']}"
            if employee["assigned"]:
                label += " (уже назначен)"
                self._already_assigned.add(employee["id"])

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, employee["id"])
            if employee["assigned"]:
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setFlags(
                    Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
                )
                item.setCheckState(Qt.CheckState.Unchecked)
            self.employees_list.addItem(item)

    def _on_save(self):
        selected_ids = []
        for index in range(self.employees_list.count()):
            item = self.employees_list.item(index)
            user_id = item.data(Qt.ItemDataRole.UserRole)
            if user_id is None:
                continue
            if (
                item.checkState() == Qt.CheckState.Checked
                and user_id not in self._already_assigned
            ):
                selected_ids.append(user_id)

        try:
            count = self.course_service.assign_course(
                self.actor_user.id, self.course_id, selected_ids
            )
            QMessageBox.information(
                self, "Готово", f"Курс назначен {count} сотрудникам"
            )
            self.accept()
        except PermissionError as exc:
            QMessageBox.warning(self, "Доступ запрещён", str(exc))
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось назначить курс: {exc}")


def open_assign_course_dialog(parent, actor_user, course_service, course_id=None, on_success=None):
    if not course_id and hasattr(parent, "courses_table"):
        course_id = get_selected_course_id(parent.courses_table)
    if not course_id:
        QMessageBox.information(parent, "Назначение", "Выберите курс в таблице")
        return
    try:
        dialog = AssignCourseDialog(
            parent.db_manager,
            actor_user,
            course_service,
            course_id,
            parent=parent,
        )
    except (PermissionError, ValueError) as exc:
        QMessageBox.warning(parent, "Ошибка", str(exc))
        return

    if dialog.exec() == QDialog.DialogCode.Accepted and on_success:
        on_success()


def offer_assign_after_create(parent, actor_user, course_service, course_id, on_success):
    answer = QMessageBox.question(
        parent,
        "Назначить обучение",
        "Курс создан. Назначить его сотрудникам сейчас?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if answer == QMessageBox.StandardButton.Yes:
        try:
            dialog = AssignCourseDialog(
                parent.db_manager,
                actor_user,
                course_service,
                course_id,
                parent=parent,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted and on_success:
                on_success()
        except (PermissionError, ValueError) as exc:
            QMessageBox.warning(parent, "Ошибка", str(exc))


def _materials_file_filter():
    patterns = " ".join(f"*{ext}" for ext in sorted(ALLOWED_MATERIAL_EXTENSIONS))
    return f"Поддерживаемые файлы ({patterns});;Все файлы (*.*)"


class CourseMaterialsDialog(QDialog):
    def __init__(self, actor_user, material_service, course_id, on_change=None, parent=None):
        super().__init__(parent)
        self.actor_user = actor_user
        self.material_service = material_service
        self.course_id = course_id
        self.on_change = on_change
        self._can_manage = False

        self.setMinimumSize(700, 480)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.hint_label = QLabel()
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

        settings_row = QHBoxLayout()
        settings_row.addWidget(QLabel("Количество этапов:"))
        self.modules_input = QSpinBox()
        self.modules_input.setRange(MIN_MODULES_PER_COURSE, MAX_MODULES_PER_COURSE)
        settings_row.addWidget(self.modules_input)
        self.save_modules_btn = QPushButton("Сохранить")
        self.save_modules_btn.clicked.connect(self._save_module_count)
        settings_row.addWidget(self.save_modules_btn)
        settings_row.addStretch()
        layout.addLayout(settings_row)

        self.materials_table = QTableWidget()
        configure_readonly_table(self.materials_table, MODULE_MATERIALS_HEADERS)
        self.materials_table.doubleClicked.connect(self._open_selected_material)
        layout.addWidget(self.materials_table)

        actions = QHBoxLayout()
        self.attach_btn = QPushButton("Прикрепить к этапу")
        self.attach_btn.clicked.connect(self._attach_to_stage)
        self.open_btn = QPushButton("Открыть")
        self.open_btn.clicked.connect(self._open_selected_material)
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self._delete_selected_material)
        actions.addWidget(self.attach_btn)
        actions.addWidget(self.open_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch()
        layout.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _load_data(self):
        try:
            payload = self.material_service.list_materials(
                self.actor_user.id, self.course_id
            )
        except (PermissionError, ValueError) as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            self.reject()
            return

        self._payload = payload
        self._can_manage = payload["can_manage"]
        self.setWindowTitle(f"Материалы: {payload['course_title']}")
        self.title_label.setText(
            f"Курс: {payload['course_title']} | "
            f"этапов: {payload['module_count']} | "
            f"материалов: {payload['attached_count']}/{payload['module_count']}"
        )
        if self._can_manage and payload.get("is_practice"):
            self.hint_label.setText(
                "Курс типа «Практика»: к каждому этапу прикрепите .docx файл с вопросами.\n"
                "Формат:\n"
                "Вопрос: Текст вопроса?\n"
                "A) Вариант 1\nB) Вариант 2\nОтвет: B\n\n"
                f"Максимальный размер файла: {format_file_size(MAX_MATERIAL_SIZE_BYTES)}."
            )
        elif self._can_manage:
            self.hint_label.setText(
                "К каждому этапу можно прикрепить один файл. "
                "При повторной загрузке файл этапа будет заменён. "
                f"Максимальный размер: {format_file_size(MAX_MATERIAL_SIZE_BYTES)}."
            )
        else:
            self.hint_label.setText(
                "Материалы по этапам курса. Выберите этап и нажмите «Открыть»."
            )

        self.modules_input.blockSignals(True)
        self.modules_input.setValue(payload["module_count"])
        self.modules_input.blockSignals(False)
        self.modules_input.setEnabled(self._can_manage)
        self.save_modules_btn.setVisible(self._can_manage)
        self.attach_btn.setVisible(self._can_manage)
        self.delete_btn.setVisible(self._can_manage)
        fill_module_materials_table(self.materials_table, payload["modules"])

    def _save_module_count(self):
        try:
            self.material_service.update_module_count(
                self.actor_user.id,
                self.course_id,
                self.modules_input.value(),
            )
        except (PermissionError, ValueError) as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки: {exc}")
            return

        QMessageBox.information(self, "Готово", "Количество этапов обновлено")
        self._load_data()
        if self.on_change:
            self.on_change()

    def _attach_to_stage(self):
        module_index = get_selected_module_index(self.materials_table)
        if not module_index:
            QMessageBox.information(self, "Прикрепить", "Выберите этап в таблице")
            return

        file_filter = (
            "Тест Word (*.docx)"
            if self._payload and self._payload.get("is_practice")
            else _materials_file_filter()
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Файл для этапа {module_index}",
            "",
            file_filter,
        )
        if not file_path:
            return
        try:
            self.material_service.add_material(
                self.actor_user.id,
                self.course_id,
                module_index,
                file_path,
            )
        except PermissionError as exc:
            QMessageBox.warning(self, "Доступ запрещён", str(exc))
            return
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прикрепить файл: {exc}")
            return

        QMessageBox.information(self, "Готово", f"Файл прикреплён к этапу {module_index}")
        self._load_data()
        if self.on_change:
            self.on_change()

    def _open_selected_material(self):
        material_id = get_selected_material_id(self.materials_table)
        if not material_id:
            QMessageBox.information(
                self, "Открыть", "Для выбранного этапа материал не прикреплён"
            )
            return
        self._open_material_by_id(material_id)

    def _open_material_by_id(self, material_id):
        try:
            file_path = self.material_service.get_material_path(
                self.actor_user.id, material_id
            )
        except (PermissionError, ValueError) as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return

        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path))):
            QMessageBox.warning(
                self,
                "Открыть",
                f"Не удалось открыть файл:\n{file_path}",
            )

    def _delete_selected_material(self):
        module_index = get_selected_module_index(self.materials_table)
        if not module_index:
            QMessageBox.information(self, "Удаление", "Выберите этап в таблице")
            return
        material_id = get_selected_material_id(self.materials_table)
        if not material_id:
            QMessageBox.information(self, "Удаление", "Для этого этапа материал не прикреплён")
            return

        row = self.materials_table.currentRow()
        file_name = self.materials_table.item(row, 1).text()
        answer = QMessageBox.question(
            self,
            "Удаление",
            f"Удалить материал этапа {module_index} («{file_name}»)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.material_service.delete_material(self.actor_user.id, material_id)
        except (PermissionError, ValueError) as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить файл: {exc}")
            return

        self._load_data()
        if self.on_change:
            self.on_change()


def open_course_materials_dialog(parent, actor_user, material_service, course_id, on_change=None):
    CourseMaterialsDialog(
        actor_user,
        material_service,
        course_id,
        on_change=on_change,
        parent=parent,
    ).exec()


class CoursePassingDialog(QDialog):
    def __init__(
        self,
        actor_user,
        course_service,
        course_id,
        material_service=None,
        on_progress=None,
        parent=None,
    ):
        super().__init__(parent)
        self.actor_user = actor_user
        self.course_service = course_service
        self.material_service = material_service
        self.course_id = course_id
        self.on_progress = on_progress

        self.setMinimumSize(560, 480)
        self._init_ui()
        self._load_state()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.meta_label = QLabel()
        self.meta_label.setWordWrap(True)
        layout.addWidget(self.meta_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        self.module_label = QLabel()
        layout.addWidget(self.module_label)

        self.content = QTextEdit()
        self.content.setReadOnly(True)
        layout.addWidget(self.content)

        self.quiz_scroll = QScrollArea()
        self.quiz_scroll.setWidgetResizable(True)
        self.quiz_container = QWidget()
        self.quiz_layout = QVBoxLayout(self.quiz_container)
        self.quiz_scroll.setWidget(self.quiz_container)
        self.quiz_scroll.hide()
        layout.addWidget(self.quiz_scroll)
        self._quiz_button_groups = []

        materials_row = QHBoxLayout()
        self.materials_label = QLabel("Материалы курса: нет")
        materials_row.addWidget(self.materials_label)
        self.materials_btn = QPushButton("Открыть материал этапа")
        self.materials_btn.clicked.connect(self._open_materials)
        materials_row.addWidget(self.materials_btn)
        materials_row.addStretch()
        layout.addLayout(materials_row)

        self.advance_btn = QPushButton("Завершить этап")
        self.advance_btn.clicked.connect(self._on_advance)
        layout.addWidget(self.advance_btn)

        self.submit_quiz_btn = QPushButton("Сдать тест")
        self.submit_quiz_btn.clicked.connect(self._on_submit_quiz)
        self.submit_quiz_btn.hide()
        layout.addWidget(self.submit_quiz_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _load_state(self):
        try:
            state = self.course_service.get_passing_state(
                self.actor_user.id, self.course_id
            )
        except (PermissionError, ValueError) as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            self.reject()
            return

        self._state = state
        self.setWindowTitle(f"Прохождение: {state['title']}")
        self.title_label.setText(state["title"])
        self.meta_label.setText(
            f"Отдел: {state['department_name']} | "
            f"Срок: {state['deadline_days']} дн. | "
            f"Порог сдачи: {state['pass_threshold']}% | "
            f"Статус: {state['status']}"
        )
        self.progress_bar.setValue(int(round(state["progress"])))
        self.progress_bar.setFormat(f"Прогресс: {state['progress']:.0f}%")

        self._clear_quiz_ui()
        self.quiz_scroll.hide()
        self.submit_quiz_btn.hide()
        self.advance_btn.show()

        if state["is_completed"]:
            self.module_label.setText(
                f"Курс завершён ({state['modules_completed']}/{state['module_count']} этапов)"
            )
            self.content.setPlainText(
                "Поздравляем! Вы прошли все этапы курса.\n\n"
                "При необходимости вы можете просмотреть материалы через кнопку «Просмотр»."
            )
            self.advance_btn.setEnabled(False)
            self.advance_btn.setText("Курс завершён")
            self._load_materials_info()
            return

        module_index = state["current_module"]
        self.module_label.setText(
            f"Этап {module_index} из {state['module_count']} "
            f"(пройдено: {state['modules_completed']})"
        )

        if state.get("is_practice"):
            self.advance_btn.hide()
            module_quiz = state.get("module_quiz") or {}
            if module_quiz.get("has_quiz"):
                self.content.setPlainText(
                    f"Курс типа «Практика» — этап {module_index}.\n\n"
                    f"Ответьте на {module_quiz['question_count']} вопросов. "
                    f"Для перехода к следующему этапу нужно набрать "
                    f"не менее {state['pass_threshold']}% правильных ответов."
                )
                self._build_quiz_ui(module_quiz)
                self.quiz_scroll.show()
                self.submit_quiz_btn.show()
                self.submit_quiz_btn.setEnabled(True)
                self.submit_quiz_btn.setText(f"Сдать тест этапа {module_index}")
            else:
                self.content.setPlainText(
                    f"Этап {module_index}: тест не загружен.\n\n"
                    "Обратитесь к руководителю — к этапу должен быть прикреплён "
                    ".docx файл с вопросами и ответами."
                )
                self.submit_quiz_btn.show()
                self.submit_quiz_btn.setEnabled(False)
                self.submit_quiz_btn.setText("Тест не загружен")
        else:
            course_stub = SimpleNamespace(description=state["description"])
            module_text = build_module_content(
                course_stub, module_index, state["module_count"]
            )
            module_text += (
                "\n\nИзучите материал текущего этапа и нажмите «Открыть материал этапа», "
                "если файл прикреплён."
            )
            self.content.setPlainText(module_text)
            self.advance_btn.setEnabled(True)
            self.advance_btn.setText(f"Завершить этап {module_index}")

        self._load_materials_info()

    def _clear_quiz_ui(self):
        while self.quiz_layout.count():
            item = self.quiz_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._quiz_button_groups = []

    def _build_quiz_ui(self, module_quiz):
        self._clear_quiz_ui()
        option_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for question_index, question in enumerate(module_quiz.get("questions", []), start=1):
            question_label = QLabel(f"{question_index}. {question['question']}")
            question_label.setWordWrap(True)
            question_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.quiz_layout.addWidget(question_label)

            group = QButtonGroup(self)
            group.setExclusive(True)
            for option_index, option_text in enumerate(question["options"]):
                letter = (
                    option_letters[option_index]
                    if option_index < len(option_letters)
                    else str(option_index + 1)
                )
                radio = QRadioButton(f"{letter}) {option_text}")
                group.addButton(radio, option_index)
                self.quiz_layout.addWidget(radio)
            self._quiz_button_groups.append(group)
            self.quiz_layout.addSpacing(8)

    def _current_module_index(self):
        if not hasattr(self, "_state"):
            return None
        if self._state.get("is_completed"):
            return self._state.get("module_count")
        return self._state.get("current_module")

    def _load_materials_info(self):
        if not self.material_service:
            self.materials_label.setText("Материал этапа: недоступен")
            self.materials_btn.setEnabled(False)
            self.materials_btn.setText("Открыть материал этапа")
            return

        module_index = self._current_module_index()
        if not module_index:
            self.materials_label.setText("Материал этапа: —")
            self.materials_btn.setEnabled(False)
            return

        try:
            payload = self.material_service.list_materials(
                self.actor_user.id,
                self.course_id,
                module_index=module_index,
            )
            material = payload.get("current_module", {}).get("material")
            self._current_material = material
            if material:
                display_name = material.get("display_name", material["original_name"])
                self.materials_label.setText(f"Этап {module_index}: {display_name}")
                is_quiz = material.get("content_kind") == "quiz"
                self.materials_btn.setEnabled(
                    not is_quiz or not self.actor_user.is_role("employee")
                )
                if is_quiz and self.actor_user.is_role("employee"):
                    self.materials_btn.setText("Тест ниже")
                else:
                    self.materials_btn.setText("Открыть материал этапа")
            else:
                self._current_material = None
                self.materials_label.setText(f"Этап {module_index}: материал не прикреплён")
                self.materials_btn.setEnabled(False)
                self.materials_btn.setText("Открыть материал этапа")
        except (PermissionError, ValueError):
            self._current_material = None
            self.materials_label.setText("Материал этапа: нет доступа")
            self.materials_btn.setEnabled(False)
            self.materials_btn.setText("Открыть материал этапа")

    def _open_materials(self):
        if not self.material_service:
            return
        module_index = self._current_module_index()
        if not module_index:
            return
        try:
            file_path = self.material_service.get_module_material_path(
                self.actor_user.id, self.course_id, module_index
            )
        except ValueError:
            open_course_materials_dialog(
                self,
                self.actor_user,
                self.material_service,
                self.course_id,
            )
            return
        except (PermissionError, ValueError) as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return

        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path))):
            QMessageBox.warning(self, "Открыть", f"Не удалось открыть файл:\n{file_path}")

    def _on_submit_quiz(self):
        if not self._quiz_button_groups:
            return

        answers = []
        for index, group in enumerate(self._quiz_button_groups, start=1):
            selected = group.checkedId()
            if selected < 0:
                QMessageBox.warning(
                    self, "Тест", f"Ответьте на вопрос {index}"
                )
                return
            answers.append(selected)

        try:
            new_progress = self.course_service.submit_module_quiz(
                self.actor_user.id, self.course_id, answers
            )
        except (PermissionError, ValueError) as exc:
            QMessageBox.warning(self, "Тест не сдан", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сдать тест: {exc}")
            return

        if self.on_progress:
            self.on_progress()

        if new_progress >= 100:
            QMessageBox.information(self, "Готово", "Тест сдан! Курс успешно завершён!")
        else:
            QMessageBox.information(self, "Готово", "Тест сдан! Переход к следующему этапу.")
        self._load_state()

    def _on_advance(self):
        try:
            new_progress = self.course_service.advance_module(
                self.actor_user.id, self.course_id
            )
        except (PermissionError, ValueError) as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить прогресс: {exc}")
            return

        if self.on_progress:
            self.on_progress()

        if new_progress >= 100:
            QMessageBox.information(self, "Готово", "Курс успешно завершён!")
        self._load_state()


def open_course_passing_dialog(
    actor_user, course_service, course_id, parent, material_service=None, on_success=None
):
    dialog = CoursePassingDialog(
        actor_user,
        course_service,
        course_id,
        material_service=material_service,
        on_progress=on_success,
        parent=parent,
    )
    dialog.exec()


class CourseDetailsDialog(QDialog):
    def __init__(
        self,
        course,
        progress=None,
        materials_summary="0/0",
        actor_user=None,
        material_service=None,
        parent=None,
    ):
        super().__init__(parent)
        self.actor_user = actor_user
        self.material_service = material_service
        self.course_id = course.id
        self.setWindowTitle("Просмотр курса")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        info = QTextEdit()
        info.setReadOnly(True)

        module_count = getattr(course, "module_count", DEFAULT_MODULES_PER_COURSE) or DEFAULT_MODULES_PER_COURSE
        lines = [
            f"Название: {course.title}",
            f"Тип курса: {course_type_label(getattr(course, 'course_type', None))}",
            f"Отдел: {course.department.name if course.department else '—'}",
            f"Создатель: {course.creator.full_name if course.creator else '—'}",
            f"Количество этапов: {module_count}",
            f"Срок прохождения: {course.deadline_days} дн.",
            f"Порог сдачи: {course.pass_threshold}%",
            f"Материалов: {materials_summary}",
            f"Статус: {'Активен' if course.is_active else 'Неактивен'}",
            f"Создан: {course.created_at.strftime('%d.%m.%Y %H:%M') if course.created_at else '—'}",
        ]
        if progress is not None:
            lines.append(f"Ваш прогресс: {progress:.0f}%")
        lines.append("")
        lines.append("Описание:")
        lines.append(course.description or "Описание не указано")
        info.setPlainText("\n".join(lines))
        layout.addWidget(info)

        actions = QHBoxLayout()
        self.materials_btn = QPushButton("Материалы курса")
        self.materials_btn.clicked.connect(self._open_materials)
        self.materials_btn.setEnabled(
            material_service is not None and actor_user is not None
        )
        actions.addWidget(self.materials_btn)
        actions.addStretch()
        layout.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _open_materials(self):
        if not self.material_service or not self.actor_user:
            return
        open_course_materials_dialog(
            self,
            self.actor_user,
            self.material_service,
            self.course_id,
        )


def show_course_details(
    actor_user, course_service, course_id, parent, material_service=None
):
    try:
        course, progress = course_service.get_course_details(actor_user.id, course_id)
    except PermissionError as exc:
        QMessageBox.warning(parent, "Доступ запрещён", str(exc))
        return
    except ValueError as exc:
        QMessageBox.warning(parent, "Ошибка", str(exc))
        return

    materials_summary = "0/0"
    if material_service:
        try:
            payload = material_service.list_materials(actor_user.id, course_id)
            materials_summary = (
                f"{payload['attached_count']}/{payload['module_count']}"
            )
        except (PermissionError, ValueError):
            materials_summary = "0/0"

    CourseDetailsDialog(
        course,
        progress,
        materials_summary=materials_summary,
        actor_user=actor_user,
        material_service=material_service,
        parent=parent,
    ).exec()

