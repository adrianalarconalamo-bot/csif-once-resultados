import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


# ============================================================
# CONFIGURACIÓN
# ============================================================

TZ = ZoneInfo("Europe/Madrid")

AHORA = datetime.now(TZ)
HOY = AHORA.strftime("%d/%m/%Y")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ARCHIVO_RESULTADOS = "resultados.json"
ARCHIVO_WHATSAPP = "whatsapp.txt"
ARCHIVO_ESTADO = "telegram_enviado.json"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def limpiar(valor):
    """Convierte cualquier valor en texto limpio."""
    if valor is None:
        return ""

    return str(valor).strip()


def es_tipo(tipo, *nombres):
    """Comprueba si el tipo contiene alguno de los nombres."""
    tipo = limpiar(tipo).upper()

    return any(
        nombre.upper() in tipo
        for nombre in nombres
    )


def numero_sorteo(resultado):
    """
    Extrae el número de sorteo de textos como:
    'Lunes, 05/10/2026, Sorteo 3'
    """

    fecha = limpiar(resultado.get("fecha", ""))

    marcador = "SORTEO "

    posicion = fecha.upper().rfind(marcador)

    if posicion == -1:
        return 999

    valor = fecha[posicion + len(marcador):].strip()

    try:
        return int(valor)
    except ValueError:
        return 999


def cargar_json(ruta):
    """Carga un JSON y muestra un error claro si falla."""

    try:
        with open(
            ruta,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except FileNotFoundError:

        raise SystemExit(
            f"ERROR: no existe {ruta}"
        )

    except json.JSONDecodeError as e:

        raise SystemExit(
            f"ERROR: {ruta} contiene JSON inválido: {e}"
        )

    except Exception as e:

        raise SystemExit(
            f"ERROR leyendo {ruta}: {e}"
        )


def guardar_json(ruta, datos):
    """Guarda JSON con formato legible."""

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            datos,
            f,
            ensure_ascii=False,
            indent=2
        )


def obtener_resultados_hoy(resultados):
    """
    Selecciona exclusivamente los resultados cuya fecha
    contiene la fecha española actual.
    """

    encontrados = []

    for resultado in resultados:

        fecha = limpiar(
            resultado.get("fecha", "")
        )

        if HOY in fecha:

            encontrados.append(resultado)

    return encontrados


def formatear_dupla(valor):
    """
    Calcula premiado, anterior y posterior.
    Dupla utiliza números del 01 al 15.
    """

    valor = limpiar(valor)

    try:

        numero = int(valor)

    except ValueError:

        return valor, "—", "—"

    if not 1 <= numero <= 15:

        return valor, "—", "—"

    anterior = 15 if numero == 1 else numero - 1
    posterior = 1 if numero == 15 else numero + 1

    return (
        f"{numero:02d}",
        f"{anterior:02d}",
        f"{posterior:02d}"
    )


def separar_mi_dia(valor):
    """
    Convierte:

    04 SEP 1977 01

    en:

    04 SEP 1977
    01
    """

    valor = limpiar(valor)

    partes = valor.rsplit(" ", 1)

    if len(partes) == 2:

        return (
            partes[0].strip(),
            partes[1].strip()
        )

    return valor, "—"


# ============================================================
# CARGAR RESULTADOS
# ============================================================

datos = cargar_json(
    ARCHIVO_RESULTADOS
)

resultados = datos.get(
    "resultados",
    []
)

if not isinstance(resultados, list):

    raise SystemExit(
        "ERROR: 'resultados' no es una lista."
    )


if not resultados:

    print(
        "resultados.json todavía está vacío."
    )

    sys.exit(0)


print("")
print("==========================================")
print(" GENERAR WHATSAPP CSIF ONCE")
print("==========================================")
print(
    f"Fecha actual: {HOY}"
)
print(
    f"Hora actual:  {AHORA.strftime('%H:%M:%S')}"
)
print("")


