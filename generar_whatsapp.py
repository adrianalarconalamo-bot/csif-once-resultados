import json
import html
import re
import os
import unicodedata
import requests

from datetime import datetime
from pathlib import Path


INPUT_FILE = "resultados.json"
OUTPUT_FILE = "whatsapp.txt"

TELEFONO = "652 33 86 27"


def limpiar_texto(texto):

    if not texto:
        return ""

    texto = html.unescape(
        str(texto)
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def normalizar(texto):

    texto = limpiar_texto(
        texto
    )

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    return texto.upper()


def formatear_super11(numero):

    numeros = re.findall(
        r"\d+",
        str(numero)
    )

    numeros = [
        numero.zfill(2)
        for numero in numeros
    ]

    grupos = []

    for i in range(
        0,
        len(numeros),
        10
    ):

        grupos.append(
            " · ".join(
                numeros[i:i + 10]
            )
        )

    return "\n".join(
        grupos
    )


def enviar_telegram(mensaje):

    token = os.environ.get(
        "TELEGRAM_BOT_TOKEN"
    )

    chat_id = os.environ.get(
        "TELEGRAM_CHAT_ID"
    )

    if not token or not chat_id:

        print(
            "⚠️ Faltan las credenciales de Telegram."
        )

        return

    url = (
        f"https://api.telegram.org/"
        f"bot{token}/sendMessage"
    )

    payload = {
        "chat_id": chat_id,
        "text": mensaje
    }

    try:

        respuesta = requests.post(
            url,
            json=payload,
            timeout=30
        )

        if respuesta.ok:

            print(
                "✅ Mensaje enviado a Telegram."
            )

        else:

            print(
                "❌ Error Telegram:",
                respuesta.text
            )

    except Exception as error:

        print(
            "❌ Error conectando con Telegram:",
            error
        )


def obtener_resultados():

    if not Path(
        INPUT_FILE
    ).exists():

        raise RuntimeError(
            f"No existe {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as archivo:

        datos = json.load(
            archivo
        )

    if not isinstance(
        datos,
        dict
    ):

        raise RuntimeError(
            "resultados.json no tiene "
            "la estructura esperada."
        )

    resultados = datos.get(
        "resultados",
        []
    )

    if not resultados:

        raise RuntimeError(
            "resultados.json no contiene resultados."
        )

    return datos


def generar_whatsapp():

    datos = obtener_resultados()

    resultados = datos["resultados"]

    actualizado = datos.get(
        "actualizado",
        datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        )
    )

    lineas = []

    lineas.append(
        "📢 CSIF INFORMA"
    )

    lineas.append("")

    lineas.append(
        "🎟️ RESULTADOS ONCE"
    )

    lineas.append(
        f"Actualizado: {actualizado}"
    )

    lineas.append("")

    triplex = 0
    dupla = 0

    for resultado in resultados:

        tipo_original = limpiar_texto(
            resultado.get(
                "tipo",
                ""
            )
        )

        tipo = normalizar(
            tipo_original
        )

        fecha = limpiar_texto(
            resultado.get(
                "fecha",
                ""
            )
        )

        numero = limpiar_texto(
            resultado.get(
                "numero",
                ""
            )
        )

        serie = limpiar_texto(
            resultado.get(
                "serie",
                ""
            )
        )

        bote = limpiar_texto(
            resultado.get(
                "importebote",
                "0"
            )
        )

        if not tipo:
            continue

        # CUPÓN
        if (
            "CUPON" in tipo
            or "SUELDAZO" in tipo
        ):

            lineas.append(
                "🎫 CUPÓN"
            )

            lineas.append(
                fecha
            )

            if numero:

                lineas.append(
                    f"Número: {numero}"
                )

            if serie:

                lineas.append(
                    f"Serie: {serie}"
                )

            lineas.append("")

        # MI DÍA
        elif "MI DIA" in tipo:

            lineas.append(
                "📅 MI DÍA"
            )

            lineas.append(
                fecha
            )

            lineas.append(
                f"Número: {numero}"
            )

            lineas.append("")

        # TRIPLEX
        elif "TRIPLEX" in tipo:

            triplex += 1

            lineas.append(
                "🔢 TRIPLEX DE LA ONCE"
            )

            lineas.append(
                f"{fecha}, Sorteo {triplex}"
            )

            lineas.append(
                f"Número: {numero}"
            )

            lineas.append("")

        # DUPLA
        elif "DUPLA" in tipo:

            dupla += 1

            lineas.append(
                "🔢 DUPLA DE LA ONCE"
            )

            lineas.append(
                f"{fecha}, Sorteo {dupla}"
            )

            lineas.append(
                f"Número: {numero}"
            )

            lineas.append("")

        # SUPER 11
        elif (
            "SUPER 11" in tipo
            or "SUREP 11" in tipo
        ):

            lineas.append(
                "🔢 SUPER 11"
            )

            lineas.append(
                fecha
            )

            lineas.append(
                formatear_super11(
                    numero
                )
            )

            if bote and bote != "0":

                lineas.append(
                    f"Bote: {bote}"
                )

            lineas.append("")

        # OTROS
        else:

            lineas.append(
                f"🎟️ {tipo_original}"
            )

            if fecha:
                lineas.append(
                    fecha
                )

            if numero:
                lineas.append(
                    f"Número: {numero}"
                )

            if serie:
                lineas.append(
                    f"Serie: {serie}"
                )

            lineas.append("")

    lineas.append(
        "🌙 Buenas noches."
    )

    lineas.append(
        f"📞 {TELEFONO}"
    )

    lineas.append(
        "🤝 CSIF, todo por todos."
    )

    mensaje = "\n".join(
        lineas
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            mensaje
        )

    print(
        f"{OUTPUT_FILE} creado correctamente."
    )

    print(
        f"Resultados procesados: {len(resultados)}"
    )

    enviar_telegram(
        mensaje
    )


def main():

    generar_whatsapp()


if __name__ == "__main__":
    main()