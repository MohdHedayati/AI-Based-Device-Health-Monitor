import os
import sys
import json

from PyQt5.QtWidgets import QApplication

from auth import LoginWindow
from dashboard import DashboardWindow

TOKEN_FILE = "token.json"          # where Google credentials are stored

def load_user_name_from_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
        # Google's userinfo response usually has "name" and "email"
        profile = data.get("profile", {})
        return profile.get("name") or profile.get("email")
    except Exception:
        return None


def main():

    app = QApplication(sys.argv)

    # Check token file to decide whether user is already logged in
    user_name = load_user_name_from_token()
    print(user_name)
    if user_name:
        # Show dashboard directly
        window = DashboardWindow(user_name=user_name)
    else:
        # Show login window
        window = LoginWindow()

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
