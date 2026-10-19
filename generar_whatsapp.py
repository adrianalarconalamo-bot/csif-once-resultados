#!/usr/bin/env python3
"""Carga la versión buena de generar_whatsapp desde un commit estable y la ejecuta."""
import urllib.request
import runpy
import tempfile
import os

URL = (
    "https://raw.githubusercontent.com/adrianalarconalamo-bot/"
    "csif-once-resultados/de63a1190fec83c3b3ef7914e8374279409d439a/generar_whatsapp.py"
)

print("Descargando generar_whatsapp.py estable...")
req = urllib.request.Request(URL, headers={"User-Agent": "csif-once-bot"})
with urllib.request.urlopen(req, timeout=30) as r:
    codigo = r.read().decode("utf-8")

# Inyectar log de message_id si no está
marker = 'if not respuesta_json.get("ok"):'
injection = '''
resultado_tg = respuesta_json.get("result") or {}
msg_id = resultado_tg.get("message_id")
chat = resultado_tg.get("chat") or {}
print(f"Telegram OK → message_id={msg_id} chat_id={chat.get('id')} tipo={chat.get('type')} titulo={chat.get('title') or chat.get('username') or chat.get('first_name')}")
'''

if "Telegram OK → message_id" not in codigo and marker in codigo:
    # Insertar después del bloque ok
    idx = codigo.find('raise SystemExit(\n        "ERROR Telegram: "')
    if idx != -1:
        # encontrar el final de ese raise SystemExit
        end = codigo.find(')\n', idx)
        if end != -1:
            end = codigo.find('\n', end + 1)
            codigo = codigo[:end+1] + injection + codigo[end+1:]

path = os.path.join(tempfile.gettempdir(), "generar_whatsapp_stable.py")
with open(path, "w", encoding="utf-8") as f:
    f.write(codigo)

print(f"Ejecutando {path} ({len(codigo)} chars)...")
runpy.run_path(path, run_name="__main__")
