from datetime import datetime, timedelta
import asyncio
from loguru import logger

from core.apis.ruz_api import RuzApi
from core.apis.calendar_api import GCalendar
from core.db.models import Session, Room, OnlineRoom, Record, UserRecord, User
from core.apis.nvr_api import Nvr_Api
from core.redis_caching.caching import redis_connect


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
        status = await self.nvr_api.check_lesson(lesson)

        # Lesson not found in Erudite, so we add it
        if status[0] == "Not found":
            event = await self.calendar_api.create_event(room.calendar, lesson)
            try:
                lesson["gcalendar_event_id"] = event["id"]
                lesson["gcalendar_calendar_id"] = room.calendar
                await self.nvr_api.add_lesson(lesson)
                await self.create_record(room, event)
            except Exception:
                logger.error(f"Something wrong with Google - {event}.")

        # Lesson found in Erudite, but the data of this lesson has to be updated
        elif status[0] == "Update":
            await self.calendar_api.delete_event(room.calendar, status[2])
            event = await self.calendar_api.create_event(room.calendar, lesson)
            lesson["gcalendar_event_id"] = event["id"]
            lesson["gcalendar_calendar_id"] = room.calendar
            await self.create_record(room, event)
            await self.nvr_api.update_lesson(status[1], lesson)

        # Lesson found in Erudite and it is up to date
        else:
            pass

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
            if not self.nvr_api.check_all_lessons(classes, room.name):
                logger.info(
                    f"""
                Successfully got lessons for room {room.ruz_id}
                Adding offline classes to calendar and Erudite
                """
                )
                for i in range(0, len(classes), 7):
                    chunk = classes[i : i + 7]

                    tasks = [self.add_offline_classes(room, lesson) for lesson in chunk]
                    await asyncio.gather(*tasks)
                    await asyncio.sleep(0.5)
                await self.nvr_api.check_delete_Erudite_lessons(classes, room.name)
            else:
                logger.info("Lessons in Erudite and Ruz for offline rooms are the same")

    async def fetch_offline_rooms(
        self,
    ):
        rooms = self.session.query(Room).all()

        tasks = [self.fetch_offline_room(room) for room in rooms if room.sources]

        await asyncio.gather(*tasks)

        logger.info(
            f"Created events for {datetime.today().date() + timedelta(days=1)} - {datetime.today().date() + timedelta(days=60)}"
        )

    async def add_online_room(self, lesson: dict, ruz: OnlineRoom, jitsi: OnlineRoom):
        status = await self.nvr_api.check_lesson(lesson)

        # Lesson not found in Erudite, so we add it
        if status[0] == "Not found":
            if lesson["ruz_url"] is None or "meet.miem.hse.ru" not in lesson["ruz_url"]:
                event = await self.calendar_api.create_event(ruz.calendar, lesson)
                lesson["gcalendar_event_id"] = event["id"]
                lesson["gcalendar_calendar_id"] = ruz.calendar
                await self.nvr_api.add_lesson(lesson)

            elif lesson["ruz_url"] is not None and "meet.miem.hse.ru" in lesson["ruz_url"]:
                event = await self.calendar_api.create_event(jitsi.calendar, lesson)
                lesson["gcalendar_event_id"] = event["id"]
                lesson["gcalendar_calendar_id"] = jitsi.calendar
                await self.nvr_api.add_lesson(lesson)
            else:
                pass

        # Lesson found in Erudite, but the data of this lesson has to be updated
        elif status[0] == "Update":
            if lesson["ruz_url"] is None or "meet.miem.hse.ru" not in lesson["ruz_url"]:
                await self.calendar_api.delete_event(ruz.calendar, status[2])
                event = await self.calendar_api.create_event(ruz.calendar, lesson)
                lesson["gcalendar_event_id"] = event["id"]
                lesson["gcalendar_calendar_id"] = ruz.calendar
                await self.nvr_api.update_lesson(status[1], lesson)
            elif lesson["ruz_url"] is not None and "meet.miem.hse.ru" in lesson["ruz_url"]:
                await self.calendar_api.delete_event(jitsi.calendar, status[2])
                event = await self.calendar_api.create_event(jitsi.calendar, lesson)
                lesson["gcalendar_event_id"] = event["id"]
                lesson["gcalendar_calendar_id"] = jitsi.calendar
                await self.nvr_api.update_lesson(status[1], lesson)
            else:
                pass

        # Lesson found in Erudite and it is up to date
        else:
            pass

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

        logger.info("Adding jitsi and RUZ classes")

        for i in range(0, classes_len, 5):
            chunk = classes[i : i + 5]

            tasks = [self.add_online_room(lesson, ruz, jitsi) for lesson in chunk]
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.5)

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


@logger.catch
async def main():
    await redis_connect()
    manager = CalendarManager()

    tasks = [
        manager.fetch_offline_rooms(),
        manager.fetch_online_rooms(),
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
