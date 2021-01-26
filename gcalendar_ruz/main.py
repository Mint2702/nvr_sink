from datetime import datetime, timedelta
import asyncio
from loguru import logger
import time

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

    async def add_lesson(
        self,
        room_id: str,
        lesson: dict,
        offline_rooms: list,
    ):
        status = await self.nvr_api.check_lesson(lesson)

        # Lesson not found in Erudite, so we add it
        if status[0] == "Not found":
            if lesson["ruz_url"] is None or "meet.miem.hse.ru" not in lesson["ruz_url"]:
                logger.info("Adding ruz lesson")
                event = await self.calendar_api.create_event(ruz.calendar, lesson)
                try:
                    lesson["gcalendar_event_id"] = event["id"]
                    lesson["gcalendar_calendar_id"] = ruz.calendar
                    await self.nvr_api.add_lesson(lesson)

                    if lesson["ruz_auditorium"] in offline_rooms:
                        room = (
                            self.session.query(Room)
                            .filter_by(name=lesson["ruz_auditorium"])
                            .first()
                        )
                        self.create_record(room, event)
                except Exception:
                    logger.error(f"Something wrong with Google - {event}.")

            elif (
                lesson["ruz_url"] is not None
                and "meet.miem.hse.ru" in lesson["ruz_url"]
            ):
                logger.info("Adding jitsi lesson")
                event = await self.calendar_api.create_event(jitsi.calendar, lesson)
                try:
                    lesson["gcalendar_event_id"] = event["id"]
                    lesson["gcalendar_calendar_id"] = jitsi.calendar
                    await self.nvr_api.add_lesson(lesson)
                except Exception:
                    logger.error(f"Something wrong with Google - {event}.")
            else:
                pass

        # Lesson found in Erudite, but the data of this lesson has to be updated
        elif status[0] == "Update":
            if lesson["ruz_url"] is None or "meet.miem.hse.ru" not in lesson["ruz_url"]:
                logger.info("Updating ruz lesson")
                event = await self.calendar_api.update_event(
                    ruz.calendar, status[2], lesson
                )
                try:
                    lesson["gcalendar_event_id"] = event["id"]
                    lesson["gcalendar_calendar_id"] = ruz.calendar
                    await self.nvr_api.update_lesson(status[1], lesson)

                    if lesson["ruz_auditorium"] in offline_rooms:
                        room = (
                            self.session.query(Room)
                            .filter_by(name=lesson["ruz_auditorium"])
                            .first()
                        )
                        self.create_record(room, event)
                except Exception:
                    logger.error(f"Something wrong with Google - {event}.")

            elif (
                lesson["ruz_url"] is not None
                and "meet.miem.hse.ru" in lesson["ruz_url"]
            ):
                logger.info("Updating jitsi lesson")
                event = await self.calendar_api.update_event(
                    jitsi.calendar, status[2], lesson
                )
                try:
                    lesson["gcalendar_event_id"] = event["id"]
                    lesson["gcalendar_calendar_id"] = jitsi.calendar
                    await self.nvr_api.update_lesson(status[1], lesson)
                except Exception:
                    logger.error(f"Something wrong with Google - {event}.")
            else:
                pass

        # Lesson found in Erudite and it is up to date
        else:
            pass

    async def fetch_room(self, room_id: str, offline_rooms: list):
        print(room_id)
        try:
            lessons = await self.ruz_api.get_classes(room_id)
        except Exception as err:
            lessons = None
            logger.error(err)

        if lessons:
            if not self.nvr_api.check_all_lessons(lessons, room_id):
                logger.info(
                    f"""
                Successfully got lessons for room {room_id}
                Adding lessons to calendar and Erudite
                """
                )
                for i in range(0, len(lessons), 3):
                    chunk = lessons[i : i + 3]

                    tasks = [
                        self.add_lesson(room_id, lesson, offline_rooms)
                        for lesson in chunk
                    ]
                    await asyncio.gather(*tasks)
                    time.sleep(2)
                await self.nvr_api.check_delete_Erudite_lessons(lessons, room_id)
            else:
                logger.info("Lessons in Erudite and Ruz for offline rooms are the same")

    async def fetch_rooms(
        self,
    ):
        global ruz
        global jitsi

        ruz = self.session.query(OnlineRoom).filter_by(name="РУЗ").first()
        jitsi = self.session.query(OnlineRoom).filter_by(name="Jitsi").first()

        offline_rooms = [room.name for room in self.session.query(Room).all()]

        rooms = await self.ruz_api.get_auditoriumoid()

        tasks = [
            self.fetch_room(room["auditoriumOid"], offline_rooms) for room in rooms
        ]

        await asyncio.gather(*tasks)

        logger.info(
            f"Created events for {datetime.today().date() + timedelta(days=1)} - {datetime.today().date() + timedelta(days=60)}"
        )

    async def create_record(self, room: Room, event: dict):
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


@logger.catch
async def main():
    await redis_connect()
    manager = CalendarManager()

    await asyncio.gather(manager.fetch_rooms())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
