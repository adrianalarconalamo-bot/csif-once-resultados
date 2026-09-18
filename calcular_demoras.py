import json
from datetime import datetime, timedelta

RESULTADOS_FILE = "resultados.json"
SALIDA_FILE = "demoras_texto.txt"


# ============================================================
# ESTADO INICIAL DE LAS DEMORAS
# ============================================================
#
# Estos son los últimos días en los que apareció cada dígito
# según el listado facilitado por Adrián.
#
# PRIMERAS CIFRAS
# 0 -> 10/08/2026
# 7 -> 11/08/2026
# 2 -> 04/09/2026
# 1 -> 08/09/2026
# 6 -> 09/09/2026
# 9 -> 11/09/2026
# 5 -> 15/09/2026
# 3 -> 16/09/2026
# 8 -> 17/09/2026
# 4 -> 18/09/2026
#
# TERMINACIONES
# 1 -> 24/08/2026
# 6 -> 27/08/2026
# 0 -> 30/08/2026
# 7 -> 01/09/2026
# 4 -> 07/09/2026
# 5 -> 09/09/2026
# 9 -> 13/09/2026
# 3 -> 15/09/2026
# 8 -> 17/09/2026
# 2 -> 18/09/2026
#
# IMPORTANTE:
# La demora se calcula solamente con días de lunes a viernes.
# Sábado y domingo NO incrementan la demora.
# ============================================================


ULTIMA_PRIMERA_CIFRA = {
    "0": "10/08/2026",
    "7": "11/08/2026",
    "2": "04/09/2026",
    "1": "08/09/2026",
    "6": "09/09/2026",
    "9": "11/09/2026",
    "5": "15/09/2026",
    "3": "16/09/2026",
    "8": "17/09/2026",
    "4": "18/09/2026",
}


ULTIMA_TERMINACION = {
    "1": "24/08/2026",
    "6": "27/08/2026",
    "0": "30/08/2026",
    "7": "01/09/2026",
    "4": "07/09/2026",
    "5": "09/09/2026",
    "9": "13/09/2026",
    "3": "15/09/2026",
    "8": "17/09/2026",
    "2": "18/09/2026",
}


# ============================================================
# CONVERSIÓN DE FECHAS
# ============================================================

def convertir_fecha(fecha_texto):
    try:
        return datetime.strptime(
            fecha_texto,
            "%d/%m/%Y"
        ).date()
    except ValueError:
        return None


# ============================================================
# DÍAS LABORABLES
# ============================================================

def es_laborable(fecha):
    """
    Lunes = 0
    Martes = 1
    Miércoles = 2
    Jueves = 3
    Viernes = 4
    Sábado = 5
    Domingo = 6
    """
    return fecha.weekday() < 5


def contar_dias_laborables(fecha_inicio, fecha_fin):
    """
    Cuenta días de lunes a viernes desde el día siguiente
    a fecha_inicio hasta fecha_fin, ambos inclusive.

    Ejemplo:

    Salió el jueves 17.
    Viernes 18 = 1 día.
    Sábado 19 = no cuenta.
    Domingo 20 = no cuenta.
    Lunes 21 = 2 días.
    """

    if fecha_fin <= fecha_inicio:
        return 0

    dias = 0
    fecha = fecha_inicio + timedelta(days=1)

    while fecha <= fecha_fin:

        if es_laborable(fecha):
            dias += 1

        fecha += timedelta(days=1)

    return dias


# ============================================================
# FORMATO DE DÍAS
# ============================================================

def formato_dias(dias):
    """
    Formato solicitado:

    01 día
    02 días
    09 días
    30 días
    """

    if dias == 1:
        return "01 día"

    return f"{dias:02d} días"


# ============================================================
# CALCULAR DEMORAS
# ============================================================

def calcular_lista(ultimas_fechas, fecha_actual):

    resultado = []

    for digito, fecha_texto in ultimas_fechas.items():

        fecha_salida = convertir_fecha(fecha_texto)

        if fecha_salida is None:
            continue

        demora = contar_dias_laborables(
            fecha_salida,
            fecha_actual
        )

        resultado.append({
            "digito": digito,
            "fecha": fecha_salida,
            "demora": demora
        })

    # Orden cronológico:
    # primero el que lleva más tiempo esperando.
    resultado.sort(
        key=lambda x: (
            x["fecha"],
            int(x["digito"])
        )
    )

    return resultado


# ============================================================
# GENERAR TEXTO
# ============================================================

def generar_texto(fecha_actual):

    primeras = calcular_lista(
        ULTIMA_PRIMERA_CIFRA,
        fecha_actual
    )

    terminaciones = calcular_lista(
        ULTIMA_TERMINACION,
        fecha_actual
    )

    lineas = []

    # --------------------------------------------------------
    # CABECERA
    # --------------------------------------------------------

    lineas.append(
        fecha_actual.strftime("%d  %B  %Y")
        .replace("September", "Septiembre")
    )

    lineas.append("")

    # --------------------------------------------------------
    # PRIMERAS CIFRAS
    # --------------------------------------------------------

    lineas.append(
        "*Demora el reintegro  de las primeras cifras del cupón*"
    )

    lineas.append(
        "Sorteo  Lunes a Viernes"
    )

    lineas.append("")

    for dato in primeras:

        lineas.append(
            f"{dato['digito']} "
            f"{dato['fecha'].strftime('%d %b %y')}"
            f"  {formato_dias(dato['demora'])}"
        )

    lineas.append("")

    lineas.append(
        "Hola la primera cifra  solo se cuenta de lunes a viernes,"
    )

    lineas.append(
        "(_*el sábado y domingo no hay reintegro y esos días no se cuentan. )*"
    )

    lineas.append("")

    # --------------------------------------------------------
    # TERMINACIONES
    # --------------------------------------------------------

    lineas.append(
        "*Demora las terminaciones*"
    )

    lineas.append(
        "*del cupón*"
    )

    lineas.append("")

    for dato in terminaciones:

        lineas.append(
            f"{dato['digito']} "
            f"{dato['fecha'].strftime('%d %b %y')}"
            f"  {formato_dias(dato['demora'])}"
        )

    lineas.append("")

    # --------------------------------------------------------
    # PIE
    # --------------------------------------------------------

    lineas.append("CSIF ONCE")
    lineas.append("ESTAMOS POR TI")
    lineas.append("TEL: *652338627*")
    lineas.append("*Buenas noches*")

    return "\n".join(lineas)


# ============================================================
# FECHA DE TRABAJO
# ============================================================

def obtener_fecha_actual():

    try:
        with open(
            RESULTADOS_FILE,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(archivo)

    except Exception:
        datos = {}

    fechas = []

    for resultado in datos.get("resultados", []):

        fecha_texto = resultado.get("fecha", "")

        if not fecha_texto:
            continue

        try:

            # Ejemplo:
            # "Viernes, 18/09/2026"

            fecha_parte = fecha_texto.split(",")[-1].strip()

            fecha = convertir_fecha(fecha_parte)

            if fecha:
                fechas.append(fecha)

        except Exception:
            continue

    if fechas:
        return max(fechas)

    # Si no existe resultados.json o no contiene fechas,
    # utilizamos la fecha del sistema.
    return datetime.now().date()


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    fecha_actual = obtener_fecha_actual()

    texto = generar_texto(fecha_actual)

    with open(
        SALIDA_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(texto)

    print("")
    print("========================================")
    print("     DEMORAS CSIF ONCE")
    print("========================================")
    print("")
    print(texto)
    print("")
    print(
        f"Archivo generado: {SALIDA_FILE}"
    )


if __name__ == "__main__":
    main()