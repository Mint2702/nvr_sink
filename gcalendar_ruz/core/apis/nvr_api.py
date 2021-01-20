from aiohttp import ClientSession
from loguru import logger

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

        logger.info(f"nvr.get_course_emails returned {res.status}")

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
        """ Posts a lesson to Erudite """

        async with ClientSession() as session:
            res = await session.post(
                f"{self.NVR_API_URL}/lessons",
                json=lesson,
                headers={"key": self.NVR_API_KEY},
            )
        logger.info(f"nvr.add_lesson returned {res.status}")

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
            logger.error("Erudite is not working properly...")

    @semlock
    async def update_lesson(self, lesson_id: str, lesson_data: dict):
        """ Updates a lesson in Erudite """

        async with ClientSession() as session:
            res = await session.put(
                f"{self.NVR_API_URL}/lessons/{lesson_id}",
                json=lesson_data,
                headers={"key": self.NVR_API_KEY},
            )

        if res.status == 200:
            logger.info(f"Lesson with id: {lesson_id} updated")
        else:
            logger.error("Erudite is not working properly...")

    @semlock
    async def check_and_update_lessons(self, lesson: dict) -> bool:
        """ Compares two lessons """

        async with ClientSession() as session:
            res = await session.get(
                f"{self.NVR_API_URL}/lessons",
                params={"ruz_lesson_oid": lesson["ruz_lesson_oid"]},
            )
            async with res:
                data = await res.json()

        if type(data) != list:
            # This means that there is no such lesson found in Erudite, so it needs to be added
            return False

        # The is statement deletes all but one lessons with the same ruz_lesson_oid if there are more than 1 of them
        if len(data) > 1:
            data_del = data[1:]
            for i in data_del:
                await self.delete_lesson(i["id"])

        data = data[0]

        lesson_id = data.pop("id")
        data.pop("gcalendar_event_id")
        data.pop("gcalendar_calendar_id")
        if data == lesson:
            return True

        # If code run up to this point, it means that lesson with such ruz_lesson_oid is found in Erudite, but it differs from the one in RUZ, so it needs to be updated
        await self.update_lesson(lesson_id, lesson)

        return True
