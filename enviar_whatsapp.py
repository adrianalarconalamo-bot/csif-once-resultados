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

# CallMeBot (WhatsApp)
APIKEY = os.getenv("CALLMEBOT_APIKEY")
PHONE = os.getenv("CALLMEBOT_PHONE")  # Ejemplo: +34685138060

ARCHIVO_RESULTADOS = "resultados.json"
ARCHIVO_WHATSAPP = "whatsapp.txt"
ARCHIVO_ESTADO = "whatsapp_enviado.json"


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
print(" GENERAR Y ENVIAR WHATSAPP CSIF ONCE (CallMeBot)")
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
# CONSTRUIR MENSAJE (~999 caracteres máx. para CallMeBot)
# ============================================================

lineas = [
    "📢 CSIF INFORMA · RESULTADOS ONCE",
    f"📅 {HOY}",
    "━━━━━━━━━━━━━━━━━━",
]

# ------------------------------------------------------------
# CUPÓN DIARIO
# ------------------------------------------------------------
if cupon_diario:
    numero = limpiar(cupon_diario.get("numero", "—"))
    serie = limpiar(cupon_diario.get("serie", ""))
    lineas.append("🎫 CUPÓN DIARIO")
    if serie:
        lineas.append(f"🔢 {numero} · Serie {serie}")
    else:
        lineas.append(f"🔢 {numero}")
    lineas.append("━━━━━━━━━━━━━━━━━━")

# ------------------------------------------------------------
# CUPONAZO
# ------------------------------------------------------------
if cuponazo:
    numero = limpiar(cuponazo.get("numero", "—"))
    serie = limpiar(cuponazo.get("serie", ""))
    lineas.append("🎟️ CUPONAZO")
    if serie:
        lineas.append(f"🔢 {numero} · Serie {serie}")
    else:
        lineas.append(f"🔢 {numero}")
    lineas.append("━━━━━━━━━━━━━━━━━━")

# ------------------------------------------------------------
# SUELDAZO
# ------------------------------------------------------------
if sueldazo_principal or sueldazo_adicionales:
    lineas.append("💰 SUELDAZO FIN DE SEMANA")
    if sueldazo_principal:
        numero = limpiar(sueldazo_principal.get("numero", "—"))
        serie = limpiar(sueldazo_principal.get("serie", ""))
        if serie:
            lineas.append(f"🏆 {numero} · Serie {serie}")
        else:
            lineas.append(f"🏆 {numero}")
    if sueldazo_adicionales:
        extras = []
        for resultado in sueldazo_adicionales:
            n = limpiar(resultado.get("numero", "—"))
            s = limpiar(resultado.get("serie", ""))
            extras.append(f"{n}/{s}" if s else n)
        lineas.append("🎁 " + " · ".join(extras))
    lineas.append("━━━━━━━━━━━━━━━━━━")

# ------------------------------------------------------------
# EUROJACKPOT
# ------------------------------------------------------------
if eurojackpot:
    numero = limpiar(eurojackpot.get("numero", "—"))
    serie = limpiar(eurojackpot.get("serie", ""))
    bote = limpiar(eurojackpot.get("importebote", ""))
    lineas.append("🇪🇺 EUROJACKPOT")
    linea_ej = f"🔢 {numero}"
    if serie:
        linea_ej += f" · ☀️ {serie}"
    if bote and bote not in ("", "0", "0.0", "1000000"):
        try:
            bote_num = int(float(bote))
            if bote_num >= 1_000_000:
                linea_ej += f" · 💰 {bote_num // 1_000_000}M€"
            else:
                linea_ej += f" · 💰 {bote}€"
        except ValueError:
            linea_ej += f" · 💰 {bote}€"
    lineas.append(linea_ej)
    lineas.append("━━━━━━━━━━━━━━━━━━")

# ------------------------------------------------------------
# MI DÍA
# ------------------------------------------------------------
if mi_dia:
    valor = limpiar(mi_dia.get("numero", "—"))
    fecha_mi_dia, numero_suerte = separar_mi_dia(valor)
    lineas.append(f"📅 MI DÍA · {fecha_mi_dia} · 🍀 {numero_suerte}")
    lineas.append("━━━━━━━━━━━━━━━━━━")

