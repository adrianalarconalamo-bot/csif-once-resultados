import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ============================================================
# CONFIGURACIÓN
# ============================================================

HISTORIAL_FILE = "historial_cupones.json"
SALIDA_FILE = "demoras_texto.txt"
RESULTADOS_FILE = "resultados.json"

ZONA_HORARIA = ZoneInfo("Europe/Madrid")


# ============================================================
# MEMORIA INICIAL FACILITADA POR ADRIÁN
#
# Esta es la memoria EXACTA desde la que debe continuar
# el cálculo.
#
# La memoria corresponde al informe del:
# 18 de septiembre de 2026
#
# Los últimos sorteos utilizados son del:
# 17 de septiembre de 2026
# ============================================================

MEMORIA_INICIAL = {
    "fecha_base": "17/09/2026",
    "ultima_actualizacion": "17/09/2026",

    "memoria_demoras": {

        "primeras": {
            "0": {
                "fecha": "10/08/2026",
                "dias": 29
            },
            "7": {
                "fecha": "11/08/2026",
                "dias": 28
            },
            "2": {
                "fecha": "04/09/2026",
                "dias": 10
            },
            "1": {
                "fecha": "08/09/2026",
                "dias": 8
            },
            "6": {
                "fecha": "09/09/2026",
                "dias": 7
            },
            "9": {
                "fecha": "11/09/2026",
                "dias": 5
            },
            "4": {
                "fecha": "14/09/2026",
                "dias": 4
            },
            "5": {
                "fecha": "15/09/2026",
                "dias": 3
            },
            "3": {
                "fecha": "16/09/2026",
                "dias": 2
            },
            "8": {
                "fecha": "17/09/2026",
                "dias": 1
            }
        },

        "terminaciones": {
            "1": {
                "fecha": "24/08/2026",
                "dias": 25
            },
            "6": {
                "fecha": "27/08/2026",
                "dias": 22
            },
            "0": {
                "fecha": "30/08/2026",
                "dias": 19
            },
            "2": {
                "fecha": "31/08/2026",
                "dias": 18
            },
            "7": {
                "fecha": "01/09/2026",
                "dias": 17
            },
            "4": {
                "fecha": "07/09/2026",
                "dias": 11
            },
            "5": {
                "fecha": "09/09/2026",
                "dias": 9
            },
            "9": {
                "fecha": "13/09/2026",
                "dias": 5
            },
            "3": {
                "fecha": "15/09/2026",
                "dias": 3
            },
            "8": {
                "fecha": "17/09/2026",
                "dias": 1
            }
        }
    }
}


