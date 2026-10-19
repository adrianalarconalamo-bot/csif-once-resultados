#!/usr/bin/env python3
"""
Envío a WhatsApp (CallMeBot) del MISMO mensaje que llega a Telegram.
Versión reforzada: más espera entre mensajes, logs completos, reintentos.
"""

import json
import os
import sys
import time
import urllib.parse
from datetime import datetime
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

    if AHORA.hour < 21 or (AHORA.hour == 21 and AHORA.minute < 30):
        print(f"[{AHORA.strftime('%H:%M')}] Todavía no son las 21:30. No se envía.")
        sys.exit(0)

    estado = cargar_json(ARCHIVO_ESTADO)
    if isinstance(estado, dict) and estado.get("fecha") == HOY:
        print(f"[{HOY}] WhatsApp ya enviado hoy. No se vuelve a enviar.")
        sys.exit(0)

    if not os.path.exists(ARCHIVO_MENSAJE):
        print(f"AVISO: no existe {ARCHIVO_MENSAJE}.")
        sys.exit(0)

    with open(ARCHIVO_MENSAJE, "r", encoding="utf-8") as f:
        mensaje_completo = f.read().strip()

    if not mensaje_completo:
        print(f"AVISO: {ARCHIVO_MENSAJE} vacío.")
        sys.exit(0)

    if "---MENSAJE 2---" in mensaje_completo:
        mensaje_completo = mensaje_completo.split("---MENSAJE 2---", 1)[0].strip()

    print(f"Mensaje original (mismo que Telegram): {len(mensaje_completo)} caracteres")
    partes = partir_mensaje(mensaje_completo)
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
        "fecha": HOY,
        "hora": AHORA.strftime("%H:%M:%S"),
        "metodo": "callmebot",
        "partes": len(partes),
        "caracteres": longitudes,
        "demoras": demoras_enviadas,
        "formato": "mismo mensaje original que Telegram (partido si >950 chars)",
    })

    print("")
    print("✅ WhatsApp: CallMeBot aceptó los mensajes (HTTP 200).")
    print("   Si no llegan al móvil: reautoriza el bot (+34 623 91 22 04)")
    print("   con el texto: I allow callmebot to send me messages")
    print("")


if __name__ == "__main__":
    main()
