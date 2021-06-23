from datetime import datetime, timedelta
import asyncio
from loguru import logger
import time

from core.api.ruz_api import RuzApi
from core.api.erudite_api import Erudite
from core.models.models import Room, Lesson


class CalendarManager:
    def __init__(self):
        self.ruz_api = RuzApi()
        self.erudite = Erudite()

    async def get_rooms(self):
        """ Gets rooms in specified building """

        rooms = await self.ruz_api.get_rooms()
        return rooms

    async def start_synchronization(self, rooms: list) -> bool:
        """ Start point of synchronization """

        tasks = [self.get_lessons_in_room(Room(room)) for room in rooms]
        await asyncio.gather(*tasks)

    async def get_lessons_in_room(self, room: Room) -> list:
        """ Gets lessons in specified room and adds email to the lessons """

        lessons_without_emails = await self.ruz_api.get_lessons_in_room(
            room.ruz_room_id
        )
        for lesson in lessons_without_emails:
            lesson_class = Lesson(lesson)
            print(lesson_class.date)

        # tasks = [self.add_cource_emails_to_lessons(lesson) for lesson in lessons_without_emails]
        # await asyncio.gather(*tasks)

        # logger.info(lessons_without_emails)

    async def add_cource_emails_to_lessons(self, lesson: list) -> None:
        """ Adds grp_emails to lessons """

        if lesson["ruz_group"] is not None:
            stream = lesson["course_code"]
            grp_emails = await self.erudite.get_course_emails(stream)
            if grp_emails != []:
                lesson["grp_emails"] = grp_emails
            else:
                logger.warning(f"Stream: {stream} has no groups")


@logger.catch
async def main():
    manager = CalendarManager()

    rooms = await manager.get_rooms()
    status = await manager.start_synchronization(rooms)

    logger.info("Finished!!!")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
