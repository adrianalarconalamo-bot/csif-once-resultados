import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from pathlib import Path

URL = "https://www.juegosonce.es/rss/sorteos2.xml"


def descargar_xml():
    req = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=30) as respuesta:
        return respuesta.read()


def main():
    datos = descargar_xml()
    raiz = ET.fromstring(datos)

    resultados = []

    for item in raiz.iter():
        if item.tag.lower().endswith("item"):
            titulo = ""
            fecha = ""
            descripcion = ""

            for elemento in item:
                nombre = elemento.tag.lower()

                if nombre.endswith("title"):
                    titulo = elemento.text or ""

                elif nombre.endswith("pubdate"):
                    fecha = elemento.text or ""

                elif nombre.endswith("description"):
                    descripcion = elemento.text or ""

            resultados.append({
                "titulo": titulo.strip(),
                "fecha": fecha.strip(),
                "descripcion": descripcion.strip()
            })

    salida = {
        "actualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "resultados": resultados
    }

    archivo = Path("resultados.json")

    archivo.write_text(
        json.dumps(salida, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"OK: {len(resultados)} resultados guardados.")
    print(f"Archivo generado: {archivo}")


if __name__ == "__main__":
    main()