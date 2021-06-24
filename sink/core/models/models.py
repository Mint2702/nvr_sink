from loguru import logger
from copy import deepcopy

from ..utils import camel_to_snake


class Lesson:
    def __init__(self, lesson_attributes: dict, source: str = "ruz") -> None:
        """ Converts given dictionary of lesson's attributes to the Lesson's fields, depending on the source of data about lesson """

        if source == "ruz":
            self.ruz_convertation(lesson_attributes)
        else:
            logger.error("Source not supported")

    def ruz_convertation(self, lesson_attributes: dict) -> None:
        """ Converts given list of lesson's attributes to the Lesson's fields """

        self.raw: dict = lesson_attributes

        date = lesson_attributes["date"].split(".")
        self.date: str = "-".join(date)

        self.start_time = lesson_attributes["beginLesson"]
        self.end_time = lesson_attributes["endLesson"]

        self.summary = lesson_attributes["discipline"]
        self.location = (
            f"{lesson_attributes['auditorium']}/{lesson_attributes['building']}"
        )

        self.url = lesson_attributes["url1"]

        self.grp_emails = None

        if not lesson_attributes["group"]:
            self.course_code = None
        else:
            self.course_code: str = lesson_attributes["group"].split("#")[0]

        self.description = (
            f"Поток: {self.course_code}\n"
            f"Преподаватель: {lesson_attributes['lecturer']}\n"
            f"Тип занятия: {lesson_attributes['kindOfWork']}\n"
        )

        if self.url:
            self.description += f"URL: {self.url}\n"

        if lesson_attributes["lecturerEmail"]:
            self.miem_lecturer_email: str = (
                lesson_attributes["lecturerEmail"].split("@")[0] + "@miem.hse.ru"
            )

    def to_json(self) -> dict:
        """ Converts data, stored in the object to dict """

        lesson = {}
        raw_lesson = deepcopy(self.raw)

        raw_lesson.pop("date")
        lesson["date"] = self.date

        lesson["start_time"] = raw_lesson.pop("beginLesson")
        lesson["end_time"] = raw_lesson.pop("endLesson")

        lesson["summary"] = raw_lesson["discipline"]
        lesson["location"] = self.location

        for key in raw_lesson:
            new_key = f"ruz_{camel_to_snake(key)}"
            lesson[new_key] = raw_lesson[key]

        lesson["ruz_url"] = lesson["ruz_url1"]

        lesson["course_code"] = self.course_code

        if self.grp_emails:
            lesson["grp_emails"] = self.grp_emails

        lesson["description"] = self.description

        if lesson.get("ruz_lecturer_email"):  # None or ""
            lesson["miem_lecturer_email"] = self.miem_lecturer_email

        return lesson


class Room:
    def __init__(self, room_attributes: dict) -> None:
        self.ruz_room_id: int = room_attributes["auditoriumOid"]
        self.building_id: str = room_attributes["buildingGid"]

    def __str__(self) -> None:
        return f"Room id - {self.ruz_room_id}\nBuilding id - {self.building_id}"
