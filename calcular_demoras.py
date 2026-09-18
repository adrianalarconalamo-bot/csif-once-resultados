import json
from datetime import datetime, timedelta

RESULTADOS_FILE = "resultados.json"
SALIDA_FILE = "demoras_texto.txt"

# Estado conocido al 17/09/2026.
# Formato: dígito -> días de demora acumulados.
DEMORAS_INICIALES = {
    "0": 29,
    "1": 0,
    "2": 0,
    "3": 0,
    "4": 0,
    "5": 0,
    "6": 0,
    "7": 28,
    "8": 0,
    "9": 0,
}


def es_laborable(fecha):
    """Cuenta solamente lunes a viernes."""
    return fecha.weekday() < 5


def siguiente_dia_laborable(fecha):
    fecha += timedelta(days=1)

    while not es_laborable(fecha):
        fecha += timedelta(days=1)

    return fecha


def extraer_numero(resultado):
    numero = str(resultado.get("numero", "")).strip()

    # Elimina espacios y caracteres innecesarios.
    numero = "".join(c for c in numero if c.isdigit())

    return numero


def afecta_demora(numero, digito):
    """
    Un dígito reinicia su contador si aparece:
    - en la primera cifra
    - o en la terminación del número
    """

    if not numero:
        return False

    primera_cifra = numero[0]
    terminacion = numero[-1]

    return (
        digito == primera_cifra
        or digito == terminacion
    )


def obtener_fecha_resultados(datos):
    fechas = []

    for resultado in datos.get("resultados", []):
        fecha_texto = resultado.get("fecha", "")

        try:
            parte = fecha_texto.split(",")[-1].strip()
            fecha = datetime.strptime(parte, "%d/%m/%Y").date()
            fechas.append(fecha)
        except Exception:
            continue

    if not fechas:
        return datetime.now().date()

    return max(fechas)


def calcular_demoras(datos):
    fecha_actual = obtener_fecha_resultados(datos)

    # Copia independiente del estado inicial.
    demoras = dict(DEMORAS_INICIALES)

    # Resultados del día actual.
    resultados_hoy = []

    for resultado in datos.get("resultados", []):
        fecha_texto = resultado.get("fecha", "")

        try:
            parte = fecha_texto.split(",")[-1].strip()
            fecha = datetime.strptime(
                parte,
                "%d/%m/%Y"
            ).date()
        except Exception:
            continue

        if fecha == fecha_actual:
            resultados_hoy.append(resultado)

    # Primero comprobamos qué dígitos han salido hoy.
    reiniciados = set()

    for resultado in resultados_hoy:
        numero = extraer_numero(resultado)

        if not numero:
            continue

        for digito in "0123456789":
            if afecta_demora(numero, digito):
                reiniciados.add(digito)

    # Los dígitos que han salido en primera cifra o terminación
    # vuelven a 0.
    for digito in reiniciados:
        demoras[digito] = 0

    # Los demás continúan acumulando un día laborable.
    for digito in "0123456789":
        if digito not in reiniciados:
            demoras[digito] += 1

    return fecha_actual, demoras, reiniciados


def generar_texto(fecha, demoras):
    fecha_formateada = fecha.strftime("%d/%m/%Y")

    lineas = []

    lineas.append("📊 CSIF ONCE")
    lineas.append("DEMORAS")
    lineas.append("")
    lineas.append(f"📅 {fecha_formateada}")
    lineas.append("")

    # Ordenamos de mayor a menor demora.
    ordenados = sorted(
        demoras.items(),
        key=lambda x: (-x[1], int(x[0]))
    )

    for digito, dias in ordenados:
        lineas.append(
            f"🔢 {digito} → {dias} días"
        )

    lineas.append("")
    lineas.append("CSIF ONCE")
    lineas.append("ESTAMOS POR TI")
    lineas.append("TEL: 652338627")
    lineas.append("Buenas noches")

    return "\n".join(lineas)


def main():
    try:
        with open(
            RESULTADOS_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            datos = json.load(f)

    except FileNotFoundError:
        raise SystemExit(
            "ERROR: no existe resultados.json"
        )

    fecha, demoras, reiniciados = calcular_demoras(datos)

    texto = generar_texto(fecha, demoras)

    with open(
        SALIDA_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(texto)

    print(texto)

    print("")
    print(
        "Dígitos reiniciados:",
        ", ".join(sorted(reiniciados))
        if reiniciados
        else "ninguno"
    )


if __name__ == "__main__":
    main()