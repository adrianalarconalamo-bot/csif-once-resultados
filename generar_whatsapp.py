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


# ============================================================
# COMPROBAR HORA
# ============================================================

# No hacemos el envío antes de las 21:30 hora española.
if AHORA.hour < 21 or (
    AHORA.hour == 21 and AHORA.minute < 30
):

    print(
        f"[{AHORA.strftime('%H:%M')}] "
        "Todavía no son las 21:30. "
        "No se envía nada."
    )

    sys.exit(0)


# ============================================================
# COMPROBAR CREDENCIALES
# ============================================================

if not TOKEN or not CHAT_ID:

    raise SystemExit(
        "ERROR: faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID"
    )


# ============================================================
# COMPROBAR SI YA SE ENVIÓ HOY
# ============================================================

try:

    with open(
        "telegram_enviado.json",
        "r",
        encoding="utf-8"
    ) as f:

        estado_envio = json.load(f)

except FileNotFoundError:

    estado_envio = {}


if estado_envio.get("fecha") == HOY:

    print(
        f"[{HOY}] Los resultados ya fueron enviados hoy. "
        "No se vuelve a enviar."
    )

    sys.exit(0)


# ============================================================
# CARGAR RESULTADOS
# ============================================================

try:

    with open(
        "resultados.json",
        "r",
        encoding="utf-8"
    ) as f:

        datos = json.load(f)

except Exception as e:

    raise SystemExit(
        f"ERROR leyendo resultados.json: {e}"
    )


resultados = datos.get(
    "resultados",
    []
)


if not resultados:

    print(
        "resultados.json todavía está vacío."
    )

    sys.exit(0)


# ============================================================
# ASEGURAR QUE SON RESULTADOS DE HOY
# ============================================================

resultados_hoy = []

for r in resultados:

    fecha = str(
        r.get("fecha", "")
    )

    if HOY in fecha:

        resultados_hoy.append(r)


if not resultados_hoy:

    print(
        f"No hay resultados correspondientes a {HOY}."
    )

    sys.exit(0)


# ============================================================
# CLASIFICAR RESULTADOS
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

    tipo = str(
        r.get("tipo", "")
    ).upper().strip()


    if (
        "CUPÓN DIARIO" in tipo
        or "CUPON DIARIO" in tipo
    ):

        cupon_diario = r


    elif "CUPONAZO" in tipo:

        cuponazo = r


    elif "SUELDAZO ADICIONAL" in tipo:

        sueldazo_adicionales.append(r)


    elif "SUELDAZO" in tipo:

        sueldazo_principal = r


    elif (
        "MI DÍA" in tipo
        or "MI DIA" in tipo
    ):

        mi_dia = r


    elif "TRIPLEX" in tipo:

        triplex.append(r)


    elif "DUPLA" in tipo:

        dupla.append(r)


    elif (
        "SUPER 11" in tipo
        or "SUPERONCE" in tipo
    ):

        super11.append(r)


    elif "EUROJACKPOT" in tipo:

        eurojackpot = r


# ============================================================
# COMPROBAR COMPLETITUD
# ============================================================

DIA_SEMANA = AHORA.weekday()

# 0 = lunes
# 1 = martes
# 2 = miércoles
# 3 = jueves
# 4 = viernes
# 5 = sábado
# 6 = domingo


faltan = []


# ------------------------------------------------------------
# JUEGOS DIARIOS
# ------------------------------------------------------------

if len(triplex) < 5:

    faltan.append(
        f"Triplex ({len(triplex)}/5)"
    )


if len(dupla) < 5:

    faltan.append(
        f"Dupla ({len(dupla)}/5)"
    )


if len(super11) < 5:

    faltan.append(
        f"Super 11 ({len(super11)}/5)"
    )


if mi_dia is None:

    faltan.append(
        "Mi Día"
    )


# ------------------------------------------------------------
# LUNES A VIERNES
# ------------------------------------------------------------

if DIA_SEMANA <= 4:

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
# SUELDAZO COMPLETO
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
# SI FALTA ALGO, NO ENVIAR
# ============================================================

if faltan:

    print("")
    print("⏳ RESULTADOS TODAVÍA INCOMPLETOS")
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
        "Se volverá a comprobar en 5 minutos."
    )

    sys.exit(0)


# ============================================================
# TODO COMPLETO
# ============================================================

print("")
print("✅ TODOS LOS RESULTADOS DISPONIBLES")
print(
    f"📅 {HOY}"
)
print("")


# ============================================================
# CABECERA
# ============================================================

fecha = resultados_hoy[0].get(
    "fecha",
    ""
)


