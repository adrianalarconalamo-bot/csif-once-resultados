import urllib.request
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime
from pathlib import Path
from html import unescape


URL = "https://www.juegosonce.es/rss/sorteos2.xml"

ARCHIVO_SALIDA = Path("resultados.json")
ARCHIVO_XML_DEBUG = Path("sorteos2_debug.xml")


def descargar_xml():
    """
    Descarga el XML oficial de JuegosONCE.
    """
    request = urllib.request.Request(
        URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0 Safari/537.36"
            ),
            "Accept": (
                "application/xml,text/xml,"
                "application/rss+xml,application/rss;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "es-ES,es;q=0.9"
        }
    )

    with urllib.request.urlopen(request, timeout=60) as respuesta:
        datos = respuesta.read()

    if not datos:
        raise RuntimeError("La fuente RSS/XML ha devuelto contenido vacío.")

    return datos


def limpiar_nombre(nombre):
    """
    Elimina namespace y normaliza el nombre de una etiqueta XML.
    """
    if not nombre:
        return ""

    nombre = str(nombre)

    if "}" in nombre:
        nombre = nombre.split("}", 1)[1]

    if ":" in nombre:
        nombre = nombre.split(":", 1)[1]

    return nombre.strip().lower()


def limpiar_texto(texto):
    """
    Limpia HTML, CDATA, espacios y entidades.
    """
    if texto is None:
        return ""

    texto = str(texto)
    texto = unescape(texto)

    texto = re.sub(
        r"<!\[CDATA\[(.*?)\]\]>",
        r"\1",
        texto,
        flags=re.DOTALL | re.IGNORECASE
    )

    texto = re.sub(
        r"<[^>]+>",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def texto_elemento(elemento):
    """
    Obtiene todo el texto contenido dentro de un elemento,
    incluyendo elementos hijos.
    """
    partes = []

    for texto in elemento.itertext():
        texto = limpiar_texto(texto)

        if texto:
            partes.append(texto)

    return " ".join(partes).strip()


def buscar_campo(elemento, nombres):
    """
    Busca un campo por diferentes nombres posibles.
    """
    nombres = {
        limpiar_nombre(nombre)
        for nombre in nombres
    }

    for hijo in elemento.iter():
        nombre = limpiar_nombre(hijo.tag)

        if nombre in nombres:
            valor = texto_elemento(hijo)

            if valor:
                return valor

            for atributo, valor_atributo in hijo.attrib.items():
                valor_atributo = limpiar_texto(valor_atributo)

                if valor_atributo:
                    return valor_atributo

    return ""


def buscar_atributo(elemento, nombres):
    """
    Busca atributos con nombres habituales.
    """
    nombres = {
        limpiar_nombre(nombre)
        for nombre in nombres
    }

    for nodo in elemento.iter():
        for atributo, valor in nodo.attrib.items():
            if limpiar_nombre(atributo) in nombres:
                valor = limpiar_texto(valor)

                if valor:
                    return valor

    return ""


def encontrar_items(root):
    """
    Detecta automáticamente los elementos que representan
    cada resultado.

    Primero intenta RSS estándar:
        channel/item

    Después busca etiquetas habituales:
        item, resultado, sorteo, result
    """

    # RSS estándar
    items = []

    for elemento in root.iter():
        if limpiar_nombre(elemento.tag) == "item":
            items.append(elemento)

    if items:
        return items

    # Otros formatos posibles
    nombres = {
        "resultado",
        "result",
        "sorteo",
        "draw",
        "entry"
    }

    for elemento in root.iter():
        if limpiar_nombre(elemento.tag) in nombres:
            items.append(elemento)

    return items


def extraer_resultado(item):
    """
    Extrae un resultado independientemente de pequeñas variaciones
    en la estructura del XML.
    """

    titulo = buscar_campo(
        item,
        [
            "title",
            "titulo",
            "nombre",
            "juego",
            "producto",
            "nombreJuego",
            "nombreSorteo"
        ]
    )

    fecha = buscar_campo(
        item,
        [
            "pubdate",
            "pubDate",
            "date",
            "fecha",
            "fechaSorteo",
            "sorteoFecha",
            "dc:date",
            "published"
        ]
    )

    descripcion = buscar_campo(
        item,
        [
            "description",
            "descripcion",
            "result",
            "resultado",
            "numero",
            "premio",
            "combinacion",
            "combinación",
            "contenido",
            "content"
        ]
    )

    # Algunos XML utilizan atributos en lugar de nodos.
    if not titulo:
        titulo = buscar_atributo(
            item,
            [
                "title",
                "titulo",
                "name",
                "nombre",
                "juego",
                "producto"
            ]
        )

    if not fecha:
        fecha = buscar_atributo(
            item,
            [
                "date",
                "fecha",
                "pubdate",
                "published"
            ]
        )

    if not descripcion:
        descripcion = buscar_atributo(
            item,
            [
                "description",
                "descripcion",
                "result",
                "resultado",
                "numero"
            ]
        )

    return {
        "titulo": titulo,
        "fecha": fecha,
        "descripcion": descripcion
    }


def eliminar_duplicados(resultados):
    """
    Elimina duplicados conservando el orden.
    """

    vistos = set()
    salida = []

    for resultado in resultados:

        clave = (
            resultado.get("titulo", "").strip().lower(),
            resultado.get("fecha", "").strip().lower(),
            resultado.get("descripcion", "").strip().lower()
        )

        if clave in vistos:
            continue

        vistos.add(clave)
        salida.append(resultado)

    return salida


def generar():
    print("======================================")
    print(" GENERADOR DE RESULTADOS ONCE")
    print("======================================")

    print()
    print("Descargando:")
    print(URL)

    datos = descargar_xml()

    print()
    print(f"XML descargado: {len(datos)} bytes")

    # Guardamos una copia para diagnóstico.
    try:
        ARCHIVO_XML_DEBUG.write_bytes(datos)
        print(f"XML guardado en: {ARCHIVO_XML_DEBUG}")
    except Exception as error:
        print(f"No se pudo guardar XML de diagnóstico: {error}")

    # Parseamos el XML.
    try:
        root = ET.fromstring(datos)
    except ET.ParseError as error:
        print()
        print("ERROR PARSEANDO XML:")
        print(error)

        # Intento adicional eliminando BOM.
        try:
            datos_limpios = datos.decode(
                "utf-8-sig",
                errors="replace"
            ).encode("utf-8")

            root = ET.fromstring(datos_limpios)

        except Exception:
            raise RuntimeError(
                "No ha sido posible interpretar el XML de JuegosONCE."
            )

    print()
    print("Elemento raíz:")
    print(root.tag)

    items = encontrar_items(root)

    print()
    print(f"Elementos de resultados encontrados: {len(items)}")

    resultados = []

    for numero, item in enumerate(items, start=1):

        resultado = extraer_resultado(item)

        print()
        print(f"Resultado {numero}:")
        print(f"  Título:      {resultado['titulo']}")
        print(f"  Fecha:       {resultado['fecha']}")
        print(f"  Descripción: {resultado['descripcion']}")

        # Solo descartamos elementos completamente vacíos.
        if (
            resultado["titulo"]
            or resultado["fecha"]
            or resultado["descripcion"]
        ):
            resultados.append(resultado)

    resultados = eliminar_duplicados(resultados)

    salida = {
        "actualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "resultados": resultados
    }

    with ARCHIVO_SALIDA.open(
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            salida,
            archivo,
            ensure_ascii=False,
            indent=2
        )

        archivo.write("\n")

    print()
    print("======================================")
    print(" RESULTADO FINAL")
    print("======================================")
    print(f"Resultados válidos: {len(resultados)}")
    print(f"Archivo generado: {ARCHIVO_SALIDA}")

    if not resultados:
        print()
        print("ATENCIÓN:")
        print("No se ha encontrado ningún resultado utilizable.")
        print()
        print(
            "El XML descargado se ha guardado como "
            "sorteos2_debug.xml para poder analizar "
            "su estructura real."
        )

    print()


if __name__ == "__main__":
    generar()