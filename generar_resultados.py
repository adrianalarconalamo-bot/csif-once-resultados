import urllib.request
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime
from pathlib import Path

URL = "https://www.juegosonce.es/rss/sorteos2.xml"

ARCHIVO_RESULTADOS = Path("resultados.json")
ARCHIVO_XML = Path("once_resultados.xml")


def descargar_xml():
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/xml,text/xml,*/*"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as respuesta:
        datos = respuesta.read()

    return datos


def limpiar_texto(texto):
    if texto is None:
        return ""

    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def extraer_elementos(raiz):
    resultados = []

    for elemento in raiz.iter():
        texto = limpiar_texto(elemento.text)

        if not texto:
            continue

        # Guardamos únicamente elementos que tengan información
        # relacionada con sorteos/resultados.
        padre = elemento.tag.lower()

        resultados.append({
            "elemento": padre,
            "texto": texto
        })

    return resultados


def procesar_xml(datos):
    try:
        raiz = ET.fromstring(datos)
    except ET.ParseError as error:
        print("ERROR AL INTERPRETAR EL XML:")
        print(error)
        return []

    resultados = extraer_elementos(raiz)

    print("Elementos encontrados:", len(resultados))

    for resultado in resultados[:30]:
        print(
            resultado["elemento"],
            "=>",
            resultado["texto"]
        )

    return resultados


def guardar_resultados(resultados):
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    datos = {
        "actualizado": ahora,
        "resultados": resultados
    }

    with open(
        ARCHIVO_RESULTADOS,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=2
        )


def main():
    print("======================================")
    print(" GENERADOR DE RESULTADOS ONCE")
    print("======================================")

    print("Descargando XML:")
    print(URL)

    try:
        datos_xml = descargar_xml()

        print("XML descargado correctamente.")
        print("Tamaño:", len(datos_xml), "bytes")

        # Guardamos una copia para poder comprobar
        # exactamente qué está devolviendo ONCE.
        with open(ARCHIVO_XML, "wb") as archivo:
            archivo.write(datos_xml)

        print("XML guardado en:", ARCHIVO_XML)

    except Exception as error:
        print("ERROR DESCARGANDO EL XML:")
        print(error)

        guardar_resultados([])

        raise

    resultados = procesar_xml(datos_xml)

    guardar_resultados(resultados)

    print("--------------------------------------")
    print("RESULTADOS EXTRAÍDOS:", len(resultados))
    print("Archivo generado:", ARCHIVO_RESULTADOS)
    print("======================================")


if __name__ == "__main__":
    main()