# ============================================================
# SELECCIONAR ÚNICAMENTE LOS RESULTADOS DE HOY
# ============================================================

resultados_hoy = obtener_resultados_hoy(
    resultados
)

print(
    f"Resultados encontrados para {HOY}: "
    f"{len(resultados_hoy)}"
)
print("")


if not resultados_hoy:

    print(
        f"NO hay resultados del {HOY} todavía."
    )

    print(
        "No se genera ni se envía ningún WhatsApp."
    )

    sys.exit(0)


# ============================================================
# CLASIFICACIÓN
# ============================================================

cupon_diario = None
cuponazo = None

sueldazo_principal = None
sueldazo_adicionales = []

mi_dia = None

triplex = []
dupla = []
super11 = []

eurojackpot = None


for resultado in resultados_hoy:

    tipo = limpiar(
        resultado.get("tipo", "")
    )

    if es_tipo(
        tipo,
        "CUPÓN DIARIO",
        "CUPON DIARIO"
    ):

        cupon_diario = resultado


    elif es_tipo(
        tipo,
        "CUPONAZO"
    ):

        cuponazo = resultado


    elif es_tipo(
        tipo,
        "SUELDAZO ADICIONAL"
    ):

        sueldazo_adicionales.append(
            resultado
        )


    elif es_tipo(
        tipo,
        "SUELDAZO"
    ):

        sueldazo_principal = resultado


    elif es_tipo(
        tipo,
        "MI DÍA",
        "MI DIA"
    ):

        mi_dia = resultado


    elif es_tipo(
        tipo,
        "TRIPLEX"
    ):

        triplex.append(
            resultado
        )


    elif es_tipo(
        tipo,
        "DUPLA"
    ):

        dupla.append(
            resultado
        )


    elif es_tipo(
        tipo,
        "SUPER 11",
        "SUPERONCE"
    ):

        super11.append(
            resultado
        )


    elif es_tipo(
        tipo,
        "EUROJACKPOT"
    ):

        eurojackpot = resultado


# ============================================================
# ORDENAR SORTEOS
# ============================================================

triplex.sort(
    key=numero_sorteo
)

dupla.sort(
    key=numero_sorteo
)

super11.sort(
    key=numero_sorteo
)

sueldazo_adicionales.sort(
    key=lambda r: (
        limpiar(r.get("numero", "")),
        limpiar(r.get("serie", ""))
    )
)


# ============================================================
# DÍA DE LA SEMANA
# ============================================================

DIA_SEMANA = AHORA.weekday()

# 0 lunes
# 1 martes
# 2 miércoles
# 3 jueves
# 4 viernes
# 5 sábado
# 6 domingo


# ============================================================
# COMPROBAR RESULTADOS COMPLETOS
# ============================================================

faltan = []


# ------------------------------------------------------------
# TRIPLEX
# ------------------------------------------------------------

if len(triplex) < 5:

    faltan.append(
        f"Triplex ({len(triplex)}/5)"
    )


# ------------------------------------------------------------
# DUPLA
# ------------------------------------------------------------

if len(dupla) < 5:

    faltan.append(
        f"Dupla ({len(dupla)}/5)"
    )


# ------------------------------------------------------------
# SUPER 11
# ------------------------------------------------------------

if len(super11) < 5:

    faltan.append(
        f"Super 11 ({len(super11)}/5)"
    )


# ------------------------------------------------------------
# MI DÍA
# ------------------------------------------------------------

if mi_dia is None:

    faltan.append(
        "Mi Día"
    )


# ------------------------------------------------------------
# LUNES A JUEVES
# ------------------------------------------------------------

if DIA_SEMANA <= 3:

    if cupon_diario is None:

        faltan.append(
            "Cupón Diario"
        )


# ------------------------------------------------------------
# VIERNES
# ------------------------------------------------------------

if DIA_SEMANA == 4:

    if cuponazo is None:

        faltan.append(
            "Cuponazo"
        )


