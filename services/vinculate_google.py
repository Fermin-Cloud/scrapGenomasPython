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
        """Añade datos a Google Sheets."""

        body = {"values": values}
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=self.range_name,
            valueInputOption="RAW",
            body=body
        ).execute()

    def obtener_principios_guardados(self) -> List[List[str]]:
        """Lee los datos desde Google Sheets y retorna las líneas completas de los principios activos almacenados."""
        
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.spreadsheet_id, range=self.range_name).execute()
        values = result.get("values", [])

        if not values:
            print("No se encontraron datos en Google Sheets.")
            return []

        # Filtrar filas con datos en la columna de principios activos (columna 5)
        valid_rows = [row for row in values if len(row) > 4 and row[4].strip()]
        
        return valid_rows
