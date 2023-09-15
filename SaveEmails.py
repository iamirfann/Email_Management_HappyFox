import os
from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import asyncio, json

# Gmail Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Creds Json
CLIENT_SECRET_FILE = 'credentials.json'

# logic for fetching email's
async def fetch_emails(email_id, creds):
    print() 

def main():
    # Authenticate the Gmail
    creds = None
    if os.path.exists('token.json'):
        creds = credentials.Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())


    # gmail api service
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])

    if messages:
        print("Emails in Inbox")
        # task
    else:
        print("No Emails")


if __name__ == '__main__':
    asyncio.run(main())