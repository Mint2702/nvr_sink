from aiohttp import ClientSession
from loguru import logger
import asyncio

from ..settings import settings
from ..utils import semlock, NVR


class Nvr_Api:
    NVR_API_URL = "http://localhost:8000"  # "https://nvr.miem.hse.ru/api/erudite"
    NVR_API_KEY = settings.nvr_api_key
    SERVICE = NVR

    @semlock
    async def get_course_emails(self, course_code: str):
        """ Gets emails from a GET responce from Erudite """

        async with ClientSession() as session:
            res = await session.get(
                f"{self.NVR_API_URL}/disciplines", params={"course_code": course_code}
            )
            async with res:
                data = await res.json()

        logger.info(f"nvr.get_course_emails returned {res.status}, with body {await res.text()}")

        # If the responce is not list -> the responce is a message that discipline is not found, and it should not be analysed further
        if type(data) == list:
            grp_emails = data[0].get("emails")
        else:
            return None

        if grp_emails == [""]:
            return None

        return grp_emails

    @semlock
    async def add_lesson(self, lesson: dict):
        """Posts a lesson to Erudite

        async with ClientSession() as session:
            res = await session.post(
                f"{self.NVR_API_URL}/lessons", json=lesson, headers={"key": self.NVR_API_KEY}
            )
        logger.info(f"nvr.add_lesson returned {res.status}, with body {await res.text()}")
        """
        pass

    @semlock
    async def delete_lesson(self, lesson_id: str):
        """ Deletes a lesson from Erudite """

        async with ClientSession() as session:
            res = await session.delete(
                f"{self.NVR_API_URL}/lessons/{lesson_id}",
                headers={"key": self.NVR_API_KEY},
            )
        if res.status == 200:
            logger.info(f"Lesson with id: {lesson_id} deleted")
        elif res.status == 404:
            logger.info(f"Lesson with id: {lesson_id} is not found in Erudite")
        else:
            logger.error(f"Erudite is not working properly...")