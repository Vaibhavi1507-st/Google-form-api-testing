
import streamlit as st

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_FILE = "credentials/credentials.json"


def connect_google_account():
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        SCOPES,
    )

    credentials = flow.run_local_server(
        port=0,
        prompt="select_account",
    )

    st.session_state["google_credentials"] = credentials


def get_credentials():
    credentials = st.session_state.get("google_credentials")

    if not credentials:
        return None

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        st.session_state["google_credentials"] = credentials

    if not credentials.valid:
        st.session_state.pop("google_credentials", None)
        return None

    return credentials


def fetch_forms():
    credentials = get_credentials()

    if not credentials:
        return []

    drive_service = build(
        "drive",
        "v3",
        credentials=credentials,
    )

    forms = []
    page_token = None

    while True:
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.form' and trashed=false",
            pageSize=100,
            orderBy="modifiedTime desc",
            fields="nextPageToken, files(id, name, webViewLink, modifiedTime)",
            pageToken=page_token,
        ).execute()

        forms.extend(results.get("files", []))
        page_token = results.get("nextPageToken")

        if not page_token:
            break

    return forms
