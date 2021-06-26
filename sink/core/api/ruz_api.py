import httpx
from datetime import datetime, timedelta
import json

from loguru import logger

from ..utils import handle_web_errors
from ..settings import settings


class RuzApi:
    def __init__(self, url: str = "http://92.242.58.221/ruzservice.svc"):
        self.url = url
        self.period = settings.period

    # building id МИЭМа = 92
    @handle_web_errors
    def get_rooms(self, building_id: int = 92) -> list:
        """ Gets rooms (by default in MIEM) """

        result_raw = httpx.get(f"{self.url}/auditoriums?buildingoid=0")
        all_auditories = result_raw.json()

        rooms = [
            room
            for room in all_auditories
            if room["buildingGid"] == building_id
            and room["typeOfAuditorium"] != "Неаудиторные"
        ]

        return rooms

    def get_lessons_in_room(self, ruz_room_id: str) -> list:
        """
        Gets lessons in room for a specified period and converts them into the Erudite needed format
        """

        needed_date = (datetime.today() + timedelta(days=self.period)).strftime(
            "%Y.%m.%d"
        )
        # today = datetime.today().strftime("%Y.%m.%d")
        today = (datetime.today() - timedelta(10)).strftime("%Y.%m.%d")
        params = dict(
            fromdate=today, todate=needed_date, auditoriumoid=str(ruz_room_id)
        )

        lessons = self._request_lessons_in_room(params)

        return lessons

    @handle_web_errors
    def _request_lessons_in_room(self, params: str) -> dict:
        """ Gets lessons from RUZ by given parameters """

        result_raw = httpx.get(f"{self.url}/lessons", params=params)
        lessons = result_raw.json()

        return lessons
