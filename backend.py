import hashlib
import hmac
import secrets
import time
import os
import streamlit as st

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]




def create_oauth_flow(state=None):
    oauth = st.secrets["google_oauth"]
    redirect_uri = oauth["redirect_uri"]

    client_config = {
        "web": {
            "client_id": oauth["client_id"],
            "client_secret": oauth["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = redirect_uri
    return flow

def create_signed_state():
    secret = st.secrets["google_oauth"]["state_secret"]
    timestamp = str(int(time.time()))
    nonce = secrets.token_urlsafe(24)

    payload = f"{timestamp}.{nonce}"
    signature = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload}.{signature}"


def validate_signed_state(state):
    if not state:
        return False

    try:
        timestamp, nonce, signature = state.split(".", 2)

        payload = f"{timestamp}.{nonce}"
        secret = st.secrets["google_oauth"]["state_secret"]

        expected_signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            return False

        age = int(time.time()) - int(timestamp)
        return 0 <= age <= 600

    except (ValueError, TypeError):
        return False




def get_authorization_url():
    state = create_signed_state()
    flow = create_oauth_flow(state=state)

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return authorization_url





def complete_authorization(code, returned_state):
    if not validate_signed_state(returned_state):
        raise ValueError(
            "OAuth state is invalid or expired. Please connect again."
        )

    flow = create_oauth_flow(state=returned_state)
    flow.fetch_token(code=code)

    st.session_state["google_credentials"] = flow.credentials


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
