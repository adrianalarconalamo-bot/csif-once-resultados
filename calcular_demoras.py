import json
from datetime import datetime, date, timedelta

RESULTADOS_FILE = "resultados.json"
ESTADO_FILE = "demoras_estado.json"
SALIDA_FILE = "demoras_texto.txt"


# ============================================================
# ESTADO INICIAL
# Último estado conocido al finalizar el 18/09/2026
# ============================================================

ESTADO_INICIAL = {
    "ultima_fecha_procesada": "18/09/2026",

    "primeras": {
        "0": "10/08/2026",
        "1": "08/09/2026",
        "2": "04/09/2026",
        "3": "16/09/2026",
        "4": "18/09/2026",
        "5": "15/09/2026",
        "6": "09/09/2026",
        "7": "11/08/2026",
        "8": "17/09/2026",
        "9": "11/09/2026"
    },

    "terminaciones": {
        "0": "30/08/2026",
        "1": "24/08/2026",
        "2": "18/09/2026",
        "3": "15/09/2026",
        "4": "07/09/2026",
        "5": "09/09/2026",
        "6": "27/08/2026",
        "7": "19/09/2026",
        "8": "17/09/2026",
        "9": "13/09/2026"
    }
}


# ============================================================
# CARGAR / GUARDAR ESTADO
# ============================================================

def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as archivo:
            estado = json.load(archivo)

        estado.setdefault(
            "ultima_fecha_procesada",
            ESTADO_INICIAL["ultima_fecha_procesada"]
        )

        estado.setdefault(
            "primeras",
            ESTADO_INICIAL["primeras"].copy()
        )

        estado.setdefault(
            "terminaciones",
            ESTADO_INICIAL["terminaciones"].copy()
        )

        return estado

    except (FileNotFoundError, json.JSONDecodeError):
        return json.loads(json.dumps(ESTADO_INICIAL))


