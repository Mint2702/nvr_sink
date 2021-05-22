from aiohttp import ClientSession
from loguru import logger
import time
from datetime import datetime
import pytz

from ..settings import settings
from ..utils import semlock, NVR


class Erudite:
    NVR_API_URL = "https://nvr.miem.hse.ru/api/erudite"
    NVR_API_KEY = settings.nvr_api_key
    SERVICE = NVR

    def __init__(self) -> None:
        tzmoscow = pytz.timezone("Europe/Moscow")
        self.dt: str = (
            datetime.now().replace(microsecond=0, tzinfo=tzmoscow).isoformat()
        )

    @semlock
    async def get_lessons_in_room(self, ruz_auditorium_oid: str) -> list:
        """ Gets all lessons from Erudite """

        async with ClientSession() as session:
            res = await session.get(
                f"{self.NVR_API_URL}/lessons",
                params={"ruz_auditorium_oid": ruz_auditorium_oid, "fromdate": self.dt},
            )
            async with res:
                lessons = await res.json()

        if res.status == 200:
            return lessons
        else:
            logger.info("Lesson not found")
            return []
