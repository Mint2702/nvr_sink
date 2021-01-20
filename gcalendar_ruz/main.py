from datetime import datetime, timedelta
import asyncio
from loguru import logger
import time

from core.apis.ruz_api import RuzApi
from core.apis.calendar_api import GCalendar
from core.db.models import Session, Room, OnlineRoom, Record, UserRecord, User
from core.apis.nvr_api import Nvr_Api
from core.redis_caching.caching import redis_connect
import core.utils as test


class CalendarManager:
    def __init__(self):
        self.session = Session()
        self.ruz_api = RuzApi()
        self.nvr_api = Nvr_Api()
        self.calendar_api = GCalendar()

    def __del__(self):
        self.session.close()

    async def add_offline_classes(
        self,
        room: Room,
        lesson: dict,
    ):
        if not await self.nvr_api.check_lessons(lesson):
            event = await self.calendar_api.create_event(room.calendar, lesson)
            lesson["gcalendar_event_id"] = event["id"]
            lesson["gcalendar_calendar_id"] = room.calendar
            await self.nvr_api.add_lesson(lesson)
            await self.create_record(room, event)

    async def fetch_offline_room(
        self,
        room: Room,
    ):
        try:
            classes = await self.ruz_api.get_classes(room.ruz_id)
        except Exception as err:
            classes = None
            logger.error(err)

        if classes:

            logger.info("Adding classes to calendar and Erudite")
            for i in range(0, len(classes), 5):
                chunk = classes[i : i + 5]
                tasks = [self.add_offline_classes(room, lesson) for lesson in chunk]

                await asyncio.gather(*tasks)

    async def fetch_offline_rooms(
        self,
    ):
        rooms = self.session.query(Room).all()

        tasks = [self.fetch_offline_room(room) for room in rooms if room.sources]

        await asyncio.gather(*tasks)

        logger.info(
            f"Created events for {datetime.today().date() + timedelta(days=1)} - {datetime.today().date() + timedelta(days=60)}"
        )

    async def add_online_room(self, classes: list, i: int, ruz: RuzApi, jitsi):
        chunk = classes[i : i + 10]
        ruz_classes = [
            lesson
            for lesson in chunk
            if lesson["ruz_url"] is None or "meet.miem.hse.ru" not in lesson["ruz_url"]
        ]
        jitsi_classes = [
            class_
            for class_ in chunk
            if class_["ruz_url"] is not None and "meet.miem.hse.ru" in class_["ruz_url"]
        ]

        logger.info("Adding ruz classes: ")
        for lesson in ruz_classes:
            event = await self.calendar_api.create_event(ruz.calendar, lesson)
            lesson["gcalendar_event_id"] = event["id"]
            lesson["gcalendar_calendar_id"] = ruz.calendar
            await self.nvr_api.add_lesson(lesson)

        logger.info("Adding jitsi classes: ")
        for lesson in jitsi_classes:
            event = await self.calendar_api.create_event(jitsi.calendar, lesson)
            lesson["gcalendar_event_id"] = event["id"]
            lesson["gcalendar_calendar_id"] = jitsi.calendar
            await self.nvr_api.add_lesson(lesson)

    async def fetch_online_room(
        self,
        room: Room,
        ruz: OnlineRoom,
        jitsi: OnlineRoom,
    ):
        try:
            classes = await self.ruz_api.get_classes(room["auditoriumOid"], online=True)
            classes_len = len(classes)
        except Exception as err:
            logger.error(err)
            return False

        tasks = [self.add_online_room(classes, i, ruz, jitsi) for i in range(0, classes_len, 10)]

        await asyncio.gather(*tasks)

    async def fetch_online_rooms(
        self,
    ):
        ruz = self.session.query(OnlineRoom).filter_by(name="РУЗ").first()
        jitsi = self.session.query(OnlineRoom).filter_by(name="Jitsi").first()

        rooms = await self.ruz_api.get_auditoriumoid()

        tasks = [self.fetch_online_room(room, ruz, jitsi) for room in rooms]

        await asyncio.gather(*tasks)

        logger.info(f"Creating events for {datetime.today().date() + timedelta(days=1)} done\n")

    async def create_record(self, room: Room, event: dict):
        start_date = event["start"]["dateTime"].split("T")[0]
        end_date = event["end"]["dateTime"].split("T")[0]

        if start_date != end_date:
            return

        creator = self.session.query(User).filter_by(email=event["creator"]["email"]).first()
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

    async def delete_online_events(self):
        ruz = self.session.query(OnlineRoom).filter_by(name="РУЗ").first()
        jitsi = self.session.query(OnlineRoom).filter_by(name="Jitsi").first()

        events = await self.calendar_api.get_events(jitsi.calendar)
        for event in events:
            await self.calendar_api.delete_event(jitsi.calendar, event["id"])

        events = await self.calendar_api.get_events(ruz.calendar)
        for event in events:
            await self.calendar_api.delete_event(ruz.calendar, event["id"])


@logger.catch
async def main():
    await redis_connect()
    manager = CalendarManager()

    tasks = [
        manager.fetch_offline_rooms(),
        # manager.fetch_online_rooms(),
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
