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

        # Statistics
        self.lessons_with_no_group = 0
        self.lessons_with_group = 0
        self.lessons_with_no_course_code = 0
        self.lessons_added = 0
        self.lessons_updated = 0
        self.lessons_deleted = 0

    async def get_rooms(self):
        """ Gets rooms in specified building """

        rooms = await self.ruz_api.get_rooms()
        return rooms

    async def start_synchronization(self, rooms: list) -> bool:
        """ Start point of synchronization. Ruz does not allow to work with it asynchroniously, so all work done synchroniousily. """

        rooms = [Room(room) for room in rooms]
        for room in rooms:
            await self.synchronize_lessons_in_room(room)

        # Тут можно добавить подсчет пар, которые не удалось синхронизмровать, сколько пар было изменено, добавлено, удалено и тд

    async def synchronize_lessons_in_room(self, room: Room) -> list:
        """ Synchronization of lessons in the room for a period of time, specified in .env file """

        ruz_lessons = await self.get_lessons_in_room(room.ruz_room_id)

        await self.add_group_email_to_lessons(ruz_lessons)

        erudite_lessons = await self.erudite.get_lessons_in_room(room.ruz_room_id)

        print(len(erudite_lessons))
        for lesson in erudite_lessons:
            print(lesson)

    async def get_lessons_in_room(self, ruz_room_id: str) -> list:
        """ Gets lessons in specified room and adds email to the lessons """

        time.sleep(0.5)
        lessons = await self.ruz_api.get_lessons_in_room(ruz_room_id)

        # Convert lessons in dict to their class format
        converted_lessons = [Lesson(lesson) for lesson in lessons]

        return converted_lessons

    async def add_group_email_to_lessons(self, lessons: list) -> None:
        """ Adds course email for lesson, if it's course code is specified """

        for lesson in lessons:
            if lesson.course_code:
                await self.add_group_email_to_lesson(lesson)
            else:
                # logger.warning("No cource code")
                self.lessons_with_no_course_code += 1

    async def add_group_email_to_lesson(self, lesson: Lesson) -> None:
        """ Adds grp_emails(group emails) to lesson """

        stream = lesson.course_code
        grp_emails = await self.erudite.get_course_emails(stream)
        if len(grp_emails) > 0:
            lesson.grp_emails = grp_emails
            # logger.info(f"Good - {lesson.grp_emails}")
            self.lessons_with_group += 1
        else:
            # logger.info(f"Stream: {stream} has no groups")
            self.lessons_with_no_group += 1

    def statistics(self) -> None:
        logger.info(
            f"\nLessons without course code - {self.lessons_with_no_course_code}\nLessons without group - {self.lessons_with_no_group}\nLessons with group - {self.lessons_with_group}\nLessons added - {self.lessons_added}\nLessons updated - {self.lessons_updated}\nLessons deleted - {self.lessons_deleted}"
        )


@logger.catch
async def main():
    manager = CalendarManager()

    rooms = await manager.get_rooms()
    status = await manager.start_synchronization(rooms)

    logger.info("Finished!!!")
    manager.statistics()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