# ------------------------------------------------------------
# EUROJACKPOT
# MARTES Y VIERNES
# ------------------------------------------------------------

if DIA_SEMANA in (1, 4):

    if eurojackpot is None:

        faltan.append(
            "Eurojackpot"
        )


# ------------------------------------------------------------
# SÁBADO Y DOMINGO
# ------------------------------------------------------------

if DIA_SEMANA in (5, 6):

    if sueldazo_principal is None:

        faltan.append(
            "Sueldazo principal"
        )

    if len(sueldazo_adicionales) < 4:

        faltan.append(
            "Sueldazo adicionales "
            f"({len(sueldazo_adicionales)}/4)"
        )


# ============================================================
# NO ENVIAR ANTES DE LAS 21:30
# ============================================================

if AHORA.hour < 21 or (
    AHORA.hour == 21
    and AHORA.minute < 30
):

    print(
        f"[{AHORA.strftime('%H:%M')}] "
        "Todavía no son las 21:30."
    )

    print(
        "No se envía el mensaje todavía."
    )

    if faltan:

        print("")
        print(
            "Además, todavía faltan resultados:"
        )

        for item in faltan:

            print(
                f"  - {item}"
            )

    print("")

    sys.exit(0)


# ============================================================
# DESPUÉS DE LAS 21:30:
# NO ENVIAR SI FALTA ALGÚN RESULTADO
# ============================================================

if faltan:

    print("")
    print("==========================================")
    print(" RESULTADOS TODAVÍA INCOMPLETOS")
    print("==========================================")
    print("")

    print(
        "Todavía faltan:"
    )

    for item in faltan:

        print(
            f"  - {item}"
        )

    print("")

    print(
        "Se volverá a comprobar en la siguiente ejecución."
    )

    sys.exit(0)


# ============================================================
# COMPROBAR SI YA SE ENVIÓ HOY
# ============================================================

try:

    estado_envio = cargar_json(
        ARCHIVO_ESTADO
    )

except SystemExit:

    estado_envio = {}


if (
    isinstance(estado_envio, dict)
    and estado_envio.get("fecha") == HOY
):

    print(
        f"[{HOY}] Los resultados ya fueron enviados hoy."
    )

    print(
        "No se vuelve a enviar."
    )

    sys.exit(0)


# ============================================================
# CONSTRUIR MENSAJE
# ============================================================

lineas = [

    "📢 CSIF INFORMA",

    "",

    "🎟️✨ RESULTADOS ONCE ✨",

    "",

    f"📅 {HOY}",

    "",

    "━━━━━━━━━━━━━━━━━━",

    ""

]


# ============================================================
# CUPÓN DIARIO
# ============================================================

if cupon_diario:

    numero = limpiar(
        cupon_diario.get("numero", "—")
    )

    serie = limpiar(
        cupon_diario.get("serie", "")
    )

    lineas += [

        "🎫⭐ CUPÓN DIARIO",

        "",

        f"🔢 Número: {numero}"

    ]

    if serie:

        lineas.append(
            f"🔖 Serie: {serie}"
        )

    lineas += [

        "",

        "━━━━━━━━━━━━━━━━━━",

        ""

    ]


# ============================================================
# CUPONAZO
# ============================================================

if cuponazo:

    numero = limpiar(
        cuponazo.get("numero", "—")
    )

    serie = limpiar(
        cuponazo.get("serie", "")
    )

    lineas += [

        "🎟️💥 CUPONAZO",

        "",

        f"🔢 Número: {numero}"

    ]

    if serie:

        lineas.append(
            f"🔖 Serie: {serie}"
        )

    lineas += [

        "",

        "━━━━━━━━━━━━━━━━━━",

        ""

    ]


# ============================================================
# SUELDAZO
# ============================================================

