import json
import os
import requests


# =========================
# CONFIGURACIÓN TELEGRAM
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


if not TOKEN or not CHAT_ID:
    raise SystemExit(
        "ERROR: faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID"
    )


# =========================
# CARGAR RESULTADOS
# =========================

with open(
    "resultados.json",
    "r",
    encoding="utf-8"
) as f:
    datos = json.load(f)


resultados = datos.get("resultados", [])


if not resultados:
    raise SystemExit(
        "ERROR: resultados.json está vacío."
    )


# =========================
# AGRUPAR RESULTADOS
# =========================

cupon_diario = None
cuponazo = None

sueldazo = []

mi_dia = None

triplex = []
dupla = []
super11 = []

eurojackpot = None


for r in resultados:

    tipo = str(
        r.get("tipo", "")
    ).upper().strip()


    # CUPÓN DIARIO
    if "CUPÓN DIARIO" in tipo or "CUPON DIARIO" in tipo:
        cupon_diario = r


    # CUPONAZO
    elif "CUPONAZO" in tipo or "CUPONAZO" in tipo:
        cuponazo = r


    # SUELDAZO
    elif "SUELDAZO" in tipo:
        sueldazo.append(r)


    # MI DÍA
    elif "MI DÍA" in tipo or "MI DIA" in tipo:
        mi_dia = r


    # TRIPLEX
    elif "TRIPLEX" in tipo:
        triplex.append(r)


    # DUPLA
    elif "DUPLA" in tipo:
        dupla.append(r)


    # SUPER 11
    elif "SUPER 11" in tipo or "SUPERONCE" in tipo:
        super11.append(r)


    # EUROJACKPOT
    elif "EUROJACKPOT" in tipo:
        eurojackpot = r


# =========================
# FECHA
# =========================

fecha = resultados[0].get(
    "fecha",
    ""
)


# =========================
# CREAR MENSAJE
# =========================

lineas = []

lineas.append("📢 CSIF INFORMA")
lineas.append("")
lineas.append("🎟️ RESULTADOS ONCE")
lineas.append("")

if fecha:
    lineas.append(f"📅 {fecha}")
    lineas.append("")


# =========================
# CUPÓN DIARIO
# =========================

if cupon_diario:

    lineas.append("🎫 CUPÓN DIARIO")

    numero = cupon_diario.get(
        "numero",
        "—"
    )

    serie = cupon_diario.get(
        "serie",
        ""
    )

    lineas.append(
        f"Número: {numero}"
    )

    if serie:
        lineas.append(
            f"Serie: {serie}"
        )

    lineas.append("")


# =========================
# CUPONAZO
# =========================

if cuponazo:

    lineas.append("🎫 CUPONAZO")

    numero = cuponazo.get(
        "numero",
        "—"
    )

    serie = cuponazo.get(
        "serie",
        ""
    )

    lineas.append(
        f"Número: {numero}"
    )

    if serie:
        lineas.append(
            f"Serie: {serie}"
        )

    lineas.append("")


# =========================
# SUELDAZO
# =========================

for r in sueldazo:

    lineas.append("💰 SUELDAZO")

    numero = r.get(
        "numero",
        "—"
    )

    serie = r.get(
        "serie",
        ""
    )

    lineas.append(
        f"Número: {numero}"
    )

    if serie:
        lineas.append(
            f"Serie: {serie}"
        )

    lineas.append("")


# =========================
# EUROJACKPOT
# =========================

if eurojackpot:

    lineas.append("🇪🇺 EUROJACKPOT")

    numero = eurojackpot.get(
        "numero",
        "—"
    )

    soles = eurojackpot.get(
        "serie",
        ""
    )

    lineas.append(
        f"Números: {numero}"
    )

    if soles:
        lineas.append(
            f"Soles: {soles}"
        )

    bote = eurojackpot.get(
        "importebote",
        ""
    )

    if bote:
        lineas.append(
            f"💶 Bote: {bote} €"
        )

    lineas.append("")


# =========================
# MI DÍA
# =========================

if mi_dia:

    lineas.append("📅 MI DÍA")

    numero = mi_dia.get(
        "numero",
        "—"
    )

    lineas.append(
        f"Número: {numero}"
    )

    lineas.append("")


# =========================
# TRIPLEX
# =========================

if triplex:

    lineas.append("🔢 TRIPLEX")

    for r in triplex:

        numero = r.get(
            "numero",
            "—"
        )

        lineas.append(
            f"• {numero}"
        )

    lineas.append("")


# =========================
# DUPLA
# =========================

if dupla:

    lineas.append("🔢 DUPLA")

    for r in dupla:

        numero = r.get(
            "numero",
            "—"
        )

        lineas.append(
            f"• {numero}"
        )

    lineas.append("")


# =========================
# SUPER 11
# =========================

if super11:

    lineas.append("🔢 SUPER 11")

    for r in super11:

        numero = r.get(
            "numero",
            "—"
        )

        lineas.append(
            f"• {numero}"
        )

    lineas.append("")


# =========================
# PIE
# =========================

lineas.append(
    "━━━━━━━━━━━━━━━━━━"
)

lineas.append(
    "CSIF ONCE INFORMA"
)

lineas.append(
    "Resultados oficiales ONCE"
)


texto = "\n".join(lineas)


# =========================
# GUARDAR ARCHIVO
# =========================

with open(
    "whatsapp.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(texto)


# =========================
# ENVIAR TELEGRAM
# =========================

url = (
    f"https://api.telegram.org/"
    f"bot{TOKEN}/sendMessage"
)


respuesta = requests.post(

    url,

    json={
        "chat_id": CHAT_ID,
        "text": texto,
        "disable_web_page_preview": True
    },

    timeout=15
)


if not respuesta.ok:

    raise SystemExit(
        f"ERROR Telegram: "
        f"{respuesta.status_code} - "
        f"{respuesta.text}"
    )


print(
    "Mensaje CSIF INFORMA enviado "
    "correctamente a Telegram."
)