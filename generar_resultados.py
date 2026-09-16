 import urllib.request
import xml.etree.ElementTree as ET
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

    texto = []

    texto.append("🍀 RESULTADOS ONCE")
    texto.append(datetime.now().strftime("%d/%m/%Y"))
    texto.append("")

    # Buscar todos los elementos <item> del RSS
    items = raiz.findall(".//item")

    print(f"Items encontrados: {len(items)}")

    for item in items:
        titulo = item.findtext("title", default="").strip()
        descripcion = item.findtext("description", default="").strip()

        if not titulo:
            continue

        texto.append(titulo)

        if descripcion:
            texto.append(descripcion)

        texto.append("")

    Path("salida").mkdir(exist_ok=True)

    contenido = "\n".join(texto)

    Path("salida/mensaje.txt").write_text(
        contenido,
        encoding="utf-8"
    )

    print(contenido)


if __name__ == "__main__":
    main()