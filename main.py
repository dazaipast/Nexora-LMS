"""
Nexora LMS — система корпоративного обучения.
"""

import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from database import DatabaseManager
from services import AuthManager
from ui.theme import application_stylesheet, FONT_FAMILY
from ui.windows import LoginWindow, MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(application_stylesheet())
    app.setFont(QFont(FONT_FAMILY, 10))
    db_manager = DatabaseManager()
    db_manager.init_test_data()
    db_manager.ensure_demo_users()
    auth_manager = AuthManager(db_manager)

    login = LoginWindow(auth_manager)
    main_window = None

    def on_login():
        nonlocal main_window
        main_window = MainWindow(auth_manager, db_manager)
        main_window.show()

    login.login_success.connect(on_login)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
