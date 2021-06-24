class Lesson:
    def __init__(self, lesson_attributes: dict) -> None:
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


class Room:
    def __init__(self, room_attributes: dict) -> None:
        self.ruz_room_id: int = room_attributes["auditoriumOid"]
        self.building_id: str = room_attributes["buildingGid"]

    def __str__(self) -> None:
        return f"Room id - {self.ruz_room_id}\nBuilding id - {self.building_id}"
