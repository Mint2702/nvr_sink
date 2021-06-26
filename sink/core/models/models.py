from loguru import logger
from copy import deepcopy


class Lesson:
    def __init__(self, lesson_attributes: dict, source: str = "ruz") -> None:
        """ Converts given dictionary of lesson's attributes to the Lesson's fields, depending on the source of data about lesson """

        if source == "ruz":
            self.ruz_convertation(lesson_attributes)
        elif source == "erudite":
            self.erudite_convertation(lesson_attributes)
        else:
            logger.error("Source not supported")

    def ruz_convertation(self, lesson_attributes: dict) -> None:
        """ Converts given list of lesson's attributes to the Lesson's fields """

        self.original: dict = deepcopy(lesson_attributes)

        date = lesson_attributes["date"].split(".")
        self.date: str = "-".join(date)

        try:
            self.id = lesson_attributes["lessonOid"]
        except:
            print(lesson_attributes)
            raise Exception

        self.start_time = lesson_attributes["beginLesson"]
        self.end_time = lesson_attributes["endLesson"]

        self.url = lesson_attributes["url1"]

        self.auditorium = lesson_attributes["auditorium"]

        # We later fill group email with function
        self.grp_emails = None

        if not lesson_attributes["group"]:
            self.course_code = None
        else:
            self.course_code: str = lesson_attributes["group"].split("#")[0]

    def erudite_convertation(self, lesson_attributes: dict) -> None:
        """ Converts given list of lesson's attributes to the Lesson's fields """

        self.id = lesson_attributes["ruz_lesson_id"]
        self.erudite_id = lesson_attributes["id"]
        self.original = lesson_attributes["original"]

        self.date = lesson_attributes["date"]
        self.start_time = lesson_attributes["start_time"]
        self.end_time = lesson_attributes["end_time"]

        self.auditorium = lesson_attributes["ruz_auditorium_id"]
        self.url = lesson_attributes["url"]

        grp_emails = lesson_attributes.get("grp_emails")
        if grp_emails:
            self.grp_emails = grp_emails

        self.course_code = lesson_attributes["course_code"]

    def to_json(self) -> dict:
        """ Converts data, stored in the object to dict """

        lesson = {}
        original_lesson = deepcopy(self.original)

        lesson["ruz_lesson_id"] = self.id

        lesson["original"] = original_lesson
        lesson["date"] = self.date

        lesson["start_time"] = self.start_time
        lesson["end_time"] = self.end_time

        lesson["url"] = self.url

        lesson["ruz_auditorium_id"] = self.auditorium
        if self.course_code is not None:
            lesson["course_code"] = self.course_code
        else:
            lesson["course_code"] = ""

        if self.grp_emails:
            lesson["grp_emails"] = self.grp_emails

        return lesson


class Room:
    def __init__(self, room_attributes: dict) -> None:
        self.ruz_room_id: int = room_attributes["auditoriumOid"]
        self.building_id: str = room_attributes["buildingGid"]

    def __str__(self) -> None:
        return f"Room id - {self.ruz_room_id}\nBuilding id - {self.building_id}"
