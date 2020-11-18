import os.path
import pickle
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GCalendar:
    def __init__(
        self,
        creds_path: str,
        token_path: str,
        scopes: str or list = "https://www.googleapis.com/auth/calendar",
    ):
        """
        Setting up calendar
        """
        creds = None
        if os.path.exists(token_path):
            with open(token_path, "rb") as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
                creds = flow.run_local_server(port=0)
            with open(token_path, "wb") as token:
                pickle.dump(creds, token)

        self.service = build("calendar", "v3", credentials=creds)

    def create_event_(
        self,
        calendar_id: str,
        summary: str,
        location: str,
        description: str,
        start_time: str,
        end_time: str or None = None,
    ) -> str:
        """
        format: "%Y-%m-%dT%H:%M:%S"
        ex: 2019-11-12T15:00
        """
        date_format = "%Y-%m-%dT%H:%M:%S"
        if not end_time:
            end_time = start_time + timedelta(minutes=80)

        event = {
            "summary": summary,
            "location": location,
            "start": {
                "dateTime": start_time.strftime(date_format),
                "timeZone": "Europe/Moscow",
            },
            "end": {
                "dateTime": end_time.strftime(date_format),
                "timeZone": "Europe/Moscow",
            },
            "description": description,
        }

        event = (
            self.service.events().insert(calendarId=calendar_id, body=event).execute()
        )

        return event

    def add_classes_to_calendar(self, classes: list, calendar_id: str):
        for class_ in classes:
            self.create_event_(
                calendar_id,
                class_["summary"],
                class_["location"],
                class_["description"],
                class_["start_time"],
                class_["end_time"],
            )

    def get_events(self, calendar_id: str) -> dict:
        now = datetime.utcnow()
        nowISO = now.isoformat() + "Z"  # 'Z' indicates UTC time
        nowffISO = (now + timedelta(days=1)).isoformat() + "Z"
        events_result = (
            self.service.events()
            .list(
                calendarId=calendar_id,
                timeMin=nowISO,
                timeMax=nowffISO,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        return events
