import json
import html
import re
import os
import requests
from pathlib import Path
from datetime import datetime

INPUT_FILE = "resultados.json"
OUTPUT_FILE = "whatsapp.txt"
TELEFONO = "652 33 86 27"


def limpiar_texto(texto):
    if not texto:
        return ""
    return html.unescape(str(texto)).strip()


def formatear_super11(numero_str):
    nums = re.findall(r'\d+', str(numero_str))

    if not nums:
        return numero_str

    lineas = []

    for i in range(0, len(nums), 10):
        bloque = " · ".join(
            f"{int(n):02d}"
            for n in nums[i:i + 10]
        )
        lineas.append(bloque)

    return "\n".join(lineas)


def enviar_telegram(texto_mensaje):

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("⚠️ No se envía a Telegram: Faltan secretos.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": texto_mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        respuesta = requests.post(
            url,
            json=payload,
            timeout=10
        )

        if respuesta.ok:
            print("Mensaje enviado correctamente a Telegram.")
        else:
            print(
                f"⚠️ Telegram respondió con "
                f"código {respuesta.status_code}"
            )

    except Exception as error:
        print(f"⚠️ Error enviando a Telegram: {error}")


def generar_whatsapp():

    ruta = Path(INPUT_FILE)

    if not ruta.exists():
        print(f"⚠️ No existe {INPUT_FILE}")
        return

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        datos = json.load(archivo)

    resultados = datos.get(
        "resultados",
        []
    )

    if not resultados:
        print("⚠️ No hay resultados.")
        return

    actualizado_str = datos.get(
        "actualizado",
        ""
    )

    try:

        dt = datetime.strptime(
            actualizado_str,
            "%d/%m/%Y %H:%M"
        )

        dias_minus = [
            "lunes",
            "martes",
            "miércoles",
            "jueves",
            "viernes",
            "sábado",
            "domingo"
        ]

        meses_val = [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre"
        ]

        fecha_larga = (
            f"{dias_minus[dt.weekday()]}, "
            f"{dt.day} de "
            f"{meses_val[dt.month - 1]} de "
            f"{dt.year}"
        )

        dias_cap = [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo"
        ]

        fecha_corta = (
            f"{dias_cap[dt.weekday()]}, "
            f"{dt.day:02d}/"
            f"{dt.month:02d}/"
            f"{dt.year}"
        )

        hora_act = dt.strftime("%H:%M")

    except Exception:

        fecha_larga = actualizado_str
        fecha_corta = actualizado_str
        hora_act = "21:30"


    cupon_principal = None
    mi_dia = None
    triplex_list = []
    dupla_list = []
    super11_list = []


    for r in resultados:

        tipo = limpiar_texto(
            r.get("tipo", "")
        ).upper()

        if (
            "CUPÓN" in tipo
            or "CUPONAZO" in tipo
            or "SUELDAZO" in tipo
        ):
            cupon_principal = r

        elif (
            "MI DÍA" in tipo
            or "MI DIA" in tipo
        ):
            mi_dia = r

        elif "TRIPLEX" in tipo:
            triplex_list.append(r)

        elif (
            "SÚPER 11" in tipo
            or "SUPER 11" in tipo
        ):
            super11_list.append(r)

        elif "DUPLA" in tipo:
            dupla_list.append(r)


    lineas = []

    separador = "━━━━━━━━━━━━━━━━━━"


    # ==========================================================
    # CABECERA
    # ==========================================================

    lineas.append("📢 CSIF INFORMA")
    lineas.append("")

    lineas.append("🎟️ RESULTADOS ONCE")
    lineas.append(f"📅 {fecha_larga}")
    lineas.append(f"🕒 Actualizado: {hora_act}")


    # ==========================================================
    # CUPÓN PRINCIPAL
    # ==========================================================

    if cupon_principal:

        lineas.append("")
        lineas.append(separador)
        lineas.append("")

        tipo_cupon = limpiar_texto(
            cupon_principal.get(
                "tipo",
                "Cupón Diario"
            )
        )

        lineas.append(
            f"🎟️ {tipo_cupon}"
        )

        lineas.append(
            fecha_corta
        )

        numero = cupon_principal.get(
            "numero",
            ""
        )

        serie = cupon_principal.get(
            "serie",
            ""
        )

        lineas.append(
            str(numero)
        )

        if serie:
            lineas.append(
                f"Serie: {serie}"
            )


    # ==========================================================
    # TRIPLEX
    # ==========================================================

    for idx, item in enumerate(
        triplex_list,
        start=1
    ):

        lineas.append("")
        lineas.append(separador)
        lineas.append("")

        lineas.append(
            f"🔵 Triplex de la ONCE — Sorteo {idx}"
        )

        lineas.append(
            str(item.get("numero", ""))
        )


    # ==========================================================
    # MI DÍA
    # ==========================================================

    if mi_dia:

        lineas.append("")
        lineas.append(separador)
        lineas.append("")

        lineas.append("🎟️ Mi Día")

        lineas.append(
            str(mi_dia.get("numero", ""))
        )


    # ==========================================================
    # DUPLA
    # ==========================================================

    for idx, item in enumerate(
        dupla_list,
        start=1
    ):

        lineas.append("")
        lineas.append(separador)
        lineas.append("")

        lineas.append(
            f"🟢 Dupla de la ONCE — Sorteo {idx}"
        )

        lineas.append(
            str(item.get("numero", ""))
        )


    # ==========================================================
    # SUPER 11
    # ==========================================================

    for idx, item in enumerate(
        super11_list,
        start=1
    ):

        lineas.append("")
        lineas.append(separador)
        lineas.append("")

        lineas.append(
            f"🔴 Super 11 — Sorteo {idx}"
        )

        num_s11 = item.get(
            "numero",
            ""
        )

        lineas.append(
            formatear_super11(num_s11)
        )


    # ==========================================================
    # PIE
    # ==========================================================

    lineas.append("")
    lineas.append(separador)
    lineas.append("")

    lineas.append("🌙 Buenas noches.")
    lineas.append("")

    lineas.append(
        f"📞 {TELEFONO}"
    )

    lineas.append("")

    lineas.append(
        "🤝 CSIF, todo por todos."
    )


    texto_final = (
        "\n".join(lineas).strip()
        + "\n"
    )


    # ==========================================================
    # GUARDAR
    # ==========================================================

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            texto_final
        )


    print(
        f"{OUTPUT_FILE} generado correctamente."
    )

    enviar_telegram(
        texto_final
    )


if __name__ == "__main__":
    generar_whatsapp()