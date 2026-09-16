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

    for elemento in raiz.iter():
        nombre = elemento.find("title")
        descripcion = elemento.find("description")

        if nombre is not None and nombre.text:
            titulo = nombre.text.strip()

            if descripcion is not None and descripcion.text:
                descripcion_texto = descripcion.text.strip()
                texto.append(f"{titulo}")
                texto.append(descripcion_texto)
                texto.append("")

    Path("salida").mkdir(exist_ok=True)

    Path("salida/mensaje.txt").write_text(
        "\n".join(texto),
        encoding="utf-8"
    )

    print("\n".join(texto))

if __name__ == "__main__":
    main()