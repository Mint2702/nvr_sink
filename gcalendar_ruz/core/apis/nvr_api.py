import requests
import logging

from ..settings import settings


NVR_API_URL = "https://nvr.miem.hse.ru/api/erudite"
NVR_API_KEY = settings.nvr_api_key

logger = logging.getLogger("ruz_logger")


# @cach("emails") - нет смысла кешировать эту функцию, так как она работает только вместе с функцией get_classes
def get_course_emails(course_code: str):
    res = requests.get(f"{NVR_API_URL}/disciplines", params={"course_code": course_code})
    logger.info(f"nvr.get_course_emails returned {res.status_code}, with body {res.text}")

    data = res.json()
    # If the responce is not list -> the responce is a message that discipline is not found, and it should not be analysed further
    if type(data) == list:
        grp_emails = data[0].get("emails")
    else:
        return None

    if grp_emails == [""]:
        return None

    return grp_emails


def add_lesson(lesson):
    res = requests.post(f"{NVR_API_URL}/lessons", json=lesson, headers={"key": NVR_API_KEY})
    logger.info(f"nvr.add_lesson returned {res.status_code}, with body {res.text}")