if (
    sueldazo_principal
    or sueldazo_adicionales
):

    lineas += [

        "💰🌟 SUELDAZO FIN DE SEMANA",

        ""

    ]

    if sueldazo_principal:

        numero = limpiar(
            sueldazo_principal.get(
                "numero",
                "—"
            )
        )

        serie = limpiar(
            sueldazo_principal.get(
                "serie",
                ""
            )
        )

        lineas += [

            "🏆 PREMIO PRINCIPAL",

            "",

            f"🔢 Número: {numero}"

        ]

        if serie:

            lineas.append(
                f"🔖 Serie: {serie}"
            )

        lineas += [

            "",

            "💶 2.000 € al mes durante 10 años",

            ""

        ]


    if sueldazo_adicionales:

        lineas += [

            "🎁 PREMIOS ADICIONALES",

            ""

        ]

        for resultado in sueldazo_adicionales:

            numero = limpiar(
                resultado.get(
                    "numero",
                    "—"
                )
            )

            serie = limpiar(
                resultado.get(
                    "serie",
                    ""
                )
            )

            if serie:

                lineas.append(
                    f"🎁 {numero} — Serie {serie}"
                )

            else:

                lineas.append(
                    f"🎁 {numero}"
                )

        lineas += [

            "",

            "━━━━━━━━━━━━━━━━━━",

            ""

        ]


# ============================================================
# EUROJACKPOT
# ============================================================

if eurojackpot:

    numero = limpiar(
        eurojackpot.get(
            "numero",
            "—"
        )
    )

    serie = limpiar(
        eurojackpot.get(
            "serie",
            ""
        )
    )

    lineas += [

        "🇪🇺💎 EUROJACKPOT",

        "",

        f"🔢 Números: {numero}"

    ]

    if serie:

        lineas.append(
            f"☀️ Soles: {serie}"
        )

    bote = limpiar(
        eurojackpot.get(
            "importebote",
            ""
        )
    )

    if bote not in (
        "",
        "0",
        "0.0",
        "1000000"
    ):

        lineas.append(
            f"💰 Bote: {bote} €"
        )

    lineas += [

        "",

        "━━━━━━━━━━━━━━━━━━",

        ""

    ]


# ============================================================
# MI DÍA
# ============================================================

if mi_dia:

    valor = limpiar(
        mi_dia.get(
            "numero",
            "—"
        )
    )

    fecha_mi_dia, numero_suerte = separar_mi_dia(
        valor
    )

    lineas += [

        "📅🍀 MI DÍA",

        "",

        f"📆 Fecha: {fecha_mi_dia}",

        "",

        f"🍀 Número de la suerte: {numero_suerte}",

        "",

        "━━━━━━━━━━━━━━━━━━",

        ""

    ]


# ============================================================
# TRIPLEX
# ============================================================

if triplex:

    lineas += [

        "🔵🎯 TRIPLEX",

        ""

    ]

    for i, resultado in enumerate(
        triplex,
        1
    ):

        numero = limpiar(
            resultado.get(
                "numero",
                "—"
            )
        )

        horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
        hora = horas[i - 1] if i <= len(horas) else ""
        if hora:
            lineas.append(
                f"🕐 {hora} h · Sorteo {i} → {numero}"
            )
        else:
            lineas.append(
                f"🎲 Sorteo {i}: {numero}"
            )

        lineas.append("")

    lineas += [

        "━━━━━━━━━━━━━━━━━━",

        ""

    ]


# ============================================================
# DUPLA
# ============================================================

if dupla:

    lineas += [

        "🟢🔄 DUPLA",

        "",

        "ℹ️ Números del 01 al 15",

        ""

    ]

    for i, resultado in enumerate(
        dupla,
        1
    ):

        premiado, anterior, posterior = formatear_dupla(
            resultado.get(
                "numero",
                "—"
            )
        )

        horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
        hora = horas[i - 1] if i <= len(horas) else ""
        if hora:
            lineas.append(
                f"🕐 {hora} h · Sorteo {i}"
            )
        else:
            lineas.append(
                f"🎲 Sorteo {i}"
            )
        lineas += [
            f"🏆 Premiado → {premiado}",
            f"⬅️ Anterior {anterior}  ·  ➡️ Posterior {posterior}",
            ""
        ]

    lineas += [

        "━━━━━━━━━━━━━━━━━━",

        ""

    ]


