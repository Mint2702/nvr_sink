import os.path
import pickle
from datetime import datetime, timedelta
from aiohttp import ClientSession

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..redis_caching.caching import cache
from ..utils import semlock, GOOGLE


class GCalendar:
    SERVICE = GOOGLE

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

        self.HEADERS = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {creds.token}",
        }

        self.service = build("calendar", "v3", credentials=creds)

    @semlock
    async def create_event(
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

        async with ClientSession() as session:
            event_post = await session.post(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                json=event,
                headers=self.HEADERS,
            )
            async with event_post:
                event_json = await event_post.json()

        return event_json

    @semlock
    async def delete_event(self, calendar_id, event_id):
        async with ClientSession() as session:
            await session.delete(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}"
            )

    @cache
    @semlock
    async def get_events(self, calendar_id: str) -> dict:
        now = datetime.utcnow()
        nowISO = now.isoformat() + "Z"  # 'Z' indicates UTC time
        nowffISO = (now + timedelta(days=1)).isoformat() + "Z"
        async with ClientSession() as session:
            events_result = await session.get(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                timeMin=nowISO,
                timeMax=nowffISO,
                singleEvents=True,
                orderBy="startTime",
            )
            async with events_result:
                events_result = events_result.json()

        events = events_result.get("items", [])
        return events
