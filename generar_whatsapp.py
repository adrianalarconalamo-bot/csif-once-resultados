#!/usr/bin/env python3
"""Descarga y ejecuta la versión corregida de generar_whatsapp."""
import urllib.request
import runpy
import tempfile
import os

URL = (
    "https://raw.githubusercontent.com/adrianalarconalamo-bot/"
    "csif-once-resultados/main/generar_whatsapp_core.py"
)

print("Descargando generar_whatsapp_core.py (versión madrugada)...")
req = urllib.request.Request(URL, headers={"User-Agent": "csif-once-bot"})
with urllib.request.urlopen(req, timeout=30) as r:
    codigo = r.read().decode("utf-8")

path = os.path.join(tempfile.gettempdir(), "generar_whatsapp_core_runtime.py")
with open(path, "w", encoding="utf-8") as f:
    f.write(codigo)
print(f"Ejecutando {path} ({len(codigo)} chars)...")
runpy.run_path(path, run_name="__main__")
