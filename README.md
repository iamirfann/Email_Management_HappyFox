# Email_Management_HappyFox

Python scripts for connecting to Gmail using OAuth authentication, fetching emails, and applying rules to emails in real-time.


## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Authentication](#authentication)
- [Features](#features)
- [Rules](#rules)


## Installation

1. Clone the repository to your local machine:

    ```bash
    git clone https://github.com/iamirfann/Email_Management_HappyFox.git

    cd email-management

    pip install -r requirements.txt


## Usage

Provide detailed instructions on how to use your email management scripts. Include examples and command-line usage if applicable.

To fetch and process emails, follow these steps:

1. Run the first script to connect to Gmail and fetch emails:

    ```bash
    python SaveEmails.py

2. Run the second script to process, apply rules and perform action:

    ```bash
    python ProcessEmails.py


## Authentication

1. When you run the scripts, you will redirect to google authentication page in your default browser.

2. Select your gmail account and click on advanced and again click on go to irfan's app.

3. Then click on select all to select all permissions enable to run this scripts and click on continue.

4. Then you will see a text "your authentication has been completed"

5. Now go to your terminal where you have run the scripts. It would have started collecting emails.



## Features

- OAuth authentication for connecting to Gmail.
- Fetching and storing emails in a SQLite database.
- Applying rules to emails in real-time.
- Support for customizable rule conditions [you can edit/add the rules.json for your customizable rules].
- Marking emails as read or unread.
- Moving emails to specified folders.


## Rules

Rules are defined in a JSON format. Each rule consists of conditions and actions. Here's an example:
You can manually edit/add any json values to the rules.json 

```json
{
    "collective_predicate": "All",
    "conditions": [
        {
            "field": "subject",
            "predicate": "contains",
            "value": "Interview"
        },
        {
            "field": "sender",
            "predicate": "does not contain",
            "value": "happyfox.hire.trakstar.com"
        },
        {
            "field": "date",
            "predicate": "lesser than",
            "value": "2023-09-12"
        }
    ],
    "actions": {
        "mark_as_read": true,
        "move_to_folder": "Inbox"
    },
    "active": 1
}
