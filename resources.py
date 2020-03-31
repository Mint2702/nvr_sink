from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from ruz import get_auditoriumoid


class GoogleAdminService:
    def __init__(self):
        SCOPES = 'https://www.googleapis.com/auth/admin.directory.resource.calendar'
        SERVICE_ACCOUNT_FILE = 'resources-parser.json'
        GSUIT_DOMAIN_ACCOUNT = 'resources@miem.hse.ru'

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        delegated_credentials = credentials.create_delegated(
            GSUIT_DOMAIN_ACCOUNT)
        self.service = build('admin', 'directory_v1',
                             credentials=delegated_credentials)

    def set_resource(self, body):
        results = self.service.resources().calendars().insert(
            customer='C03s7v7u4', body=body).execute()
        return results


if __name__ == '__main__':
    googleAdminService = GoogleAdminService()
    auditories = get_auditoriumoid()
    for room in auditories:
        body = {"resourceId": room['auditoriumOid'],
                "resourceName": f"Аудитория {room['number']}",
                'floorSection': room['number'],
                "resourceDescription": room['typeOfAuditorium'],
                'capacity': room['amount'],
                'userVisibleDescription': f"Аудитория {room['number']}\n"
                                          f"https://meet.miem.hse.ru/{room['number']}",
                'resourceType': 'Room'}

        if room['number'] == '504':
            resource = googleAdminService.set_resource(body)
