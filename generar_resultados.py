import json
from datetime import datetime

OUTPUT_FILE = "resultados.json"

def generar_resultados():
    """
    Crea el archivo resultados.json con la estructura que espera el script de envío.
    """
    datos = {
        "actualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "resultados": [
            {
                "tipo": "Cupón Diario",
                "numero": "14062",
                "serie": "021"
            },
            {
                "tipo": "Triplex de la ONCE",
                "numero": "123"
            },
            {
                "tipo": "Triplex de la ONCE",
                "numero": "456"
            },
            {
                "tipo": "Mi Día",
                "numero": "12/10/1980 - 05"
            },
            {
                "tipo": "Dupla de la ONCE",
                "numero": "12"
            },
            {
                "tipo": "Super 11",
                "numero": "01, 05, 12, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 81, 85, 90",
                "importebote": "0"
            }
        ]
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=4)
    
    print(f"✅ Archivo {OUTPUT_FILE} generado correctamente.")

if __name__ == "__main__":
    generar_resultados()
