import json
from datetime import datetime, date, timedelta

RESULTADOS_FILE = "resultados.json"
ESTADO_FILE = "demoras_estado.json"
SALIDA_FILE = "demoras_texto.txt"

ESTADO_INICIAL = {
    "ultima_fecha_procesada": "18/09/2026",
    "primeras": {
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


def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            estado = json.load(f)

        estado.setdefault("primeras", ESTADO_INICIAL["primeras"].copy())
        estado.setdefault(
            "terminaciones",
            ESTADO_INICIAL["terminaciones"].copy()
        )
        estado.setdefault(
            "ultima_fecha_procesada",
            ESTADO_INICIAL["ultima_fecha_procesada"]
        )

        return estado

    except (FileNotFoundError, json.JSONDecodeError):
        return json.loads(json.dumps(ESTADO_INICIAL))


def guardar_estado(estado):
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def fecha_desde_texto(texto):
    return datetime.strptime(texto, "%d/%m/%Y").date()


def contar_dias_laborables(fecha_inicio, fecha_fin):
    """
    Cuenta días transcurridos de lunes a viernes.
    El día de aparición cuenta como 00 días.
    """
    if fecha_inicio >= fecha_fin:
        return 0

    dias = 0
    actual = fecha_inicio + timedelta(days=1)

    while actual <= fecha_fin:
        if actual.weekday() < 5:
            dias += 1
        actual += timedelta(days=1)

    return dias


def contar_dias_naturales(fecha_inicio, fecha_fin):
    """
    Cuenta días transcurridos de lunes a domingo.
    El día de aparición cuenta como 00 días.
    """
    if fecha_inicio >= fecha_fin:
        return 0

    return (fecha_fin - fecha_inicio).days


def obtener_fecha_actual(resultados):
    """
    Obtiene la fecha del sorteo actual desde resultados.json.
    """
    hoy = date.today()

    for resultado in resultados:
        fecha_texto = str(resultado.get("fecha", ""))

        partes = fecha_texto.split(",")

        if len(partes) >= 2:
            posible_fecha = partes[1].strip()

            try:
                fecha = datetime.strptime(
                    posible_fecha,
                    "%d/%m/%Y"
                ).date()

                if fecha == hoy:
                    return fecha

            except ValueError:
                pass

    return hoy


def obtener_resultado_principal_del_dia(resultados, fecha_actual):
    """
    Entre semana:
        Cupón Diario / Cuponazo

    Fin de semana:
        Sueldazo principal

    Los Sueldazos adicionales NO se consideran.
    """

    fecha_objetivo = fecha_actual.strftime("%d/%m/%Y")

    if fecha_actual.weekday() < 5:
        tipos_validos = (
            "cupón diario",
            "cupon diario",
            "cuponazo"
        )
    else:
        tipos_validos = (
            "sueldazo",
        )

    for resultado in resultados:
        tipo = str(resultado.get("tipo", "")).strip().lower()
        fecha_texto = str(resultado.get("fecha", ""))

        if fecha_objetivo not in fecha_texto:
            continue

        if tipo in tipos_validos:
            numero = str(resultado.get("numero", "")).strip()

            if numero.isdigit():
                return numero, resultado.get("tipo", "")

    return None, None


def actualizar_estado(estado, numero, fecha_actual):
    """
    Aplica las reglas de demora:

    Lunes-Viernes:
        primera cifra -> se reinicia
        terminación -> se reinicia

    Sábado-Domingo:
        primera cifra -> NO se toca
        terminación -> se reinicia
    """

    if not numero or not numero.isdigit():
        return

    numero = numero.zfill(5)

    primera_cifra = numero[0]
    terminacion = numero[-1]

    fecha_texto = fecha_actual.strftime("%d/%m/%Y")

    es_laborable = fecha_actual.weekday() < 5

    # La terminación SIEMPRE se reinicia.
    estado["terminaciones"][terminacion] = fecha_texto

    # La primera cifra SOLO se reinicia de lunes a viernes.
    if es_laborable:
        estado["primeras"][primera_cifra] = fecha_texto


def generar_lista_primeras(estado, fecha_actual):
    lineas = []

    for numero in range(10):
        digito = str(numero)
        fecha_ultima = fecha_desde_texto(
            estado["primeras"][digito]
        )

        demora = contar_dias_laborables(
            fecha_ultima,
            fecha_actual
        )

        lineas.append(
            f"{digito}️⃣ {demora:02d} días"
        )

    return lineas


def generar_lista_terminaciones(estado, fecha_actual):
    lineas = []

    for numero in range(10):
        digito = str(numero)
        fecha_ultima = fecha_desde_texto(
            estado["terminaciones"][digito]
        )

        demora = contar_dias_naturales(
            fecha_ultima,
            fecha_actual
        )

        lineas.append(
            f"{digito}️⃣ {demora:02d} días"
        )

    return lineas


def generar_mensaje(estado, fecha_actual):
    fecha_texto = fecha_actual.strftime("%d/%m/%Y")

    lineas = [
        "📊 DEMORAS ONCE",
        "",
        f"📅 {fecha_texto}",
        "",
        "━━━━━━━━━━━━━━━━━━",
        "",
        "*Demora el reintegro de las primeras cifras del cupón*",
        "",
        "🎯 Sorteo  Lunes a Viernes",
        "",
        "La primera cifra solo se contabiliza de lunes a viernes.",
        "Los sábados y domingos no suman días ni reinician la primera cifra.",
        ""
    ]

    lineas.extend(generar_lista_primeras(estado, fecha_actual))

    lineas += [
        "",
        "━━━━━━━━━━━━━━━━━━",
        "",
        "*Demora las terminaciones del cupón*",
        "",
        "🎯 Sorteo  Lunes a Domingo",
        "",
        "La terminación se contabiliza todos los días.",
        "Los sábados y domingos también cuentan.",
        ""
    ]

    lineas.extend(
        generar_lista_terminaciones(
            estado,
            fecha_actual
        )
    )

    lineas += [
        "",
        "━━━━━━━━━━━━━━━━━━",
        "",
        "CSIF ONCE",
        "ESTAMOS POR TI",
        "TEL: *652338627*",
        "",
        "*Buenas noches*"
    ]

    return "\n".join(lineas)


def main():
    try:
        with open(RESULTADOS_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)

    except FileNotFoundError:
        raise SystemExit(
            "ERROR: no existe resultados.json"
        )

    resultados = datos.get("resultados", [])

    if not resultados:
        raise SystemExit(
            "ERROR: resultados.json está vacío."
        )

    estado = cargar_estado()

    fecha_actual = obtener_fecha_actual(resultados)

    numero, tipo = obtener_resultado_principal_del_dia(
        resultados,
        fecha_actual
    )

    if numero:
        actualizar_estado(
            estado,
            numero,
            fecha_actual
        )

        print(
            f"Resultado principal del día: "
            f"{numero} ({tipo})"
        )

        if fecha_actual.weekday() < 5:
            print(
                "Primera cifra actualizada: "
                f"{numero[0]}"
            )
        else:
            print(
                "Fin de semana: "
                "la primera cifra NO se actualiza."
            )

        print(
            "Terminación actualizada: "
            f"{numero[-1]}"
        )

    else:
        print(
            "AVISO: todavía no se ha encontrado "
            "el resultado principal del día."
        )

    estado["ultima_fecha_procesada"] = (
        fecha_actual.strftime("%d/%m/%Y")
    )

    guardar_estado(estado)

    mensaje = generar_mensaje(
        estado,
        fecha_actual
    )

    with open(
        SALIDA_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(mensaje)

    print(
        "demoras_texto.txt generado correctamente."
    )


if __name__ == "__main__":
    main()