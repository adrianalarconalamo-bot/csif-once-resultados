import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# URL del RSS de Juegos ONCE
RSS_URL = "https://www.juegosonce.es/rss/sorteos2.xml"
OUTPUT_FILE = "resultados.json"


def clean_html(text: str) -> str:
  """Limpia etiquetas HTML y espacios sobrantes del texto."""
  if not text:
    return ""
  clean = re.sub(r"<[^>]+>", " ", text)
  return re.sub(r"\s+", " ", clean).strip()


def obtener_resultados_rss():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "es-ES,es;q=0.9",
  }

  print(f"Descargando RSS desde: {RSS_URL}")

  req = urllib.request.Request(RSS_URL, headers=headers)

  try:
    with urllib.request.urlopen(req, timeout=15) as response:
      content = response.read()
      print(f"Respuesta recibida ({len(content)} bytes).")

      # Muestra de los primeros 600 caracteres en los logs de GitHub Actions
      sample = content[:600].decode("utf-8", errors="ignore")
      print("--- MUESTRA DEL CONTENIDO RECIBIDO ---")
      print(sample)
      print("--- FIN DE MUESTRA ---")

      root = ET.fromstring(content)

  except Exception as e:
    print(f"ERROR al descargar o procesar el XML: {e}")
    return []

  items = []

  # Buscar todos los elementos 'item' independientemente de la estructura interna
  nodes = root.findall(".//item")
  if not nodes:
    # Intento de reserva por si usan nombres con namespace o estructura alternativa
    nodes = [
        elem for elem in root.iter() if elem.tag.split("}")[-1].lower() == "item"
    ]

  print(f"Elementos <item> encontrados: {len(nodes)}")

  for item in nodes:
    resultado_item = {}

    for child in item:
      tag_name = child.tag.split("}")[-1].lower()
      text_val = child.text.strip() if child.text else ""

      if tag_name == "title":
        resultado_item["titulo"] = text_val
      elif tag_name == "pubdate" or tag_name == "date":
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


def main():
  resultados = obtener_resultados_rss()

  data = {
      "actualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
      "resultados": resultados,
  }

  with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  print(f"Archivo '{OUTPUT_FILE}' guardado correctamente.")


if __name__ == "__main__":
  main()
