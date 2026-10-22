#!/usr/bin/env python3
"""
Envío a WhatsApp (CallMeBot) del MISMO mensaje que llega a Telegram.
Versión reforzada: solo envía si el mensaje está completo (misma lógica que Telegram).
"""

import json
import os
import sys
import time
import urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

TZ = ZoneInfo("Europe/Madrid")
AHORA = datetime.now(TZ)
HOY = AHORA.strftime("%d/%m/%Y")

APIKEY = os.getenv("CALLMEBOT_APIKEY")
PHONE = os.getenv("CALLMEBOT_PHONE")

ARCHIVO_MENSAJE = "whatsapp.txt"
ARCHIVO_DEMORAS = "demoras_texto.txt"
ARCHIVO_ESTADO = "whatsapp_enviado.json"
ARCHIVO_TELEGRAM = "telegram_enviado.json"
LIMITE_CHARS = 950  # margen bajo 999


def cargar_json(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def guardar_json(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def partir_mensaje(texto, limite=LIMITE_CHARS):
    texto = texto.strip()
    if not texto:
        return []
    if len(texto) <= limite:
        return [texto]

    partes = []
    restante = texto
    while restante:
        if len(restante) <= limite:
            partes.append(restante)
            break
        corte = restante.rfind("\n", 0, limite)
        if corte < limite // 3:
            corte = limite
        trozo = restante[:corte].rstrip()
        if trozo:
            partes.append(trozo)
        restante = restante[corte:].lstrip("\n")
    return partes


def mensaje_completo(texto, fecha_resultados):
    """
    Comprueba que whatsapp.txt es el mensaje real de hoy/ayer,
    no un mensaje antiguo ni uno generado a medias.
    """
    if not texto:
        return False
    upper = texto.upper()
    if fecha_resultados not in texto:
        return False
    # Debe incluir el sorteo principal del día
    tiene_principal = (
        "CUPÓN DIARIO" in upper
        or "CUPON DIARIO" in upper
        or "CUPONAZO" in upper
        or "SUELDAZO" in upper
    )
    if not tiene_principal:
        return False
    # Señales mínimas de que el bloque de resultados está presente
    if "TRIPLEX" not in upper and "MI DÍA" not in upper and "MI DIA" not in upper:
        # En fin de semana puede no haber Triplex en el mensaje si solo hay Sueldazo;
        # con principal ya basta.
        pass
    return True


def enviar_callmebot(msg, etiqueta, reintentos=3):
    if not APIKEY or not PHONE:
        raise SystemExit("ERROR: faltan CALLMEBOT_APIKEY o CALLMEBOT_PHONE")

    phone = PHONE.strip()
    if not phone.startswith("+"):
        print(f"AVISO: CALLMEBOT_PHONE no empieza por +. Valor actual (enmascarado): {phone[:4]}...")

    url = (
        f"https://api.callmebot.com/whatsapp.php"
        f"?phone={urllib.parse.quote(phone)}"
        f"&text={urllib.parse.quote(msg)}"
        f"&apikey={urllib.parse.quote(APIKEY)}"
    )

    ultimo_error = None
    for intento in range(1, reintentos + 1):
        print(f"Enviando {etiqueta} ({len(msg)} chars) intento {intento}/{reintentos}...")
        try:
            r = requests.get(url, timeout=45)
        except requests.RequestException as e:
            ultimo_error = str(e)
            print(f"  Excepción de red: {e}")
            time.sleep(5)
            continue

        cuerpo = (r.text or "")[:400]
        print(f"  HTTP {r.status_code}")
        print(f"  Respuesta: {cuerpo}")

        texto_resp = (r.text or "").lower()
        if "invalid apikey" in texto_resp or "wrong apikey" in texto_resp:
            raise SystemExit(f"ERROR CallMeBot: APIKEY inválida → {cuerpo}")
        if "not authorized" in texto_resp or "i allow callmebot" in texto_resp:
            raise SystemExit(
                "ERROR CallMeBot: el número no ha autorizado el bot. "
                "Envía 'I allow callmebot to send me messages' al +34 623 91 22 04"
            )
        if "error" in texto_resp and "queued" not in texto_resp and r.status_code != 200:
            ultimo_error = cuerpo
            print(f"  Fallo detectado, reintento en 8s...")
            time.sleep(8)
            continue

        if r.status_code == 200:
            return len(msg)

        ultimo_error = cuerpo
        time.sleep(8)

    raise SystemExit(f"ERROR CallMeBot {etiqueta} tras {reintentos} intentos: {ultimo_error}")


def main():
    print("")
    print("==========================================")
    print(" ENVIAR WHATSAPP (mismo formato Telegram)")
    print("==========================================")
    print(f"Fecha: {HOY}  Hora: {AHORA.strftime('%H:%M:%S')}")
    print(f"PHONE configurado: {'SÍ' if PHONE else 'NO'}  APIKEY: {'SÍ' if APIKEY else 'NO'}")
    print("")

    # Permitir envío a partir de las 21:30, y también en madrugada (< 03:00)
    en_ventana = (
        AHORA.hour > 21
        or (AHORA.hour == 21 and AHORA.minute >= 30)
        or AHORA.hour < 3
    )
    if not en_ventana:
        print(f"[{AHORA.strftime('%H:%M')}] Todavía no son las 21:30. No se envía.")
        sys.exit(0)

    # Fecha de los resultados
    fecha_resultados = HOY
    try:
        with open("resultados.json", encoding="utf-8") as f:
            datos = json.load(f)
        for r in datos.get("resultados", []):
            ftxt = str(r.get("fecha", ""))
            ayer = (AHORA.date() - timedelta(days=1)).strftime("%d/%m/%Y")
            if HOY in ftxt:
                fecha_resultados = HOY
                break
            if ayer in ftxt:
                fecha_resultados = ayer
                break
    except Exception:
        pass
    print(f"Fecha de resultados a enviar: {fecha_resultados}")

    # Solo enviar si Telegram YA envió el mensaje completo de esta fecha.
    # Así evitamos mandar whatsapp.txt antiguo o incompleto.
    estado_tg = cargar_json(ARCHIVO_TELEGRAM)
    if not isinstance(estado_tg, dict) or estado_tg.get("fecha") != fecha_resultados:
        print(
            f"Telegram aún no ha enviado los resultados de {fecha_resultados}. "
            "WhatsApp espera a que el mensaje esté completo."
        )
        sys.exit(0)

    if not os.path.exists(ARCHIVO_MENSAJE):
        print(f"AVISO: no existe {ARCHIVO_MENSAJE}.")
        sys.exit(0)

    with open(ARCHIVO_MENSAJE, "r", encoding="utf-8") as f:
        mensaje_completo_txt = f.read().strip()

    if not mensaje_completo_txt:
        print(f"AVISO: {ARCHIVO_MENSAJE} vacío.")
        sys.exit(0)

    if "---MENSAJE 2---" in mensaje_completo_txt:
        mensaje_completo_txt = mensaje_completo_txt.split("---MENSAJE 2---", 1)[0].strip()

    if not mensaje_completo(mensaje_completo_txt, fecha_resultados):
        print(
            f"AVISO: {ARCHIVO_MENSAJE} no contiene un mensaje completo de {fecha_resultados} "
            "(falta fecha o cupón/cuponazo/sueldazo). NO se marca como enviado."
        )
        sys.exit(0)

    estado = cargar_json(ARCHIVO_ESTADO)
    if isinstance(estado, dict) and estado.get("fecha") == fecha_resultados:
        print(f"[{fecha_resultados}] WhatsApp ya enviado correctamente. No se vuelve a enviar.")
        sys.exit(0)

    print(f"Mensaje original (mismo que Telegram): {len(mensaje_completo_txt)} caracteres")
    partes = partir_mensaje(mensaje_completo_txt)
    print(f"Se enviará en {len(partes)} parte(s)")

    longitudes = []
    for i, parte in enumerate(partes, 1):
        etiqueta = f"resultados parte {i}/{len(partes)}"
        longitudes.append(enviar_callmebot(parte, etiqueta))
        if i < len(partes):
            print("Esperando 8s entre partes...")
            time.sleep(8)

    demoras_enviadas = False
    if os.path.exists(ARCHIVO_DEMORAS):
        with open(ARCHIVO_DEMORAS, "r", encoding="utf-8") as f:
            demoras = f.read().strip()
        if demoras:
            print("Esperando 8s antes de demoras...")
            time.sleep(8)
            if len(demoras) > LIMITE_CHARS:
                for j, parte in enumerate(partir_mensaje(demoras), 1):
                    enviar_callmebot(parte, f"demoras parte {j}")
                    time.sleep(5)
            else:
                enviar_callmebot(demoras, "demoras")
            demoras_enviadas = True

    guardar_json(ARCHIVO_ESTADO, {
        "fecha": fecha_resultados,
        "hora": AHORA.strftime("%H:%M:%S"),
        "metodo": "callmebot",
        "partes": len(partes),
        "caracteres": longitudes,
        "demoras": demoras_enviadas,
        "formato": "mismo mensaje original que Telegram (partido si >950 chars)",
        "completo": True,
    })

    print("")
    print("✅ WhatsApp: CallMeBot aceptó los mensajes (HTTP 200).")
    print("   Si no llegan al móvil: reautoriza el bot (+34 623 91 22 04)")
    print("   con el texto: I allow callmebot to send me messages")
    print("")


if __name__ == "__main__":
    main()