# ============================================================
# SUPER 11
# ============================================================

if super11:

    lineas += [

        "🔴🔥 SUPER 11",

        ""

    ]

    for i, resultado in enumerate(
        super11,
        1
    ):

        numero = limpiar(
            resultado.get(
                "numero",
                "—"
            )
        )

        horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
        hora = horas[i - 1] if i <= len(horas) else ""
        if hora:
            lineas.append(
                f"🕐 {hora} h · Sorteo {i}"
            )
        else:
            lineas.append(
                f"🎲 Sorteo {i}"
            )
        lineas += [
            f"🔢 {numero}",
            ""
        ]

    # IMPORTANTE:
    # No mostramos importebote.
    # Así nunca aparecerá el 1000000.

    lineas += [

        "━━━━━━━━━━━━━━━━━━",

        ""

    ]


# ============================================================
# PIE DEL MENSAJE
# ============================================================

lineas += [

    "🤝 CSIF ONCE",

    "ESTAMOS POR TI",

    "",

    "📞 TEL: 652338627",

    "",

    "🌙 Buenas noches.",

    "",

    "CSIF, todo por todos."

]


texto = "\n".join(
    lineas
).strip()


# ============================================================
# GUARDAR WHATSAPP.TXT
# ============================================================

try:

    with open(
        ARCHIVO_WHATSAPP,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(texto)

except Exception as e:

    raise SystemExit(
        f"ERROR guardando {ARCHIVO_WHATSAPP}: {e}"
    )


print("")
print("==========================================")
print(" MENSAJE GENERADO CORRECTAMENTE")
print("==========================================")
print("")
print(texto)
print("")


# ============================================================
# COMPROBAR CREDENCIALES TELEGRAM
# ============================================================

if not TOKEN or not CHAT_ID:

    raise SystemExit(
        "ERROR: faltan TELEGRAM_BOT_TOKEN "
        "o TELEGRAM_CHAT_ID"
    )


# ============================================================
# ENVIAR TELEGRAM
# ============================================================

url = (
    "https://api.telegram.org/"
    f"bot{TOKEN}/sendMessage"
)


try:

    respuesta = requests.post(

        url,

        json={

            "chat_id": CHAT_ID,

            "text": texto,

            "disable_web_page_preview": True

        },

        timeout=20

    )

except requests.RequestException as e:

    raise SystemExit(
        f"ERROR conectando con Telegram: {e}"
    )


# ============================================================
# COMPROBAR RESPUESTA TELEGRAM
# ============================================================

if not respuesta.ok:

    raise SystemExit(
        "ERROR Telegram: "
        f"{respuesta.status_code} - "
        f"{respuesta.text}"
    )


try:

    respuesta_json = respuesta.json()

except ValueError:

    raise SystemExit(
        "ERROR: Telegram devolvió una respuesta "
        "que no es JSON."
    )


if not respuesta_json.get("ok"):

    raise SystemExit(
        "ERROR Telegram: "
        f"{respuesta.text}"
    )


# ============================================================
# MARCAR COMO ENVIADO
# ============================================================

guardar_json(

    ARCHIVO_ESTADO,

    {

        "fecha": HOY,

        "hora": AHORA.strftime(
            "%H:%M:%S"
        )

    }

)


# ============================================================
# FIN
# ============================================================

print("")
print("==========================================")
print(" ✅ MENSAJE CSIF ENVIADO CORRECTAMENTE")
print("==========================================")
print("")
print(
    f"📅 Fecha: {HOY}"
)
print(
    f"🕐 Hora: {AHORA.strftime('%H:%M:%S')}"
)
print("")