import asyncio
from config.env import get_settings
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from services.scrap import GoogleSheetsClient, Scraper

# Definir el alcance de los permisos
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# ID de la hoja de cálculo
SPREADSHEET_ID = "1VNzEOTnam34cY1rB7qVrlH7W3fj9InD2MG_HpIfWHWo"
RANGE_NAME = "A1:Z100"

def get_google_sheets_service():
    """Autentica y retorna un servicio de Google Sheets."""
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service

def obtener_principios_guardados():
    """Lee los datos de Google Sheets y devuelve un conjunto de principios activos ya registrados."""
    service = get_google_sheets_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    if not values:
        print("No se encontraron datos en Google Sheets.")
        return set()

    # Extraer la columna de principios activos (asumiendo que está en la columna 5)
    principios_guardados = {row[4].strip().lower() for row in values if len(row) > 4}
    return principios_guardados

async def main():
    principios_activos = [
        "Alpelisib",
        "Fulvestrant",
        "Inavolisib",
        "Palbociclib",
    ]

    # Obtener principios activos ya en la base de datos
    principios_guardados = obtener_principios_guardados()

    # Filtrar solo los principios activos que no están en la base de datos
    principios_a_buscar = [p for p in principios_activos if p.lower() not in principios_guardados]

    if not principios_a_buscar:
        print("Todos los principios activos ya están en la base de datos. No es necesario hacer scraping.")
        return

    print(f"Principios activos a scrapear: {principios_a_buscar}")

    google_sheets_client = GoogleSheetsClient("1VNzEOTnam34cY1rB7qVrlH7W3fj9InD2MG_HpIfWHWo", "A1:F100")
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
