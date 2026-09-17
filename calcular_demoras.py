import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


HISTORIAL_FILE = "historial_cupones.json"
RESULTADOS_FILE = "resultados.json"
OUTPUT_DEMORAS = "demoras_texto.txt"

TELEFONO = "652338627"


def cargar_json(path):
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def es_laborable(fecha):
    return fecha.weekday() < 5


def obtener_cupon_hoy():
    datos = cargar_json(RESULTADOS_FILE)

    for resultado in datos.get("resultados", []):

        tipo = str(resultado.get("tipo", "")).upper()

        if "CUPÓN" in tipo or "CUPON" in tipo:

            numero = str(
                resultado.get("numero", "")
            )

            digitos = "".join(
                c for c in numero if c.isdigit()
            )

            if len(digitos) == 5:
                return digitos

    return None


def actualizar_historial(cupon, fecha):
    historial = cargar_json(HISTORIAL_FILE)

    if not isinstance(historial, dict):
        historial = {}

    historial[fecha] = cupon

    with open(
        HISTORIAL_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            historial,
            f,
            ensure_ascii=False,
            indent=2
        )

    return historial


def convertir_fecha(fecha_texto):
    """
    Convierte fechas del historial a objetos date.
    Admite:
    DD/MM/YYYY
    D/M/YYYY
    """

    for formato in (
        "%d/%m/%Y",
        "%-d/%-m/%Y"
    ):

        try:
            return datetime.strptime(
                fecha_texto,
                formato
            ).date()
        except Exception:
            pass

    # Método alternativo compatible con cualquier sistema
    try:
        partes = fecha_texto.split("/")

        if len(partes) == 3:

            dia = int(partes[0])
            mes = int(partes[1])
            año = int(partes[2])

            return datetime(
                año,
                mes,
                dia
            ).date()

    except Exception:
        pass

    return None


def obtener_ultima_fecha_de_cifra(
    historial,
    posicion,
    cifra
):
    """
    Busca la última fecha en la que apareció
    una determinada cifra en una posición concreta.
    """

    ultima_fecha = None

    for fecha_texto, numero in historial.items():

        fecha = convertir_fecha(fecha_texto)

        if fecha is None:
            continue

        digitos = "".join(
            c for c in str(numero)
            if c.isdigit()
        )

        if len(digitos) != 5:
            continue

        try:
            cifra_en_posicion = int(
                digitos[posicion]
            )
        except Exception:
            continue

        if cifra_en_posicion != cifra:
            continue

        if (
            ultima_fecha is None
            or fecha > ultima_fecha
        ):
            ultima_fecha = fecha

    return ultima_fecha


def calcular_dias_laborables(
    fecha_inicio,
    fecha_fin
):
    """
    Cuenta días de lunes a viernes,
    incluyendo la fecha inicial y final.
    """

    dias = 0
    fecha = fecha_inicio

    while fecha <= fecha_fin:

        if es_laborable(fecha):
            dias += 1

        fecha += timedelta(days=1)

    return dias


def calcular_dias_naturales(
    fecha_inicio,
    fecha_fin
):
    """
    Cuenta días naturales incluyendo
    fecha inicial y final.
    """

    return (
        fecha_fin - fecha_inicio
    ).days + 1


def nombre_mes_abreviado(fecha):
    meses = [
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic"
    ]

    return (
        f"{fecha.day:02d} "
        f"{meses[fecha.month - 1]} "
        f"{str(fecha.year)[2:]}"
    )


def calcular_demoras_primera_cifra(
    historial,
    fecha_fin
):
    resultados = []

    for cifra in range(10):

        ultima_fecha = (
            obtener_ultima_fecha_de_cifra(
                historial,
                0,
                cifra
            )
        )

        if ultima_fecha is None:

            resultados.append(
                (
                    cifra,
                    None,
                    0
                )
            )

            continue

        dias = calcular_dias_laborables(
            ultima_fecha,
            fecha_fin
        )

        resultados.append(
            (
                cifra,
                ultima_fecha,
                dias
            )
        )

    # De mayor a menor demora
    resultados.sort(
        key=lambda x: x[2],
        reverse=True
    )

    return resultados


