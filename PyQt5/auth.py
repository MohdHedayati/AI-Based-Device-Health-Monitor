import os
import json
import socket

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QInputDialog,
)
from PyQt5.QtCore import Qt

from google_auth_oauthlib.flow import InstalledAppFlow
import webbrowser

TOKEN_FILE = "token.json"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login with Google")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.info_label = QLabel("Please log in with your Google account.")
        self.info_label.setAlignment(Qt.AlignCenter)

        self.login_button = QPushButton("Login with Google")
        self.login_button.clicked.connect(self.handle_login)

        layout.addWidget(self.info_label)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def handle_login(self):
        if not self._has_internet():
            QMessageBox.critical(
                self,
                "Network Error",
                "No internet connection. Please connect to the internet and try again.",
            )
            return

        try:
            # Create flow without local server
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                scopes=SCOPES,
            )
            # IMPORTANT: set redirect URI for manual copy-paste flow
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            # Step 1: get authorization URL
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
            )

            # Step 2: open browser for user to authenticate
            webbrowser.open(auth_url, new=1)

            # Step 3: user pastes authorization code back
            code, ok = QInputDialog.getText(
                self,
                "Google Login",
                "1. A browser tab opened.\n"
                "2. Complete login and grant access.\n"
                "3. On the final page, copy the authorization code.\n"
                "4. Paste it here:",
            )
            if not ok or not code:
                return

            # Step 4: exchange code for tokens
            flow.fetch_token(code=code)

            creds = flow.credentials
            session = flow.authorized_session()
            profile_info = session.get(
                "https://www.googleapis.com/userinfo/v2/me"
            ).json()

            data_to_store = {
                "token": creds.token,
                "refresh_token": getattr(creds, "refresh_token", None),
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": list(creds.scopes) if hasattr(creds, "scopes") else SCOPES,
                "profile": profile_info,
            }

            with open(TOKEN_FILE, "w") as f:
                json.dump(data_to_store, f)
            
            from dashboard import DashboardWindow

            user_name = profile_info.get("name") or profile_info.get("email", "User")
            self.dashboard = DashboardWindow(user_name=user_name)
            self.dashboard.show()
            self.close()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Login Failed",
                f"An error occurred during login:\n{e}",
            )

    def _has_internet(self, host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.close()
            return True
        except OSError:
            return False