# ------------------------------------------------------------
# TRIPLEX
# ------------------------------------------------------------
if triplex:
    lineas.append("🔵 TRIPLEX")
    horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
    fila1 = []
    fila2 = []
    for i, resultado in enumerate(triplex):
        numero = limpiar(resultado.get("numero", "—"))
        hora = horas[i] if i < len(horas) else f"S{i+1}"
        item = f"{hora}→{numero}"
        if i < 3:
            fila1.append(item)
        else:
            fila2.append(item)
    if fila1:
        lineas.append(" · ".join(fila1))
    if fila2:
        lineas.append(" · ".join(fila2))
    lineas.append("━━━━━━━━━━━━━━━━━━")

# ------------------------------------------------------------
# DUPLA (con anterior y posterior)
# ------------------------------------------------------------
if dupla:
    lineas.append("🟢 DUPLA (01-15)")
    horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
    items = []
    for i, resultado in enumerate(dupla):
        premiado, ant, pos = formatear_dupla(resultado.get("numero", "—"))
        hora = horas[i] if i < len(horas) else f"S{i+1}"
        items.append(f"{hora}→{premiado} (a{ant}/p{pos})")
    for j in range(0, len(items), 2):
        grupo = items[j:j+2]
        lineas.append(" · ".join(grupo))
    lineas.append("━━━━━━━━━━━━━━━━━━")

# ------------------------------------------------------------
# SUPER 11
# ------------------------------------------------------------
if super11:
    lineas.append("🔴 SUPER 11")
    horas = ["10h", "12h", "14h", "17h", "21h"]
    for i, resultado in enumerate(super11):
        numero = limpiar(resultado.get("numero", "—"))
        numero = numero.replace(",", ",").strip()
        while "  " in numero:
            numero = numero.replace("  ", " ")
        hora = horas[i] if i < len(horas) else f"S{i+1}"
        lineas.append(f"{hora}: {numero}")
    lineas.append("━━━━━━━━━━━━━━━━━━")

# ------------------------------------------------------------
# PIE
# ------------------------------------------------------------
lineas += [
    "🤝 CSIF ONCE · ESTAMOS POR TI",
    "📞 TEL: 652338627 · 🌙 Buenas noches",
]

texto = "\n".join(lineas).strip()

# Recortar si supera 999 caracteres (CallMeBot)
if len(texto) > 999:
    texto = texto[:996] + "..."
    print(f"AVISO: mensaje recortado a 999 caracteres.")

print(f"Longitud mensaje: {len(texto)} caracteres")


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
print(f"Longitud: {len(texto)} caracteres")
print("")


# ============================================================
# COMPROBAR CREDENCIALES CALLMEBOT
# ============================================================

if not APIKEY or not PHONE:

    raise SystemExit(
        "ERROR: faltan CALLMEBOT_APIKEY "
        "o CALLMEBOT_PHONE"
    )


# ============================================================
# ENVIAR WHATSAPP (CallMeBot)
# ============================================================

import urllib.parse

texto_encoded = urllib.parse.quote(texto)

url = (
    "https://api.callmebot.com/whatsapp.php"
    f"?phone={PHONE}"
    f"&text={texto_encoded}"
    f"&apikey={APIKEY}"
)

print("")
print("Enviando mensaje por WhatsApp (CallMeBot)...")
print(f"Destino: {PHONE}")

try:

    respuesta = requests.get(
        url,
        timeout=30
    )

except requests.RequestException as e:

    raise SystemExit(
        f"ERROR conectando con CallMeBot: {e}"
    )


# ============================================================
# COMPROBAR RESPUESTA CALLMEBOT
# ============================================================

print(f"Respuesta HTTP: {respuesta.status_code}")
print(f"Cuerpo: {respuesta.text[:300]}")

if respuesta.status_code != 200:

    raise SystemExit(
        "ERROR CallMeBot: "
        f"{respuesta.status_code} - "
        f"{respuesta.text}"
    )

# CallMeBot suele devolver HTML con "Message queued" si va bien
cuerpo = respuesta.text.lower()
if "error" in cuerpo and "queued" not in cuerpo:

    raise SystemExit(
        "ERROR CallMeBot: "
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
        ),
        "metodo": "callmebot",
        "caracteres": len(texto),
    }

)


# ============================================================
# FIN
# ============================================================

print("")
print("==========================================")
print(" ✅ MENSAJE CSIF ENVIADO POR WHATSAPP")
print("==========================================")
print("")
print(
    f"📅 Fecha: {HOY}"
)
print(
    f"🕐 Hora: {AHORA.strftime('%H:%M:%S')}"
)
print(
    f"📱 Destino: {PHONE}"
)
print("")
