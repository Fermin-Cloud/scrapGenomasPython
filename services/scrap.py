from playwright.async_api import async_playwright
from typing import List, Dict

from services.vinculate_google import GoogleSheetsClient

# active substance

class Scraper:
    def __init__(self, url: str, principios_activos: List[str]) -> None:
        self.url = url
        self.resultados: List[Dict[str, str]] = []
        self.principios_activos = principios_activos

    async def iniciar_navegador(self) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(60000)

    async def buscar_principio_activo(self, principio: str) -> None:
        print(f"Buscando principio activo: {principio}")
        await self.page.goto(self.url)
        await self.page.wait_for_selector("#ctl00_ContentPlaceHolder1_chkTipoBusqueda_1")
        await self.page.check("#ctl00_ContentPlaceHolder1_chkTipoBusqueda_1")
        await self.page.wait_for_selector("#ctl00_ContentPlaceHolder1_txtPrincipio")
        await self.page.fill("#ctl00_ContentPlaceHolder1_txtPrincipio", principio)
        await self.page.click("#ctl00_ContentPlaceHolder1_btnBuscar")
        await self.page.wait_for_load_state("networkidle")
        
        tabla_visible = await self.page.is_visible("#ctl00_ContentPlaceHolder1_gvDatosBusqueda")
        if not tabla_visible:
            print(f"No se encontraron resultados para: {principio}")
            return
        
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
        await self.iniciar_navegador()
        for principio in self.principios_activos:
            await self.buscar_principio_activo(principio)
        await self.browser.close()
        await self.playwright.stop()

    def enviar_a_google_sheets(self, google_sheets_client: GoogleSheetsClient):
        if not self.resultados:
            print("No hay resultados para enviar.")
            return
        
        valores = [[d["registro"], d["nombre"], d["fechaRegistro"], d["empresa"], d["principioActivo"], d["controlLegal"]] for d in self.resultados]
        google_sheets_client.append_data(valores)
        print("Datos enviados a Google Sheets")

    def get_result(self) -> List[Dict[str, str]]:
        if self.resultados:
            return self.resultados
