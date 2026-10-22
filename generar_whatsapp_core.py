import json
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests


# ============================================================
# CONFIGURACIÓN
# ============================================================

TZ = ZoneInfo("Europe/Madrid")

AHORA = datetime.now(TZ)
HOY = AHORA.strftime("%d/%m/%Y")
# 0=lunes … 6=domingo
DIA_SEMANA = AHORA.weekday()

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
    """Guarda un diccionario como JSON."""

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
    Selecciona los resultados de hoy.
    En madrugada (< 03:00) también acepta los de ayer,
    porque el cron llega hasta ~01:55 CEST.
    """

    ayer = (AHORA.date() - timedelta(days=1)).strftime("%d/%m/%Y")
    permitir_ayer = AHORA.hour < 3

    encontrados = []

    for resultado in resultados:

        fecha = limpiar(
            resultado.get("fecha", "")
        )

        if HOY in fecha:
            encontrados.append(resultado)
        elif permitir_ayer and ayer in fecha:
            encontrados.append(resultado)

    return encontrados


def formatear_dupla(valor):
    """
    Calcula premiado, anterior y posterior.
    Dupla utiliza números del 01 al 15.
    """

    valor = limpiar(valor)

    try:

        n = int(valor)

    except ValueError:

        return valor, "", ""

    if n < 1 or n > 15:

        return f"{n:02d}", "", ""

    anterior = n - 1 if n > 1 else 15
    posterior = n + 1 if n < 15 else 1

    return f"{n:02d}", f"{anterior:02d}", f"{posterior:02d}"


def formatear_bote(valor):
    """Formatea importebote numérico como 10.000.000 €."""
    texto = limpiar(valor).replace(".", "").replace(",", "").replace("€", "").strip()
    if not texto or texto == "0":
        return ""
    try:
        n = int(texto)
    except ValueError:
        return limpiar(valor)
    return f"{n:,}".replace(",", ".") + " €"


def separar_mi_dia(valor):
    """Separa fecha y número de la suerte de Mi Día."""

    valor = limpiar(valor)

    partes = valor.rsplit(" ", 1)

    if len(partes) == 2:

        return partes[0], partes[1]

    return valor, ""


# ============================================================
# CARGA DE RESULTADOS
# ============================================================

print("")
print("=" * 50)
print("   GENERAR / ENVIAR RESULTADOS ONCE (Telegram)")
print("=" * 50)
print("")
print(f"Fecha actual: {HOY}")
print(f"Hora actual:  {AHORA.strftime('%H:%M:%S')}")
print("")

datos = cargar_json(ARCHIVO_RESULTADOS)
resultados = datos.get("resultados", [])

resultados_hoy = obtener_resultados_hoy(resultados)

print(f"Resultados encontrados para {HOY}: {len(resultados_hoy)}")
print("")

if not resultados_hoy:

    print(
        f"NO hay resultados del {HOY} todavía"
        + (" ni de ayer (madrugada)." if AHORA.hour < 3 else ".")
    )

    print("No se genera ni se envía ningún mensaje.")

    sys.exit(0)

# Fecha real de los resultados (puede ser ayer si estamos en madrugada)
FECHA_RESULTADOS = HOY
for r in resultados_hoy:
    f = limpiar(r.get("fecha", ""))
    for candidate in (HOY, (AHORA.date() - timedelta(days=1)).strftime("%d/%m/%Y")):
        if candidate in f:
            FECHA_RESULTADOS = candidate
            break
    else:
        continue
    break
print(f"Fecha de los resultados a enviar: {FECHA_RESULTADOS}")

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

for r in resultados_hoy:

    tipo = limpiar(r.get("tipo", ""))

    if es_tipo(tipo, "Cupón Diario", "Cupon Diario"):
        cupon_diario = r
    elif es_tipo(tipo, "Cuponazo"):
        cuponazo = r
    elif es_tipo(tipo, "Sueldazo adicional"):
        sueldazo_adicionales.append(r)
    elif es_tipo(tipo, "Sueldazo"):
        sueldazo_principal = r
    elif es_tipo(tipo, "Mi Día", "Mi Dia"):
        mi_dia = r
    elif es_tipo(tipo, "Triplex"):
        triplex.append(r)
    elif es_tipo(tipo, "Dupla"):
        dupla.append(r)
    elif es_tipo(tipo, "Super 11", "Superonce", "Super Once"):
        super11.append(r)
    elif es_tipo(tipo, "Eurojackpot"):
        eurojackpot = r

triplex.sort(key=numero_sorteo)
dupla.sort(key=numero_sorteo)
super11.sort(key=numero_sorteo)

# ============================================================
# COMPROBAR COMPLETITUD (según día de la semana)
# Lun-Jue: Cupón Diario | Vie: Cuponazo | Sáb-Dom: Sueldazo
# ============================================================

faltan = []

# Día de la semana de la FECHA de resultados (no del reloj, por si es madrugada)
try:
    partes_f = FECHA_RESULTADOS.split("/")
    fecha_obj = datetime(
        int(partes_f[2]), int(partes_f[1]), int(partes_f[0]), tzinfo=TZ
    )
    dia_res = fecha_obj.weekday()
except Exception:
    dia_res = DIA_SEMANA

if dia_res <= 3:  # lun-jue
    if not cupon_diario:
        faltan.append("Cupón Diario")
elif dia_res == 4:  # viernes
    if not cuponazo:
        faltan.append("Cuponazo")
else:  # sáb-dom
    if not sueldazo_principal:
        faltan.append("Sueldazo")

# Mi Día / Triplex / Dupla / Super11 solo se exigen entre semana
if dia_res <= 4:
    if not mi_dia:
        faltan.append("Mi Día")
    if len(triplex) < 5:
        faltan.append(f"Triplex ({len(triplex)}/5)")
    if len(dupla) < 5:
        faltan.append(f"Dupla ({len(dupla)}/5)")
    if len(super11) < 5:
        faltan.append(f"Super 11 ({len(super11)}/5)")

# ============================================================
# NO ENVIAR ANTES DE LAS 21:30 (salvo madrugada)
# ============================================================

en_ventana_envio = (
    AHORA.hour > 21
    or (AHORA.hour == 21 and AHORA.minute >= 30)
    or AHORA.hour < 3
)

if not en_ventana_envio:

    print(f"[{AHORA.strftime('%H:%M')}] Todavía no son las 21:30.")
    print("No se envía el mensaje todavía.")

    if faltan:
        print("")
        print("Además, todavía faltan resultados:")
        for item in faltan:
            print(f"  - {item}")

    print("")
    sys.exit(0)

# ============================================================
# DESPUÉS DE LAS 21:30: NO ENVIAR SI FALTA ALGÚN RESULTADO
# ============================================================

if faltan:

    print("")
    print("==========================================")
    print(" RESULTADOS TODAVÍA INCOMPLETOS")
    print("==========================================")
    print("")
    print("Todavía faltan:")
    for item in faltan:
        print(f"  - {item}")
    print("")
    print("Se volverá a comprobar en la siguiente ejecución.")
    sys.exit(0)

# ============================================================
# COMPROBAR SI YA SE ENVIÓ
# ============================================================

try:
    estado_envio = cargar_json(ARCHIVO_ESTADO)
except SystemExit:
    estado_envio = {}

if (
    isinstance(estado_envio, dict)
    and estado_envio.get("fecha") == FECHA_RESULTADOS
):

    print(f"[{FECHA_RESULTADOS}] Los resultados ya fueron enviados.")
    print("No se vuelve a enviar.")
    sys.exit(0)

# ============================================================
# CONSTRUIR MENSAJE
# ============================================================

lineas = [
    "📢 CSIF INFORMA",
    "",
    "🎟️✨ RESULTADOS ONCE ✨",
    "",
    f"📅 {FECHA_RESULTADOS}",
    "",
    "━━━━━━━━━━━━━━━━━━",
]

if cupon_diario:
    lineas += [
        "",
        "🎫⭐ CUPÓN DIARIO",
        "",
        f"🔢 Número: {limpiar(cupon_diario.get('numero'))}",
        f"🔖 Serie: {limpiar(cupon_diario.get('serie'))}",
        "",
        "━━━━━━━━━━━━━━━━━━",
    ]

if cuponazo:
    lineas += [
        "",
        "🎫🔥 CUPONAZO",
        "",
        f"🔢 Número: {limpiar(cuponazo.get('numero'))}",
        f"🔖 Serie: {limpiar(cuponazo.get('serie'))}",
        "",
        "━━━━━━━━━━━━━━━━━━",
    ]

if sueldazo_principal:
    lineas += [
        "",
        "💰 SUELDAZO",
        "",
        f"🔢 Número: {limpiar(sueldazo_principal.get('numero'))}",
        f"🔖 Serie: {limpiar(sueldazo_principal.get('serie'))}",
        "",
        "━━━━━━━━━━━━━━━━━━",
    ]

if mi_dia:
    fecha_mi_dia, numero_suerte = separar_mi_dia(mi_dia.get("numero", ""))
    lineas += [
        "",
        "📅🍀 MI DÍA",
        "",
        f"📆 Fecha: {fecha_mi_dia}",
        "",
        f"🍀 Número de la suerte: {numero_suerte}",
        "",
        "━━━━━━━━━━━━━━━━━━",
    ]

if triplex:
    lineas += ["", "🔵🎯 TRIPLEX", ""]
    horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
    for i, r in enumerate(triplex, 1):
        hora = horas[i - 1] if i <= len(horas) else ""
        numero = limpiar(r.get("numero"))
        if hora:
            lineas.append(f"🕐 {hora} h · Sorteo {i} → {numero}")
        else:
            lineas.append(f"Sorteo {i} → {numero}")
        lineas.append("")
    lineas.append("━━━━━━━━━━━━━━━━━━")

if dupla:
    lineas += ["", "🟢🔄 DUPLA", "", "ℹ️ Números del 01 al 15", ""]
    horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
    for i, r in enumerate(dupla, 1):
        hora = horas[i - 1] if i <= len(horas) else ""
        premiado, ant, post = formatear_dupla(r.get("numero", ""))
        if hora:
            lineas.append(f"🕐 {hora} h · Sorteo {i}")
        else:
            lineas.append(f"Sorteo {i}")
        lineas.append(f"🏆 Premiado → {premiado}")
        if ant and post:
            lineas.append(f"⬅️ Anterior {ant}  ·  ➡️ Posterior {post}")
        lineas.append("")
    lineas.append("━━━━━━━━━━━━━━━━━━")

if super11:
    lineas += ["", "🔴🔥 SUPER 11", ""]
    horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
    for i, r in enumerate(super11, 1):
        hora = horas[i - 1] if i <= len(horas) else ""
        numero = limpiar(r.get("numero"))
        if hora:
            lineas.append(f"🕐 {hora} h · Sorteo {i}")
        else:
            lineas.append(f"Sorteo {i}")
        lineas.append(f"🔢 {numero}")
        lineas.append("")
    lineas.append("━━━━━━━━━━━━━━━━━━")

if eurojackpot:
    bote = formatear_bote(eurojackpot.get("importebote", ""))
    lineas += [
        "",
        "🇪🇺 EUROJACKPOT",
        "",
        f"🔢 {limpiar(eurojackpot.get('numero'))}",
        f"⭐ Estrellas: {limpiar(eurojackpot.get('serie'))}",
    ]
    if bote:
        lineas.append(f"💰 Bote: {bote}")
    lineas += [
        "",
        "━━━━━━━━━━━━━━━━━━",
    ]

lineas += [
    "",
    "🤝 CSIF ONCE",
    "ESTAMOS POR TI",
    "",
    "📞 TEL: 652338627",
    "",
    "🌙 Buenas noches.",
    "",
    "CSIF, todo por todos.",
]

mensaje = "\n".join(lineas)

# Guardar para WhatsApp
with open(ARCHIVO_WHATSAPP, "w", encoding="utf-8") as f:
    f.write(mensaje)

print(f"Mensaje generado: {len(mensaje)} caracteres")
print(f"Guardado en {ARCHIVO_WHATSAPP}")

# ============================================================
# ENVIAR A TELEGRAM
# ============================================================

if not TOKEN or not CHAT_ID:
    print("AVISO: faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID. No se envía.")
    sys.exit(0)

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
respuesta = requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": mensaje,
        "disable_web_page_preview": True,
    },
    timeout=30,
)

respuesta_json = {}
try:
    respuesta_json = respuesta.json()
except Exception:
    pass

if not respuesta.ok or not respuesta_json.get("ok"):
    print(f"ERROR Telegram: {respuesta.status_code} - {respuesta.text[:500]}")
    sys.exit(1)

resultado_tg = respuesta_json.get("result") or {}
msg_id = resultado_tg.get("message_id")
chat = resultado_tg.get("chat") or {}
print(
    f"Telegram OK → message_id={msg_id} chat_id={chat.get('id')} "
    f"tipo={chat.get('type')} titulo={chat.get('title') or chat.get('username') or chat.get('first_name')}"
)

guardar_json(
    ARCHIVO_ESTADO,
    {
        "fecha": FECHA_RESULTADOS,
        "hora": AHORA.strftime("%H:%M:%S"),
    },
)

print("")
print("==========================================")
print(" ✅ MENSAJE CSIF ENVIADO CORRECTAMENTE")
print("==========================================")
print("")
print(f"📅 Fecha: {FECHA_RESULTADOS}")
print(f"🕐 Hora: {AHORA.strftime('%H:%M:%S')}")
print("")
