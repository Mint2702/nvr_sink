import requests

API_URL = "https://nvr.miem.hse.ru/api/erudite"


def get_course_emails(course_code):
    res = requests.get(f"{API_URL}/disciplines", params={"course_code": course_code})
    
    data = res.json()['data']
    grp_emails = data.get("emails")

    if grp_emails == ['']:
        return None

    return grp_emails