def guardar_estado(estado):
    with open(ESTADO_FILE, "w", encoding="utf-8") as archivo:
        json.dump(
            estado,
            archivo,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# FECHAS
# ============================================================

def convertir_fecha(texto):
    return datetime.strptime(texto, "%d/%m/%Y").date()


def extraer_fecha(resultado):
    """
    Extrae la fecha desde el campo 'fecha' de resultados.json.
    Admite formatos del tipo:

    'Cupón Diario, 19/09/2026'
    '19/09/2026'
    """

    texto = str(resultado.get("fecha", "")).strip()

    partes = texto.replace("-", "/").split(",")

    candidatos = []

    for parte in partes:
        parte = parte.strip()

        try:
            fecha = datetime.strptime(
                parte,
                "%d/%m/%Y"
            ).date()

            candidatos.append(fecha)

        except ValueError:
            continue

    if candidatos:
        return max(candidatos)

    return None


def obtener_fecha_actual(resultados):
    """
    Utiliza la fecha más reciente disponible en resultados.json.
    """

    fechas = []

    for resultado in resultados:
        fecha = extraer_fecha(resultado)

        if fecha:
            fechas.append(fecha)

    if not fechas:
        return date.today()

    return max(fechas)


# ============================================================
# RESULTADO PRINCIPAL
# ============================================================

def obtener_resultado_principal(resultados, fecha_actual):
    """
    Entre semana:
        Cupón Diario / Cuponazo

    Fin de semana:
        Sueldazo

    Se da prioridad al Cuponazo cuando existe.
    """

    candidatos = []

    for resultado in resultados:

        fecha = extraer_fecha(resultado)

        if fecha != fecha_actual:
            continue

        tipo = str(
            resultado.get("tipo", "")
        ).strip().lower()

        numero = str(
            resultado.get("numero", "")
        ).strip()

        if not numero.isdigit():
            continue

        # Viernes: Cuponazo
        if tipo in (
            "cuponazo",
            "cuponazo fin de semana"
        ):
            candidatos.append(
                (3, numero, resultado.get("tipo", ""))
            )

        # Lunes a viernes: Cupón
        elif tipo in (
            "cupón diario",
            "cupon diario",
            "cupón",
            "cupon"
        ):
            candidatos.append(
                (2, numero, resultado.get("tipo", ""))
            )

        # Sábado y domingo: Sueldazo
        elif tipo in (
            "sueldazo",
            "sueldazo fin de semana"
        ):
            candidatos.append(
                (1, numero, resultado.get("tipo", ""))
            )

    if not candidatos:
        return None, None

    candidatos.sort(
        key=lambda elemento: elemento[0],
        reverse=True
    )

    _, numero, tipo = candidatos[0]

    return numero.zfill(5), tipo


# ============================================================
# ACTUALIZAR ESTADO
# ============================================================

def actualizar_estado(
    estado,
    numero,
    fecha_actual
):
    """
    Actualiza:

    - Primera cifra: SOLO lunes-viernes.
    - Terminación: TODOS los días.

    Una fecha ya procesada nunca vuelve a modificar el estado.
    """

    fecha_texto = fecha_actual.strftime("%d/%m/%Y")

    ultima_fecha = estado.get(
        "ultima_fecha_procesada"
    )

    # Evita duplicar un mismo sorteo si GitHub Actions
    # ejecuta el programa varias veces.
    if ultima_fecha == fecha_texto:
        print(
            f"La fecha {fecha_texto} ya estaba procesada. "
            "No se modifica el estado."
        )
        return False

    numero = str(numero).zfill(5)

    primera = numero[0]
    terminacion = numero[-1]

    # --------------------------------------------------------
    # TERMINACIÓN
    # Se actualiza TODOS los días.
    # --------------------------------------------------------

    estado["terminaciones"][terminacion] = fecha_texto

    print(
        f"Terminación {terminacion} actualizada: "
        f"{fecha_texto}"
    )

    # --------------------------------------------------------
    # PRIMERA CIFRA
    # Solo lunes-viernes.
    # --------------------------------------------------------

    if fecha_actual.weekday() < 5:

        estado["primeras"][primera] = fecha_texto

        print(
            f"Primera cifra {primera} actualizada: "
            f"{fecha_texto}"
        )

    else:

        print(
            "Fin de semana: "
            "la primera cifra NO se actualiza."
        )

    # Solo marcamos la fecha como procesada cuando
    # realmente hemos aplicado un resultado.
    estado["ultima_fecha_procesada"] = fecha_texto

    return True


# ============================================================
# CÁLCULO PRIMERAS CIFRAS
# ============================================================

def contar_dias_primeras(
    fecha_salida,
    fecha_actual
):
    """
    Primera cifra:

    - Solo lunes-viernes.
    - El día de salida NO se cuenta.
    - Se cuentan los días laborables posteriores
      hasta la fecha actual.
    """

    if fecha_salida >= fecha_actual:
        return 0

    contador = 0
    fecha = fecha_salida + timedelta(days=1)

    while fecha <= fecha_actual:

        if fecha.weekday() < 5:
            contador += 1

        fecha += timedelta(days=1)

    return contador


# ============================================================
# CÁLCULO TERMINACIONES
# ============================================================

def contar_dias_terminaciones(
    fecha_salida,
    fecha_actual
):
    """
    Terminaciones:

    - Se cuentan todos los días naturales.
    - Lunes a domingo.
    - El día de salida NO se cuenta.
    """

    if fecha_salida >= fecha_actual:
        return 0

    return (
        fecha_actual - fecha_salida
    ).days


# ============================================================
# GENERAR PRIMERAS CIFRAS
# ============================================================

def generar_primeras(
    estado,
    fecha_actual
):
    lineas = []

    for numero in range(10):

        digito = str(numero)

        fecha_salida = convertir_fecha(
            estado["primeras"][digito]
        )

        demora = contar_dias_primeras(
            fecha_salida,
            fecha_actual
        )

        palabra = "día" if demora == 1 else "días"

        lineas.append(
            f"{digito} {estado['primeras'][digito]} "
            f"{demora:02d} {palabra}"
        )

    return lineas


# ============================================================
# GENERAR TERMINACIONES
# ============================================================

def generar_terminaciones(
    estado,
    fecha_actual
):
    lineas = []

    for numero in range(10):

        digito = str(numero)

        fecha_salida = convertir_fecha(
            estado["terminaciones"][digito]
        )

        demora = contar_dias_terminaciones(
            fecha_salida,
            fecha_actual
        )

        palabra = "día" if demora == 1 else "días"

        lineas.append(
            f"{digito} {estado['terminaciones'][digito]} "
            f"{demora:02d} {palabra}"
        )

    return lineas


# ============================================================
# GENERAR MENSAJE
# ============================================================

def generar_mensaje(
    estado,
    fecha_actual
):

    fecha_texto = fecha_actual.strftime(
        "%d/%m/%Y"
    )

    lineas = [

        f"{fecha_texto}",

        "",

        "*Demora el reintegro de las primeras cifras del cupón*",

        "Sorteo  Lunes a Viernes",

        ""
    ]

    lineas.extend(
        generar_primeras(
            estado,
            fecha_actual
        )
    )

    lineas.extend([

        "",

        "Hola la primera cifra solo se cuenta de lunes a viernes,",

        "(_*el sábado y domingo no hay reintegro y esos días no se cuentan. )*_",

        "",

        "*Demora las terminaciones*",

        "*del cupón*",

        ""
    ])

    lineas.extend(
        generar_terminaciones(
            estado,
            fecha_actual
        )
    )

    lineas.extend([

        "",

        "CSIF ONCE",

        "ESTAMOS POR TI",

        "TEL: *652338627*",

        "*Buenas noches *"
    ])

    return "\n".join(lineas)


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Cargar resultados
    # --------------------------------------------------------

    try:

        with open(
            RESULTADOS_FILE,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(archivo)

    except FileNotFoundError:

        raise SystemExit(
            "ERROR: no existe resultados.json"
        )

    resultados = datos.get(
        "resultados",
        []
    )

    if not resultados:

        raise SystemExit(
            "ERROR: resultados.json está vacío."
        )

    # --------------------------------------------------------
    # Cargar estado
    # --------------------------------------------------------

    estado = cargar_estado()

    # --------------------------------------------------------
    # Determinar fecha actual
    # --------------------------------------------------------

    fecha_actual = obtener_fecha_actual(
        resultados
    )

    print(
        f"Fecha de trabajo: "
        f"{fecha_actual.strftime('%d/%m/%Y')}"
    )

    # --------------------------------------------------------
    # Buscar resultado principal
    # --------------------------------------------------------

    numero, tipo = obtener_resultado_principal(
        resultados,
        fecha_actual
    )

    if numero:

        print(
            f"Resultado principal: "
            f"{numero} ({tipo})"
        )

        actualizar_estado(
            estado,
            numero,
            fecha_actual
        )

    else:

        print(
            "AVISO: todavía no existe "
            "el resultado principal del día."
        )

        print(
            "El estado NO se modifica."
        )

    # --------------------------------------------------------
    # Guardar estado
    # --------------------------------------------------------

    guardar_estado(estado)

    # --------------------------------------------------------
    # Generar texto
    # --------------------------------------------------------

    mensaje = generar_mensaje(
        estado,
        fecha_actual
    )

    with open(
        SALIDA_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(mensaje)

    print(
        "demoras_texto.txt generado correctamente."
    )


if __name__ == "__main__":
    main()