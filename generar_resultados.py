import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo  # Incluido en la librería estándar de Python 3.9+

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
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
    }

    print(f"Descargando RSS desde: {RSS_URL}")
    request = urllib.request.Request(RSS_URL, headers=headers)

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

    # Obtenemos la fecha actual referenciada SIEMPRE al horario de España
    ahora_espana = datetime.now(ZoneInfo("Europe/Madrid"))
    fecha_hoy = ahora_espana.strftime("%d/%m/%Y")
    
    # Formato alternativo sin ceros iniciales (por si el RSS pone 5/9/2026 en lugar de 05/09/2026)
    dia_sin_cero = str(ahora_espana.day)
    mes_sin_cero = str(ahora_espana.month)
    fecha_hoy_corta = f"{dia_sin_cero}/{mes_sin_cero}/{ahora_espana.year}"

    resultados = []
    todos_los_resultados = []

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

        if resultado:
            todos_los_resultados.append(resultado)
            
            # Comprobación de fecha flexible en cualquiera de los campos de texto
            texto_completo = f"{resultado.get('fecha', '')} {resultado.get('tipo', '')} {resultado.get('descripcion', '')}"
            if fecha_hoy in texto_completo or fecha_hoy_corta in texto_completo:
                resultados.append(resultado)

    # Si no hay resultados estrictos de hoy (por retraso en la publicación del RSS),
    # tomamos los primeros 5 elementos del RSS para evitar dejar el JSON vacío
    if not resultados and todos_los_resultados:
        print("⚠️ No se encontraron elementos coincidentes con la fecha exacta de hoy. Guardando últimos disponibles.")
        resultados = todos_los_resultados[:5]

    print(f"Resultados procesados: {len(resultados)}")
    return resultados


def main():
    ahora_espana = datetime.now(ZoneInfo("Europe/Madrid"))
    resultados = obtener_resultados_rss()

    data = {
        "actualizado": ahora_espana.strftime("%d/%m/%Y %H:%M"),
        "resultados": resultados
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as archivo:
        json.dump(data, archivo, ensure_ascii=False, indent=2)

    print(f"Archivo {OUTPUT_FILE} creado correctamente.")


if __name__ == "__main__":
    main()
