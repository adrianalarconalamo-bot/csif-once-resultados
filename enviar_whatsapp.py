#!/usr/bin/env python3
"""
Envío a WhatsApp (CallMeBot) del MISMO mensaje que llega a Telegram.

- Lee whatsapp.txt generado por generar_whatsapp.py (formato original).
- Lo parte en trozos ≤999 caracteres respetando saltos de línea.
- Envía también el informe de demoras (demoras_texto.txt) como mensaje aparte.
- Usa whatsapp_enviado.json para no reenviar el mismo día.
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
LIMITE_CHARS = 999


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
    """Parte el texto en trozos ≤ limite respetando saltos de línea."""
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
            # No hay salto de línea razonable: corta duro
            corte = limite
        trozo = restante[:corte].rstrip()
        if trozo:
            partes.append(trozo)
        restante = restante[corte:].lstrip("\n")
    return partes


def enviar_callmebot(msg, etiqueta):
    if not APIKEY or not PHONE:
        raise SystemExit("ERROR: faltan CALLMEBOT_APIKEY o CALLMEBOT_PHONE")

    url = (
        f"https://api.callmebot.com/whatsapp.php"
        f"?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
    )
    print(f"Enviando {etiqueta} ({len(msg)} chars)...")
    r = requests.get(url, timeout=30)
    print(f"  HTTP {r.status_code}: {r.text[:200]}")
    texto_resp = (r.text or "").lower()
    if r.status_code != 200 or ("error" in texto_resp and "queued" not in texto_resp):
        raise SystemExit(f"ERROR CallMeBot {etiqueta}: {r.text}")
    return len(msg)


def main():
    print("")
    print("==========================================")
    print(" ENVIAR WHATSAPP (mismo formato Telegram)")
    print("==========================================")
    print(f"Fecha: {HOY}  Hora: {AHORA.strftime('%H:%M:%S')}")
    print("")

    # No enviar antes de 21:30
    if AHORA.hour < 21 or (AHORA.hour == 21 and AHORA.minute < 30):
        print(f"[{AHORA.strftime('%H:%M')}] Todavía no son las 21:30. No se envía.")
        sys.exit(0)

    # Ya enviado hoy
    estado = cargar_json(ARCHIVO_ESTADO)
    if isinstance(estado, dict) and estado.get("fecha") == HOY:
        print(f"[{HOY}] WhatsApp ya enviado hoy. No se vuelve a enviar.")
        sys.exit(0)

    # El mensaje original lo genera generar_whatsapp.py
    if not os.path.exists(ARCHIVO_MENSAJE):
        print(f"AVISO: no existe {ARCHIVO_MENSAJE}. "
              "Probablemente los resultados aún no están completos o Telegram no los generó.")
        sys.exit(0)

    with open(ARCHIVO_MENSAJE, "r", encoding="utf-8") as f:
        mensaje_completo = f.read().strip()

    if not mensaje_completo:
        print(f"AVISO: {ARCHIVO_MENSAJE} está vacío. No se envía.")
        sys.exit(0)

    # Si el archivo contiene el separador antiguo de dos mensajes, quedarnos solo con el primero
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
            time.sleep(3)

    # Demoras como mensaje adicional (mismo contenido que Telegram)
    demoras_enviadas = False
    if os.path.exists(ARCHIVO_DEMORAS):
        with open(ARCHIVO_DEMORAS, "r", encoding="utf-8") as f:
            demoras = f.read().strip()
        if demoras:
            time.sleep(3)
            msg_demoras = demoras
            if len(msg_demoras) > LIMITE_CHARS:
                for j, parte in enumerate(partir_mensaje(msg_demoras), 1):
                    enviar_callmebot(parte, f"demoras parte {j}")
                    time.sleep(2)
            else:
                enviar_callmebot(msg_demoras, "demoras")
            demoras_enviadas = True

    guardar_json(ARCHIVO_ESTADO, {
        "fecha": HOY,
        "hora": AHORA.strftime("%H:%M:%S"),
        "metodo": "callmebot",
        "partes": len(partes),
        "caracteres": longitudes,
        "demoras": demoras_enviadas,
        "formato": "mismo mensaje original que Telegram (partido si >999 chars)",
    })

    print("")
    print("✅ WhatsApp enviado correctamente (mismo formato que Telegram)")
    print("")


if __name__ == "__main__":
    main()
