import json
import os
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise SystemExit("ERROR: faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")

with open("resultados.json", "r", encoding="utf-8") as f:
    datos = json.load(f)

resultados = datos.get("resultados", [])

if not resultados:
    raise SystemExit("ERROR: resultados.json está vacío.")

cupon_diario = None
cuponazo = None
sueldazo = []
mi_dia = None
triplex = []
dupla = []
super11 = []
eurojackpot = None


# ============================================================
# AGRUPAR RESULTADOS
# ============================================================

for r in resultados:

    tipo = str(r.get("tipo", "")).upper().strip()

    if "CUPÓN DIARIO" in tipo or "CUPON DIARIO" in tipo:
        cupon_diario = r

    elif "CUPONAZO" in tipo:
        cuponazo = r

    elif "SUELDAZO" in tipo:
        sueldazo.append(r)

    elif "MI DÍA" in tipo or "MI DIA" in tipo:
        mi_dia = r

    elif "TRIPLEX" in tipo:
        triplex.append(r)

    elif "DUPLA" in tipo:
        dupla.append(r)

    elif "SUPER 11" in tipo or "SUPERONCE" in tipo:
        super11.append(r)

    elif "EUROJACKPOT" in tipo:
        eurojackpot = r


# ============================================================
# FECHA
# ============================================================

fecha = resultados[0].get("fecha", "")

lineas = [
    "📢 CSIF INFORMA",
    "",
    "🎟️ RESULTADOS ONCE",
    "",
]

if fecha:
    lineas += [
        f"📅 {fecha}",
        "",
        "━━━━━━━━━━━━━━━━━━",
        ""
    ]


# ============================================================
# CUPÓN DIARIO
# ============================================================

if cupon_diario:

    lineas += [
        "🎫 CUPÓN DIARIO",
        "",
        f"Número: {cupon_diario.get('numero', '—')}"
    ]

    if cupon_diario.get("serie"):
        lineas.append(
            f"Serie: {cupon_diario['serie']}"
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

    lineas += [
        "🎫 CUPONAZO",
        "",
        f"Número: {cuponazo.get('numero', '—')}"
    ]

    if cuponazo.get("serie"):
        lineas.append(
            f"Serie: {cuponazo['serie']}"
        )

    lineas += [
        "",
        "━━━━━━━━━━━━━━━━━━",
        ""
    ]


# ============================================================
# SUELDAZO
# ============================================================

for r in sueldazo:

    lineas += [
        "💰 SUELDAZO",
        "",
        f"Número: {r.get('numero', '—')}"
    ]

    if r.get("serie"):
        lineas.append(
            f"Serie: {r['serie']}"
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

    lineas += [
        "🇪🇺 EUROJACKPOT",
        "",
        f"Números: {eurojackpot.get('numero', '—')}"
    ]

    if eurojackpot.get("serie"):
        lineas.append(
            f"Soles: {eurojackpot['serie']}"
        )

    if eurojackpot.get("importebote"):
        lineas.append(
            f"💶 Bote: {eurojackpot['importebote']} €"
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

    valor = str(
        mi_dia.get("numero", "—")
    ).strip()

    partes = valor.rsplit(" ", 1)

    if len(partes) == 2:
        fecha_mi_dia = partes[0]
        numero_suerte = partes[1]
    else:
        fecha_mi_dia = valor
        numero_suerte = "—"

    lineas += [
        "📅 MI DÍA",
        "",
        f"📆 {fecha_mi_dia}",
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
        "🔢 TRIPLEX",
        ""
    ]

    for i, r in enumerate(triplex, 1):

        numero = r.get(
            "numero",
            "—"
        )

        lineas += [
            f"🎯 Sorteo {i}",
            f"🔢 {numero}",
            ""
        ]

    lineas += [
        "━━━━━━━━━━━━━━━━━━",
        ""
    ]


# ============================================================
# DUPLA
# ============================================================

if dupla:

    lineas += [
        "🔢 DUPLA",
        "",
        "ℹ️ Números del 01 al 15",
        ""
    ]

    for i, r in enumerate(dupla, 1):

        valor = str(
            r.get("numero", "—")
        ).strip()

        try:

            numero = int(valor)

            if 1 <= numero <= 15:

                anterior = (
                    15 if numero == 1
                    else numero - 1
                )

                posterior = (
                    1 if numero == 15
                    else numero + 1
                )

                premiado = f"{numero:02d}"
                reintegro_anterior = f"{anterior:02d}"
                reintegro_posterior = f"{posterior:02d}"

            else:

                premiado = valor
                reintegro_anterior = "—"
                reintegro_posterior = "—"

        except ValueError:

            premiado = valor
            reintegro_anterior = "—"
            reintegro_posterior = "—"

        lineas += [
            f"🎯 Sorteo {i}",
            f"🏆 Número premiado: {premiado}",
            f"🔄 Reintegro anterior: {reintegro_anterior}",
            f"🔄 Reintegro posterior: {reintegro_posterior}",
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
        "🔢 SUPER 11",
        ""
    ]

    for i, r in enumerate(super11, 1):

        numero = r.get(
            "numero",
            "—"
        )

        lineas += [
            f"🎯 Sorteo {i}",
            f"🔢 {numero}",
            ""
        ]

    lineas += [
        "━━━━━━━━━━━━━━━━━━",
        ""
    ]


# ============================================================
# PIE
# ============================================================

lineas += [
    "CSIF ONCE INFORMA",
    "Resultados oficiales ONCE"
]


texto = "\n".join(lineas).strip()


# ============================================================
# GUARDAR
# ============================================================

with open(
    "whatsapp.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(texto)


# ============================================================
# TELEGRAM
# ============================================================

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