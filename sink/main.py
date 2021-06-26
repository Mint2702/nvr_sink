from datetime import datetime, timedelta
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

    def get_rooms(self):
        """ Gets rooms in specified building """

        rooms = self.ruz_api.get_rooms()
        return rooms

    def start_synchronization(self, rooms: list) -> bool:
        """ Start point of synchronization. Ruz does not allow to work with it asynchroniously, so all work done synchroniousily. """

        rooms = [Room(room) for room in rooms]
        for room in rooms:
            self.synchronize_lessons_in_room(room)

        # Тут можно добавить подсчет пар, которые не удалось синхронизмровать, сколько пар было изменено, добавлено, удалено и тд

    def synchronize_lessons_in_room(self, room: Room) -> list:
        """ Synchronization of lessons in the room for a period of time, specified in .env file """

        ruz_lessons = self.get_lessons_in_room(room.ruz_room_id)

        self.add_group_email_to_lessons(ruz_lessons)

        # erudite_lessons = self.erudite.get_lessons_in_room(room.ruz_room_id)

        # print(len(erudite_lessons))
        for lesson in ruz_lessons:
            self.synchronize_lesson_from_RUZ_to_erudite(lesson)

    def get_lessons_in_room(self, ruz_room_id: str) -> list:
        """ Gets lessons in specified room and adds email to the lessons """

        lessons = self.ruz_api.get_lessons_in_room(ruz_room_id)

        # Convert lessons in dict to their class format
        converted_lessons = [Lesson(lesson, source="ruz") for lesson in lessons]

        return converted_lessons

    def add_group_email_to_lessons(self, lessons: list) -> None:
        """ Adds course email for lesson, if it's course code is specified """

        for lesson in lessons:
            if lesson.course_code:
                self.add_group_email_to_lesson(lesson)
            else:
                # logger.warning("No cource code")
                self.lessons_with_no_course_code += 1

    def add_group_email_to_lesson(self, lesson: Lesson) -> None:
        """ Adds grp_emails(group emails) to lesson """

        stream = lesson.course_code
        grp_emails = self.erudite.get_course_emails(stream)
        if len(grp_emails) > 0:
            lesson.grp_emails = grp_emails
            # logger.info(f"Good - {lesson.grp_emails}")
            self.lessons_with_group += 1
        else:
            # logger.info(f"Stream: {stream} has no groups")
            self.lessons_with_no_group += 1

    def synchronize_lesson_from_schedule_service_to_erudite(
        self, schedule_lesson: Lesson
    ) -> None:
        """ Synchronizing lesson from the schedule service (RUZ) with the same lesson in Erudite """

        erudite_lesson = self.erudite.get_lesson_by_lessonOid(schedule_lesson.id)
        if erudite_lesson:
            erudite_lesson = Lesson(erudite_lesson, source="erudite")
            self.update_lesson_if_needed(erudite_lesson, schedule_lesson)
        else:
            self.add_lesson(lesson)

    def add_lesson(self, lesson: Lesson) -> None:
        """ Adds lesson to Erudite if it was not there already """

        self.lessons_added += 1
        # Add

    def update_lesson_if_needed(
        self, erudite_lesson: Lesson, ruz_lesson: Lesson
    ) -> None:
        """ Updates lesson in Erudite using data from the RUZ lesson """

        if erudite_lesson.raw == ruz_lesson.raw:
            self.lessons_updated += 1
            # Update

    def statistics(self) -> None:
        """ Prints out statistics about lessons that were checked during the synchronization process """

        logger.info(
            f"\nLessons without course code - {self.lessons_with_no_course_code}\nLessons without group - {self.lessons_with_no_group}\nLessons with group - {self.lessons_with_group}\nLessons added - {self.lessons_added}\nLessons updated - {self.lessons_updated}\nLessons deleted - {self.lessons_deleted}"
        )


@logger.catch
def main():
    manager = CalendarManager()

    rooms = manager.get_rooms()
    status = manager.start_synchronization(rooms)

    logger.info("Finished!!!")
    manager.statistics()


if __name__ == "__main__":
    main()
