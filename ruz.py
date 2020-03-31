import requests
from datetime import datetime, timedelta
from calendarSettings import create_event_

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Room
import os

engine = create_engine(os.environ.get('SQLALCHEMY_DATABASE_URI'))
Session = sessionmaker(bind=engine)
RUZ_API_URL = 'http://92.242.58.221/ruzservice.svc'


# building id МИЭМа = 92
def get_auditoriumoid(building_id=92):
    all_auditories = requests.get(
        f'{RUZ_API_URL}/auditoriums?buildingoid=0').json()

    return [room for room in all_auditories if room['buildingGid'] == building_id]


# function that requests information about classes for 7 days from today and returns list of dicts
def get_classes(aud_id):
    # getting current date (from_date) and a month after (to_date)
    from_date = datetime.today().strftime('%Y.%m.%d')
    to_date = (datetime.strptime(from_date, '%Y.%m.%d') +
               timedelta(days=6)).strftime('%Y.%m.%d')

    res = requests.get(f"{RUZ_API_URL}/lessons?fromdate=" +
                       from_date + "&todate=" + to_date + "&auditoriumoid=" + aud_id)

    classes = []
    for class_ in res.json():
        lesson = {'room': class_['auditorium']}
        lesson['start_time'] = datetime.strptime(
            (class_['date'] + class_['beginLesson']), '%Y.%m.%d%H:%M')
        lesson['summary'] = class_['discipline']
        lesson['location'] = f"{class_['auditorium']}/{class_['building']}"
        lesson['description'] = (f"{class_['discipline']}\n{class_['lecturer']}\n"
                                 f"{class_['stream']}\n{class_['kindOfWork']}\n{lesson['location']}")
        classes.append(lesson)

    return classes


def add_classes_to_calendar(classes):
    session = Session()

    for class_ in classes:
        room_name = class_['room']
        room = session.query(Room).filter(Room.name == room_name).first()
        create_event_(room.calendar, class_['summary'],
                      class_['location'], class_['description'], class_['start_time'])

    session.close()
