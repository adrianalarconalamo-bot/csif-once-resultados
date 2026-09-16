import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from pathlib import Path

URL = "https://www.juegosonce.es/rss/sorteos2.xml"


def descargar_xml():
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as respuesta:
        return respuesta.read()


def limpiar_texto(texto):
    if texto is None:
        return ""
    return " ".join(texto.split())


def main():
    print("Descargando RSS de ONCE...")

    datos = descargar_xml()

    print("RSS descargado correctamente.")

    raiz = ET.fromstring(datos)

    resultados = []

    for item in raiz.iter():
        tag = item.tag.split("}")[-1]

        if tag != "item":
            continue

        titulo = ""
        descripcion = ""
        fecha = ""

        for elemento in list(item):
            nombre = elemento.tag.split("}")[-1]

            if nombre == "title":
                titulo = limpiar_texto(elemento.text)

            elif nombre == "description":
                descripcion = limpiar_texto(elemento.text)

            elif nombre in ("pubDate", "date"):
                fecha = limpiar_texto(elemento.text)

        if titulo or descripcion or fecha:
            resultados.append({
                "titulo": titulo,
                "fecha": fecha,
                "descripcion": descripcion
            })

    print(f"Resultados encontrados: {len(resultados)}")

    archivo = Path("resultados.json")

    archivo.write_text(
        json.dumps(
            resultados,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("resultados.json creado correctamente.")


if __name__ == "__main__":
    main()