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
        """Appends data to Google Sheets."""

        body = {"values": values}
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=self.range_name,
            valueInputOption="RAW",
            body=body
        ).execute()

    def get_all_data(self) -> List[List[str]]:
        """Gets all data from the spreadsheet within the specified range."""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=self.range_name
        ).execute()
        
        # If no data exists, return an empty list
        return result.get('values', [])

    def obtener_principios_guardados(self) -> List[List[str]]:
        """Reads the data from Google Sheets and returns the complete rows of stored active ingredients."""
        
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.spreadsheet_id, range=self.range_name).execute()
        values = result.get("values", [])

        if not values:
            print("No data found in Google Sheets.")
            return []

        # Filter rows with data in the active ingredient column (column 5)
        valid_rows = [row for row in values if len(row) > 4 and row[4].strip()]
        
        return valid_rows

    def query(self) -> str:
        self.connect()
        return "API response"
