from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QListWidget, QTableWidget, QMessageBox, QFileDialog, QDialog,
)
from PyQt6.QtCore import Qt

from constants import COURSE_TABLE_HEADERS
from ui.style_helpers import styled_widget
from ui.table_helpers import (
    configure_readonly_table,
    fill_events_list,
    fill_audit_table,
    get_selected_row_id,
)
from ui.dialogs import (
    AddCourseDialog,
    open_assign_course_dialog,
    deactivate_selected_course,
    show_course_details,
    offer_assign_after_create,
    open_course_materials_dialog,
)

class StatCardMixin:
    def _create_stat_card(self, title, value_label, description=None):
        card = styled_widget(QWidget(), "statCard")
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(20, 18, 20, 18)

        title_label = QLabel(title)
        styled_widget(title_label, "statTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        if description:
            desc_label = QLabel(description)
            styled_widget(desc_label, "statDesc")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        layout.addStretch()
        value_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom
        )
        layout.addWidget(value_label)
        return card


class QuickActionsMixin:
    def _switch_to_tab(self, tab_title):
        for index in range(self.tabs.count()):
            if self.tabs.tabText(index) == tab_title:
                self.tabs.setCurrentIndex(index)
                return

    def _create_quick_actions_group(self, actions):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(10)
        for label, callback in actions:
            button = QPushButton(label)
            button.setProperty("class", "headerBtn")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.style().unpolish(button)
            button.style().polish(button)
            button.clicked.connect(callback)
            layout.addWidget(button)
        layout.addStretch()
        return container

    def _export_csv_report(self, export_callable, default_filename):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт",
            default_filename,
            "CSV файлы (*.csv)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"
        try:
            export_callable(file_path)
            QMessageBox.information(self, "Готово", f"Отчёт сохранён:\n{file_path}")
        except (PermissionError, ValueError) as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчёт: {exc}")


class AuditPanelMixin:
    def _create_events_group(self):
        group = QGroupBox("Последние события")
        layout = QVBoxLayout()
        self.events_list = QListWidget()
        self.events_list.setMaximumHeight(170)
        layout.addWidget(self.events_list)
        group.setLayout(layout)
        return group

    def _create_audit_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.audit_table = QTableWidget()
        configure_readonly_table(
            self.audit_table,
            ["Дата", "Пользователь", "Отдел", "Действие", "Подробности"],
        )
        layout.addWidget(self.audit_table)
        return tab

    def _refresh_audit_widgets(self, db):
        logs = self.audit_service.list_logs(self.actor_user.id, db=db)
        fill_audit_table(self.audit_table, logs)
        events_list = getattr(self, "events_list", None)
        if events_list is not None:
            events = self.audit_service.list_recent_events(self.actor_user.id, db=db)
            fill_events_list(events_list, events)


class CoursesPanelMixin:
    course_fixed_department_id = None
    course_created_message = "Курс успешно создан"

    def _add_courses_toolbar(self, layout):
        actions = QHBoxLayout()
        create_btn = QPushButton("Создать курс")
        create_btn.clicked.connect(self._open_create_course_dialog)
        view_btn = QPushButton("Просмотр")
        view_btn.clicked.connect(self._open_view_course_dialog)
        assign_btn = QPushButton("Назначить обучение")
        assign_btn.clicked.connect(self._open_assign_course_dialog)
        materials_btn = QPushButton("Материалы")
        materials_btn.clicked.connect(self._open_course_materials_dialog)
        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self._deactivate_selected_course)
        actions.addWidget(create_btn)
        actions.addWidget(view_btn)
        actions.addWidget(assign_btn)
        actions.addWidget(materials_btn)
        actions.addWidget(delete_btn)
        actions.addStretch()
        layout.addLayout(actions)

    def _create_courses_table(self):
        table = QTableWidget()
        configure_readonly_table(table, COURSE_TABLE_HEADERS)
        table.doubleClicked.connect(self._open_view_course_dialog)
        return table

    def _open_create_course_dialog(self):
        dialog = AddCourseDialog(
            self.db_manager,
            self.actor_user,
            self.course_service,
            fixed_department_id=self.course_fixed_department_id,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Готово", self.course_created_message)
            self._load_data()
            offer_assign_after_create(
                self,
                self.actor_user,
                self.course_service,
                dialog.created_course_id,
                self._load_data,
            )

    def _open_assign_course_dialog(self):
        open_assign_course_dialog(
            self, self.actor_user, self.course_service, on_success=self._load_data
        )

    def _deactivate_selected_course(self):
        deactivate_selected_course(
            self, self.actor_user, self.course_service, self.courses_table, self._load_data
        )

    def _open_view_course_dialog(self):
        course_id = get_selected_row_id(self.courses_table)
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
        course_id = get_selected_row_id(self.courses_table)
        if not course_id:
            QMessageBox.information(self, "Материалы", "Выберите курс в таблице")
            return
        open_course_materials_dialog(
            self,
            self.actor_user,
            self.material_service,
            course_id,
            on_change=self._load_data,
        )

