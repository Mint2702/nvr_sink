from aiohttp import ClientSession
from datetime import datetime, timedelta

from loguru import logger

from ..utils import camel_to_snake, semlock, RUZ
from ..settings import settings


class RuzApi:
    SERVICE = RUZ

    def __init__(self, url: str = "http://92.242.58.221/ruzservice.svc"):
        self.url = url
        self.period = settings.period

    # building id МИЭМа = 92
    @semlock
    async def get_miem_rooms(self, building_id: int = 92) -> list:
        """ Gets rooms in MIEM """

        async with ClientSession() as session:
            res = await session.get(f"{self.url}/auditoriums?buildingoid=0")
            async with res:
                all_auditories = await res.json()

        rooms = [
            room
            for room in all_auditories
            if room["buildingGid"] == building_id
            and room["typeOfAuditorium"] != "Неаудиторные"
        ]

        return rooms

    @semlock
    async def get_lessons_in_room(self, ruz_room_id: str) -> list:
        """
        Gets lessons in room for a specified period and converts them into the Erudite needed format
        """

        needed_date = (datetime.today() + timedelta(days=self.period)).strftime(
            "%Y.%m.%d"
        )
        today = datetime.today().strftime("%Y.%m.%d")

        params = dict(
            fromdate=today, todate=needed_date, auditoriumoid=str(ruz_room_id)
        )

        raw_lessons = await self._get_lessons_in_room_raw(params)
        lessons = self._parce_lessons(raw_lessons)

        return lessons

    async def _get_lessons_in_room_raw(self, params: str) -> dict:
        """ Gets lessons from RUZ by given parameters """

        async with ClientSession() as session:
            res = await session.get(f"{self.url}/lessons", params=params)
            async with res:
                res = await res.json(content_type=None)

        return res

    def _parce_lessons(self, lessons_raw: list) -> list:
        """ Parses lessons that were returned from RUZ to the Erudite needed format """

        lessons = []
        for class_ in lessons_raw:
            lesson = {}

            date = class_.pop("date")
            date = date.split(".")
            lesson["date"] = "-".join(date)

            lesson["start_time"] = class_.pop("beginLesson")
            lesson["end_time"] = class_.pop("endLesson")

            lesson["summary"] = class_["discipline"]
            lesson["location"] = f"{class_['auditorium']}/{class_['building']}"

            for key in class_:
                new_key = f"ruz_{camel_to_snake(key)}"
                lesson[new_key] = class_[key]

            lesson["ruz_url"] = lesson["ruz_url1"]

            if lesson["ruz_group"] is not None:
                stream = lesson["ruz_group"].split("#")[0]
            else:
                stream = ""
            lesson["course_code"] = stream

            lesson["description"] = (
                f"Поток: {stream}\n"
                f"Преподаватель: {lesson['ruz_lecturer']}\n"
                f"Тип занятия: {lesson['ruz_kind_of_work']}\n"
            )

            if lesson["ruz_url"]:
                lesson["description"] += f"URL: {lesson['ruz_url']}\n"

            if lesson.get("ruz_lecturer_email"):  # None or ""
                lesson["miem_lecturer_email"] = (
                    lesson["ruz_lecturer_email"].split("@")[0] + "@miem.hse.ru"
                )

            lessons.append(lesson)

        return lessons
