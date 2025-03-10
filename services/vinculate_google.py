from typing import List
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

class GoogleSheetsClient:
    def __init__(self, spreadsheet_id: str, range_name: str) -> None:
        self.spreadsheet_id: str = spreadsheet_id
        self.range_name: str = range_name
        self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        self.creds = Credentials.from_service_account_file("credentials.json", scopes=self.scopes)
        self.service = build("sheets", "v4", credentials=self.creds)

    def append_data(self, values: List[List[str]]) -> None:
        body = {"values": values}
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=self.range_name,
            valueInputOption="RAW",
            body=body
        ).execute()