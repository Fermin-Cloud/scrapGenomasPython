import asyncio
from typing import Set, List
from config.env import get_settings
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from services.scrap import GoogleSheetsClient, Scraper

def get_google_sheets_service() -> object:
    """Authenticates and returns a Google Sheets service."""
    creds: Credentials = Credentials.from_service_account_file("credentials.json", scopes=settings.SCOPES)
    return build("sheets", "v4", credentials=creds)

def obtener_principios_guardados() -> Set[str]:
    """Reads data from Google Sheets and returns a set of already recorded active ingredients."""
    service = get_google_sheets_service()
    sheet = service.spreadsheets()
    result: dict = sheet.values().get(spreadsheetId=settings.SPREADSHEET_ID, range=settings.RANGE_NAME).execute()
    values: List[List[str]] = result.get("values", [])

    if not values:
        print("No data found in Google Sheets.")
        return set()

    # Extract the column of active ingredients (col 5)
    return {row[4].strip().lower() for row in values if len(row) > 4}

async def main() -> None:
    """Run the scraping process if there are new active ingredients."""
    principios_activos: List[str] = [
        "Alpelisib",
        "Fulvestrant",
        "Inavolisib",
        "Palbociclib",
    ]

    # Obtener principios activos ya en la base de datos
    principios_guardados: Set[str] = obtener_principios_guardados()

    # Filtrar solo los principios activos que no están en la base de datos
    principios_a_buscar: List[str] = [p for p in principios_activos if p.lower() not in principios_guardados]

    if not principios_a_buscar:
        print("Todos los principios activos ya están en la base de datos. No es necesario hacer scraping.")
        return

    print(f"Principios activos a scrapear: {principios_a_buscar}")

    google_sheets_client = GoogleSheetsClient(settings.SPREADSHEET_ID, "A1:F100")
    scraper = Scraper("https://registrosanitario.ispch.gob.cl/", principios_a_buscar)

    await scraper.ejecutar()
    scraper.enviar_a_google_sheets(google_sheets_client)

if __name__ == "__main__":
    settings = get_settings()

    print("Environment variables:")
    print(f"Document URL: {settings.DOCUMENT_URL_GOOGLE}")
    print(f"API URL: {settings.API_GOOGLE_URL}")
    print(f"Secret Key: {settings.SECRET_KEY}")
    print("########################")

    asyncio.run(main())
