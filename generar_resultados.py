import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

RSS_URL = "https://www.juegosonce.es/rss/sorteos2.xml"
OUTPUT_FILE = "resultados.json"


def limpiar_html(texto):
    if not texto:
        return ""

    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = texto.replace("&nbsp;", " ")
    texto = texto.replace("&amp;", "&")
    texto = texto.replace("&quot;", '"')
    texto = texto.replace("&#39;", "'")
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def nombre_tag(tag):
    return tag.split("}")[-1].lower()


def descargar_rss():
    print(f"Descargando RSS desde: {RSS_URL}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "es-ES,es;q=0.9",
    }

    request = urllib.request.Request(
        RSS_URL,
        headers=headers
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as respuesta:
            contenido = respuesta.read()

        print(f"XML descargado: {len(contenido)} bytes")

        return contenido

    except Exception as error:
        raise RuntimeError(
            f"No se pudo descargar el RSS de ONCE: {error}"
        )


def obtener_items(contenido):
    try:
        raiz = ET.fromstring(contenido)
    except Exception as error:
        raise RuntimeError(
            f"No se pudo interpretar el XML del RSS: {error}"
        )

    items = []

    for elemento in raiz.iter():
        if nombre_tag(elemento.tag) == "item":
            items.append(elemento)

    print(f"Elementos <item> encontrados: {len(items)}")

    return items


def leer_item(item):
    campos = {}

    for hijo in item:

        nombre = nombre_tag(hijo.tag)

        valor = "".join(hijo.itertext())

        valor = limpiar_html(valor)

        if valor:
            campos[nombre] = valor

    return campos


def extraer_numero(texto):
    patrones = [
        r"(?:número|numero|number)\s*[:=-]\s*([0-9][0-9\s,.-]*)",
        r"(?:resultado)\s*[:=-]\s*([0-9][0-9\s,.-]*)",
    ]

    for patron in patrones:

        encontrado = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if encontrado:
            return encontrado.group(1).strip()

    return ""


def extraer_serie(texto):

    encontrado = re.search(
        r"serie\s*[:=-]\s*([0-9]+)",
        texto,
        re.IGNORECASE
    )

    if encontrado:
        return encontrado.group(1).strip()

    return ""


def extraer_bote(texto):

    patrones = [
        r"importe\s*bote\s*[:=-]\s*([0-9.,]+)",
        r"bote\s*[:=-]\s*([0-9.,]+)",
    ]

    for patron in patrones:

        encontrado = re.search(
            patron,
            texto,
            re.IGNORECASE
        )

        if encontrado:
            return encontrado.group(1).strip()

    return "0"


def convertir_item(campos):

    tipo = (
        campos.get("title")
        or campos.get("titulo")
        or ""
    ).strip()

    descripcion = (
        campos.get("description")
        or campos.get("descripcion")
        or ""
    ).strip()

    fecha = (
        campos.get("pubdate")
        or campos.get("date")
        or campos.get("fecha")
        or ""
    ).strip()

    enlace = (
        campos.get("link")
        or campos.get("enlace")
        or ""
    ).strip()

    numero = (
        campos.get("numero")
        or campos.get("number")
        or ""
    ).strip()

    serie = (
        campos.get("serie")
        or ""
    ).strip()

    bote = (
        campos.get("importebote")
        or campos.get("bote")
        or ""
    ).strip()

    adic = (
        campos.get("adic")
        or ""
    ).strip()

    texto_completo = (
        tipo + " " +
        descripcion
    )

    if not numero:
        numero = extraer_numero(
            texto_completo
        )

    if not serie:
        serie = extraer_serie(
            texto_completo
        )

    if not bote:
        bote = extraer_bote(
            texto_completo
        )

    resultado = {
        "tipo": tipo,
        "fecha": fecha,
        "numero": numero,
        "serie": serie,
        "importebote": bote,
    }

    if adic:
        resultado["adic"] = adic

    if enlace:
        resultado["enlace"] = enlace

    if descripcion:
        resultado["descripcion"] = descripcion

    return resultado


def obtener_resultados():

    contenido = descargar_rss()

    items = obtener_items(
        contenido
    )

    resultados = []

    for item in items:

        campos = leer_item(item)

        resultado = convertir_item(
            campos
        )

        if resultado["tipo"]:

            resultados.append(
                resultado
            )

    print(
        f"RESULTADOS OBTENIDOS: {len(resultados)}"
    )

    return resultados


def guardar_resultados(resultados):

    if not resultados:

        raise RuntimeError(
            "El RSS de ONCE no ha devuelto resultados. "
            "No se sobrescribe resultados.json."
        )

    ahora = datetime.now(
        ZoneInfo("Europe/Madrid")
    )

    datos = {
        "actualizado": ahora.strftime(
            "%d/%m/%Y %H:%M"
        ),
        "resultados": resultados
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"{OUTPUT_FILE} creado correctamente."
    )


def main():

    resultados = obtener_resultados()

    guardar_resultados(
        resultados
    )


if __name__ == "__main__":
    main()