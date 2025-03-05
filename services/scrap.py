import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from typing import List, Dict

class Scraper:
    def __init__(self, url: str):
        self.url = url
        self.resultados: List[Dict[str, str]] = []
        self.principios_activos = [
            "Alpelisib",
            "Fulvestrant",
            "Inavolisib",
            "Palbociclib",
        ]

    async def iniciar_navegador(self):
        """Inicia el navegador en modo headless."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(60000)  

    async def buscar_principio_activo(self, principio: str):
        """Realiza la búsqueda y extrae los datos de la tabla."""
        print(f"Buscando principio activo: {principio}")

        await self.page.goto(self.url)

        # Seleccionar el checkbox de "Principio Activo"
        await self.page.wait_for_selector("#ctl00_ContentPlaceHolder1_chkTipoBusqueda_1")
        await self.page.check("#ctl00_ContentPlaceHolder1_chkTipoBusqueda_1")

        # Esperar y llenar el campo de texto
        await self.page.wait_for_selector("#ctl00_ContentPlaceHolder1_txtPrincipio")
        await self.page.fill("#ctl00_ContentPlaceHolder1_txtPrincipio", principio)

        # Clic en el botón de búsqueda
        await self.page.click("#ctl00_ContentPlaceHolder1_btnBuscar")
        await self.page.wait_for_load_state("networkidle")  # Esperar a que cargue la página

        # Verificar si hay resultados
        tabla_visible = await self.page.is_visible("#ctl00_ContentPlaceHolder1_gvDatosBusqueda")

        if not tabla_visible:
            print(f"No se encontraron resultados para: {principio}")
            return

        # Extraer datos de la tabla
        datos = await self.page.evaluate('''
            () => {
                const rows = document.querySelectorAll("#ctl00_ContentPlaceHolder1_gvDatosBusqueda tbody tr");
                return Array.from(rows).map(row => {
                    const cells = row.querySelectorAll("td");
                    return {
                        registro: cells[1]?.innerText.trim() || "",
                        nombre: cells[2]?.innerText.trim() || "",
                        fechaRegistro: cells[3]?.innerText.trim() || "",
                        empresa: cells[4]?.innerText.trim() || "",
                        principioActivo: cells[5]?.innerText.trim() || "",
                        controlLegal: cells[6]?.innerText.trim() || "",
                    };
                });
            }
        ''')

        self.resultados.extend(datos)
        print(f"Resultados obtenidos para: {principio}")

    async def ejecutar(self):
        """Ejecuta el scraping para todos los principios activos."""
        await self.iniciar_navegador()

        for principio in self.principios_activos:
            await self.buscar_principio_activo(principio)

        await self.browser.close()
        await self.playwright.stop()

        # Guardar los resultados en un CSV
        self.generar_csv()

    def generar_csv(self, archivo: str = "resultados.csv"):
        """Genera un archivo CSV con los resultados obtenidos."""
        if not self.resultados:
            print("No hay resultados para guardar.")
            return
        
        df = pd.DataFrame(self.resultados)
        df.to_csv(archivo, index=False, encoding="utf-8")
        print(f"Archivo CSV generado: {archivo}")

# Ejecutar el scraper
async def main():
    scraper = Scraper("https://registrosanitario.ispch.gob.cl/")
    await scraper.ejecutar()

asyncio.run(main())