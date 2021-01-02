import os.path
import pickle
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..redis.caching import cach


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

    def create_event(
        self,
        calendar_id: str,
        lesson: dict,
    ) -> str:
        """
        format: "%Y-%m-%dT%H:%M:%S"
        ex: 2019-11-12T15:00
        """

        event = {
            "summary": lesson["summary"],
            "location": lesson["location"],
            "start": {
                "dateTime": f"{lesson['date']}T{lesson['start_time']}:00",
                "timeZone": "Europe/Moscow",
            },
            "end": {
                "dateTime": f"{lesson['date']}T{lesson['end_time']}:00",
                "timeZone": "Europe/Moscow",
            },
            "description": lesson["description"],
        }

        if lesson.get("ruz_lecturer_email"):
            event["attendees"] = [{"email": lesson["ruz_lecturer_email"]}]
            if lesson.get("grp_emails"):
                event["attendees"] += [{"email": grp} for grp in lesson["grp_emails"]]

            event["reminders"] = {"useDefault": True}

        event = self.service.events().insert(calendarId=calendar_id, body=event).execute()

        return event

    def delete_event(self, calendar_id, event_id):
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

    @cach("events")
    def get_events(self, _calendar_id: str) -> dict:
        now = datetime.utcnow()
        nowISO = now.isoformat() + "Z"  # 'Z' indicates UTC time
        nowffISO = (now + timedelta(days=1)).isoformat() + "Z"
        events_result = (
            self.service.events()
            .list(
                calendarId=_calendar_id,
                timeMin=nowISO,
                timeMax=nowffISO,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        return events
