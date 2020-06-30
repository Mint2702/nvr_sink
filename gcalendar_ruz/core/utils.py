from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from .db.models import Room
from .apis.calendar_api import create_event_


engine = create_engine(os.environ.get('SQLALCHEMY_DATABASE_URI'))
Session = sessionmaker(bind=engine)


def add_classes_to_calendar(classes):
    session = Session()

    for class_ in classes:
        room_name = class_['room']
        room = session.query(Room).filter(Room.name == room_name).first()
        create_event_(room.calendar, class_['summary'],
                      class_['location'], class_['description'], class_['start_time'])

    session.close()
