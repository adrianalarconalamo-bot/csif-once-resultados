import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from pathlib import Path
import re

URL = "https://www.juegosonce.es/rss/sorteos2.xml"


def descargar_xml():
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as respuesta:
        return respuesta.read()


def limpiar_html(texto):
    if not texto:
        return ""

    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = texto.replace("&nbsp;", " ")
    texto = texto.replace("&amp;", "&")
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def obtener_texto(elemento, nombres):
    for nombre in nombres:
        hijo = elemento.find(nombre)

        if hijo is not None and hijo.text:
            texto = limpiar_html(hijo.text)

            if texto:
                return texto

    return ""


def main():

    datos = descargar_xml()

    raiz = ET.fromstring(datos)

    resultados = []

    for elemento in raiz.iter():

        titulo = obtener_texto(
            elemento,
            ["title", "titulo", "name", "nombre"]
        )

        fecha = obtener_texto(
            elemento,
            ["pubDate", "date", "fecha", "dc:date"]
        )

        descripcion = obtener_texto(
            elemento,
            ["description", "descripcion", "content"]
        )

        if titulo or fecha or descripcion:

            resultados.append({
                "titulo": titulo,
                "fecha": fecha,
                "descripcion": descripcion
            })

    # Eliminar duplicados
    resultados_limpios = []

    vistos = set()

    for resultado in resultados:

        clave = (
            resultado["titulo"],
            resultado["fecha"],
            resultado["descripcion"]
        )

        if clave not in vistos:

            vistos.add(clave)
            resultados_limpios.append(resultado)

    # Nos quedamos con los últimos resultados
    resultados_limpios = resultados_limpios[:30]

    salida = {
        "actualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "resultados": resultados_limpios
    }

    Path("resultados.json").write_text(
        json.dumps(
            salida,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    # También generamos el mensaje de texto
    Path("salida").mkdir(exist_ok=True)

    texto = []

    texto.append("🍀 RESULTADOS ONCE")
    texto.append(datetime.now().strftime("%d/%m/%Y"))
    texto.append("")

    for resultado in resultados_limpios:

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

    print("Resultados encontrados:", len(resultados_limpios))
    print(json.dumps(salida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()