import os
import csv
from typing import List

class FileManager:
    """Clase para manejar archivos locales en formato CSV."""
    
    def __init__(self, archivo: str = "principios_activos_local.csv"):
        self.archivo = archivo

    def archivo_existe(self) -> bool:
        """Verifica si el archivo local existe."""
        return os.path.exists(self.archivo)

    def actualizar_documento_local(self, principios_activos: List[List[str]]) -> None:
        """Actualiza o crea un archivo CSV con los principios activos."""
        existentes = set()

        if self.archivo_existe():
            with open(self.archivo, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                existentes = {tuple(row) for row in reader}  

        nuevos = [row for row in principios_activos if tuple(row) not in existentes]

        if nuevos:
            with open(self.archivo, "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(nuevos)
            print(f"Se actualizaron {len(nuevos)} registros en el archivo CSV local.")
        else:
            print("No hay nuevos principios activos para agregar.")

    def leer_archivo_local(self) -> List[List[str]]:
        """Lee el archivo CSV local y devuelve las filas completas."""
        try:
            with open(self.archivo, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                return [row for row in reader]
        except FileNotFoundError:
            return []
