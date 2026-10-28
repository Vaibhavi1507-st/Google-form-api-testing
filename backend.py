import hashlib
import hmac
import secrets
import time
import os
import streamlit as st
import json
from datetime import datetime, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]




def create_oauth_flow(state=None):
    try:
       oauth = st.secrets["google_oauth"]
    except Exception:
       oauth = {}
    client_id = os.getenv(
        "GOOGLE_CLIENT_ID",
        oauth.get("client_id", ""),
    )
    client_secret = os.getenv(
        "GOOGLE_CLIENT_SECRET",
        oauth.get("client_secret", ""),
    )
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI",
        oauth.get("redirect_uri", ""),
    )
    
    client_id = os.getenv("GOOGLE_CLIENT_ID") or oauth.get("client_id", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or oauth.get("client_secret", "")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or oauth.get("redirect_uri", "")

    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
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
    secret = os.getenv("OAUTH_STATE_SECRET")

    if not secret:
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
        secret = os.getenv("OAUTH_STATE_SECRET")

        if not secret:
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

    except (ValueError, TypeError, KeyError):
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

    print(": Credentials found:", credentials is not None)

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

def fetch_form_responses(form_id):
    credentials = get_credentials()

    if not credentials:
        return []

    forms_service = build(
        "forms",
        "v1",
        credentials=credentials,
    )

    results = forms_service.forms().responses().list(
        formId=form_id,
    ).execute()

    return results.get("responses", [])



def save_responses_to_json(form_id, form_name, responses):
    questions = fetch_form_questions(form_id)

    os.makedirs("data", exist_ok=True)
    simplified_responses = []

    for response in responses:
        answers = {}

        for question_id, answer_data in response.get("answers", {}).items():
            question_title = questions.get(question_id, question_id)

            values = [
                answer.get("value", "")
                for answer in answer_data.get("textAnswers", {}).get("answers", [])
            ]

            answers[question_title] = ", ".join(values)

        simplified_responses.append({
            "response_id": response.get("responseId"),
            "submitted_at": response.get("lastSubmittedTime"),
            "answers": answers
        })

    data = {
        "form_id": form_id,
        "form_name": form_name,
        "responses": simplified_responses
    }

    file_path = os.path.join("data", f"responses_{form_id}.json")

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    return file_path

def fetch_form_questions(form_id):
    credentials = get_credentials()

    if not credentials:
        return {}

    forms_service = build(
        "forms",
        "v1",
        credentials=credentials,
    )

    form = forms_service.forms().get(
        formId=form_id
    ).execute()

    questions = {}

    for item in form.get("items", []):
        question_item = item.get("questionItem", {})
        question = question_item.get("question", {})
        question_id = question.get("questionId")

        if question_id:
            questions[question_id] = item.get(
                "title", "Untitled question"
            )

    return questions
