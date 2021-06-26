import httpx
from loguru import logger
import time
from datetime import datetime
import pytz

from ..settings import settings
from ..utils import handle_web_errors


class Erudite:
    NVR_API_URL = "https://nvr.miem.hse.ru/api/erudite"  # "http://localhost:8000"
    NVR_API_KEY = settings.nvr_api_key

    def __init__(self) -> None:
        tzmoscow = pytz.timezone("Europe/Moscow")
        self.dt: str = (
            datetime.now().replace(microsecond=0, tzinfo=tzmoscow).isoformat()
        )

    @handle_web_errors
    def get_lessons_in_room(self, ruz_auditorium_oid: str) -> list:
        """ Gets all lessons from Erudite """

        result_raw = httpx.get(
            f"{self.NVR_API_URL}/lessons",
            params={"ruz_auditorium_oid": ruz_auditorium_oid, "fromdate": self.dt},
        )
        lessons = result_raw.json()

        if result_raw.status_code == 200:
            return lessons
        else:
            # logger.info("Lessons not found")
            return []

    @handle_web_errors
    def get_course_emails(self, course_code: str) -> list:
        """ Gets emails from a GET responce from Erudite """

        result_raw = httpx.get(
            f"{self.NVR_API_URL}/disciplines",
            params={"course_code": course_code},
        )
        group_email = result_raw.json()

        if result_raw.status_code == 200:
            grp_emails = group_email[0].get("emails")
        else:
            return []

        if grp_emails == [""]:
            return []

        return grp_emails

    @handle_web_errors
    def get_lesson_by_lessonOid(self, lesson_id: str) -> dict or None:
        """ Gets lesson by it's lessonOid """

        result_raw = httpx.get(
            f"{self.NVR_API_URL}/lessons", params={"ruz_lesson_oid": lesson_id}
        )
        lesson = result_raw.json()

        if result_raw.status_code == 200:
            return lesson
        else:
            return None
