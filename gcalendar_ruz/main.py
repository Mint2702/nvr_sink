import time
from datetime import datetime, timedelta
import asyncio
from loguru import logger

from core.apis.ruz_api import RuzApi
from core.apis.calendar_api import GCalendar
from core.db.models import Session, Room, OnlineRoom, Record, UserRecord, User
from core.apis import nvr_api


class CalendarManager:
    def __init__(self):
        self.session = Session()
        self.ruz_api = RuzApi()
        self.calendar_api = GCalendar(
            "core/creds/credentials.json",
            "core/creds/tokenCalendar.pickle",
        )

    def __del__(self):
        self.session.close()

    async def fetch_offline_rooms(
        self,
        sem_google: asyncio.Semaphore,
        sem_ruz: asyncio.Semaphore,
        sem_nvr: asyncio.Semaphore,
    ):
        rooms = self.session.query(Room).all()

        for room in rooms:
            if not room.sources:
                continue

            try:
                async with sem_ruz:
                    classes = await self.ruz_api.get_classes(room.ruz_id)
            except Exception:
                continue

            for i in range(0, len(classes), 10):
                chunk = classes[i : i + 10]
                logger.info(f"Adding classes: {chunk}")
                for lesson in chunk:
                    async with sem_google:
                        event = await self.calendar_api.create_event(room.calendar, lesson)
                    lesson["gcalendar_event_id"] = event["id"]
                    lesson["gcalendar_calendar_id"] = room.calendar
                    async with sem_nvr:
                        await nvr_api.add_lesson(lesson)
                    await self.create_record(room, event)

        logger.info(f"Created events for {datetime.today().date() + timedelta(days=1)}")

    async def fetch_online_rooms(
        self,
        sem_google: asyncio.Semaphore,
        sem_ruz: asyncio.Semaphore,
        sem_nvr: asyncio.Semaphore,
    ):
        ruz = self.session.query(OnlineRoom).filter_by(name="РУЗ").first()
        jitsi = self.session.query(OnlineRoom).filter_by(name="Jitsi").first()

        async with sem_ruz:
            rooms = await self.ruz_api.get_auditoriumoid()

        for room in rooms:
            try:
                async with sem_ruz:
                    classes = await self.ruz_api.get_classes(room["auditoriumOid"], online=True)
                classes_len = len(classes)
            except Exception as err:
                logger.error(err, exc_info=True)
                continue

            for i in range(0, classes_len, 10):
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

                logger.info(f"Adding ruz classes: {ruz_classes}")
                for lesson in ruz_classes:
                    async with sem_google:
                        event = await self.calendar_api.create_event(ruz.calendar, lesson)
                    try:  # Не забыть убрать на проде!!!
                        lesson["gcalendar_event_id"] = event["id"]
                    except:
                        continue
                    lesson["gcalendar_calendar_id"] = ruz.calendar
                    async with sem_nvr:
                        await nvr_api.add_lesson(lesson)

                logger.info(f"Adding jitsi classes: {jitsi_classes}")
                for lesson in jitsi_classes:
                    async with sem_google:
                        event = await self.calendar_api.create_event(jitsi.calendar, lesson)
                    lesson["gcalendar_event_id"] = event["id"]
                    lesson["gcalendar_calendar_id"] = jitsi.calendar
                    async with sem_nvr:
                        await nvr_api.add_lesson(lesson)

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
    sem_google = asyncio.Semaphore(10)
    sem_ruz = asyncio.Semaphore(10)
    sem_nvr = asyncio.Semaphore(10)

    manager = CalendarManager()
    await manager.fetch_offline_rooms(sem_google, sem_ruz, sem_nvr)
    await manager.fetch_online_rooms(sem_google, sem_ruz, sem_nvr)


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    end = time.time()
    logger.info("Время выполнения: {} секунд.".format(end - start))
