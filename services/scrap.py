import asyncio
from typing import List
from playwright.async_api import async_playwright
from pathlib import Path
from services.vinculate_google import GoogleSheetsClient
import pandas as pd

class Scraper:
    def __init__(self, url: str, principios_activos: List[str]) -> None:
        self.url = url
        self.principios_activos = principios_activos

    async def iniciar_navegador(self) -> None:
        self.playwright = await async_playwright().start()

        # Configure the custom downloads folder
        download_path = Path("downloads")
        if not download_path.exists():
            download_path.mkdir(parents=True, exist_ok=True)

        # Create the context with accept_downloads=True
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(accept_downloads=True)

        # Open a new page within this context
        self.page = await self.context.new_page()
        self.page.set_default_timeout(60000)

    async def buscar_principio_activo(self, principio: str) -> None:
        print(f"Searching for active ingredient: {principio}")
        await self.page.goto(self.url)
        await self.page.wait_for_selector("#ctl00_ContentPlaceHolder1_chkTipoBusqueda_1")
        await self.page.check("#ctl00_ContentPlaceHolder1_chkTipoBusqueda_1")
        await self.page.wait_for_selector("#ctl00_ContentPlaceHolder1_txtPrincipio")
        await self.page.fill("#ctl00_ContentPlaceHolder1_txtPrincipio", principio)
        await self.page.click("#ctl00_ContentPlaceHolder1_btnBuscar")
        await self.page.wait_for_load_state("networkidle")

        # Check if there are records available
        cantidad_elemento = await self.page.query_selector("#ctl00_ContentPlaceHolder1_lblCantidadEC")
        cantidad_registros = int(await cantidad_elemento.inner_text()) if cantidad_elemento else 0

        if cantidad_registros == 0:
            print(f"No records found for: {principio}")
            return

        # If there are records, try downloading the file
        await self.descargar_archivo()

    def acumular_en_base_local(self, nuevo_csv: Path, base_csv: Path = Path("downloads/local.csv")):
        nuevo_df = pd.read_csv(nuevo_csv)

        if not base_csv.exists() or base_csv.stat().st_size == 0:
            # If it doesn't exist or is empty, create it with headers
            nuevo_df.to_csv(base_csv, index=False)
            print(f"Created local base with: {nuevo_csv.name}")
        else:
            # If it already exists, append without headers
            nuevo_df.to_csv(base_csv, mode='a', header=False, index=False)
            print(f"Added content from {nuevo_csv.name} to the local base.")

    def convertir_html_a_csv(self, path_html: Path, path_csv: Path):
        # the fake .xls
        tablas = pd.read_html(path_html)

        if tablas:
            df = tablas[0]

            if 'Unnamed: 0' in df.columns and df['Unnamed: 0'].isna().all():
                df = df.drop(columns=['Unnamed: 0'])

            df.to_csv(path_csv, index=False)
            print(f"Converted to CSV: {path_csv}")
        else:
            print("No tables found in the HTML file.")

    async def descargar_archivo(self) -> None:
        for intento in range(2):  # Max 2 attempts
            try:
                print(f"Attempting download... (attempt {intento + 1})")
                await self.page.wait_for_selector("#ctl00_ContentPlaceHolder1_ImgBntExcel", state="visible")

                async with self.page.expect_download() as download_info:
                    await self.page.click("#ctl00_ContentPlaceHolder1_ImgBntExcel")

                download = await download_info.value

                if download.suggested_filename.endswith('.xls') or download.suggested_filename.endswith('.xlsx'):
                    archivo_html = Path(f"./downloads/{download.suggested_filename}")
                    await download.save_as(archivo_html)
                    print(f"File downloaded and saved at {archivo_html}")

                    archivo_csv = archivo_html.with_suffix('.csv')
                    self.convertir_html_a_csv(archivo_html, archivo_csv)

                    # Accumulate in local base
                    self.acumular_en_base_local(archivo_csv)

                    # Delete temporary files
                    archivo_html.unlink(missing_ok=True)  # Delete the .xls 
                    archivo_csv.unlink(missing_ok=True)   # Delete the .csv
                    print(f"Temporary files deleted: {archivo_html.name}, {archivo_csv.name}")

                    return  # Successful download, exit function!
                else:
                    raise Exception(f"Unexpected file extension: {download.suggested_filename}")

            except Exception as e:
                print(f"Error on attempt {intento + 1}: {e}")
                if intento == 0:
                    print("Retrying download...")
                    await asyncio.sleep(1)  
                else:
                    raise RuntimeError(f"Failed to download the file after 2 attempts.") from e

    async def enviar_a_google_sheets_desde_local(self, google_sheets_client: GoogleSheetsClient, base_csv: Path = Path("downloads/local.csv")):
        if not base_csv.exists():
            print("No local.csv file to send.")
            return

        # Read the local CSV
        df_local = pd.read_csv(base_csv)

        # Read existing data from Google Sheets
        valores_actuales = google_sheets_client.get_all_data() 
        
        # Check if the Google Sheets is empty
        hoja_vacia = not valores_actuales  
        registros_existentes = set(row[0] for row in valores_actuales if row) 

        # Filter only new records (that are not already in Google Sheets)
        nuevos_df = df_local[~df_local["Registro"].isin(registros_existentes)]

        if nuevos_df.empty:
            print("No new records to add to Google Sheets.")
            return

        # Clean the values before sending
        valores = nuevos_df.values.tolist()

        # Validate that there are no empty or unexpected values
        valores_limpios = []
        for fila in valores:
            # Replace NaN with "-"
            fila_limpia = [val if not pd.isna(val) else "-" for val in fila]

            # Remove rows with invalid data
            if any(val is None or str(val).strip() == "" for val in fila_limpia):
                print("A row with empty or invalid data was found, it will be skipped:", fila_limpia)
                continue  # Skip this row if it has empty values

            valores_limpios.append(fila_limpia)

        # If the sheet is empty, add the headers
        if hoja_vacia:
            cabeceras = df_local.columns.tolist()
            valores_limpios.insert(0, cabeceras)  # Insert headers at the beginning

        # Now valores_limpios is ready to be sent
        google_sheets_client.append_data(valores_limpios)
        print(f"{len(valores_limpios)} records were sent to Google Sheets.")

    async def ejecutar(self):
        await self.iniciar_navegador()
        for principio in self.principios_activos:
            await self.buscar_principio_activo(principio)
        await self.browser.close()
        await self.playwright.stop()
