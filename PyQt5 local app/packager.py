import json
import uuid

TOKEN_FILE = "token.json"
HISTORY_FILE = "data/history.json"

def load_email():
    with open(TOKEN_FILE, "r") as f:
        token = json.load(f)
    return token["profile"]["email"]

def generate_secret_id():
    # Stable per-machine secret
    # (store once, reuse forever)
    try:
        with open(".secret_id", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        secret_id = str(uuid.uuid4())
        with open(".secret_id", "w") as f:
            f.write(secret_id)
        return secret_id

def build_payload():
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    return {
        "email": load_email(),
        "secret_id": generate_secret_id(),
        "data": history
    }
