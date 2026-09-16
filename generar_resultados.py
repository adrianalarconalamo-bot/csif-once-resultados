import json
import html
import re
import os
import requests
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

INPUT_FILE = "resultados.json"
OUTPUT_FILE = "whatsapp.txt"
TELEFONO = "652 33 86 27"


def limpiar_texto(texto):
    if not texto:
        return ""
    return html.unescape(str(texto)).strip()


def extraer_numero_sorteo(texto):
    """Detecta el número de sorteo (1 al 5) si viene indicado explícitamente."""
    m = re.search(r'(?i)sorteo\s*(\d)', texto)
    if m:
        return int(m.group(1))
    return None


def formatear_super11(numero_str):
    """Agrupa los números del Super 11 de 5 en 5."""
    nums = re.findall(r'\d+', str(numero_str))
    if not nums:
        return numero_str

    lineas = []
    for i in range(0, len(nums), 5):
        bloque = " ".join(f"{int(n):02d}" for n in nums[i:i+5])
        lineas.append(bloque)
    return "\n".join(lineas)


def enviar_telegram(texto_mensaje):
    """Envía el mensaje maquetado a Telegram."""
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
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            print("✅ Mensaje enviado a Telegram correctamente.")
        else:
            print(f"❌ Error enviando a Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Excepción enviando a Telegram: {e}")


def generar_whatsapp():
    ruta = Path(INPUT_FILE)
    if not ruta.exists():
        print(f"ERROR: No existe {INPUT_FILE}")
        return

    with open(ruta, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    resultados = datos.get("resultados", [])
    if not resultados:
        print("AVISO: No hay resultados en el JSON.")
        return

    ahora_espana = datetime.now(ZoneInfo("Europe/Madrid"))
    dia_semana = ahora_espana.weekday()  # 0=Lunes, 4=Viernes, 5=Sábado, 6=Domingo

    # Identificar la etiqueta adecuada para el cupón según el día
    if dia_semana == 4:
        etiqueta_cupon = "🔘 *Cuponazo*"
    elif dia_semana in (5, 6):
        etiqueta_cupon = "🔘 *Sueldazo*"
    else:
        etiqueta_cupon = "🔘 *Cupón Diario*"

    cupon_principal = None
    eurojackpot = None
    mi_dia = None

    sorteos_diarios = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}}
    contadores = {"triplex": 1, "super11": 1, "dupla": 1}

    for r in resultados:
        tipo = limpiar_texto(r.get("tipo", "")).upper()
        desc = limpiar_texto(r.get("descripcion", "")).upper()
        texto_comb = f"{tipo} {desc}"

        num_explicit = extraer_numero_sorteo(texto_comb)

        if "CUPÓN" in tipo or "CUPONAZO" in tipo or "SUELDAZO" in tipo:
            cupon_principal = r
        elif "EUROJACKPOT" in tipo or "EURO JACKPOT" in tipo:
            eurojackpot = r
        elif "MI DÍA" in tipo or "MI DIA" in tipo:
            mi_dia = r
        elif "TRIPLEX" in tipo:
            slot = num_explicit if num_explicit else contadores["triplex"]
            if slot <= 5:
                sorteos_diarios[slot]["triplex"] = r
                contadores["triplex"] = slot + 1
        elif "SÚPER 11" in tipo or "SUPER 11" in tipo:
            slot = num_explicit if num_explicit else contadores["super11"]
            if slot <= 5:
                sorteos_diarios[slot]["super11"] = r
                contadores["super11"] = slot + 1
        elif "DUPLA" in tipo:
            slot = num_explicit if num_explicit else contadores["dupla"]
            if slot <= 5:
                sorteos_diarios[slot]["dupla"] = r
                contadores["dupla"] = slot + 1

    # CONSTRUCCIÓN DEL MENSAJE
    lineas = []
    lineas.append("📢 *CSIF INFORMA*")
    lineas.append("El sorteo de hoy")

    dias_nombre = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    lineas.append(f"*{dias_nombre[dia_semana]}*")
    lineas.append(f"*{ahora_espana.day:02d}  {ahora_espana.month:02d}  {ahora_espana.year}*")
    lineas.append("")

    # 1. Cupón Principal (Cupón Diario / Cuponazo / Sueldazo)
    if cupon_principal:
        lineas.append(etiqueta_cupon)
        numero = cupon_principal.get('numero', '')
        serie = cupon_principal.get('serie', '')
        if serie:
            lineas.append(f"*{numero}* serie *{serie}*")
        else:
            lineas.append(f"*{numero}*")
        lineas.append("")

    # 2. Eurojackpot
    if eurojackpot:
        lineas.append("💸 *Euro Jackpot* 💸")
        numero = eurojackpot.get('numero', '')
        bote = eurojackpot.get('importebote', eurojackpot.get('bote', ''))

        if numero:
            lineas.append(f"*{numero}*")

        if bote and bote != "0":
            try:
                millones = int(float(bote)) // 1000000
                if millones > 0:
                    lineas.append("*BOTE*")
                    lineas.append(f"*{millones}* Millones €")
                else:
                    lineas.append(f"*BOTE:* {bote} €")
            except Exception:
                lineas.append(f"*BOTE:* {bote} €")
        lineas.append("")

    # 3. Sorteos 1 al 5
    for i in range(1, 6):
        s = sorteos_diarios[i]
        if s or (i == 5 and mi_dia):
            lineas.append(f"▫ *Sorteo {i}*")

            if "dupla" in s:
                lineas.append("Dupla")
                lineas.append(f"*{s['dupla'].get('numero', '')}*")

            if "triplex" in s:
                lineas.append("Tríplex")
                lineas.append(f"*{s['triplex'].get('numero', '')}*")

            if "super11" in s:
                lineas.append("Súper 11")
                lineas.append(formatear_super11(s['super11'].get('numero', '')))

            if i == 5 and mi_dia:
                lineas.append("Mi Día 🍀")
                lineas.append(f"*{mi_dia.get('numero', '')}*")

            lineas.append("")

    # Pie de mensaje
    lineas.append("━━━━━━━━━━━━━━━")
    lineas.append("🟢 *CSIF ONCE*")
    lineas.append("ESTAMOS POR TI")
    lineas.append(f"TEL: *{TELEFONO}*")
    lineas.append("*Buenas Noches*")

    texto_final = "\n".join(lineas).strip() + "\n"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as archivo:
        archivo.write(texto_final)

    enviar_telegram(texto_final)


if __name__ == "__main__":
    generar_whatsapp()
