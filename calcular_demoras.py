import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

RESULTADOS_FILE = "resultados.json"
ESTADO_FILE = "demoras_estado.json"
SALIDA_FILE = "demoras_texto.txt"

ZONA_HORARIA = ZoneInfo("Europe/Madrid")


# ============================================================
# ESTADO INICIAL
# ============================================================
#
# Estado conocido al 18/09/2026.
# A partir de aquí el programa continuará automáticamente.
# ============================================================

ESTADO_INICIAL = {
    "ultima_fecha_procesada": "18/09/2026",

    "primeras_cifras": {
        "0": "10/08/2026",
        "7": "11/08/2026",
        "2": "04/09/2026",
        "1": "08/09/2026",
        "6": "09/09/2026",
        "9": "11/09/2026",
        "5": "15/09/2026",
        "3": "16/09/2026",
        "8": "17/09/2026",
        "4": "18/09/2026"
    },

    "terminaciones": {
        "1": "24/08/2026",
        "6": "27/08/2026",
        "0": "30/08/2026",
        "7": "01/09/2026",
        "4": "07/09/2026",
        "5": "09/09/2026",
        "9": "13/09/2026",
        "3": "15/09/2026",
        "8": "17/09/2026",
        "2": "18/09/2026"
    }
}


# ============================================================
# FECHAS
# ============================================================

def convertir_fecha(texto):
    try:
        return datetime.strptime(
            texto,
            "%d/%m/%Y"
        ).date()
    except (ValueError, TypeError):
        return None


def fecha_hoy():
    """
    Fecha real de España.
    No utilizamos la fecha del servidor de GitHub directamente.
    """
    return datetime.now(ZONA_HORARIA).date()


def es_laborable(fecha):
    return fecha.weekday() < 5


def contar_dias_laborables(fecha_inicio, fecha_fin):
    """
    Cuenta únicamente lunes-viernes.

    El día de aparición NO cuenta.

    Ejemplo:
    Viernes 18 -> Sábado 19 = 0
    Viernes 18 -> Domingo 20 = 0
    Viernes 18 -> Lunes 21 = 1
    """

    if fecha_fin <= fecha_inicio:
        return 0

    contador = 0
    fecha = fecha_inicio + timedelta(days=1)

    while fecha <= fecha_fin:

        if es_laborable(fecha):
            contador += 1

        fecha += timedelta(days=1)

    return contador


# ============================================================
# CARGAR / GUARDAR ESTADO
# ============================================================

def cargar_estado():

    try:
        with open(
            ESTADO_FILE,
            "r",
            encoding="utf-8"
        ) as archivo:
            estado = json.load(archivo)

        return estado

    except (FileNotFoundError, json.JSONDecodeError):

        estado = ESTADO_INICIAL.copy()

        estado["primeras_cifras"] = (
            ESTADO_INICIAL["primeras_cifras"].copy()
        )

        estado["terminaciones"] = (
            ESTADO_INICIAL["terminaciones"].copy()
        )

        return estado


