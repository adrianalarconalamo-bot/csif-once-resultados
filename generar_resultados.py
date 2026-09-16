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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
            "Accept": "application/xml,text/xml,*/*"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as respuesta:
        datos = respuesta.read()

    print("XML descargado:", len(datos), "bytes")

    return datos


def limpiar_html(texto):
    if not texto:
        return ""

    texto = unescape(texto)

    texto = re.sub(r"<br\s*/?>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<[^>]+>", " ", texto)

    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n", texto)

    return texto.strip()


def nombre_tag(tag):
    """
    Elimina cualquier namespace XML.

    Ejemplo:
    {http://purl.org/rss/1.0/}title
    se convierte en:
    title
    """

    if "}" in tag:
        return tag.split("}", 1)[1].lower()

    return tag.lower()


def obtener_texto(elemento, nombres):
    """
    Busca descendientes independientemente del namespace.
    """

    nombres = {x.lower() for x in nombres}

    for hijo in elemento.iter():

        if nombre_tag(hijo.tag) in nombres:

            if hijo.text:
                texto = hijo.text.strip()

                if texto:
                    return limpiar_html(texto)

    return ""


def extraer_resultados(datos):

    raiz = ET.fromstring(datos)

    resultados = []

    print("Elemento raíz:", raiz.tag)

    # Buscamos todos los elementos que puedan ser items RSS/XML
    candidatos = []

    for elemento in raiz.iter():

        tag = nombre_tag(elemento.tag)

        if tag in ("item", "entry"):

            titulo = obtener_texto(
                elemento,
                ["title"]
            )

            fecha = obtener_texto(
                elemento,
                ["pubDate", "published", "date", "fecha"]
            )

            descripcion = obtener_texto(
                elemento,
                ["description", "summary", "content"]
            )

            if titulo or fecha or descripcion:

                candidatos.append({
                    "titulo": titulo,
                    "fecha": fecha,
                    "descripcion": descripcion
                })

    print("Elementos encontrados:", len(candidatos))

    # Si no encontramos item/entry, hacemos una búsqueda
    # más amplia de títulos y descripciones.
    if not candidatos:

        print("No se encontraron item/entry. Analizando XML completo...")

        for elemento in raiz.iter():

            titulo = obtener_texto(elemento, ["title"])
            descripcion = obtener_texto(
                elemento,
                ["description", "summary", "content"]
            )

            if titulo or descripcion:

                candidatos.append({
                    "titulo": titulo,
                    "fecha": "",
                    "descripcion": descripcion
                })

    # Eliminamos duplicados
    resultados_finales = []

    vistos = set()

    for resultado in candidatos:

        clave = (
            resultado["titulo"],
            resultado["fecha"],
            resultado["descripcion"]
        )

        if clave in vistos:
            continue

        vistos.add(clave)

        # Nunca guardamos un registro completamente vacío
        if (
            not resultado["titulo"]
            and not resultado["fecha"]
            and not resultado["descripcion"]
        ):
            continue

        resultados_finales.append(resultado)

    return resultados_finales


def crear_mensaje(resultados):

    texto = []

    texto.append("🍀 RESULTADOS ONCE")
    texto.append(
        datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    texto.append("")

    for resultado in resultados:

        titulo = resultado.get("titulo", "")
        fecha = resultado.get("fecha", "")
        descripcion = resultado.get("descripcion", "")

        if titulo:
            texto.append(titulo)

        if fecha:
            texto.append(fecha)

        if descripcion:
            texto.append(descripcion)

        texto.append("")

    return "\n".join(texto).strip()


def guardar_json(resultados):

    datos = {
        "actualizado": datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        ),
        "resultados": resultados
    }

    Path("resultados.json").write_text(
        json.dumps(
            datos,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("====================================")
    print("RESULTADOS GUARDADOS")
    print("====================================")
    print("Total:", len(resultados))

    for numero, resultado in enumerate(resultados, 1):

        print()
        print("RESULTADO", numero)
        print("Título:", resultado["titulo"])
        print("Fecha:", resultado["fecha"])
        print("Descripción:", resultado["descripcion"])


def main():

    print("====================================")
    print("GENERADOR DE RESULTADOS ONCE")
    print("====================================")
    print("Fuente:", URL)
    print()

    datos = descargar_xml()

    resultados = extraer_resultados(datos)

    guardar_json(resultados)

    mensaje = crear_mensaje(resultados)

    Path("salida").mkdir(exist_ok=True)

    Path("salida/mensaje.txt").write_text(
        mensaje,
        encoding="utf-8"
    )

    print()
    print("====================================")
    print("MENSAJE GENERADO")
    print("====================================")
    print(mensaje)

    if not resultados:
        print()
        print("ERROR: ONCE no ha devuelto resultados reconocibles.")
        print("El XML descargado tiene", len(datos), "bytes.")
        raise RuntimeError(
            "No se han podido extraer resultados del XML de ONCE."
        )


if __name__ == "__main__":
    main()