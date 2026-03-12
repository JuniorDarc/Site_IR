import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def get_drive_service():
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS")

    credentials_dict = json.loads(credentials_json)

    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=SCOPES
    )

    return build("drive", "v3", credentials=credentials)
