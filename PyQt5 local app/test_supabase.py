from supabase import create_client
import uuid

SECRETS_PATH = "supabase_secrets.json"

url = "https://YOUR_PROJECT_ID.supabase.co"
key = "SERVICE_ROLE_KEY"

supabase = create_client(url, key)

data = {
    "email": "test@local",
    "secret_id": str(uuid.uuid4()),
    "payload": {"cpu": 40, "ram": 60},
    "device_name": "arch-linux",
    "os": "Linux"
}

res = supabase.table("system_reports").insert(data).execute()
print(res)
