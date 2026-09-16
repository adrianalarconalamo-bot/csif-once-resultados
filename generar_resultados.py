import json
import re
import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo


RSS_URL = "https://www.juegosonce.es/rss/sorteos2.xml"
OUTPUT_FILE = "resultados.json"


def limpiar_texto(texto):
    if not texto:
        return ""

    texto = html.unescape(str(texto))
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = texto.replace("\xa0", " ")
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def nombre_tag(tag):
    return tag.split("}")[-1].lower().strip()


def descargar_rss():
    print(f"Descargando RSS desde: {RSS_URL}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
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

    for elemento in item.iter():

        if elemento is item:
            continue

        tag = nombre_tag(elemento.tag)

        texto = "".join(elemento.itertext())
        texto = limpiar_texto(texto)

        if not texto:
            continue

        if tag not in campos:
            campos[tag] = texto

    return campos


def buscar_campo(campos, nombres):

    for nombre in nombres:

        valor = campos.get(nombre)

        if valor:
            return limpiar_texto(valor)

    return ""


def detectar_tipo(campos):

    tipo = buscar_campo(
        campos,
        [
            "title",
            "titulo",
            "name",
            "nombre",
            "game",
            "juego",
            "product",
            "producto",
            "draw",
            "sorteo",
        ]
    )

    if tipo:
        return tipo

    texto = " ".join(campos.values()).lower()

    patrones = [
        ("Cupón Diario", ["cupón diario", "cupon diario"]),
        ("Sueldazo", ["sueldazo"]),
        ("Cuponazo", ["cuponazo"]),
        ("Mi Día", ["mi día", "mi dia"]),
        ("Triplex de la ONCE", ["triplex"]),
        ("Dupla de la ONCE", ["dupla"]),
        ("Super 11", ["super 11", "súper 11"]),
        ("Eurojackpot", ["eurojackpot"]),
        ("7 de la Suerte", ["7 de la suerte"]),
        ("El Millonario", ["el millonario", "millonario"]),
        ("Rasca", ["rasca"]),
    ]

    for nombre, palabras in patrones:

        for palabra in palabras:

            if palabra in texto:
                return nombre

    return ""


def buscar_fecha(campos):

    return buscar_campo(
        campos,
        [
            "pubdate",
            "date",
            "fecha",
            "drawdate",
            "sorteodate",
        ]
    )


def buscar_numero(campos):

    numero = buscar_campo(
        campos,
        [
            "numero",
            "number",
            "result",
            "resultado",
            "winningnumber",
            "winning-number",
            "winning_number",
            "combinacion",
            "combinación",
        ]
    )

    if numero:
        return numero

    texto = " ".join(campos.values())

    patrones = [
        r"(?:número|numero)\s*[:=]\s*([0-9][0-9\s,./-]*)",
        r"(?:resultado)\s*[:=]\s*([0-9][0-9\s,./-]*)",
        r"(?:number)\s*[:=]\s*([0-9][0-9\s,./-]*)",
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


def buscar_serie(campos):

    serie = buscar_campo(
        campos,
        [
            "serie",
            "series",
            "seriesnumber",
            "serial",
        ]
    )

    if serie:
        return serie

    texto = " ".join(campos.values())

    encontrado = re.search(
        r"serie\s*[:=]\s*([0-9]+)",
        texto,
        re.IGNORECASE
    )

    if encontrado:
        return encontrado.group(1).strip()

    return ""


def buscar_bote(campos):

    bote = buscar_campo(
        campos,
        [
            "importebote",
            "importe-bote",
            "importe_bote",
            "bote",
            "jackpot",
            "prize",
            "premio",
        ]
    )

    if bote:
        return bote

    texto = " ".join(campos.values())

    patrones = [
        r"importe\s*bote\s*[:=]\s*([0-9.,]+)",
        r"bote\s*[:=]\s*([0-9.,]+)",
        r"jackpot\s*[:=]\s*([0-9.,]+)",
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

    tipo = detectar_tipo(campos)

    if not tipo:
        return None

    fecha = buscar_fecha(campos)
    numero = buscar_numero(campos)
    serie = buscar_serie(campos)
    bote = buscar_bote(campos)

    resultado = {
        "tipo": tipo,
        "fecha": fecha,
        "numero": numero,
        "serie": serie,
        "importebote": bote,
    }

    descripcion = buscar_campo(
        campos,
        [
            "description",
            "descripcion",
            "summary",
            "content",
            "encoded",
        ]
    )

    enlace = buscar_campo(
        campos,
        [
            "link",
            "enlace",
            "url",
        ]
    )

    if descripcion:
        resultado["descripcion"] = descripcion

    if enlace:
        resultado["enlace"] = enlace

    return resultado


def obtener_resultados():

    contenido = descargar_rss()

    items = obtener_items(contenido)

    resultados = []

    for posicion, item in enumerate(items, start=1):

        campos = leer_item(item)

        print(
            f"Procesando item {posicion}: "
            f"{list(campos.keys())}"
        )

        resultado = convertir_item(campos)

        if resultado:

            resultados.append(resultado)

            print(
                f"  OK: {resultado['tipo']} "
                f"| {resultado['fecha']} "
                f"| {resultado['numero']}"
            )

        else:

            print(
                "  AVISO: no se pudo identificar "
                "el tipo del sorteo"
            )

    print(
        f"RESULTADOS OBTENIDOS ANTES DEL FILTRO: "
        f"{len(resultados)}"
    )

    # ==========================================================
    # FILTRO: SOLO RESULTADOS DEL DÍA ACTUAL EN ESPAÑA
    # ==========================================================

    ahora = datetime.now(
        ZoneInfo("Europe/Madrid")
    )

    fecha_hoy = ahora.strftime("%d/%m/%Y")

    dias = [
        "lunes",
        "martes",
        "miércoles",
        "jueves",
        "viernes",
        "sábado",
        "domingo",
    ]

    dia_hoy = dias[ahora.weekday()]

    resultados_hoy = []

    for resultado in resultados:

        fecha = limpiar_texto(
            resultado.get("fecha", "")
        ).lower()

        # Comprobamos tanto la fecha numérica como
        # el nombre del día.
        coincide_fecha = fecha_hoy in fecha
        coincide_dia = dia_hoy in fecha

        if coincide_fecha or coincide_dia:
            resultados_hoy.append(resultado)

    print(
        f"FECHA ACTUAL EN ESPAÑA: {fecha_hoy}"
    )

    print(
        f"RESULTADOS DEL DÍA: {len(resultados_hoy)}"
    )

    for resultado in resultados_hoy:

        print(
            f"  ✓ {resultado['tipo']} "
            f"| {resultado['fecha']} "
            f"| {resultado['numero']}"
        )

    return resultados_hoy


def guardar_resultados(resultados):

    if not resultados:

        raise RuntimeError(
            "El RSS de ONCE contiene resultados, "
            "pero ninguno corresponde al día actual."
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

    print(
        f"Resultados guardados: {len(resultados)}"
    )


def main():

    resultados = obtener_resultados()

    guardar_resultados(
        resultados
    )


if __name__ == "__main__":
    main()