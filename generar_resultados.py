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
        titulo = item.find("title")
        descripcion = item.find("description")

        if titulo is not None and titulo.text:
            resultados.append({
                "titulo": titulo.text.strip(),
                "fecha": datetime.now().strftime("%d/%m/%Y"),
                "descripcion": (
                    descripcion.text.strip()
                    if descripcion is not None and descripcion.text
                    else ""
                )
            })

    salida = {
        "actualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "resultados": resultados
    }

    Path("resultados.json").write_text(
        json.dumps(salida, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(json.dumps(salida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()