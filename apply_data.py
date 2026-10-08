#!/usr/bin/env python3
import base64, zlib
from pathlib import Path
Path("generar_whatsapp.py").write_bytes(zlib.decompress(base64.b64decode(Path("data_gw.b64").read_text().strip())))
Path("enviar_whatsapp.py").write_bytes(zlib.decompress(base64.b64decode(Path("data_ew.b64").read_text().strip())))
print("OK formato CSIF horas instalado")
