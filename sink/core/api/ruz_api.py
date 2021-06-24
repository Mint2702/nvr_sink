from aiohttp import ClientSession
from datetime import datetime, timedelta
import json

from loguru import logger

from ..utils import camel_to_snake, semlock, RUZ, handle_ruz_error
from ..settings import settings


class RuzApi:
    SERVICE = RUZ

    def __init__(self, url: str = "http://92.242.58.221/ruzservice.svc"):
        self.url = url
        self.period = settings.period

    # building id МИЭМа = 92
    @semlock
    @handle_ruz_error
    async def get_rooms(self, building_id: int = 92) -> list:
        """ Gets rooms (by default in MIEM) """

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

        lessons = await self._request_lessons_in_room(params)

        return lessons

    @semlock
    @handle_ruz_error
    async def _request_lessons_in_room(self, params: str) -> dict:
        """ Gets lessons from RUZ by given parameters """

        async with ClientSession() as session:
            result_raw = await session.get(f"{self.url}/lessons", params=params)
            async with result_raw as resp:
                result_text = await resp.text()

        try:
            lessons = json.loads(result_text)
        except Exception:
            logger.error(
                "Data about lessons in room could not be converted to json format"
            )
            lessons = []

        return lessons
