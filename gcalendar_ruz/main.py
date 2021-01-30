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
        check_data = await self.nvr_api.check_lesson(lesson)
        status = check_data[0]

        # Lesson not found in Erudite, so we add it
        if status == "Not found":
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
        elif status == "Update":
            lesson_id = check_data[1]
            event_id = check_data[2]
            if lesson["ruz_url"] is None or "meet.miem.hse.ru" not in lesson["ruz_url"]:
                logger.info("Updating ruz lesson")
                await self.calendar_api.get_event(ruz.calendar, event_id)
                event = await self.calendar_api.update_event(
                    ruz.calendar, event_id, lesson
                )
                try:
                    lesson["gcalendar_event_id"] = event["id"]
                    lesson["gcalendar_calendar_id"] = ruz.calendar
                    await self.nvr_api.update_lesson(lesson_id, lesson)

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
                await self.calendar_api.get_event(jitsi.calendar, event_id)
                event = await self.calendar_api.update_event(
                    jitsi.calendar, event_id, lesson
                )
                try:
                    lesson["gcalendar_event_id"] = event["id"]
                    lesson["gcalendar_calendar_id"] = jitsi.calendar
                    await self.nvr_api.update_lesson(lesson_id, lesson)
                except Exception:
                    logger.error(f"Something wrong with Google - {event}.")
            else:
                pass

            time.sleep(0.3)

        # Lesson found in Erudite and it is up to date
        else:
            return False

    async def get_and_check_lessons_from_room(
        self, room_id: str, offline_rooms: list, room_name: str
    ):
        lessons = await self.get_lessons_from_room(room_id)

        if lessons:
            logger.info(
                f"""
                Successfully got lessons for room {room_name}
                Adding lessons to calendar and Erudite
                """
            )
            for i in range(0, len(lessons), 5):
                chunk = lessons[i : i + 5]

                tasks = [
                    self.add_lesson(room_id, lesson, offline_rooms) for lesson in chunk
                ]
                await asyncio.gather(*tasks)
                time.sleep(0.4)
            await self.nvr_api.check_delete_Erudite_lessons(lessons, room_id)
            time.sleep(0.1)

    async def get_and_handle_rooms(self):
        offline_rooms = [room.name for room in self.session.query(Room).all()]

        rooms = await self.ruz_api.get_auditoriumoid()

        tasks = [
            self.get_and_check_lessons_from_room(
                room["auditoriumOid"], offline_rooms, room["number"]
            )
            for room in rooms
        ]

        await asyncio.gather(*tasks)

        logger.info(
            f"Created events for {datetime.today().date() + timedelta(days=1)} - {datetime.today().date() + timedelta(days=60)}"
        )

    async def get_lessons_from_room(self, room_id: str) -> list:
        try:
            lessons = await self.ruz_api.get_classes(room_id)
        except Exception as err:
            lessons = None
            logger.error(err)

        return lessons

    async def get_online_rooms(self):
        global ruz
        global jitsi

        ruz = self.session.query(OnlineRoom).filter_by(name="РУЗ").first()
        jitsi = self.session.query(OnlineRoom).filter_by(name="Jitsi").first()

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

    tasks = [manager.get_and_handle_rooms(), manager.get_online_rooms()]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
