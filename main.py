
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/drive.readonly"
]
flow = InstalledAppFlow.from_client_secrets_file(
    "credentials/credentials.json",
    SCOPES
)

credentials = flow.run_local_server(port=0)

service = build("forms", "v1", credentials=credentials)

# Fetch existing Google Forms
drive_service = build(
    "drive",
    "v3",
    credentials=credentials
)

results = drive_service.files().list(
    q="mimeType='application/vnd.google-apps.form' and trashed=false",
    pageSize=100,
    orderBy="modifiedTime desc",
    fields="nextPageToken, files(id, name, webViewLink, modifiedTime)"
).execute()

forms = results.get("files", [])

if not forms:
    print("No Google Forms found.")

else:
    print(f"\nFound {len(forms)} Google Form(s):\n")

    for index, form in enumerate(forms, start=1):
        print(f"{index}. {form['name']}")
        print(f"   Form ID: {form['id']}")
        print(f"   Link: {form.get('webViewLink', 'Not available')}")
        print()