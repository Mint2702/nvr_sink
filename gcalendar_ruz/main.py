import time
from datetime import datetime, timedelta
import logging


from core.apis.ruz_api import RuzApi
from core.apis.calendar_api import GCalendar
from core.db.models import Session, Room, OnlineRoom, Record, UserRecord, User


def create_logger(mode="INFO"):
    logs = {"INFO": logging.INFO, "DEBUG": logging.DEBUG}

    logger = logging.getLogger("ruz_logger")
    logger.setLevel(logs[mode])

    handler = logging.StreamHandler()
    handler.setLevel(logs[mode])

    formatter = logging.Formatter(
        "%(levelname)-8s  %(asctime)s    %(message)s", datefmt="%d-%m-%Y %I:%M:%S %p"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


logger = create_logger()


class CalendarManager:
    def __init__(self):
        self.session = Session()
        self.ruz_api = RuzApi()
        self.calendar_api = GCalendar(
            "/gcalendar_ruz/creds/creds.json",
            "/gcalendar_ruz/creds/tokenCalendar.pickle",
        )

    def __del__(self):
        self.session.close()

    def fetch_offline_rooms(self):
        rooms = self.session.query(Room).all()

        for room in rooms:
            if not room.sources:
                continue
            
            try:
                classes = self.ruz_api.get_classes(room.ruz_id)
            except Exception:
                continue

            for i in range(0, len(classes), 10):
                chunk = classes[i : i + 10]
                logger.info(f"Adding classes: {chunk}")
                for class_ in chunk:
                    event = self.calendar_api.create_event_(room.calendar, class_)
                    self.create_record(room, event)
                time.sleep(10)

        logger.info(f"Created events for {datetime.today().date() + timedelta(days=1)}")

    def fetch_online_rooms(self):
        ruz = self.session.query(OnlineRoom).filter_by(name="РУЗ").first()
        jitsi = self.session.query(OnlineRoom).filter_by(name="Jitsi").first()

        rooms = self.ruz_api.get_auditoriumoid()

        for room in rooms:
            try:
                classes = self.ruz_api.get_classes(room["auditoriumOid"], online=True)
                classes_len = len(classes)
            except Exception as err:
                logger.error(err, exc_info=True)
                continue

            for i in range(0, classes_len, 10):
                chunk = classes[i : i + 10]
                ruz_classes = [
                    class_
                    for class_ in chunk
                    if class_["url"] is None or "meet.miem.hse.ru" not in class_["url"]
                ]
                jitsi_classes = [
                    class_
                    for class_ in chunk
                    if class_["url"] is not None and "meet.miem.hse.ru" in class_["url"]
                ]

                logger.info(f"Adding ruz classes: {ruz_classes}")
                for class_ in ruz_classes:
                    self.calendar_api.create_event_(ruz.calendar, class_)

                logger.info(f"Adding jitsi classes: {jitsi_classes}")
                for class_ in jitsi_classes:
                    self.calendar_api.create_event_(jitsi.calendar, class_)

                time.sleep(10)

        logger.info(
            f"Creating events for {datetime.today().date() + timedelta(days=1)} done\n"
        )

    def create_record(self, room: Room, event: dict):
        start_date = event["start"]["dateTime"].split("T")[0]
        end_date = event["end"]["dateTime"].split("T")[0]

        if start_date != end_date:
            return

        creator = (
            self.session.query(User).filter_by(email=event["creator"]["email"]).first()
        )
        if not creator:
            return

        new_record = Record()
        new_record.room = room
        new_record.update_from_calendar(**event)
        self.session.add(new_record)
        self.session.commit()

        user_record = UserRecord(user_id=creator.id, record_id=new_record.id)
        self.session.add(user_record)
        self.session.commit()

    def delete_online_events(self):
        ruz = self.session.query(OnlineRoom).filter_by(name="РУЗ").first()
        jitsi = self.session.query(OnlineRoom).filter_by(name="Jitsi").first()

        events = self.calendar_api.get_events(jitsi.calendar)
        for event in events:
            self.calendar_api.delete_event(jitsi.calendar, event["id"])

        events = self.calendar_api.get_events(ruz.calendar)
        for event in events:
            self.calendar_api.delete_event(ruz.calendar, event["id"])


if __name__ == "__main__":
    manager = CalendarManager()
    manager.fetch_offline_rooms()
    manager.fetch_online_rooms()
