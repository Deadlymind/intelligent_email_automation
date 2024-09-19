import base64
import logging
from email.mime.text import MIMEText
from email.utils import parseaddr
from googleapiclient.errors import HttpError

from gmail_service import get_gmail_service
from openai_service import generate_response

# set up logging
logger = logging.getLogger(__name__)

def list_unread_messages(service, user_id='me'):
    try:
        results = service.users().messages().list(
            userId=user_id, labelIds=['INBOX', 'UNREAD'], maxResults=10).execute()
        messages = results.get('messages', [])
        return messages
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        return []

def get_message(service, msg_id, user_id='me'):
    try:
        message = service.users().messages().get(
            userId=user_id, id=msg_id, format='full').execute()
        return message
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        return None

def get_email_content(message):
    parts = message['payload'].get('parts', [])
    body = ''
    if parts:
        for part in parts:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                data = part['body']['data']
                decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
                body += decoded_data
    else:
        if 'data' in message['payload']['body']:
            data = message['payload']['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
    return body

def create_prompt(email_body):
    prompt = f"""You are an AI assistant that composes professional and friendly email replies. Read the email below and draft an appropriate response.

Email:
{email_body}

Response:"""
    return prompt

def create_email(to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_email(service, email, user_id='me'):
    try:
        sent_message = service.users().messages().send(
            userId=user_id, body=email).execute()
        logger.info(f"Email sent: {sent_message['id']}")
        return sent_message
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        return None

def mark_as_read(service, msg_id, user_id='me'):
    try:
        service.users().messages().modify(
            userId=user_id, id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
        logger.info(f"Marked message {msg_id} as read")
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")

def process_emails():
    service = get_gmail_service()
    messages = list_unread_messages(service)
    if not messages:
        logger.info("No unread emails found.")
        return
    for msg in messages:
        msg_id = msg['id']
        message = get_message(service, msg_id)
        if not message:
            continue
        email_body = get_email_content(message)
        if not email_body.strip():
            logger.info(f"Email {msg_id} has no content. Skipping.")
            continue
        prompt = create_prompt(email_body)
        response = generate_response(prompt)
        if not response:
            logger.error(f"Failed to generate response for email {msg_id}")
            continue
        # extract sender's email
        headers = message['payload'].get('headers', [])
        from_header = next((h for h in headers if h['name'] == 'From'), None)
        subject_header = next((h for h in headers if h['name'] == 'Subject'), None)
        if not from_header:
            logger.error(f"No sender found for email {msg_id}")
            continue
        sender_email = parseaddr(from_header['value'])[1]
        subject = subject_header['value'] if subject_header else ''
        reply_subject = f"Re: {subject}"
        email = create_email(sender_email, reply_subject, response)
        sent_message = send_email(service, email)
        if sent_message:
            mark_as_read(service, msg_id)
