import httpx
from loguru import logger
from datetime import datetime, timedelta

from ..settings import settings
from ..utils import handle_web_errors


class Erudite:
    NVR_API_URL = settings.erudite_url  # "https://nvr.miem.hse.ru/api/erudite"
    NVR_API_KEY = settings.nvr_api_key

    def __init__(self) -> None:
        self.period = settings.period
        self.needed_date = (datetime.today() + timedelta(days=self.period)).strftime(
            "%Y-%m-%d"
        )
        # today = datetime.today().strftime("%Y.%m.%d")
        self.today = (datetime.today() - timedelta(days=10)).strftime("%Y-%m-%d")

        self.needed_date += " 21:00"
        self.today += " 09:00"

    @handle_web_errors
    def get_lessons_in_room(self, schedule_auditorium_oid: str) -> list:
        """ Gets all lessons from Erudite """

        params = {
            "schedule_auditorium_id": schedule_auditorium_oid,
            "fromdate": self.today,
            "todate": self.needed_date,
        }

        responce = httpx.get(
            f"{self.NVR_API_URL}/lessons",
            params=params,
        )
        lessons = responce.json()

        if responce.status_code == 200:
            return lessons
        else:
            # logger.info("Lessons not found")
            return []

    @handle_web_errors
    def get_course_emails(self, schedule_course_code: str) -> list:
        """ Gets emails from a GET responce from Erudite """

        responce = httpx.get(
            f"{self.NVR_API_URL}/disciplines",
            params={"course_code": schedule_course_code},
        )
        group_email = responce.json()

        if responce.status_code == 200:
            grp_emails = group_email[0].get("emails")
        else:
            return []

        if grp_emails == [""]:
            return []

        return grp_emails

    @handle_web_errors
    def get_lesson_by_lesson_id(self, lesson_id: str) -> dict or None:
        """ Gets lesson by it's lessonOid """

        responce = httpx.get(
            f"{self.NVR_API_URL}/lessons", params={"schedule_lesson_id": lesson_id}
        )
        lesson = responce.json()

        if responce.status_code == 200 and len(lesson) > 0:
            return lesson[0]
        else:
            return None

    @handle_web_errors
    def post_lesson(self, lesson: dict) -> bool:
        """ Posts lesson to Erudite """

        responce = httpx.post(
            f"{self.NVR_API_URL}/lessons",
            json=lesson,
            headers={"key": self.NVR_API_KEY},
        )
        if responce.status_code == 201:
            return True

        logger.error(f"Lesson could not be added to Erudite - {responce}")
        logger.info(f"Not added lesson - {lesson}")
        return False

    @handle_web_errors
    def update_lesson(self, new_lesson: dict, old_lesson_id: str) -> bool:
        """ Updates lesson in Erudite """

        responce = httpx.put(
            f"{self.NVR_API_URL}/lessons/{old_lesson_id}",
            json=new_lesson,
            headers={"key": self.NVR_API_KEY},
        )

        if responce.status_code == 200:
            return True

        logger.error(f"Lesson could not be updated - {responce}")
        return False

    @handle_web_errors
    def delete_lesson(self, lesson_id: str) -> bool:
        """ Deletes lesson from Erudite """

        responce = httpx.delete(
            f"{self.NVR_API_URL}/lessons/{lesson_id}", headers={"key": self.NVR_API_KEY}
        )

        if responce.status_code == 200:
            return True

        logger.error(f"Lesson could not be deleted from Erudite - {responce}")
        return False
