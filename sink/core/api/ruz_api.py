import httpx
from datetime import datetime, timedelta

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

        responce = httpx.get(f"{self.url}/auditoriums?buildingoid=0")
        all_auditories = responce.json()

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

        self.needed_date = (datetime.today() + timedelta(days=self.period)).strftime(
            "%Y.%m.%d"
        )
        # today = datetime.today().strftime("%Y.%m.%d")
        self.today = (datetime.today() - timedelta(days=10)).strftime("%Y.%m.%d")

        lessons = self._request_lessons_in_room(ruz_room_id)

        return lessons

    @handle_web_errors
    def _request_lessons_in_room(self, ruz_room_id: str) -> dict:
        """ Gets lessons from RUZ by given parameters """

        params = dict(
            fromdate=self.today, todate=self.needed_date, auditoriumoid=str(ruz_room_id)
        )
        responce = httpx.get(f"{self.url}/lessons", params=params)
        lessons = responce.json()

        return lessons
