import requests
from datetime import datetime, timedelta


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
        lesson['description'] = (f"{class_['stream']}\n{class_['discipline']}\n"
                                 f"{class_['lecturer']}\n{class_['kindOfWork']}\n{lesson['location']}")
        classes.append(lesson)

    return classes
