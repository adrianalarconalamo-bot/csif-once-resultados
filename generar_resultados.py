import json
import re
import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo


RSS_URL = "https://www.juegosonce.es/rss/sorteos2.xml"
OUTPUT_FILE = "resultados.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml,text/xml,*/*"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
}


# ==========================================================
# UTILIDADES
# ==========================================================

def limpiar_texto(texto):
    if not texto:
        return ""

    texto = html.unescape(str(texto))
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = texto.replace("\xa0", " ")
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def descargar_url(url):
    print(f"Descargando: {url}")

    request = urllib.request.Request(
        url,
        headers=HEADERS
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30
        ) as respuesta:

            contenido = respuesta.read()

        print(
            f"Descargado correctamente: "
            f"{len(contenido)} bytes"
        )

        return contenido

    except Exception as error:

        print(
            f"AVISO: no se pudo descargar "
            f"{url}: {error}"
        )

        return b""


def texto_html(contenido):
    if not contenido:
        return ""

    try:
        texto = contenido.decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:
        texto = str(contenido)

    texto = html.unescape(texto)

    texto = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    texto = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        texto,
        flags=re.IGNORECASE | re.DOTALL
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


def extraer_fecha(texto):

    if not texto:
        return None

    encontrado = re.search(
        r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
        texto
    )

    if encontrado:

        try:

            return datetime(
                int(encontrado.group(3)),
                int(encontrado.group(2)),
                int(encontrado.group(1))
            ).date()

        except ValueError:
            pass

    meses = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }

    patron = re.search(
        r"(\d{1,2})\s+de\s+"
        r"(enero|febrero|marzo|abril|mayo|junio|julio|"
        r"agosto|septiembre|octubre|noviembre|diciembre)"
        r"\s+de\s+(\d{4})",
        texto.lower()
    )

    if patron:

        try:

            return datetime(
                int(patron.group(3)),
                meses[patron.group(2)],
                int(patron.group(1))
            ).date()

        except ValueError:
            pass

    return None


# ==========================================================
# RSS
# ==========================================================

def obtener_items_rss(contenido):

    if not contenido:
        return []

    try:

        raiz = ET.fromstring(contenido)

    except Exception as error:

        print(
            f"AVISO: no se pudo interpretar "
            f"el XML: {error}"
        )

        return []

    items = []

    for elemento in raiz.iter():

        if elemento.tag.split("}")[-1].lower() == "item":
            items.append(elemento)

    return items


def leer_item(item):

    campos = {}

    for elemento in item.iter():

        if elemento is item:
            continue

        tag = elemento.tag.split("}")[-1].lower()

        texto = limpiar_texto(
            "".join(elemento.itertext())
        )

        if texto and tag not in campos:
            campos[tag] = texto

    return campos


def buscar_campo(campos, nombres):

    for nombre in nombres:

        valor = campos.get(nombre)

        if valor:
            return limpiar_texto(valor)

    return ""


def detectar_tipo(campos):

    texto = " ".join(
        campos.values()
    ).lower()

    patrones = [
        (
            "Cupón Diario",
            [
                "cupón diario",
                "cupon diario"
            ]
        ),
        (
            "Cuponazo",
            [
                "cuponazo"
            ]
        ),
        (
            "Sueldazo",
            [
                "sueldazo"
            ]
        ),
        (
            "Mi Día",
            [
                "mi día",
                "mi dia"
            ]
        ),
        (
            "Triplex de la ONCE",
            [
                "triplex"
            ]
        ),
        (
            "Dupla de la ONCE",
            [
                "dupla"
            ]
        ),
        (
            "Super 11",
            [
                "super 11",
                "súper 11",
                "superonce"
            ]
        ),
        (
            "Eurojackpot",
            [
                "eurojackpot"
            ]
        ),
    ]

    for nombre, palabras in patrones:

        for palabra in palabras:

            if palabra in texto:
                return nombre

    return ""


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

    texto = " ".join(
        campos.values()
    )

    patrones = [
        r"(?:número|numero)\s*[:=]\s*"
        r"([0-9][0-9\s,./-]*)",

        r"(?:resultado)\s*[:=]\s*"
        r"([0-9][0-9\s,./-]*)",

        r"(?:number)\s*[:=]\s*"
        r"([0-9][0-9\s,./-]*)",
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

    texto = " ".join(
        campos.values()
    )

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
        ]
    )

    if bote:
        return bote

    return "0"


# ==========================================================
# RESULTADOS DESDE RSS
# ==========================================================

