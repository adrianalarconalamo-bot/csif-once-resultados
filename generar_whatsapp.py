import json
import html
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


def formatear_numero(numero):
    numero = limpiar_texto(numero)

    if not numero:
        return ""

    if "," in numero:
        numeros = [n.strip() for n in numero.split(",") if n.strip()]
        return " · ".join(numeros)

    return numero


def formatear_resultado(resultado):
    tipo = limpiar_texto(
        resultado.get("tipo")
        or resultado.get("titulo")
        or resultado.get("nombre")
        or ""
    )

    fecha = limpiar_texto(resultado.get("fecha", ""))
    numero = limpiar_texto(resultado.get("numero", ""))
    serie = limpiar_texto(resultado.get("serie", ""))
    bote = limpiar_texto(
        resultado.get("importebote")
        or resultado.get("bote")
        or ""
    )
    adic = limpiar_texto(
        resultado.get("adic")
        or resultado.get("adicional")
        or ""
    )

    lineas = []

    if tipo:
        tipo_mayusculas = tipo.upper()

        if "TRIPLEX" in tipo_mayusculas:
            emoji = "🔵"
        elif "DUPLA" in tipo_mayusculas:
            emoji = "🟢"
        elif "SUPER 11" in tipo_mayusculas:
            emoji = "🔴"
        elif "EUROJACKPOT" in tipo_mayusculas:
            emoji = "🟡"
        elif "SUELDAZO" in tipo_mayusculas:
            emoji = "🟣"
        elif "CUPÓN" in tipo_mayusculas or "CUPON" in tipo_mayusculas:
            emoji = "🎟️"
        else:
            emoji = "🎟️"

        lineas.append(f"{emoji} *{tipo}*")

    if fecha:
        lineas.append(fecha)

    if numero:
        if "," in numero:
            numeros = [n.strip() for n in numero.split(",") if n.strip()]

            if len(numeros) > 10:
                mitad = (len(numeros) + 1) // 2
                primera = " · ".join(numeros[:mitad])
                segunda = " · ".join(numeros[mitad:])

                lineas.append(f"*{primera}*")
                lineas.append(f"*{segunda}*")
            else:
                lineas.append(f"*{formatear_numero(numero)}*")
        else:
            lineas.append(f"*{numero}*")

    if serie:
        lineas.append(f"Serie: *{serie}*")

    if bote and bote != "0":
        try:
            valor = int(float(bote))
            bote_formateado = f"{valor:,}".replace(",", ".")
            lineas.append(f"💰 *Bote: {bote_formateado} €*")
        except ValueError:
            lineas.append(f"💰 *Bote: {bote} €*")

    if adic:
        lineas.append(f"Adicional: *{adic}*")

    return "\n".join(lineas)


def enviar_telegram(texto_mensaje):
    """
    Lee los secretos de GitHub Actions y realiza el envío del mensaje a Telegram.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("⚠️ AVISO: No se detectaron TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID. Se omitirá el envío a Telegram.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto_mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print("✅ Mensaje enviado a Telegram correctamente.")
        else:
            print(f"❌ Error enviando a Telegram ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Excepción en el envío a Telegram: {e}")


def generar_whatsapp():

    ruta = Path(INPUT_FILE)

    if not ruta.exists():
        print(f"ERROR: No existe {INPUT_FILE}")
        return

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

    except Exception as error:
        print(f"ERROR leyendo {INPUT_FILE}: {error}")
        return

    resultados = datos.get("resultados", [])

    if not resultados:
        print("AVISO: No hay resultados para generar el mensaje.")
        return

    lineas = []

    # CABECERA
    lineas.append("📢 *CSIF INFORMA*")
    lineas.append("")
    lineas.append("🎟️ *RESULTADOS ONCE*")

    actualizado = limpiar_texto(datos.get("actualizado", ""))

    if actualizado:
        try:
            fecha_hora = datetime.strptime(
                actualizado,
                "%d/%m/%Y %H:%M"
            )

            dias = [
                "lunes",
                "martes",
                "miércoles",
                "jueves",
                "viernes",
                "sábado",
                "domingo"
            ]

            meses = [
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

            fecha_texto = (
                f"{dias[fecha_hora.weekday()]}, "
                f"{fecha_hora.day} de "
                f"{meses[fecha_hora.month - 1]} de "
                f"{fecha_hora.year}"
            )

            lineas.append(f"📅 *{fecha_texto}*")
            lineas.append(
                f"🕒 Actualizado: {fecha_hora.strftime('%H:%M')}"
            )

        except ValueError:
            lineas.append(f"🕒 Actualizado: {actualizado}")

    lineas.append("")
    lineas.append("━━━━━━━━━━━━━━━━━━")
    lineas.append("")

    # TODOS LOS RESULTADOS DEL JSON
    for resultado in resultados:

        texto = formatear_resultado(resultado)

        if texto:
            lineas.append(texto)
            lineas.append("")
            lineas.append("━━━━━━━━━━━━━━━━━━")
            lineas.append("")

    # PIE DEL MENSAJE
    lineas.append("🌙 *Buenas noches.*")
    lineas.append("")
    lineas.append(f"📞 *{TELEFONO}*")
    lineas.append("")
    lineas.append("🤝 *CSIF, todo por todos.*")

    texto_final = "\n".join(lineas).strip() + "\n"

    # 1. Guardar en el archivo de texto
    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:
        archivo.write(texto_final)

    print(f"Archivo '{OUTPUT_FILE}' creado correctamente.")
    print(f"Resultados incluidos: {len(resultados)}")

    # 2. Enviar automáticamente por Telegram
    enviar_telegram(texto_final)


if __name__ == "__main__":
    generar_whatsapp()
