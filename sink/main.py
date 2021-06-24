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
        """ Start point of synchronization. Ruz does not allow to work with it asynchroniously, so all work done synchroniousily. """

        rooms = [Room(room) for room in rooms]
        for room in rooms:
            await self.get_lessons_in_room(room)

    async def get_lessons_in_room(self, room: Room) -> list:
        """ Gets lessons in specified room and adds email to the lessons """

        lessons_without_emails = await self.ruz_api.get_lessons_in_room(
            room.ruz_room_id
        )

        # Convert lessons in dict to their class format
        lessons_objects = [Lesson(lesson) for lesson in lessons_without_emails]

        for lesson in lessons_objects:
            if lesson.course_code:
                await self.add_cource_emails_to_lessons(lesson)

    async def add_cource_emails_to_lessons(self, lesson: Lesson) -> None:
        """ Adds grp_emails(group emails) to lesson """

        stream = lesson.course_code
        grp_emails = await self.erudite.get_course_emails(stream)
        if len(grp_emails) > 0:
            lesson.grp_emails = grp_emails
            logger.info(f"Good - {lesson.grp_emails}")
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