lineas = [

    "📢 CSIF INFORMA",

    "",

    "🎟️✨ RESULTADOS ONCE ✨",

    ""
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

        "🎫⭐ CUPÓN DIARIO",

        "",

        f"🔢 Número: "
        f"{cupon_diario.get('numero', '—')}"
    ]


    if cupon_diario.get("serie"):

        lineas.append(
            f"🔖 Serie: "
            f"{cupon_diario['serie']}"
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

        "🎟️💥 CUPONAZO",

        "",

        f"🔢 Número: "
        f"{cuponazo.get('numero', '—')}"
    ]


    if cuponazo.get("serie"):

        lineas.append(
            f"🔖 Serie: "
            f"{cuponazo['serie']}"
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

        lineas += [

            "🏆 PREMIO PRINCIPAL",

            "",

            f"🔢 Número: "
            f"{sueldazo_principal.get('numero', '—')}"
        ]


        if sueldazo_principal.get("serie"):

            lineas.append(
                f"🔖 Serie: "
                f"{sueldazo_principal['serie']}"
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


        for r in sueldazo_adicionales:

            numero = r.get(
                "numero",
                "—"
            )

            serie = r.get(
                "serie",
                ""
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

    lineas += [

        "🇪🇺💎 EUROJACKPOT",

        "",

        f"🔢 Números: "
        f"{eurojackpot.get('numero', '—')}"
    ]


    if eurojackpot.get("serie"):

        lineas.append(
            f"☀️ Soles: "
            f"{eurojackpot['serie']}"
        )


    if eurojackpot.get("importebote"):

        bote = str(
            eurojackpot["importebote"]
        )


        if bote not in (
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

    valor = str(
        mi_dia.get(
            "numero",
            "—"
        )
    ).strip()


    partes = valor.rsplit(
        " ",
        1
    )


    if len(partes) == 2:

        fecha_mi_dia = partes[0]

        numero_suerte = partes[1]

    else:

        fecha_mi_dia = valor

        numero_suerte = "—"


    lineas += [

        "📅🍀 MI DÍA",

        "",

        f"📆 Fecha: {fecha_mi_dia}",

        "",

        f"🍀 Número de la suerte: "
        f"{numero_suerte}",

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


    for i, r in enumerate(
        triplex,
        1
    ):

        numero = r.get(
            "numero",
            "—"
        )


        lineas += [

            f"🎲 Sorteo {i}: {numero}",

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

        "🟢🔄 DUPLA",

        "",

        "ℹ️ Números del 01 al 15",

        ""
    ]


    for i, r in enumerate(
        dupla,
        1
    ):

        valor = str(
            r.get(
                "numero",
                "—"
            )
        ).strip()


        try:

            numero = int(valor)


            if 1 <= numero <= 15:

                anterior = (
                    15
                    if numero == 1
                    else numero - 1
                )


                posterior = (
                    1
                    if numero == 15
                    else numero + 1
                )


                premiado = (
                    f"{numero:02d}"
                )

                reintegro_anterior = (
                    f"{anterior:02d}"
                )

                reintegro_posterior = (
                    f"{posterior:02d}"
                )

            else:

                premiado = valor

                reintegro_anterior = "—"

                reintegro_posterior = "—"


        except ValueError:

            premiado = valor

            reintegro_anterior = "—"

            reintegro_posterior = "—"


        lineas += [

            f"🎲 Sorteo {i}",

            f"🏆 Número premiado: "
            f"{premiado}",

            f"⬅️ Reintegro anterior: "
            f"{reintegro_anterior}",

            f"➡️ Reintegro posterior: "
            f"{reintegro_posterior}",

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


    for i, r in enumerate(
        super11,
        1
    ):

        numero = r.get(
            "numero",
            "—"
        )


        lineas += [

            f"🎲 Sorteo {i}",

            f"🔢 {numero}",

            ""
        ]


    # No mostramos importebote.
    # De esta forma nunca aparecerá 1000000.

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
# GUARDAR MENSAJE
# ============================================================

with open(
    "whatsapp.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(texto)


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

        timeout=15
    )


except Exception as e:

    raise SystemExit(
        f"ERROR conectando con Telegram: {e}"
    )


if not respuesta.ok:

    raise SystemExit(
        "ERROR Telegram: "
        f"{respuesta.status_code} - "
        f"{respuesta.text}"
    )


# ============================================================
# MARCAR COMO ENVIADO
# ============================================================

with open(
    "telegram_enviado.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(

        {
            "fecha": HOY,

            "hora": AHORA.strftime(
                "%H:%M:%S"
            )
        },

        f,

        ensure_ascii=False,

        indent=2
    )


print("")
print(
    "✅ MENSAJE CSIF INFORMA ENVIADO CORRECTAMENTE."
)
print(
    f"📅 Fecha: {HOY}"
)
print(
    f"🕐 Hora: {AHORA.strftime('%H:%M:%S')}"
)
print("")