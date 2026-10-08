#!/usr/bin/env python3
import base64
from pathlib import Path
for name in ["generar_whatsapp.py", "enviar_whatsapp.py"]:
    parts = [Path(f"{name}.b64p{i}").read_text().strip() for i in range(8)]
    data = base64.b64decode("".join(parts))
    Path(name).write_bytes(data)
    assert b"10:00" in data
    print(f"OK {name} {len(data)}")
