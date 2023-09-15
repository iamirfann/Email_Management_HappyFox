import os
from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import asyncio, json
from concurrent.futures import ThreadPoolExecutor

# Gmail Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Creds Json
CLIENT_SECRET_FILE = 'credentials.json'

# logic for fetching email's
async def fetch_emails(msg_id, creds):
    try:
        service = build('gmail', 'v1', credentials=creds)

        def get_email_details():
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            headers = msg['payload']['headers']
            subject = [header['value'] for header in headers if header['name'] == 'Subject'][0]
            sender = [header['value'] for header in headers if header['name'] == 'From'][0]
            to = [header['value'] for header in headers if header['name'] == 'To'][0]
            date = [header['value'] for header in headers if header['name'] == 'Date'][0]
            message_body = msg['snippet']

            respone_json = {
                "from": sender,
                "to": to,
                "date": date,
                "subject": subject,
                "message": message_body
            }
            return respone_json
        
        with ThreadPoolExecutor() as executor:
            response = await asyncio.get_event_loop().run_in_executor(
                executor, get_email_details)

        print("Date: ", response['date'])
        print("From: ", response['from'])
        print("To: ", response['to'])
        print("Message: ", response['message'])
        print("Subject: ", response['subject'])
        print('-' * 20)
    except Exception as e:
        print(f"Error fetching email details: {str(e)}")


async def main():
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
        tasks = [fetch_emails(message['id'], creds) for message in messages]
        await asyncio.gather(*tasks)
        # task
    else:
        print("No Emails")


if __name__ == '__main__':
    asyncio.run(main())
    # main()