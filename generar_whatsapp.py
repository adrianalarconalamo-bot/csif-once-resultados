#!/usr/bin/env python3
"""Ejecuta la versión local de generar_whatsapp_core (sin descargar de GitHub)."""
import runpy
import os
import sys

base = os.path.dirname(os.path.abspath(__file__))
core = os.path.join(base, "generar_whatsapp_core.py")

if not os.path.isfile(core):
    print(f"ERROR: no existe {core}")
    sys.exit(1)

print(f"Ejecutando {core} (versión local)...")
runpy.run_path(core, run_name="__main__")