def guardar_estado(estado):

    with open(
        ESTADO_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            estado,
            archivo,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# BUSCAR RESULTADO DEL CUPÓN
# ============================================================

def obtener_numero_cupon(resultado):

    tipo = str(
        resultado.get("tipo", "")
    ).lower()

    numero = str(
        resultado.get("numero", "")
    ).strip()

    if not numero:
        return None

    # No utilizar Triplex, Dupla, Super 11, Mi Día, etc.
    tipos_validos = (
        "cupón diario",
        "cupon diario",
        "cuponazo",
    )

    if any(tipo_valido in tipo for tipo_valido in tipos_validos):

        # Nos quedamos solamente con las cifras.
        numero_limpio = "".join(
            caracter
            for caracter in numero
            if caracter.isdigit()
        )

        if numero_limpio:
            return numero_limpio

    return None


def obtener_cupon_del_dia(datos, fecha):

    for resultado in datos.get("resultados", []):

        fecha_texto = str(
            resultado.get("fecha", "")
        )

        try:
            fecha_resultado = convertir_fecha(
                fecha_texto.split(",")[-1].strip()
            )
        except Exception:
            continue

        if fecha_resultado != fecha:
            continue

        numero = obtener_numero_cupon(resultado)

        if numero:
            return numero

    return None


# ============================================================
# ACTUALIZAR ESTADO
# ============================================================

def actualizar_estado(estado, fecha_actual, numero_cupon):

    ultima_fecha = convertir_fecha(
        estado["ultima_fecha_procesada"]
    )

    if ultima_fecha is None:
        ultima_fecha = fecha_actual

    # --------------------------------------------------------
    # Si todavía no hemos avanzado de fecha
    # --------------------------------------------------------

    if fecha_actual <= ultima_fecha:

        return estado

    # --------------------------------------------------------
    # El estado avanza día a día.
    #
    # Esto hace que:
    #
    # Viernes -> sábado = 0
    # sábado -> domingo = 0
    # domingo -> lunes = 1
    #
    # --------------------------------------------------------

    for fecha in (
        ultima_fecha + timedelta(days=1)
        + timedelta(days=0),
    ):
        pass

    # --------------------------------------------------------
    # Si hoy hay nuevo número de cupón, actualizamos los
    # dígitos correspondientes.
    # --------------------------------------------------------

    if numero_cupon:

        primera_cifra = numero_cupon[0]
        terminacion = numero_cupon[-1]

        estado["primeras_cifras"][
            primera_cifra
        ] = fecha_actual.strftime("%d/%m/%Y")

        estado["terminaciones"][
            terminacion
        ] = fecha_actual.strftime("%d/%m/%Y")

        print(
            f"Nuevo cupón detectado: {numero_cupon}"
        )

        print(
            f"Primera cifra actualizada: {primera_cifra}"
        )

        print(
            f"Terminación actualizada: {terminacion}"
        )

    estado["ultima_fecha_procesada"] = (
        fecha_actual.strftime("%d/%m/%Y")
    )

    return estado


# ============================================================
# FORMATO
# ============================================================

MESES_CORTOS = {
    1: "Ene",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dic",
}


MESES_LARGOS = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def formato_fecha_corta(fecha):

    return (
        f"{fecha.day:02d} "
        f"{MESES_CORTOS[fecha.month]} "
        f"{str(fecha.year)[2:]}"
    )


def formato_dias(dias):

    if dias == 1:
        return "01 día"

    return f"{dias:02d} días"


# ============================================================
# GENERAR LISTA DE DEMORAS
# ============================================================

def calcular_lista(fechas, fecha_actual):

    lista = []

    for digito, fecha_texto in fechas.items():

        fecha_salida = convertir_fecha(fecha_texto)

        if fecha_salida is None:
            continue

        demora = contar_dias_laborables(
            fecha_salida,
            fecha_actual
        )

        lista.append({
            "digito": digito,
            "fecha": fecha_salida,
            "demora": demora
        })

    # Ordenamos por fecha de aparición:
    # del más antiguo al más reciente.
    lista.sort(
        key=lambda elemento: (
            elemento["fecha"],
            int(elemento["digito"])
        )
    )

    return lista


# ============================================================
# GENERAR TEXTO FINAL
# ============================================================

def generar_texto(estado, fecha_actual):

    primeras = calcular_lista(
        estado["primeras_cifras"],
        fecha_actual
    )

    terminaciones = calcular_lista(
        estado["terminaciones"],
        fecha_actual
    )

    lineas = []

    # --------------------------------------------------------
    # CABECERA
    # --------------------------------------------------------

    lineas.append(
        f"{fecha_actual.day}  "
        f"{MESES_LARGOS[fecha_actual.month]}  "
        f"{fecha_actual.year}"
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
            f"{formato_fecha_corta(dato['fecha'])}"
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
            f"{formato_fecha_corta(dato['fecha'])}"
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
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    fecha_actual = fecha_hoy()

    print(
        f"Fecha de España: "
        f"{fecha_actual.strftime('%d/%m/%Y')}"
    )

    # Cargar resultados
    try:

        with open(
            RESULTADOS_FILE,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(archivo)

    except (FileNotFoundError, json.JSONDecodeError):

        datos = {
            "resultados": []
        }

    # Cargar estado
    estado = cargar_estado()

    ultima_fecha = convertir_fecha(
        estado["ultima_fecha_procesada"]
    )

    # Buscar el cupón del día
    numero_cupon = obtener_cupon_del_dia(
        datos,
        fecha_actual
    )

    if numero_cupon:

        print(
            f"Cupón del día encontrado: {numero_cupon}"
        )

    else:

        print(
            "No hay nuevo cupón para esta fecha."
        )

    # Actualizar estado
    if ultima_fecha is None or fecha_actual > ultima_fecha:

        estado = actualizar_estado(
            estado,
            fecha_actual,
            numero_cupon
        )

        guardar_estado(estado)

    else:

        print(
            "La fecha ya estaba procesada. "
            "No se modifica el estado."
        )

    # Generar informe
    texto = generar_texto(
        estado,
        fecha_actual
    )

    with open(
        SALIDA_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(texto)

    print("")
    print("========================================")
    print("       CSIF ONCE - DEMORAS")
    print("========================================")
    print("")
    print(texto)


if __name__ == "__main__":
    main()