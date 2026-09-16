import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

# URL del RSS de Juegos ONCE

RSS_URL = "https://www.juegosonce.es/rss/sorteos2.xml"
OUTPUT_FILE = "resultados.json"

Zona horaria de España

TIMEZONE = ZoneInfo("Europe/Madrid")

def clean_html(text: str) -> str:
"""Limpia etiquetas HTML y espacios sobrantes del texto."""
if not text:
return ""

clean = re.sub(r"<[^>]+>", " ", text)
return re.sub(r"\s+", " ", clean).strip()

def obtener_resultados_rss():
headers = {
"User-Agent": (
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
"AppleWebKit/537.36 (KHTML, like Gecko) "
"Chrome/120.0.0.0 Safari/537.36"
),
"Accept": (
"text/html,application/xhtml+xml,application/xml;"
"q=0.9,/;q=0.8"
),
"Accept-Language": "es-ES,es;q=0.9",
}

print(f"Descargando RSS desde: {RSS_URL}")

req = urllib.request.Request(RSS_URL, headers=headers)

try:
    with urllib.request.urlopen(req, timeout=15) as response:
        content = response.read()

        print(f"Respuesta recibida ({len(content)} bytes).")

        # Muestra de los primeros 600 caracteres en los logs
        sample = content[:600].decode("utf-8", errors="ignore")

        print("--- MUESTRA DEL CONTENIDO RECIBIDO ---")
        print(sample)
        print("--- FIN DE MUESTRA ---")

        root = ET.fromstring(content)

except Exception as e:
    print(f"ERROR al descargar o procesar el XML: {e}")
    return []

items = []

# Buscar todos los elementos <item>
nodes = root.findall(".//item")

if not nodes:
    # Reserva para XML con namespace
    nodes = [
        elem
        for elem in root.iter()
        if elem.tag.split("}")[-1].lower() == "item"
    ]

print(f"Elementos <item> encontrados: {len(nodes)}")

for item in nodes:
    resultado_item = {}

    for child in item:
        tag_name = child.tag.split("}")[-1].lower()
        text_val = child.text.strip() if child.text else ""

        if tag_name == "title":
            resultado_item["titulo"] = text_val

        elif tag_name in ("pubdate", "date"):
            resultado_item["fecha"] = text_val

        elif tag_name == "description":
            resultado_item["descripcion"] = clean_html(text_val)

        elif tag_name == "link":
            resultado_item["enlace"] = text_val

        elif text_val:
            resultado_item[tag_name] = text_val

    if resultado_item:
        items.append(resultado_item)

print(f"Se han extraído {len(items)} resultados válidos.")

return items

def contiene_fecha_hoy(resultado, fecha_hoy):
"""
Comprueba si el resultado corresponde al día actual.

Se busca la fecha en todos los campos de texto del resultado,
porque el RSS puede colocar la fecha en distintos campos.
"""

# Unir todos los valores de texto del resultado
texto = " ".join(
    str(valor)
    for valor in resultado.values()
    if isinstance(valor, str)
)

# Normalizar espacios
texto = re.sub(r"\s+", " ", texto).strip()

# Fecha española: 16/09/2026
fecha_es = fecha_hoy.strftime("%d/%m/%Y")

# Fecha española sin ceros: 16/9/2026
fecha_es_sin_ceros = (
    f"{fecha_hoy.day}/{fecha_hoy.month}/{fecha_hoy.year}"
)

# Fecha ISO: 2026-09-16
fecha_iso = fecha_hoy.strftime("%Y-%m-%d")

# Fecha con guiones: 16-09-2026
fecha_guiones = fecha_hoy.strftime("%d-%m-%Y")

# Fecha escrita: 16/09/2026 o 16-09-2026
if (
    fecha_es in texto
    or fecha_es_sin_ceros in texto
    or fecha_iso in texto
    or fecha_guiones in texto
):
    return True

# Comprobar también formatos escritos en español.
meses = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]

fecha_escrita = (
    f"{fecha_hoy.day} de "
    f"{meses[fecha_hoy.month - 1]} de "
    f"{fecha_hoy.year}"
)

if fecha_escrita.lower() in texto.lower():
    return True

# Formato habitual del RSS:
# "Miércoles, 16/09/2026"
# "Miércoles, 16/09/2026, Sorteo 1"
patron = re.compile(
    rf"\b{fecha_hoy.day:02d}[/-]"
    rf"{fecha_hoy.month:02d}[/-]"
    rf"{fecha_hoy.year}\b"
)

if patron.search(texto):
    return True

return False

def filtrar_resultados_de_hoy(resultados):
"""
Deja exclusivamente los resultados correspondientes
al día actual en España.
"""

ahora = datetime.now(TIMEZONE)
fecha_hoy = ahora.date()

print(
    "Fecha actual en España: "
    f"{fecha_hoy.strftime('%d/%m/%Y')}"
)

resultados_hoy = []

for resultado in resultados:
    if contiene_fecha_hoy(resultado, fecha_hoy):
        resultados_hoy.append(resultado)

print(
    f"Resultados correspondientes a hoy: "
    f"{len(resultados_hoy)}"
)

# Mostrar en los logs qué títulos han pasado el filtro
for resultado in resultados_hoy:
    titulo = resultado.get("titulo", "Sin título")
    print(f"  ✓ {titulo}")

return resultados_hoy

def main():
# Descargar todos los resultados disponibles en el RSS
resultados = obtener_resultados_rss()

# Quedarnos SOLO con los resultados de hoy
resultados = filtrar_resultados_de_hoy(resultados)

# Hora actual de España
ahora = datetime.now(TIMEZONE)

data = {
    "actualizado": ahora.strftime("%d/%m/%Y %H:%M"),
    "resultados": resultados,
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
    )

print(
    f"Archivo '{OUTPUT_FILE}' guardado correctamente."
)

print(
    f"Total de resultados guardados: {len(resultados)}"
)

if name == "main":
main()