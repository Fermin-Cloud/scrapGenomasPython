import sys
import asyncio
from typing import Set, List
from config.env import get_settings
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os
from services.scrap import Scraper
from services.vinculate_google import GoogleSheetsClient

settings = get_settings()

def get_google_sheets_service() -> object:
    """Authenticates and returns a Google Sheets service."""
    creds: Credentials = Credentials.from_service_account_file("credentials.json", scopes=settings.SCOPES)
    return build("sheets", "v4", credentials=creds)

def obtener_principios_guardados() -> List[str]:
    """Lee los datos desde Google Sheets y retorna las líneas completas de los principios activos almacenados."""
    service = get_google_sheets_service()
    sheet = service.spreadsheets()
    result: dict = sheet.values().get(spreadsheetId=settings.SPREADSHEET_ID, range=settings.RANGE_NAME).execute()
    values: List[List[str]] = result.get("values", [])

    if not values:
        print("No se encontraron datos en Google Sheets.")
        return []

    # Filtra filas que no tengan datos en la columna relevante (por ejemplo, columna 5)
    valid_rows = [
        row for row in values
        if len(row) > 4 and row[4].strip() != ""  # Filtra filas vacías o que no tienen el principio activo
    ]

    # Filtra valores no relevantes como líneas con números sueltos o texto basura
    valid_rows = [
        row for row in valid_rows
        if any(cell.strip() for cell in row) and not all(cell.isdigit() for cell in row)  # Asegura que no sea una fila con solo números
    ]

    # Imprime las filas válidas para depuración
    print(f"Filas válidas encontradas: {valid_rows}")
    return valid_rows

def actualizar_documento_local(principios_activos: List[List[str]]) -> None:
    """Actualiza o crea un archivo local con los principios activos, incluyendo la fila completa."""
    local_file = 'principios_activos_local.txt'

    # Si el archivo existe, leemos las filas guardadas.
    if os.path.exists(local_file):
        with open(local_file, 'r') as file:
            existentes = set(file.read().splitlines())
    else:
        existentes = set()

    # Filtramos solo los nuevos principios activos (considerando toda la fila).
    nuevos = [
        row for row in principios_activos
        if row[4].strip() not in existentes  # Filtra basándose en el principio activo
    ]

    # Si hay nuevos principios activos, los agregamos al archivo local.
    if nuevos:
        with open(local_file, 'a') as file:
            for row in nuevos:
                file.write("\t".join(row) + "\n")  # Escribe la fila completa
        print(f"Document updated locally with: {', '.join([row[4] for row in nuevos])}")
    else:
        print("No new active ingredients to add to the local file.")

def leer_archivo_local() -> List[str]:
    """Lee el archivo .txt local y devuelve las líneas que contienen los principios activos especificados."""
    try:
        with open('principios_activos_local.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print("El archivo local no se encontró.")
        return []
    
    return lines  # Devuelve las líneas completas

async def main(principios_activos: List[str]) -> None:
    """Corre el proceso de scraping si hay principios activos nuevos y muestra las líneas relevantes."""
    
    # Leer archivo local si existe, si no se consulta Google Sheets
    if os.path.exists('principios_activos_local.txt'):
        with open('principios_activos_local.txt', 'r') as file:
            principios_guardados = [line.split("\t")[4].strip() for line in file.readlines()]  # Leer la columna de principios activos (columna 5)
    else:
        principios_guardados = [row[4].strip() for row in obtener_principios_guardados()]  # Ahora guardamos toda la fila

        # Actualizamos el archivo local con los principios activos obtenidos de Google Sheets
        actualizar_documento_local(obtener_principios_guardados())  # Pasa las filas completas

    # Filtrar solo los principios activos que no están en la base de datos
    principios_a_buscar = [p for p in principios_activos if p.lower() not in [pa.lower() for pa in principios_guardados]]

    if not principios_a_buscar:
        print("Todos los principios activos ya están en la base de datos. No es necesario hacer scraping.")
        return

    print(f"Principios activos a scrapear: {principios_a_buscar}")

    # Leer archivo local y buscar las líneas correspondientes a los principios activos
    lines_local = leer_archivo_local()
    
    # Filtrar las líneas completas que contienen los principios activos que estamos buscando
    registros_a_guardar = [
        line for line in lines_local
        if any(p.lower() in line.lower() for p in principios_a_buscar)
    ]
    
    if registros_a_guardar:
        print(f"Líneas completas encontradas en el archivo local: {registros_a_guardar}")

    # Procesar scraping solo si es necesario
    if principios_a_buscar:
        google_sheets_client = GoogleSheetsClient(settings.SPREADSHEET_ID, "A1:F100")
        scraper = Scraper("https://registrosanitario.ispch.gob.cl/", principios_a_buscar)

        await scraper.ejecutar()
        scraper.enviar_a_google_sheets(google_sheets_client)

        # Si hay resultados, los mostramos
        if scraper:
            print(f"Resultados de scraping: {scraper.get_result()}")

# python3 main.py Alpelisib Fulvestrant Inavolisib Palbociclib
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Error: Debes proporcionar al menos un principio activo como argumento.")
        sys.exit(1)

    principios_activos = sys.argv[1:] 

    asyncio.run(main(principios_activos))
