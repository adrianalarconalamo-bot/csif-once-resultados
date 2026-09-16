import json
import html
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

    # Para listas de números del Super 11
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
    descripcion = limpiar_texto(resultado.get("descripcion", ""))

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
        numero_formateado = formatear_numero(numero)

        # Si es una lista larga de números, la ponemos en líneas
        if "," in numero:
            numeros = [n.strip() for n in numero.split(",") if n.strip()]

            if len(numeros) > 10:
                mitad = (len(numeros) + 1) // 2
                primera = " · ".join(numeros[:mitad])
                segunda = " · ".join(numeros[mitad:])

                lineas.append(f"*{primera}*")
                lineas.append(f"*{segunda}*")
            else:
                lineas.append(f"*{numero_formateado}*")
        else:
            lineas.append(f"*{numero_formateado}*")

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

    # Si el RSS trae información adicional y no hay número
    if descripcion and not numero:
        lineas.append(descripcion)

    return "\n".join(lineas)


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
        print("AVISO: No hay resultados para generar WhatsApp.")
        return

    # ---------------------------------------------------------
    # CABECERA
    # ---------------------------------------------------------

    lineas = []

    lineas.append("📢 *CSIF INFORMA*")
    lineas.append("")
    lineas.append("🎟️ *RESULTADOS ONCE*")

    # Utilizamos la fecha de actualización del JSON
    actualizado = limpiar_texto(datos.get("actualizado", ""))

    if actualizado:
        try:
            fecha_hora = datetime.strptime(
                actualizado,
                "%d/%m/%Y %H:%M"
            )

            fecha_texto = fecha_hora.strftime(
                "%A, %d de %B de %Y"
            )

            # Traducción de días y meses al español
            dias = {
                "Monday": "lunes",
                "Tuesday": "martes",
                "Wednesday": "miércoles",
                "Thursday": "jueves",
                "Friday": "viernes",
                "Saturday": "sábado",
                "Sunday": "domingo",
            }

            meses = {
                "January": "enero",
                "February": "febrero",
                "March": "marzo",
                "April": "abril",
                "May": "mayo",
                "June": "junio",
                "July": "julio",
                "August": "agosto",
                "September": "septiembre",
                "October": "octubre",
                "November": "noviembre",
                "December": "