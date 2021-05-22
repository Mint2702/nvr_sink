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
        """ Gets rooms in MIEM """

        rooms = await self.ruz_api.get_miem_rooms()
        tasks = [self.get_lessons_in_room(room["auditoriumOid"]) for room in rooms]

        await asyncio.gather(*tasks)

    async def get_lessons_in_room(self, ruz_room_id: str) -> list:
        """ Gets lessons in specified rooms and adds email to them """

        lessons_without_emails = await self.ruz_api.get_lessons_in_room(ruz_room_id)
        lessons = await self.add_cource_emails_to_lessons(lessons_without_emails)

        logger.info(lessons)

    async def add_cource_emails_to_lessons(self, lessons: list) -> list:
        """ Adds grp_emails to lessons """

        for lesson in lessons:
            if lesson["ruz_group"] is not None:
                stream = lesson["course_code"]
                grp_emails = await self.erudite.get_course_emails(stream)
                if grp_emails != []:
                    lesson["grp_emails"] = grp_emails
                else:
                    logger.warning(f"Stream: {stream} has no groups")

        return lessons


@logger.catch
async def main():
    manager = CalendarManager()

    await manager.get_rooms()

    logger.info("Finished!!!")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
