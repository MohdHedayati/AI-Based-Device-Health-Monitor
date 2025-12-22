from supabase import create_client
from packager import build_payload

SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "SERVICE_ROLE_KEY"  # desktop app = service key

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload():
    payload = build_payload()

    supabase.table("system_reports").upsert(
        payload,
        on_conflict="secret_id"
    ).execute()