MESES = {
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
    12: "Dic"
}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def cargar_memoria():
    """
    Carga la memoria persistente.

    Si no existe historial_cupones.json, utiliza EXACTAMENTE
    la memoria inicial facilitada por el usuario.
    """

    if not os.path.exists(HISTORIAL_FILE):
        print("No existe historial. Utilizando memoria inicial.")
        return copiar_memoria_inicial()

    try:
        with open(
            HISTORIAL_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            datos = json.load(f)

        # Comprobamos que tenga la estructura esperada.
        if (
            "ultima_actualizacion" not in datos
            or "memoria_demoras" not in datos
        ):
            print(
                "Historial existente con estructura antigua."
            )
            print("Utilizando memoria inicial.")
            return copiar_memoria_inicial()

        print(
            "Memoria cargada desde",
            HISTORIAL_FILE
        )

        return datos

    except Exception as e:
        print(
            "Error leyendo historial:",
            e
        )
        print("Utilizando memoria inicial.")
        return copiar_memoria_inicial()


def copiar_memoria_inicial():
    """
    Devuelve una copia independiente de la memoria inicial.
    """

    return json.loads(
        json.dumps(
            MEMORIA_INICIAL,
            ensure_ascii=False
        )
    )


def guardar_memoria(memoria):
    """
    Guarda la memoria para que el siguiente día continúe
    exactamente desde donde quedó.
    """

    with open(
        HISTORIAL_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            memoria,
            f,
            ensure_ascii=False,
            indent=2
        )


def parsear_fecha(texto):
    """
    Convierte DD/MM/YYYY a datetime.
    """

    return datetime.strptime(
        texto,
        "%d/%m/%Y"
    ).date()


def fecha_texto(fecha):
    """
    Formato:
    10 Ago 26
    """

    return (
        f"{fecha.day:02d} "
        f"{MESES[fecha.month]} "
        f"{str(fecha.year)[2:]}"
    )


def dias_singular_plural(numero):
    if numero == 1:
        return "día"

    return "días"


# ============================================================
# OBTENER CUPÓN DEL DÍA
# ============================================================

def obtener_cupon_de_fecha(fecha):
    """
    Busca en resultados.json el Cupón Diario correspondiente
    a una fecha concreta.

    Devuelve el número como texto de 5 cifras.

    Si no existe, devuelve None.
    """

    if not os.path.exists(RESULTADOS_FILE):
        print(
            "No existe",
            RESULTADOS_FILE
        )
        return None

    try:
        with open(
            RESULTADOS_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            datos = json.load(f)

    except Exception as e:
        print(
            "Error leyendo resultados.json:",
            e
        )
        return None

    resultados = datos.get(
        "resultados",
        []
    )

    fecha_objetivo = fecha.strftime(
        "%d/%m/%Y"
    )

    fecha_objetivo_alt = fecha.strftime(
        "%Y-%m-%d"
    )

    for resultado in resultados:

        tipo = str(
            resultado.get("tipo", "")
        ).lower()

        if "cupón diario" not in tipo:
            continue

        fecha_resultado = str(
            resultado.get("fecha", "")
        ).strip()

        coincide = (
            fecha_resultado == fecha_objetivo
            or fecha_resultado == fecha_objetivo_alt
        )

        if not coincide:
            continue

        numero = resultado.get(
            "numero"
        )

        if numero is None:
            continue

        numero = str(numero).strip()

        # Dejamos siempre cinco cifras.
        if numero.isdigit():
            numero = numero.zfill(5)

        if len(numero) == 5:
            return numero

    return None


# ============================================================
# AVANZAR UN DÍA
# ============================================================

def avanzar_un_dia(
    memoria,
    fecha
):
    """
    Avanza la memoria exactamente un día.

    PRIMERAS CIFRAS:
        Solo cuentan lunes a viernes.

    TERMINACIONES:
        Cuentan todos los días.

    IMPORTANTE:
        Primero se incrementan los contadores.
        Después se comprueba si el Cupón Diario de ese día
        contiene una cifra.

        Si aparece:
            contador = 0
            fecha = fecha de hoy
    """

    primeras = memoria[
        "memoria_demoras"
    ][
        "primeras"
    ]

    terminaciones = memoria[
        "memoria_demoras"
    ][
        "terminaciones"
    ]

    # --------------------------------------------------------
    # 1. PRIMERAS CIFRAS
    # --------------------------------------------------------

    # Monday = 0
    # Tuesday = 1
    # ...
    # Sunday = 6

    es_dia_laborable = fecha.weekday() < 5

    if es_dia_laborable:

        for cifra in primeras:

            primeras[cifra]["dias"] += 1

    # --------------------------------------------------------
    # 2. TERMINACIONES
    # --------------------------------------------------------

    for cifra in terminaciones:

        terminaciones[cifra]["dias"] += 1

    # --------------------------------------------------------
    # 3. BUSCAR CUPÓN DEL DÍA
    # --------------------------------------------------------

    cupon = obtener_cupon_de_fecha(
        fecha
    )

    if cupon:
        print(
            f"{fecha_texto(fecha)} "
            f"- Cupón Diario encontrado: "
            f"{cupon}"
        )

        primera = cupon[0]
        ultima = cupon[-1]

        # ----------------------------------------------------
        # PRIMERA CIFRA
        # ----------------------------------------------------

        if primera in primeras:

            primeras[primera]["dias"] = 0
            primeras[primera]["fecha"] = (
                fecha.strftime("%d/%m/%Y")
            )

            print(
                f"  Primera cifra {primera}: "
                f"RESET A 0"
            )

        # ----------------------------------------------------
        # TERMINACIÓN
        # ----------------------------------------------------

        if ultima in terminaciones:

            terminaciones[ultima]["dias"] = 0
            terminaciones[ultima]["fecha"] = (
                fecha.strftime("%d/%m/%Y")
            )

            print(
                f"  Terminación {ultima}: "
                f"RESET A 0"
            )

    else:

        print(
            f"{fecha_texto(fecha)} "
            f"- No hay Cupón Diario disponible."
        )


# ============================================================
# AVANZAR DESDE LA ÚLTIMA FECHA GUARDADA
# ============================================================

def actualizar_memoria(
    memoria,
    fecha_actual
):
    """
    Avanza desde la última fecha procesada hasta hoy.

    Esto evita que una ejecución repetida del workflow
    vuelva a sumar el mismo día.
    """

    ultima = parsear_fecha(
        memoria["ultima_actualizacion"]
    )

    if fecha_actual <= ultima:

        print(
            "La fecha actual",
            fecha_actual,
            "ya está procesada."
        )

        return

    fecha = ultima + timedelta(
        days=1
    )

    while fecha <= fecha_actual:

        print(
            "\nProcesando:",
            fecha_texto(fecha)
        )

        avanzar_un_dia(
            memoria,
            fecha
        )

        memoria[
            "ultima_actualizacion"
        ] = fecha.strftime(
            "%d/%m/%Y"
        )

        fecha += timedelta(
            days=1
        )


# ============================================================
# ORDENAR RESULTADOS
# ============================================================

def ordenar_demoras(datos):
    """
    Ordena de mayor a menor demora.
    """

    return sorted(
        datos.items(),
        key=lambda elemento: (
            -elemento[1]["dias"],
            elemento[0]
        )
    )


# ============================================================
# GENERAR TEXTO
# ============================================================

def generar_texto(
    memoria,
    fecha_informe
):
    """
    Genera el texto que posteriormente enviará Telegram.
    """

    primeras = memoria[
        "memoria_demoras"
    ][
        "primeras"
    ]

    terminaciones = memoria[
        "memoria_demoras"
    ][
        "terminaciones"
    ]

    primeras_ordenadas = ordenar_demoras(
        primeras
    )

    terminaciones_ordenadas = ordenar_demoras(
        terminaciones
    )

    # --------------------------------------------------------
    # CABECERA
    # --------------------------------------------------------

    meses_completos = {
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
        12: "Diciembre"
    }

    cabecera = (
        f"{fecha_informe.day} "
        f"{meses_completos[fecha_informe.month]} "
        f"{fecha_informe.year}"
    )

    lineas = []

    lineas.append(cabecera)
    lineas.append("")

    # --------------------------------------------------------
    # PRIMERAS CIFRAS
    # --------------------------------------------------------

    lineas.append(
        "*Demora el reintegro de las primeras cifras del cupón*"
    )

    lineas.append(
        "Sorteo Lunes a Viernes"
    )

    lineas.append("")

    for cifra, datos in primeras_ordenadas:

        dias = datos["dias"]
        fecha = parsear_fecha(
            datos["fecha"]
        )

        lineas.append(
            f"{cifra}  "
            f"{fecha_texto(fecha)}  "
            f"{dias:02d} "
            f"{dias_singular_plural(dias)}"
        )

    lineas.append("")

    lineas.append(
        "Hola la primera cifra solo se cuenta de lunes a viernes,"
    )

    lineas.append(
        "(_*el sábado y domingo no hay reintegro y esos días no se cuentan._)"
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

    for cifra, datos in terminaciones_ordenadas:

        dias = datos["dias"]
        fecha = parsear_fecha(
            datos["fecha"]
        )

        lineas.append(
            f"{cifra}  "
            f"{fecha_texto(fecha)}  "
            f"{dias:02d} "
            f"{dias_singular_plural(dias)}"
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

    print("=" * 60)
    print("CALCULAR DEMORAS ONCE")
    print("=" * 60)

    ahora = datetime.now(
        ZONA_HORARIA
    )

    fecha_actual = ahora.date()

    print(
        "Fecha/hora España:",
        ahora.strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )

    # --------------------------------------------------------
    # CARGAR MEMORIA
    # --------------------------------------------------------

    memoria = cargar_memoria()

    print(
        "Última actualización de memoria:",
        memoria["ultima_actualizacion"]
    )

    # --------------------------------------------------------
    # ACTUALIZAR MEMORIA
    # --------------------------------------------------------

    actualizar_memoria(
        memoria,
        fecha_actual
    )

    # --------------------------------------------------------
    # GUARDAR MEMORIA
    # --------------------------------------------------------

    guardar_memoria(
        memoria
    )

    print(
        "\nMemoria guardada correctamente."
    )

    # --------------------------------------------------------
    # EL INFORME ES PARA EL DÍA SIGUIENTE
    # --------------------------------------------------------

    fecha_informe = (
        fecha_actual
        + timedelta(days=1)
    )

    # --------------------------------------------------------
    # GENERAR TEXTO
    # --------------------------------------------------------

    texto = generar_texto(
        memoria,
        fecha_informe
    )

    with open(
        SALIDA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(texto)

    print(
        "\nArchivo generado:",
        SALIDA_FILE
    )

    print("\n" + "=" * 60)
    print(texto)
    print("=" * 60)


if __name__ == "__main__":
    main()