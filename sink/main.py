from loguru import logger
import sys

from core.api.ruz_api import RuzApi
from core.api.erudite_api import Erudite
from core.models.models import Room, Lesson
from core.settings import settings
from core.utils import was_modyfied


class CalendarManager:
    def __init__(self, schedule_service: str):
        # Schedule service
        self.schedule_service = schedule_service

        # Apis
        self.ruz_api = RuzApi()
        self.erudite = Erudite()

        # Statistics
        self.lessons_with_no_group = 0
        self.lessons_with_group = 0
        self.lessons_with_no_course_code = 0
        self.lessons_added = 0
        self.lessons_updated = 0
        self.lessons_deleted = 0
        self.lessons_ignored = 0

    def get_rooms(self, building_id: int):
        """ Gets rooms in specified building """

        if self.schedule_service == "RUZ":
            rooms = self.ruz_api.get_rooms(building_id=building_id)

        rooms = [Room(room) for room in rooms]
        return rooms

    def start_synchronization(self, rooms: list) -> bool:
        """ Start point of synchronization. Synchronization of lessons for each room for a period of time."""

        for room in rooms:
            self.synchronize_lessons_in_room(room)

    def synchronize_lessons_in_room(self, room: Room) -> list:
        """ Synchronization of lessons in the room for a period of time, specified in .env file """

        schedule_lessons = self.get_lessons_in_room(room.schedule_room_id)
        self.add_group_email_to_lessons(schedule_lessons)
        logger.info(
            f"Num of lessons in this room in the schedule service - {len(schedule_lessons)}"
        )

        erudite_lessons = self.erudite.get_lessons_in_room(room.schedule_room_id)
        erudite_lessons = [
            Lesson(lesson, source="Erudite") for lesson in erudite_lessons
        ]
        logger.info(f"Num of lessons in this room in Erudite - {len(erudite_lessons)}")

        # Adding and updating lessons
        for lesson in schedule_lessons:
            self.synchronize_lesson_from_schedule_service_with_erudite(lesson)

        # Deleting lessons
        for lesson in erudite_lessons:
            self.synchronize_lesson_from_erudite_with_schedule_service(
                lesson, schedule_lessons
            )

    def get_lessons_in_room(self, schedule_room_id: str) -> list:
        """ Gets lessons in specified room and adds email to the lessons """

        if self.schedule_service == "RUZ":
            lessons = self.ruz_api.get_lessons_in_room(schedule_room_id)

        # Convert lessons in dict to their class format
        converted_lessons = [
            Lesson(lesson, source=self.schedule_service) for lesson in lessons
        ]

        return converted_lessons

    def add_group_email_to_lessons(self, lessons: list) -> None:
        """ Adds group emails for lessons, if it's course code is specified """

        for lesson in lessons:
            if lesson.schedule_course_code:
                self.add_group_email_to_lesson(lesson)
            else:
                self.lessons_with_no_course_code += 1

    def add_group_email_to_lesson(self, lesson: Lesson) -> None:
        """ Adds grp_emails(group emails) to lesson """

        stream = lesson.schedule_course_code
        grp_emails = self.erudite.get_course_emails(stream)
        if len(grp_emails) > 0:
            lesson.grp_emails = grp_emails
            self.lessons_with_group += 1
        else:
            self.lessons_with_no_group += 1

    def synchronize_lesson_from_schedule_service_with_erudite(
        self, schedule_lesson: Lesson
    ) -> None:
        """
        Synchronizing lesson from the schedule service (RUZ) with the same lesson in Erudite.
        If lesson with specified schedule id is not found in Erudite, it must be added. If it is found, it must be checked if it was modyfied or not.
        """

        erudite_lesson = self.erudite.get_lesson_by_lesson_id(schedule_lesson.id)
        if erudite_lesson:
            erudite_lesson = Lesson(erudite_lesson, source="Erudite")
            self.update_lesson_if_needed(erudite_lesson, schedule_lesson)
        else:
            self.add_lesson(schedule_lesson)

    def add_lesson(self, lesson: Lesson) -> None:
        """ Adds lesson to Erudite. """

        self.lessons_added += 1
        logger.info(f"Adding lesson with id - {lesson.id}")

        lesson_json = lesson.to_json()
        status_add = self.erudite.post_lesson(lesson_json)
        if not status_add:
            sys.exit(1)

    def update_lesson_if_needed(
        self, erudite_lesson: Lesson, schedule_lesson: Lesson
    ) -> None:
        """ Updates lesson in Erudite using data from the schedule service, if it was modyfied. """

        if was_modyfied(erudite_lesson.original, schedule_lesson.original):
            self.lessons_updated += 1
            logger.info(f"Updating lesson with id - {schedule_lesson.id}")

            new_lesson_json = schedule_lesson.to_json()
            status_update = self.erudite.update_lesson(
                new_lesson_json, erudite_lesson.erudite_id
            )
            if not status_update:
                sys.exit(1)
        else:
            self.lessons_ignored += 1
            logger.info("Not added or updated")

    def synchronize_lesson_from_erudite_with_schedule_service(
        self, erudite_lesson: Lesson, schedule_lessons: list
    ) -> None:
        """
        Synchronizing lesson from Erudite with the schedule service (RUZ).
        Deleting of lesson if it was not in the schedule lessons, basicaly.
        """

        for lesson in schedule_lessons:
            if lesson.id == erudite_lesson.id:
                return None

        self.delete_lesson(erudite_lesson)

    def delete_lesson(self, erudite_lesson: Lesson) -> None:
        """ Deletes lesson from Erudite """

        self.lessons_deleted += 1
        logger.info(f"Deleting lesson with id - {erudite_lesson.id}")

        erudite_id = erudite_lesson.erudite_id
        status_delete = self.erudite.delete_lesson(erudite_id)
        if not status_delete:
            sys.exit(1)

    def statistics(self) -> None:
        """ Prints out statistics about lessons that were checked during the synchronization process """

        logger.info(
            f"\nLessons without course code - {self.lessons_with_no_course_code}\nLessons without group - {self.lessons_with_no_group}\nLessons with group - {self.lessons_with_group}\nLessons added - {self.lessons_added}\nLessons updated - {self.lessons_updated}\nLessons deleted - {self.lessons_deleted}\nLessons not added or updated - {self.lessons_ignored}"
        )


@logger.catch
def main():
    manager = CalendarManager(schedule_service="RUZ")

    buildings = settings.buildings
    for building in buildings:
        rooms = manager.get_rooms(building_id=building)
        manager.start_synchronization(rooms)

        logger.info(f"Finished synchronization for building with id - {building}")
        manager.statistics()


if __name__ == "__main__":
    main()
