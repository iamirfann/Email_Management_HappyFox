import os
from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import asyncio, json, string, re
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import datetime
import email.utils

# connect to sqlite database
conn = sqlite3.connect('email_db.sqlite')
cursor = conn.cursor()

# database table structue
cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT, emailid VARCHAR, subject TEXT, sender TEXT, receiver TEXT, date TIMESTAMP,
        message TEXT
    )'''
    )

conn.commit()

# Gmail Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.labels']

# Creds Json
CLIENT_SECRET_FILE = 'credentials.json'

# sanitize email for security purpose
async def sanitize_emails(content):
    # removing the ascii and non printables
    sanitized_content = ''.join(filter(lambda x: x in string.printable, content))
    sanitized_content = re.sub(r'[;<>&]', '', sanitized_content)
    return sanitized_content

# save email in to db
async def insert_email(email_id, subject, sender, receiver, date, message):
    try:
        query = '''
            INSERT INTO email_details (emailid, subject, sender, receiver, date, message) VALUES (?, ?, ?, ?, ?, ?)
        '''
    
        cursor.execute(query, (email_id, subject, sender, receiver, date, message))
        conn.commit()

    except Exception as e:
        print("error inserting emails", str(e))

# logic for fetching email's
async def fetch_emails(msg_id, creds):
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        def get_email_details():
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            headers = msg['payload']['headers']
            subject = [header['value'] for header in headers if header['name'] == 'Subject'][0]
            sender = [header['value'] for header in headers if header['name'] == 'From'][0]
            receiver = [header['value'] for header in headers if header['name'] == 'To'][0]
            date = [header['value'] for header in headers if header['name'] == 'Date'][0]
            formatted_date = email.utils.parsedate_to_datetime(date)
            email_date = formatted_date.strftime("%Y-%m-%d %H:%M:%S")
            message_body = msg['snippet']
            email_id = msg['id']
            
            respone_json = {
                "email_id": email_id,
                "sender": sender,
                "receiver": receiver,
                "date": email_date,
                "subject": subject,
                "message": message_body
            }
            return respone_json
        
        with ThreadPoolExecutor() as executor:
            response = await asyncio.get_event_loop().run_in_executor(
                executor, get_email_details)

        sanitized_email = await sanitize_emails(response['message'])
        email_resp = await insert_email(response['email_id'], response['subject'], response['sender'], response['receiver'], response['date'], sanitized_email)

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
        print("*" * 20, "Fetching & Saving Emails", "*" * 20) 
        tasks = [fetch_emails(message['id'], creds) for message in messages]
        await asyncio.gather(*tasks)
        # task
    else:
        print("No Emails")


if __name__ == '__main__':
    asyncio.run(main())

conn.close()
print("*" * 20, "Completed Saving Emails", "*" * 20)