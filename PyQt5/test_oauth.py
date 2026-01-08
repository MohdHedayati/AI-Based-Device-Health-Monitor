from google_auth_oauthlib.flow import InstalledAppFlow
from requests_oauthlib.oauth2_session import OAuth2Session
import json

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES,
    )

    print("client_type:", flow.client_type)
    print("client_config:", flow.client_config)

    try:
        flow.run_local_server(
            host="127.0.0.1",
            port=8088,
            open_browser=True,
        )
        creds = flow.credentials
        print("TOKEN:", creds.token)
    except Exception as e:
        print("EXCEPTION TYPE:", type(e))
        print("EXCEPTION:", e)
        # For some error types we can inspect response
        if hasattr(e, "response") and e.response is not None:
            print("STATUS:", e.response.status_code)
            print("BODY:", e.response.text)

if __name__ == "__main__":
    main()
