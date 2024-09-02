from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

load_dotenv()

service_account_file = os.getenv("SERVICE_ACCOUNT_FILE")
scopes_from_local = [os.getenv("SCOPES")]

creds = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=scopes_from_local)

drive_service = build('drive', 'v3', credentials=creds)

def upload_to_google(csv_filename):
    if not os.path.exists(csv_filename):
        print(f"File not found: {csv_filename}")
        return
    
    file_metadata = {
        'name': 'Bar Data',
        'mimeType': 'text/csv'
    }
    media = MediaFileUpload(csv_filename, mimetype='text/csv', resumable=True)
    
    try:
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        print(f'File ID: {file_id}')
        
        set_file_permissions(file_id)
    
    except HttpError as error:
        print(f"An error occurred during upload: {error}")

def set_file_permissions(file_id):
    try:
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }
        drive_service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id'
        ).execute()
        print(f"Permission set for file ID: {file_id}")
    except HttpError as error:
        print(f"An error occurred while setting permissions: {error}")

if __name__ == "__main__":
    csv_filename = 'bars_and_pubs_singapore.csv'
    upload_to_google(csv_filename)