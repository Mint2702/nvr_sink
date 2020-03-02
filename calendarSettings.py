from __future__ import print_function

import datetime
import os.path
import pickle
from datetime import datetime, timedelta
from threading import RLock

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

lock = RLock()

CAMPUS = os.environ.get('CAMPUS')
SCOPES = 'https://www.googleapis.com/auth/calendar'
"""
Setting up calendar
"""
creds = None
token_path = '.creds/tokenCalendar.pickle'
creds_path = '.creds/credentials.json'

if os.path.exists(token_path):
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
    with open(token_path, 'wb') as token:
        pickle.dump(creds, token)

calendar_service = build('calendar', 'v3', credentials=creds)


def create_event_(calendar_id: str, summary: str, location: str, description: str, start_time: str) -> str:
    """
        format 2019-11-12T15:00
    """
    date_format = "%Y-%m-%dT%H:%M:%S"

    end_time = start_time + timedelta(minutes=80)

    event = {
        'summary': summary,
        'location': location,
        'start': {
            'dateTime': start_time.strftime(date_format),
            'timeZone': "Europe/Moscow"
        },
        'end': {
            'dateTime': end_time.strftime(date_format),
            'timeZone': "Europe/Moscow"
        },
        'description': description
    }

    event = calendar_service.events().insert(
        calendarId=calendar_id, body=event).execute()

    return event['htmlLink']