def calcular_demoras_terminaciones(
    historial,
    fecha_fin
):
    resultados = []

    for cifra in range(10):

        ultima_fecha = (
            obtener_ultima_fecha_de_cifra(
                historial,
                4,
                cifra
            )
        )

        if ultima_fecha is None:

            resultados.append(
                (
                    cifra,
                    None,
                    0
                )
            )

            continue

        dias = calcular_dias_naturales(
            ultima_fecha,
            fecha_fin
        )

        resultados.append(
            (
                cifra,
                ultima_fecha,
                dias
            )
        )

    # De mayor a menor demora
    resultados.sort(
        key=lambda x: x[2],
        reverse=True
    )

    return resultados


def generar_reporte_demoras():

    ahora = datetime.now(
        ZoneInfo("Europe/Madrid")
    )

    fecha_hoy = ahora.date()

    fecha_hoy_texto = ahora.strftime(
        "%d/%m/%Y"
    )

    cupon_hoy = obtener_cupon_hoy()

    historial = cargar_json(
        HISTORIAL_FILE
    )

    if not isinstance(historial, dict):
        historial = {}

    if cupon_hoy:

        print(
            f"✅ Cupón de hoy "
            f"{fecha_hoy_texto}: "
            f"{cupon_hoy}"
        )

        historial = actualizar_historial(
            cupon_hoy,
            fecha_hoy_texto
        )

    else:

        print(
            "⚠️ No se ha encontrado "
            "el cupón de hoy."
        )

    # -------------------------------------------------
    # MUY IMPORTANTE
    #
    # El informe de mañana cuenta desde HOY.
    # Por ejemplo:
    #
    # 17 Sep -> 1 día
    # 16 Sep -> 2 días
    #
    # Por tanto, para generar el informe del
    # 18 de septiembre utilizamos el 17 de septiembre
    # como fecha final.
    # -------------------------------------------------

    fecha_fin = fecha_hoy - timedelta(days=1)

    demoras_primera = (
        calcular_demoras_primera_cifra(
            historial,
            fecha_fin
        )
    )

    demoras_terminaciones = (
        calcular_demoras_terminaciones(
            historial,
            fecha_fin
        )
    )

    # -------------------------------------------------
    # CABECERA
    # -------------------------------------------------

    fecha_titulo = fecha_hoy

    meses_completos = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre"
    ]

    lineas = []

    lineas.append(
        f"{fecha_titulo.day}  "
        f"{meses_completos[fecha_titulo.month - 1]}  "
        f"{fecha_titulo.year}"
    )

    lineas.append("")

    lineas.append(
        "*Demora el reintegro  de las primeras cifras del cupón*"
    )

    lineas.append(
        "Sorteo  Lunes a Viernes"
    )

    lineas.append("")

    # -------------------------------------------------
    # PRIMERAS CIFRAS
    # -------------------------------------------------

    for cifra, fecha, dias in demoras_primera:

        if fecha is None:
            continue

        if dias == 1:
            texto_dias = "01  día"
        else:
            texto_dias = f"{dias:02d} días"

        lineas.append(
            f"{cifra} "
            f"{nombre_mes_abreviado(fecha)}  "
            f"{texto_dias}"
        )

    lineas.append("")

    lineas.append(
        " Hola la primera cifra  solo se cuenta de lunes a viernes,"
    )

    lineas.append(
        " (_*el sábado y domingo no hay reintegro y esos días no se cuentan. )*"
    )

    lineas.append("")

    # -------------------------------------------------
    # TERMINACIONES
    # -------------------------------------------------

    lineas.append(
        "*Demora las terminaciones*"
    )

    lineas.append(
        "*del cupón*"
    )

    lineas.append("")

    for cifra, fecha, dias in demoras_terminaciones:

        if fecha is None:
            continue

        if dias == 1:
            texto_dias = "01 día"
        else:
            texto_dias = f"{dias:02d} días"

        lineas.append(
            f"{cifra} "
            f"{nombre_mes_abreviado(fecha)}  "
            f"{texto_dias}"
        )

    lineas.append("")

    # -------------------------------------------------
    # PIE
    # -------------------------------------------------

    lineas.append(
        "CSIF ONCE"
    )

    lineas.append(
        "ESTAMOS POR TI"
    )

    lineas.append(
        "TEL: *652338627*"
    )

    lineas.append(
        "*Buenas noches*"
    )

    texto_final = "\n".join(
        lineas
    )

    with open(
        OUTPUT_DEMORAS,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(texto_final)

    print(
        "✅ Informe de demoras generado correctamente."
    )


if __name__ == "__main__":
    generar_reporte_demoras()