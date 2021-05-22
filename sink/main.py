from datetime import datetime, timedelta
import asyncio
from loguru import logger
import time

from core.api.ruz_api import RuzApi
from core.api.erudite_api import Erudite


class CalendarManager:
    def __init__(self):
        self.ruz_api = RuzApi()
        self.erudite = Erudite()

    async def get_rooms(self):

        rooms = await self.ruz_api.get_auditoriumoid()

        logger.info(rooms)


@logger.catch
async def main():
    manager = CalendarManager()

    await manager.get_rooms()

    logger.info("Finished!!!")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
