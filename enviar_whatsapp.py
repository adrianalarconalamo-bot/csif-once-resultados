# CSIF ONCE WhatsApp — ensambla partes y ejecuta
from pathlib import Path

p = Path(__file__).resolve().parent
code = (p / "wa_part1.py.txt").read_text(encoding="utf-8") + (p / "wa_part2.py.txt").read_text(encoding="utf-8")
exec(compile(code, str(p / "enviar_whatsapp.py"), "exec"), {"__name__": "__main__"})
