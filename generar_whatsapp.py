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
    if not texto: return ""
    return html.unescape(str(texto)).strip()


def obtener_numero_sorteo(texto):
    """Busca si el nombre del juego contiene 'Sorteo 1', 'Sorteo 2', etc."""
    m = re.search(r'(?i)sorteo\s*(\d)', texto)
    return int(m.group(1)) if m else None


def formatear_super11(numero_str):
    """Agrupa los números del Super 11 de 5 en 5"""
    nums = re.findall(r'\d+', str(numero_str))
    if not nums: return numero_str
    
    lineas = []
    for i in range(0, len(nums), 5):
        # Une 5 números separados por espacio y rellenando con ceros a la izquierda si hiciera falta
        bloque = " ".join(f"{int(n):02d}" for n in nums[i:i+5])
        lineas.append(bloque)
    return "\n".join(lineas)


def enviar_telegram(texto_mensaje):
    """Envía el mensaje maquetado a Telegram usando los secretos de GitHub Actions"""
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
        requests.post(url, json=payload, timeout=10)
    except:
        pass


def generar_whatsapp():
    ruta = Path(INPUT_FILE)
    if not ruta.exists(): return

    with open(ruta, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    resultados = datos.get("resultados", [])
    if not resultados: return

    # Variables para organizar los juegos
    cupon_principal = None
    eurojackpot = None
    mi_dia = None
    sorteos_diarios = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}}

    # Clasificar resultados
    for r in resultados:
        tipo = limpiar_texto(r.get("tipo", "")).upper()
        num_sorteo = obtener_numero_sorteo(tipo)

        if "CUPÓN" in tipo or "CUPONAZO" in tipo or "SUELDAZO" in tipo:
            cupon_principal = r
        elif "EUROJACKPOT" in tipo or "EURO JACKPOT" in tipo:
            eurojackpot = r
        elif "MI DÍA" in tipo or "MI DIA" in tipo:
            mi_dia = r
        else:
            ns = num_sorteo if num_sorteo else 1
            if "TRIPLEX" in tipo:
                sorteos_diarios[ns]["triplex"] = r
            elif "SÚPER 11" in tipo or "SUPER 11" in tipo:
                sorteos_diarios[ns]["super11"] = r
            elif "DUPLA" in tipo:
                sorteos_diarios[ns]["dupla"] = r

    # COMENZAR A MAQUETAR EL MENSAJE
    lineas = []
    lineas.append("📢 *CSIF INFORMA*")
    lineas.append("El sorteo de hoy")
    
    # Extraer fecha
    try:
        dt = datetime.strptime(datos.get("actualizado", ""), "%d/%m/%Y %H:%M")
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        lineas.append(f"*{dias[dt.weekday()]}*")
        lineas.append(f"*{dt.day:02d}  {dt.month:02d}  {dt.year}*")
    except:
        lineas.append(f"*{datos.get('actualizado', '')}*")
    
    lineas.append("")

    # 1. Cupón Principal
    if cupon_principal:
        lineas.append("🔘 *Cupón Diario*") # O Cuponazo/Sueldazo según el día
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
            # Formatear el bote si viene en número largo
            try:
                millones = int(float(bote)) // 1000000
                if millones > 0:
                    lineas.append("*BOTE*")
                    lineas.append(f"*{millones}* Millones €")
                else:
                    lineas.append(f"*BOTE:* {bote} €")
            except:
                lineas.append(f"*BOTE:* {bote} €")
        lineas.append("")

    # 3. Sorteos (1 al 5)
    for i in range(1, 6):
        s = sorteos_diarios[i]
        # El Sorteo 5 suele llevar "Mi Día"
        if s or (i == 5 and mi_dia):
            lineas.append(f"▫ *Sorteo {i}*")
            
            if "dupla" in s:
                lineas.append("Dupla")
                lineas.append(f"*{s['dupla'].get('numero','')}*")
            
            if "triplex" in s:
                lineas.append("Tríplex")
                lineas.append(f"*{s['triplex'].get('numero','')}*")
                
            if "super11" in s:
                lineas.append("Súper 11")
                lineas.append(formatear_super11(s['super11'].get('numero','')))
                
            if i == 5 and mi_dia:
                lineas.append("Mi Día 🍀")
                lineas.append(f"*{mi_dia.get('numero','')}*")
                
            lineas.append("")

    # PIE DE MENSAJE
    lineas.append("━━━━━━━━━━━━━━━")
    lineas.append("🟢 *CSIF ONCE*")
    lineas.append("ESTAMOS POR TI")
    lineas.append(f"TEL: *{TELEFONO}*")
    lineas.append("*Buenas Noches*")

    # Guardar y enviar
    texto_final = "\n".join(lineas).strip() + "\n"
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as archivo:
        archivo.write(texto_final)
        
    enviar_telegram(texto_final)


if __name__ == "__main__":
    generar_whatsapp()
