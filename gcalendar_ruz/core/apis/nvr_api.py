import requests
import logging
from ..settings import settings


NVR_API_URL = "https://nvr.miem.hse.ru/api/erudite"
NVR_API_KEY = settings.nvr_api_key

logger = logging.getLogger("ruz_logger")

"""
def get_course_emails(course_code):
    res = requests.get(f"{NVR_API_URL}/disciplines", params={"course_code": course_code})
    logger.info(f"nvr.get_course_emails returned {res.status_code}, with body {res.text}")

    data = res.json()
    grp_emails = data.get("emails")

    if grp_emails == [""]:
        return None

    return grp_emails"""


def add_lesson(lesson):
    res = requests.post(f"{NVR_API_URL}/lessons", json=lesson, headers={"key": NVR_API_KEY})
    logger.info(f"nvr.add_lesson returned {res.status_code}, with body {res.text}")
