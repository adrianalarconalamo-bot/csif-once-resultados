import json
from datetime import datetime

OUTPUT_FILE = "resultados.json"

def generar_resultados():
    # Estructura de datos que se guardará en resultados.json
    # Aquí puedes integrar tu lógica de scraping o conexión a la API para obtener los números reales.
    datos = {
        "actualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "resultados": [
            {
                "tipo": "Cupón Diario",
                "numero": "12345",
                "serie": "012"
            },
            {
                "tipo": "Triplex de la ONCE Sorteo 1",
                "numero": "123"
            },
            {
                "tipo": "Triplex de la ONCE Sorteo 2",
                "numero": "456"
            },
            {
                "tipo": "Mi Día",
                "numero": "12/10/1980 - 05"
            },
            {
                "tipo": "Dupla de la ONCE Sorteo 1",
                "numero": "12"
            },
            {
                "tipo": "Super 11 Sorteo 1",
                "numero": "01, 05, 12, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 81, 85, 90",
                "importebote": "0"
            }
        ]
    }

    # Guardar el archivo JSON que leerá el script de envío
    with open(OUTPUT_FILE, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=4)
    
    print(f"✅ Archivo {OUTPUT_FILE} creado con éxito.")

if __name__ == "__main__":
    generar_resultados()