def obtener_resultados_rss():

    contenido = descargar_url(
        RSS_URL
    )

    items = obtener_items_rss(
        contenido
    )

    resultados = []

    for item in items:

        campos = leer_item(item)

        tipo = detectar_tipo(
            campos
        )

        if not tipo:
            continue

        resultado = {
            "tipo": tipo,
            "fecha": buscar_campo(
                campos,
                [
                    "pubdate",
                    "date",
                    "fecha",
                    "drawdate",
                    "sorteodate",
                ]
            ),
            "numero": buscar_numero(
                campos
            ),
            "serie": buscar_serie(
                campos
            ),
            "importebote": buscar_bote(
                campos
            ),
        }

        resultados.append(
            resultado
        )

    print(
        f"Resultados obtenidos del RSS: "
        f"{len(resultados)}"
    )

    return resultados


# ==========================================================
# CUPONES DESDE WEB OFICIAL
# ==========================================================

def extraer_cupon_desde_web(tipo, url):

    contenido = descargar_url(
        url
    )

    if not contenido:
        return None

    texto = texto_html(
        contenido
    )

    texto_lower = texto.lower()

    if tipo == "Cuponazo":

        if "cuponazo" not in texto_lower:
            return None

    elif tipo == "Cupón Diario":

        if (
            "cupón diario" not in texto_lower
            and "cupon diario" not in texto_lower
        ):
            return None

    fecha = extraer_fecha(
        texto
    )

    if not fecha:

        print(
            f"AVISO: no se encontró fecha "
            f"para {tipo}"
        )

        return None

    patron = re.search(
        r"Número\s*[:\-]?\s*"
        r"([0-9]{5})"
        r".{0,100}?"
        r"serie\s*[:\-]?\s*"
        r"([0-9]{3})",
        texto,
        re.IGNORECASE
    )

    if not patron:

        patron = re.search(
            r"numero\s*[:\-]?\s*"
            r"([0-9]{5})"
            r".{0,100}?"
            r"serie\s*[:\-]?\s*"
            r"([0-9]{3})",
            texto,
            re.IGNORECASE
        )

    if not patron:

        print(
            f"AVISO: no se encontró "
            f"número/serie de {tipo}"
        )

        return None

    numero = patron.group(1)
    serie = patron.group(2)

    dias = [
        "lunes",
        "martes",
        "miércoles",
        "jueves",
        "viernes",
        "sábado",
        "domingo",
    ]

    fecha_formateada = (
        f"{dias[fecha.weekday()].capitalize()}, "
        f"{fecha.strftime('%d/%m/%Y')}"
    )

    resultado = {
        "tipo": tipo,
        "fecha": fecha_formateada,
        "numero": numero,
        "serie": serie,
        "importebote": "0",
    }

    print(
        f"✓ WEB OFICIAL: "
        f"{tipo} | "
        f"{fecha_formateada} | "
        f"{numero} | "
        f"serie {serie}"
    )

    return resultado


# ==========================================================
# SUELDAZO FIN DE SEMANA
# ==========================================================

def extraer_sueldazo_desde_web(url):

    contenido = descargar_url(
        url
    )

    if not contenido:
        return []

    texto = texto_html(
        contenido
    )

    if "sueldazo" not in texto.lower():

        print(
            "AVISO: la página no contiene "
            "información del Sueldazo."
        )

        return []

    fecha = extraer_fecha(
        texto
    )

    if not fecha:

        print(
            "AVISO: no se encontró "
            "la fecha del Sueldazo."
        )

        return []

    dias = [
        "lunes",
        "martes",
        "miércoles",
        "jueves",
        "viernes",
        "sábado",
        "domingo",
    ]

    fecha_formateada = (
        f"{dias[fecha.weekday()].capitalize()}, "
        f"{fecha.strftime('%d/%m/%Y')}"
    )

    resultados = []

    # ------------------------------------------------------
    # BUSCAR TODAS LAS PAREJAS NÚMERO + SERIE
    # ------------------------------------------------------

    patrones = [
        r"N[uú]mero\s*[:\-]?\s*"
        r"([0-9]{5})"
        r".{0,150}?"
        r"Serie\s*[:\-]?\s*"
        r"([0-9]{3})",

        r"N[uú]mero\s+"
        r"([0-9]{5})"
        r".{0,150}?"
        r"Serie\s+"
        r"([0-9]{3})",
    ]

    parejas = []

    for patron in patrones:

        encontradas = re.findall(
            patron,
            texto,
            re.IGNORECASE
        )

        for numero, serie in encontradas:

            pareja = (
                numero,
                serie
            )

            if pareja not in parejas:
                parejas.append(pareja)

    # ------------------------------------------------------
    # SI LA PÁGINA DEVUELVE LAS CINCO PAREJAS,
    # LA PRIMERA ES EL PREMIO PRINCIPAL
    # Y LAS CUATRO SIGUIENTES SON LOS ADICIONALES.
    # ------------------------------------------------------

    if len(parejas) >= 1:

        numero_principal, serie_principal = parejas[0]

        resultados.append({
            "tipo": "Sueldazo",
            "fecha": fecha_formateada,
            "numero": numero_principal,
            "serie": serie_principal,
            "importebote": "0"
        })

        print(
            f"✓ SUELDAZO PRINCIPAL: "
            f"{numero_principal} | "
            f"serie {serie_principal}"
        )

    else:

        print(
            "AVISO: no se encontró "
            "el número principal del Sueldazo."
        )

    # ------------------------------------------------------
    # CUATRO PREMIOS ADICIONALES
    # ------------------------------------------------------

    for numero, serie in parejas[1:5]:

        resultados.append({
            "tipo": "Sueldazo adicional",
            "fecha": fecha_formateada,
            "numero": numero,
            "serie": serie,
            "importebote": "0"
        })

        print(
            f"✓ SUELDAZO ADICIONAL: "
            f"{numero} | "
            f"serie {serie}"
        )

    if len(parejas) < 5:

        print(
            "AVISO: el Sueldazo ha devuelto "
            f"{len(parejas)} parejas "
            "número/serie; se esperaban 5."
        )

    return resultados


