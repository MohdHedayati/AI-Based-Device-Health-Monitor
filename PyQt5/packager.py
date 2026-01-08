import json
import uuid
import platform
import os
import socket
from datetime import datetime
TOKEN_FILE = "token.json"
HISTORY_FILE = "data/history.json"

def load_email():
    with open(TOKEN_FILE, "r") as f:
        token = json.load(f)
    return token["profile"]["email"]

def generate_secret_id():
    # Stable per-machine secret
    # (store once, reuse forever)
    secret_id = str(uuid.uuid4())
    with open(".secret_id", "w") as f:
        f.write(secret_id)
    return secret_id

def build_payload():
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    return {
        # maps to user_email
        "user_email": load_email(),

        # maps to raw_data
        "raw_data": history,

        # metadata (stored directly in table)
        "device_name": socket.gethostname(),  # safer than os.getlogin()
        "os": platform.system(),

        # optional but useful
        "source": "desktop_app",

        # status handled server-side ideally,
        # but safe to set explicitly
        "status": "pending"
    }

