import os
from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import asyncio, json, string, re
from concurrent.futures import ThreadPoolExecutor
import sqlite3

# connect to sqlite database
conn = sqlite3.connect('email_db.sqlite')
cursor = conn.cursor()

# database table structue
cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, sender TEXT, receiver TEXT, date TIMESTAMP,
        message TEXT, read INTEGER, folder TEXT
    )'''
    )

conn.commit()

# Gmail Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Creds Json
CLIENT_SECRET_FILE = 'credentials.json'

# sanitize email for security purpose
async def sanitize_emails(content):
    # removing the ascii and non printables
    sanitized_content = ''.join(filter(lambda x: x in string.printable, content))
    sanitized_content = re.sub(r'[;<>&]', '', sanitized_content)
    return sanitized_content

# save email in to db
async def insert_email(subject, sender, receiver, date, message):
    try:
        print("coming in insert email")
        query = '''
            INSERT INTO email_details (subject, sender, receiver, date, message, read, folder) VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        # 
        read = 0
        folder = ""  
        cursor.execute(query, (subject, sender, receiver, date, message, read, folder))
        conn.commit()

        print("*", "saved to database")
    
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
            message_body = msg['snippet']
            respone_json = {
                "sender": sender,
                "receiver": receiver,
                "date": date,
                "subject": subject,
                "message": message_body
            }
            return respone_json
        
        with ThreadPoolExecutor() as executor:
            response = await asyncio.get_event_loop().run_in_executor(
                executor, get_email_details)

        print("Date: ", response['date'])
        print("Sender: ", response['sender'])
        print("Receiver: ", response['receiver'])
        print("Message: ", response['message'])
        print("Subject: ", response['subject'])
        print('-' * 20, "saving to database")
        
        # cursor.execute(''' INSERT INTO email_details (subject, sender, receiver, date, message) VALUES (?, ?, ?, ?, ?)''', 
        #                (response['subject'], response['sender'], response['receiver'], response['date'], response['message']))
        # conn.commit()

        # print("*", "saved to database")
        sanitized_email = await sanitize_emails(response['message'])
        email_resp = await insert_email(response['subject'], response['sender'], response['receiver'], response['date'], sanitized_email)

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