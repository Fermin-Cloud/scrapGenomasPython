"""Ejecuta la búsqueda de principios activos en la base de datos local y en la nube."""
import sys
import asyncio

from config.env import get_settings
from services.file_manager import FileManager
from services.scrap import Scraper
from services.vinculate_google import GoogleSheetsClient

settings = get_settings()
file_manager = FileManager()
google_manager = GoogleSheetsClient(settings.SPREADSHEET_ID, settings.RANGE_NAME)

async def main(principios_activos: list[str]) -> None:
    """Ejecuta la búsqueda en local, en la nube y scraping si es necesario."""
    if file_manager.archivo_existe():
        lineas_locales = file_manager.leer_archivo_local()
        principios_guardados = {line[4].strip().lower() for line in lineas_locales if len(line) > 4}
    else:
        # Si no existe, obtener datos de Google Sheets y guardarlos
        datos_sheets = google_manager.obtener_principios_guardados()
        file_manager.actualizar_documento_local(datos_sheets)
        principios_guardados = {row[4].strip().lower() for row in datos_sheets if len(row) > 4}

    # Determinar cuáles principios activos no están guardados
    principios_a_buscar = [p for p in principios_activos if p.lower() not in principios_guardados]

    if not principios_a_buscar:
        print("Todos los principios activos ya están en la base de datos.")
        return

    print(f"Principios activos a scrapear: {principios_a_buscar}")

    # Filtrar líneas del archivo local que contengan los principios activos buscados
    registros_a_guardar = [line for line in file_manager.leer_archivo_local() if any(p.lower() in line[4].lower() for p in principios_activos if len(line) > 4)]

    if registros_a_guardar:
        print(f"Líneas encontradas en el archivo local:\n{registros_a_guardar}")

    # Hacer scraping si es necesario
    if principios_a_buscar:
        google_sheets_client = GoogleSheetsClient(settings.SPREADSHEET_ID, "A1:F100")
        scraper = Scraper("https://registrosanitario.ispch.gob.cl/", principios_a_buscar)

        await scraper.ejecutar()
        scraper.enviar_a_google_sheets(google_sheets_client)

        # **Actualizar el archivo local con los datos obtenidos del scraping**
        nuevos_datos = google_manager.obtener_principios_guardados()
        file_manager.actualizar_documento_local(nuevos_datos)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Debes proporcionar al menos un principio activo.")
        sys.exit(1)

    asyncio.run(main(sys.argv[1:]))
