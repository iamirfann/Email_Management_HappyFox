import os
import sqlite3
from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import email.utils
import json
import asyncio
import datetime
import requests
from requests_oauthlib import OAuth2Session

# Gmail Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.labels']

# Creds Json
CLIENT_SECRET_FILE = 'credentials.json'

# Load the Rules Json
with open('rules.json', 'r') as rules_file:
    rules_data = json.load(rules_file)

conn = sqlite3.connect('email_db.sqlite')
cursor = conn.cursor()


async def fetch_emails(service):
    try:
        cursor.execute('SELECT * FROM email_details')
        emails = cursor.fetchall()
        if not emails:
            print('No emails found in the database.')
        else:
            print(f'Total emails in the database: {len(emails)}')
            print("*" * 20, "Fetching Emails From Database", "*" * 20) 
            print("*" * 20, "Processing Emails", "*" * 20) 
            tasks = [process_emails(service, email) for email in emails]
            await asyncio.gather(*tasks)
    
    except Exception as e:
        print(f"Error fetching emails from the database: {str(e)}")


async def process_emails(service, email):
    # Display email details
    Id = email[0]
    emailId = email[1]
    subject = email[2]
    sender = email[3]
    receiver = email[4]
    date = email[5]
    message = email[6]
    

    # fetch rules
    for rule in rules_data:
        for rule_name, rule_data in rule.items():
            if rule_data.get('active') == 1 and rule_data.get('collective_predicate') == "Any":
                if any(check_rule(email, condition) for condition in rule_data.get("conditions")):
                    if rule_data["actions"]["mark_as_read"]:
                        mark_as_read(service, emailId)
                    else:
                        mark_as_unread(service, emailId)
                    if "move_to_folder" in rule_data["actions"]:
                        move_to_folder(service, emailId, rule_data["actions"]['move_to_folder'])

                    print("*" * 20, "Rule Condition Checked and Action Performed for Email : ", emailId , "*" * 20) 

            if rule_data.get('active') == 1 and rule_data.get('collective_predicate') == "All":
                if all(check_rule(email, condition) for condition in rule_data.get("conditions")):
                    if rule_data["actions"]["mark_as_read"]:
                        mark_as_read(service, emailId)
                    else:
                        mark_as_unread(service, emailId)
                    if "move_to_folder" in rule_data["actions"]:
                        move_to_folder(service, emailId, rule_data["actions"]['move_to_folder'])
                    
                    print("*" * 20, "Rule Condition Checked and Action Performed for Email : ", emailId , "*" * 20) 


def get_label_id(service, folder_name):
    try:
        labels = service.users().labels().list(userId='me').execute()
        for label in labels['labels']:
            if label['name'] == folder_name:
                return label['id']
        return None
    except Exception as e:
        print(f"Error getting label ID for folder: {str(e)}")
        return None


def mark_as_read(service, email_id):
    try:
        service.users().messages().modify(userId='me', id=email_id, body={'removeLabelIds': ['UNREAD']}).execute()
    except Exception as e:
        print(f"Error marking email as read: {str(e)}")
    

def mark_as_unread(service, email_id):
    try:
        service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': ['UNREAD']}).execute()
    except Exception as e:
        print(f"Error marking email as read: {str(e)}")


def move_to_folder(service, email_id, folder_name):
    try:
        label_id = get_label_id(service, folder_name)
        if label_id:
            service.users().messages().modify(userId='me', id=email_id, body={'addLabelIds': [label_id]}).execute()
        else:
            print(f"Error: Label '{folder_name}' not found.")
    except Exception as e:
        print(f"Error moving email to folder: {str(e)}")


def check_rule(email, condition):
    field = condition["field"]
    predicate = condition["predicate"]
    value = condition["value"]

    if field == "subject":
        if predicate == "contains" and value in email[2]:
            return True
        elif predicate == "does not contains" and value not in email[2]:
            return True
    elif field == "sender":
        if predicate == "contains" and value in email[3]:
            return True
        elif predicate == "does not contain" and value not in email[3]:
            return True
    elif field == "receiver":
        if predicate == "contains" and value in email[4]:
            return True
        elif predicate == "does not contain" and value not in email[4]:
            return True
    elif field == "message":
        if predicate == "contains" and value in email[6]:
            return True
        elif predicate == "does not contain" and value not in email[6]:
            return True
    elif field == "date":
        email_date = datetime.datetime.strptime(email[5], "%Y-%m-%d %H:%M:%S")
        rule_date = datetime.datetime.strptime(value, "%Y-%m-%d")
        if predicate == "greater than" and email_date > rule_date:
            return True
        elif predicate == "lesser than" and email_date > rule_date:
            return True
    return False


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
    emails = await fetch_emails(service)

if __name__ == '__main__':
    asyncio.run(main())
    # asyncio.run(fetch_emails())
conn.close()
print("*" * 20, "Completed Processing Emails", "*" * 20) 