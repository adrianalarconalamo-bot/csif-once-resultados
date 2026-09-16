import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from pathlib import Path
import re


URL = "https://www.juegosonce.es/rss/sorteos2.xml"
SALIDA = Path("resultados.json")


def descargar_xml():
    print("Descargando RSS de la ONCE...")

    request = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as respuesta:
        datos = respuesta.read()

    print(f"XML descargado: {len(datos)} bytes")

    if not datos:
        raise RuntimeError("El RSS está vacío.")

    return datos


def limpiar(texto):
    if texto is None:
        return ""

    texto = str(texto)

    texto = re.sub(r"<[^>]+>", " ", texto)

    texto = texto.replace("&nbsp;", " ")
    texto = texto.replace("&amp;", "&")
    texto = texto.replace("&quot;", '"')
    texto = texto.replace("&#39;", "'")

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def nombre_local(elemento):
    """
    Devuelve el nombre de la etiqueta ignorando namespaces.
    Ejemplo:
    {http://purl.org/rss/1.0/}title -> title
    """
    return elemento.tag.split("}")[-1].lower()


def buscar_valor(elemento, nombres):
    """
    Busca recursivamente una etiqueta cuyo nombre coincida.
    """

    nombres = {x.lower() for x in nombres}

    for hijo in elemento.iter():
        if nombre_local(hijo) in nombres:
            texto = limpiar(hijo.text)

            if texto:
                return texto

    return ""


def extraer_items(raiz):
    """
    Busca elementos RSS tipo item.
    También acepta entry por si la fuente cambia a Atom.
    """

    items = []

    for elemento in raiz.iter():
        nombre = nombre_local(elemento)

        if nombre in ("item", "entry"):
            items.append(elemento)

    return items


def extraer_resultados(xml):
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError as e:
        raise RuntimeError(f"No se ha podido interpretar el XML: {e}")

    items = extraer_items(raiz)

    print(f"Elementos encontrados en el RSS: {len(items)}")

    if not items:
        raise RuntimeError(
            "El RSS se ha descargado correctamente, pero no contiene elementos item/entry."
        )

    resultados = []

    for item in items:

        titulo = buscar_valor(
            item,
            [
                "title",
                "titulo",
                "name",
                "nombre"
            ]
        )

        fecha = buscar_valor(
            item,
            [
                "pubdate",
                "published",
                "updated",
                "date",
                "fecha"
            ]
        )

        descripcion = buscar_valor(
            item,
            [
                "description",
                "summary",
                "content",
                "contenido",
                "descripcion"
            ]
        )

        resultado = {
            "titulo": titulo,
            "fecha": fecha,
            "descripcion": descripcion
        }

        # Solo añadimos resultados que tengan algún contenido real.
        if titulo or fecha or descripcion:
            resultados.append(resultado)

    return resultados


def guardar_resultados(resultados):
    if not resultados:
        raise RuntimeError(
            "ERROR: no se ha podido extraer NINGÚN resultado del RSS. "
            "No se va a generar un resultados.json vacío."
        )

    # Comprobación adicional para impedir el problema anterior.
    completos = [
        r for r in resultados
        if r["titulo"] or r["fecha"] or r["descripcion"]
    ]

    if not completos:
        raise RuntimeError(
            "ERROR: todos los resultados están vacíos. "
            "La ejecución se detiene para no publicar datos incorrectos."
        )

    datos = {
        "actualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "resultados": resultados
    }

    with SALIDA.open("w", encoding="utf-8") as archivo:
        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("======================================")
    print("RESULTADOS GENERADOS CORRECTAMENTE")
    print("======================================")
    print(f"Resultados extraídos: {len(resultados)}")
    print(f"Archivo: {SALIDA}")
    print()

    for numero, resultado in enumerate(resultados, start=1):
        print(f"{numero}. {resultado['titulo']}")
        print(f"   Fecha: {resultado['fecha']}")
        print(f"   Descripción: {resultado['descripcion']}")
        print()


def main():

    print("======================================")
    print(" GENERADOR DE RESULTADOS ONCE")
    print("======================================")

    xml = descargar_xml()

    resultados = extraer_resultados(xml)

    guardar_resultados(resultados)


if __name__ == "__main__":
    main()