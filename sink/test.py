# import ruz

# schedule = ruz.person_lessons("dimirtalibov@edu.hse.ru")
# for lesson in schedule:
#     print(lesson)
#     print()

from aiohttp import ClientSession
import asyncio
import time

from core.api.ruz_api import RuzApi


async def get_lessons(ruz_room_id):
    lessons = await ruz.get_lessons_in_room(ruz_room_id)
    time.sleep(0.5)
    print(lessons)


async def main():
    global ruz
    ruz = RuzApi()
    rooms = await ruz.get_rooms()
    tasks = [get_lessons(room["auditoriumOid"]) for room in rooms]
    await asyncio.gather(*tasks)
    # print(rooms)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
