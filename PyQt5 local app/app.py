import os
import sys
import json

from PyQt5.QtWidgets import QApplication

from auth import LoginWindow
from dashboard import DashboardWindow

TOKEN_FILE = "token.json"          # where Google credentials are stored
ENV_LOGGED_IN = "APP_LOGGED_IN"    # environment variable flag


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

    # Check env + token file to decide whether user is already logged in
    logged_in_env = os.environ.get(ENV_LOGGED_IN, "0") == "1"
    user_name = load_user_name_from_token()
    print(logged_in_env)
    print(user_name)
    if logged_in_env and user_name:
        # Show dashboard directly
        window = DashboardWindow(user_name=user_name)
    else:
        # Show login window
        window = LoginWindow()

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
