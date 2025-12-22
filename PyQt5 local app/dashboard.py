import os
import json

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtCore import Qt
import subprocess

TOKEN_FILE = "token.json"
ENV_LOGGED_IN = "APP_LOGGED_IN"


class DashboardWindow(QWidget):
    def __init__(self, user_name: str):
        super().__init__()
        self.user_name = user_name or "User"

        self.setWindowTitle("Dashboard")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.hello_label = QLabel(f"Hello, {self.user_name}!")
        self.hello_label.setAlignment(Qt.AlignCenter)

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.handle_logout)

        layout.addWidget(self.hello_label)
        layout.addWidget(self.logout_button)

        self.setLayout(layout)

        self.monitor_process = subprocess.Popen(
            ["python", "get_info.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def handle_logout(self):
        # Delete local token file and reset env so next launch shows login
        if os.path.exists(TOKEN_FILE):
            try:
                os.remove(TOKEN_FILE)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Logout Warning",
                    f"Could not delete token file:\n{e}",
                )

        os.environ[ENV_LOGGED_IN] = "0"

        QMessageBox.information(self, "Logged Out", "You have been logged out.")

        # After logout, close dashboard and reopen login window
        from auth import LoginWindow

        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()
        self.monitor_process.terminate()

    def handle_upload(self):
        try:
            from uploader import upload
            upload()
            QMessageBox.information(self, "Success", "Data uploaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Upload Failed", str(e))

