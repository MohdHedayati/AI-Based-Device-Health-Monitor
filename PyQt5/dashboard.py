import os
import json
import sys

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
        self.monitor_process = None

        self.setWindowTitle("Dashboard")
        self.setFixedSize(400, 250)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.hello_label = QLabel(f"Hello, {self.user_name}!")
        self.hello_label.setAlignment(Qt.AlignCenter)

        self.start_btn = QPushButton("Start Monitoring")
        self.stop_btn = QPushButton("Stop Monitoring")
        self.upload_btn = QPushButton("Upload Data")
        self.logout_btn = QPushButton("Logout")

        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.upload_btn.clicked.connect(self.handle_upload)
        self.logout_btn.clicked.connect(self.handle_logout)

        layout.addWidget(self.hello_label)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.upload_btn)
        layout.addWidget(self.logout_btn)

        self.setLayout(layout)


    def handle_logout(self):
        # Delete local token file  so next launch shows login
        if os.path.exists(TOKEN_FILE):
            try:
                os.remove(TOKEN_FILE)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Logout Warning",
                    f"Could not delete token file:\n{e}",
                )

        QMessageBox.information(self, "Logged Out", "You have been logged out.")
        if self.monitor_process and self.monitor_process.poll() is None:
            self.monitor_process.terminate()
            self.monitor_process.wait()
        # After logout, close dashboard and reopen login window
        from auth import LoginWindow

        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def handle_upload(self):
        try:
            from uploader import upload
            upload()
            QMessageBox.information(self, "Success", "Data uploaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Upload Failed", str(e))
    def start_monitoring(self):
        if self.monitor_process and self.monitor_process.poll() is None:
            QMessageBox.information(self, "Info", "Monitoring already running.")
            return

        self.monitor_process = subprocess.Popen(
            [sys.executable, "get_info.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        QMessageBox.information(self, "Started", "System monitoring started.")
    def stop_monitoring(self):
        if self.monitor_process and self.monitor_process.poll() is None:
            self.monitor_process.terminate()
            self.monitor_process.wait()
            self.monitor_process = None
            file_path = "data/history.json"
            if os.path.exists(file_path):
                os.remove(file_path)
            QMessageBox.information(self, "Stopped", "Monitoring stopped.")
        else:
            QMessageBox.information(self, "Info", "Monitoring not running.")



