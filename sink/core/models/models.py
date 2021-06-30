from loguru import logger
from copy import deepcopy
from datetime import datetime


class Lesson:
    def __init__(self, lesson_attributes: dict, source: str = "ruz") -> None:
        """ Converts given dictionary of lesson's attributes to the Lesson's fields, depending on the source of data about lesson """

        if source == "RUZ":
            self.ruz_convertation(lesson_attributes)
        elif source == "Erudite":
            self.erudite_convertation(lesson_attributes)
        else:
            logger.error("Source not supported")

    def ruz_convertation(self, lesson_attributes: dict) -> None:
        """ Converts given list of lesson's attributes to the Lesson's fields """

        self.original: dict = deepcopy(lesson_attributes)

        self.id = lesson_attributes["lessonOid"]

        self.start_point = datetime.strptime(
            f"{lesson_attributes['date']} {lesson_attributes['beginLesson']}",
            "%Y.%m.%d %H:%M",
        )
        self.end_point = datetime.strptime(
            f"{lesson_attributes['date']} {lesson_attributes['endLesson']}",
            "%Y.%m.%d %H:%M",
        )

        self.auditorium_id = lesson_attributes["auditoriumOid"]

        # We later fill group email with function
        self.grp_emails = None

        if not lesson_attributes["group"]:
            self.schedule_course_code = None
        else:
            self.schedule_course_code: str = lesson_attributes["group"].split("#")[0]

    def erudite_convertation(self, lesson_attributes: dict) -> None:
        """ Converts given list of lesson's attributes to the Lesson's fields """

        self.id = lesson_attributes["schedule_lesson_id"]
        self.erudite_id = lesson_attributes["id"]
        self.original = lesson_attributes["original"]

        self.start_point = datetime.strptime(
            lesson_attributes["start_point"], "%Y-%m-%dT%H:%M:%S"
        )
        self.end_point = datetime.strptime(
            lesson_attributes["end_point"], "%Y-%m-%dT%H:%M:%S"
        )

        self.auditorium_id = lesson_attributes["schedule_auditorium_id"]

        grp_emails = lesson_attributes.get("grp_emails")
        if grp_emails:
            self.grp_emails = grp_emails

        self.schedule_course_code = lesson_attributes["schedule_course_code"]

    def to_json(self) -> dict:
        """ Converts data, stored in the object to dict """

        lesson = {}
        original_lesson = deepcopy(self.original)

        lesson["schedule_lesson_id"] = self.id

        lesson["original"] = original_lesson

        lesson["start_point"] = self.start_point.strftime("%Y-%m-%dT%H:%M:%S")
        lesson["end_point"] = self.end_point.strftime("%Y-%m-%dT%H:%M:%S")

        lesson["schedule_auditorium_id"] = self.auditorium_id
        if self.schedule_course_code is not None:
            lesson["schedule_course_code"] = self.schedule_course_code
        else:
            lesson["schedule_course_code"] = ""

        if self.grp_emails:
            lesson["grp_emails"] = self.grp_emails

        return lesson


class Room:
    def __init__(self, room_attributes: dict) -> None:
        self.schedule_room_id: int = room_attributes["auditoriumOid"]
        self.building_id: str = room_attributes["buildingGid"]

    def __str__(self) -> None:
        return f"Room id - {self.ruz_room_id}\nBuilding id - {self.building_id}"
