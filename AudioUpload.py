import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
import io
from googleapiclient.errors import HttpError

import sys
import os
from enum import Enum

class AudioType(Enum):
    wav = "audio/wav"
    mp3 = "audio/mpeg"

def init():
    global service
    scope = ['https://www.googleapis.com/auth/drive']
    service_account_json_key = './client_secrets.json'
    credentials = service_account.Credentials.from_service_account_file(
                                  filename=service_account_json_key, 
                                  scopes=scope)
    service = build('drive', 'v3', credentials=credentials)
    
def upload(file_path: str, audio_type: AudioType, drive_file_name: str = None):
    global service
    file_path = file_path.strip()
    
    if not file_path.endswith('.' + audio_type.name):
        file_path += '.' + audio_type.name
    
    last_sep_loc = file_path.rfind(os.sep)
    if drive_file_name is None:
        drive_file_name = file_path[last_sep_loc+1:]
    elif not drive_file_name.endswith('.' + audio_type.name):
        drive_file_name += '.' + audio_type.name

    file_metadata = {'name': drive_file_name, 'parents': ['1d483T74fYk_yVpLDLQX5SY9WEbRy-ypr']}
    media = MediaFileUpload(file_path,
                            mimetype=audio_type.value,
                            resumable=True)

    file = service.files().create(body=file_metadata, media_body=media,
                                  fields='id').execute()
# Works for .wav as a test
def main():
    init()
    
    sys.argv.pop(0)
    if len(sys.argv) == 0:
        file_name = input("Filename to upload (.wav): ")
    elif len(sys.argv) == 1:
        file_name = sys.argv[0]
    else:
        print(f"Invalid Number of Arguments ({len(sys.argv)})")
        return
    
    upload(file_name, AudioType.wav) 
    
    print("DONE")

if __name__ == "__main__":
    main()