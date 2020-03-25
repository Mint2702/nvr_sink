from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from time import time_ns
from ruz import get_auditoriumoid

class GoogleAdminService:
    def __init__(self):
        SCOPES = ['https://www.googleapis.com/auth/admin.directory.resource.calendar.readonly',
              'https://www.googleapis.com/auth/admin.directory.resource.calendar']
        SERVICE_ACCOUNT_FILE = 'resources-parser.json'
        GSUIT_DOMAIN_ACCOUNT = 'resources@miem.hse.ru'

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
             SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        delegated_credentials = credentials.create_delegated(GSUIT_DOMAIN_ACCOUNT)
        self.service = build('admin', 'directory_v1', credentials=delegated_credentials)

    def get_cameras(self):
        results = self.service.resources().calendars().list(customer='C03s7v7u4').execute()
        return list(filter(self.__is_camera , results['items']))

    def set_resource(self, body):
        results = self.service.resources().calendars().insert(customer='C03s7v7u4', body=body).execute()
        return results

    def __is_camera(self, i):
        if 'resourceType' not in i:
            return False
        else:
            return i['resourceType'] == 'ONVIF-camera'


if __name__ == '__main__':
    googleAdminService = GoogleAdminService()
    cameras = googleAdminService.get_cameras()
    for cam in cameras:
        print(cam['resourceName'])
    auditories = get_auditoriumoid()
    for room in auditories:

        body = {"resourceId": str(time_ns()), "resourceName": str(room), "resourceDescription" : str(auditories[room])}
        resource = googleAdminService.set_resource(body)
    print(resource)
