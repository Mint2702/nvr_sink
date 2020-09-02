import time
import os
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.apis.ruz_api import RuzApi
from core.apis.calendar_api import GCalendar
from core.db.models import Room


engine = create_engine(os.environ.get('SQLALCHEMY_DATABASE_URI'))
Session = sessionmaker(bind=engine)

if __name__ == "__main__":
    ruz_api = RuzApi()
    calendar_api = GCalendar(
        '/gcalendar_ruz/creds/creds.json', '/gcalendar_ruz/creds/tokenCalendar.pickle')

    session = Session()
    rooms = session.query(Room).all()
    session.close()

    for room in rooms:
        try:
            classes = ruz_api.get_classes(room.ruz_id)
        except:
            continue

        for i in range(0, len(classes), 10):
            chunk = classes[i:i + 10]
            print(f'Adding classes: {chunk}')
            calendar_api.add_classes_to_calendar(chunk, room.calendar)
            time.sleep(10)
    print(
        f"Created events for {datetime.today().date() + timedelta(days=1)}")
