import time
import os
from datetime import datetime, timedelta
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.apis.ruz_api import RuzApi
from core.apis.calendar_api import GCalendar
from core.db.models import Room, OnlineRoom


engine = create_engine(os.environ.get("SQLALCHEMY_DATABASE_URI"))
Session = sessionmaker(bind=engine)


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

ruz_api = RuzApi()
calendar_api = GCalendar(
    "/gcalendar_ruz/creds/creds.json", "/gcalendar_ruz/creds/tokenCalendar.pickle"
)


def fetch_offline_rooms():
    session = Session()
    rooms = session.query(Room).all()
    session.close()

    for room in rooms:
        try:
            classes = ruz_api.get_classes(room.ruz_id)
        except Exception:
            continue

        for i in range(0, len(classes), 10):
            chunk = classes[i : i + 10]
            logger.info(f"Adding classes: {chunk}")
            calendar_api.add_classes_to_calendar(chunk, room.calendar)
            time.sleep(10)
    logger.info(f"Created events for {datetime.today().date() + timedelta(days=1)}")


def fetch_online_rooms():
    session = Session()
    ruz = session.query(OnlineRoom).filter_by(name="РУЗ").first()
    jitsi = session.query(OnlineRoom).filter_by(name="Jitsi").first()
    session.close()

    rooms = ruz_api.get_auditoriumoid()

    for room in rooms:
        try:
            classes = ruz_api.get_classes(room["auditoriumOid"])
            classes_len = len(classes)
        except Exception:
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
            calendar_api.add_classes_to_calendar(ruz_classes, ruz.calendar)
            logger.info(f"Adding jitsi classes: {jitsi_classes}")
            calendar_api.add_classes_to_calendar(jitsi_classes, jitsi.calendar)
            time.sleep(10)

    logger.info(
        f"Creating events for {datetime.today().date() + timedelta(days=1)} done\n"
    )


if __name__ == "__main__":
    fetch_offline_rooms()
    fetch_online_rooms()
