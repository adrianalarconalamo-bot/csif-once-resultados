import urllib.request
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime
from pathlib import Path
from html import unescape

URL = "https://www.juegosonce.es/rss/sorteos2.xml"


def descargar_xml():
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as respuesta:
        return respuesta.read()


def limpiar_html(texto):
    if not texto:
        return ""

    texto = unescape(texto)

    texto = re.sub(r"<br\s*/?>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"</p\s*>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<[^>]+>", "", texto)

    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n", texto)

    return texto.strip()


def obtener_texto(elemento, nombre):
    hijo = elemento.find(nombre)

    if hijo is not None and hijo.text:
        return hijo.text.strip()

    for subelemento in elemento.iter():
        etiqueta = subelemento.tag.split("}")[-1]

        if etiqueta == nombre and subelemento.text:
            return subelemento.text.strip()

    return ""


def main():

    print("Descargando RSS de ONCE...")

    datos = descargar_xml()

    print(f"XML descargado: {len(datos)} bytes")

    raiz = ET.fromstring(datos)

    resultados = []

    for elemento in raiz.iter():

        etiqueta = elemento.tag.split("}")[-1]

        if etiqueta not in ("item", "entry"):
            continue

        titulo = obtener_texto(elemento, "title")
        descripcion = obtener_texto(elemento, "description")

        if not descripcion:
            descripcion = obtener_texto(elemento, "summary")

        fecha = obtener_texto(elemento, "pubDate")

        if not fecha:
            fecha = obtener_texto(elemento, "date")

        titulo = limpiar_html(titulo)
        descripcion = limpiar_html(descripcion)
        fecha = limpiar_html(fecha)

        if titulo or descripcion:

            resultados.append({
                "titulo": titulo,
                "fecha": fecha,
                "descripcion": descripcion
            })

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    datos_salida = {
        "actualizado": ahora,
        "resultados": resultados
    }

    Path("resultados.json").write_text(
        json.dumps(
            datos_salida,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    Path("salida").mkdir(exist_ok=True)

    texto = []

    texto.append("🍀 RESULTADOS ONCE")
    texto.append(datetime.now().strftime("%d/%m/%Y"))
    texto.append("")

    for resultado in resultados:

        if resultado["titulo"]:
            texto.append(resultado["titulo"])

        if resultado["fecha"]:
            texto.append(resultado["fecha"])

        if resultado["descripcion"]:
            texto.append(resultado["descripcion"])

        texto.append("")

    Path("salida/mensaje.txt").write_text(
        "\n".join(texto),
        encoding="utf-8"
    )

    print("")
    print("================================")
    print("RESULTADOS OBTENIDOS:", len(resultados))
    print("================================")
    print("")

    for resultado in resultados:
        print("TÍTULO:", resultado["titulo"])
        print("FECHA:", resultado["fecha"])
        print("DESCRIPCIÓN:", resultado["descripcion"])
        print("--------------------------------")


if __name__ == "__main__":
    main()