# ==========================================================
# OBTENER ÚLTIMO CUPÓN DISPONIBLE
# ==========================================================

def obtener_cupones_oficiales():

    paginas = [
        (
            "Cupón Diario",
            "https://www.juegosonce.es/"
            "resultados-cupon-diario"
        ),
        (
            "Cuponazo",
            "https://www.juegosonce.es/"
            "resultados-cuponazo"
        ),
    ]

    resultados = []

    # ------------------------------------------------------
    # CUPÓN DIARIO Y CUPONAZO
    # ------------------------------------------------------

    for tipo, url in paginas:

        resultado = extraer_cupon_desde_web(
            tipo,
            url
        )

        if resultado:

            resultados.append(
                resultado
            )

    # ------------------------------------------------------
    # SUELDAZO FIN DE SEMANA
    # ------------------------------------------------------

    url_sueldazo = (
        "https://www.juegosonce.es/"
        "resultados-sueldazo-fin-de-semana"
    )

    resultados_sueldazo = (
        extraer_sueldazo_desde_web(
            url_sueldazo
        )
    )

    resultados.extend(
        resultados_sueldazo
    )

    return resultados


# ==========================================================
# COMBINAR RESULTADOS
# ==========================================================

def clave_resultado(resultado):

    return (
        resultado.get("tipo", "").upper(),
        resultado.get("fecha", ""),
        resultado.get("numero", ""),
        resultado.get("serie", "")
    )


def combinar_resultados(
    resultados_rss,
    resultados_web
):

    todos = []

    for resultado in (
        resultados_rss +
        resultados_web
    ):

        clave = clave_resultado(
            resultado
        )

        if not any(
            clave_resultado(x) == clave
            for x in todos
        ):

            todos.append(
                resultado
            )

    return todos


# ==========================================================
# FILTRAR FECHA MÁS RECIENTE
# ==========================================================

def filtrar_fecha_reciente(
    resultados
):

    fechas = []

    for resultado in resultados:

        fecha = extraer_fecha(
            resultado.get(
                "fecha",
                ""
            )
        )

        if fecha:

            fechas.append(
                fecha
            )

    if not fechas:

        raise RuntimeError(
            "No se pudo determinar "
            "ninguna fecha."
        )

    fecha_objetivo = max(
        fechas
    )

    print(
        "Fecha más reciente encontrada: "
        f"{fecha_objetivo.strftime('%d/%m/%Y')}"
    )

    finales = []

    for resultado in resultados:

        fecha = extraer_fecha(
            resultado.get(
                "fecha",
                ""
            )
        )

        if fecha == fecha_objetivo:

            finales.append(
                resultado
            )

    return finales


# ==========================================================
# GUARDAR
# ==========================================================

def guardar_resultados(
    resultados
):

    if not resultados:

        raise RuntimeError(
            "No hay resultados para guardar."
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
        f"Resultados finales: "
        f"{len(resultados)}"
    )

    for resultado in resultados:

        print(
            f"  {resultado['tipo']} | "
            f"{resultado['fecha']} | "
            f"{resultado['numero']} | "
            f"{resultado.get('serie', '')}"
        )


# ==========================================================
# PROGRAMA PRINCIPAL
# ==========================================================

def main():

    print(
        "=========================================="
    )

    print(
        "   ACTUALIZADOR RESULTADOS ONCE"
    )

    print(
        "=========================================="
    )

    resultados_rss = (
        obtener_resultados_rss()
    )

    resultados_web = (
        obtener_cupones_oficiales()
    )

    todos = combinar_resultados(
        resultados_rss,
        resultados_web
    )

    if not todos:

        raise RuntimeError(
            "No se obtuvo ningún resultado."
        )

    resultados_finales = (
        filtrar_fecha_reciente(
            todos
        )
    )

    guardar_resultados(
        resultados_finales
    )


if __name__ == "__main__":
    main()