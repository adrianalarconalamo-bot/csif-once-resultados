import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from pathlib import Path
import re
import html


URL = "https://www.juegosonce.es/rss/sorteos2.xml"
SALIDA = Path("resultados.json")


def descargar_xml():
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/xml,text/xml,*/*",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as respuesta:
        contenido = respuesta.read()

    return contenido


def limpiar_texto(texto):
    if not texto:
        return ""

    texto = html.unescape(texto)

    texto = re.sub(r"<br\s*/?>", " ", texto, flags=re.I)
    texto = re.sub(r"<[^>]+>", " ", texto)

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def quitar_namespace(tag):
    if "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def obtener_texto(elemento):
    if elemento is None:
        return ""

    texto = "".join(elemento.itertext())

    return limpiar_texto(texto)


def buscar_hijo(elemento, nombres):
    nombres = {nombre.lower() for nombre in nombres}

    for hijo in elemento.iter():
        nombre = quitar_namespace(hijo.tag).lower()

        if nombre in nombres:
            texto = obtener_texto(hijo)

            if texto:
                return texto

    return ""


def procesar_xml(xml):
    raiz = ET.fromstring(xml)

    resultados = []

    # Buscamos elementos que tengan estructura de noticia/item
    candidatos = []

    for elemento in raiz.iter():
        nombre = quitar_namespace(elemento.tag).lower()

        if nombre in (
            "item",
            "entry",
            "sorteo",
            "resultado",
            "result",
            "noticia",
        ):
            candidatos.append(elemento)

    # Si el XML utiliza otra estructura, buscamos elementos
    # que contengan información reconocible.
    if not candidatos:
        for elemento in raiz.iter():
            titulo = buscar_hijo(elemento, ["title", "titulo"])
            fecha = buscar_hijo(elemento, ["pubDate", "published", "date", "fecha"])
            descripcion = buscar_hijo(
                elemento,
                ["description", "descripcion", "content", "summary"],
            )

            if titulo or fecha or descripcion:
                candidatos.append(elemento)

    vistos = set()

    for elemento in candidatos:

        titulo = buscar_hijo(
            elemento,
            [
                "title",
                "titulo",
                "name",
                "nombre",
            ],
        )

        fecha = buscar_hijo(
            elemento,
            [
                "pubDate",
                "published",
                "updated",
                "date",
                "fecha",
            ],
        )

        descripcion = buscar_hijo(
            elemento,
            [
                "description",
                "descripcion",
                "summary",
                "content",
                "contenido",
            ],
        )

        # También comprobamos atributos por si el XML de ONCE
        # utiliza información en atributos.
        if not titulo:
            for clave, valor in elemento.attrib.items():
                clave_l = clave.lower()

                if clave_l in ("title", "titulo", "name", "nombre"):
                    titulo = limpiar_texto(valor)
                    break

        if not fecha:
            for clave, valor in elemento.attrib.items():
                clave_l = clave.lower()

                if clave_l in (
                    "date",
                    "fecha",
                    "pubdate",
                    "published",
                    "updated",
                ):
                    fecha = limpiar_texto(valor)
                    break

        if not descripcion:
            for clave, valor in elemento.attrib.items():
                clave_l = clave.lower()

                if clave_l in (
                    "description",
                    "descripcion",
                    "summary",
                    "content",
                    "contenido",
                ):
                    descripcion = limpiar_texto(valor)
                    break

        # Ignoramos elementos completamente vacíos.
        if not titulo and not fecha and not descripcion:
            continue

        clave = (titulo, fecha, descripcion)

        if clave in vistos:
            continue

        vistos.add(clave)

        resultados.append(
            {
                "titulo": titulo,
                "fecha": fecha,
                "descripcion": descripcion,
            }
        )

    return resultados


def guardar_resultados(resultados):
    datos = {
        "actualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "resultados": resultados,
    }

    with SALIDA.open("w", encoding="utf-8") as archivo:
        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=2,
        )


def main():
    print("Descargando XML de JuegosONCE...")
    
    xml = descargar_xml()

    print("XML descargado correctamente.")
    print("Tamaño:", len(xml), "bytes")

    resultados = procesar_xml(xml)

    print("Resultados encontrados:", len(resultados))

    # Mostramos información en Actions para poder comprobar
    # exactamente qué está leyendo el programa.
    for i, resultado in enumerate(resultados, start=1):
        print()
        print("RESULTADO", i)
        print("Título:", resultado["titulo"])
        print("Fecha:", resultado["fecha"])
        print("Descripción:", resultado["descripcion"])

    guardar_resultados(resultados)

    print()
    print("Archivo resultados.json generado correctamente.")
    print("Ruta:", SALIDA.resolve())


if __name__ == "__main__":
    main()