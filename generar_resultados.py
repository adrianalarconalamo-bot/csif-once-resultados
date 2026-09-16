import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

RSS_URL = "https://www.juegosonce.es/rss/sorteos2.xml"
OUTPUT_FILE = "resultados.json"


def clean_html(text):
    if not text:
        return ""

    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean)

    return clean.strip()


def obtener_resultados_rss():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "es-ES,es;q=0.9",
    }

    print(f"Descargando RSS desde: {RSS_URL}")

    request = urllib.request.Request(
        RSS_URL,
        headers=headers
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()

        print(f"Respuesta recibida: {len(content)} bytes")

        root = ET.fromstring(content)

    except Exception as error:
        print(f"ERROR descargando/procesando RSS: {error}")
        return []

    nodes = root.findall(".//item")

    if not nodes:
        nodes = [
            element
            for element in root.iter()
            if element.tag.split("}")[-1].lower() == "item"
        ]

    print(f"Elementos <item> encontrados: {len(nodes)}")

    # Obtenemos la fecha del día actual en formato DD/MM/YYYY
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")

    resultados = []

    for item in nodes:
        resultado = {}

        for child in item:
            tag = child.tag.split("}")[-1].lower()

            text = child.text or ""
            text = clean_html(text)

            if not text:
                continue

            if tag == "title":
                resultado["tipo"] = text

            elif tag in ("pubdate", "date"):
                resultado["fecha"] = text

            elif tag == "description":
                resultado["descripcion"] = text

            elif tag == "link":
                resultado["enlace"] = text

            else:
                resultado[tag] = text

        # Filtrado: solo añadimos el resultado si incluye la fecha de hoy
        if resultado and "fecha" in resultado:
            if fecha_hoy in resultado["fecha"]:
                resultados.append(resultado)

    print(f"Resultados del día ({fecha_hoy}) extraídos: {len(resultados)}")

    return resultados


def main():
    resultados = obtener_resultados_rss()

    data = {
        "actualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "resultados": resultados
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as archivo:
        json.dump(
            data,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    print(f"Archivo {OUTPUT_FILE} creado correctamente.")


if __name__ == "__main__":
    main()
