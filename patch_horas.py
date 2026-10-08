from pathlib import Path

for fname in ["generar_whatsapp.py", "enviar_whatsapp.py"]:
    p = Path(fname)
    t = p.read_text(encoding="utf-8")

    old_t = (
        '        lineas.append(\n'
        '            f"\U0001f3b2 Sorteo {i}: {numero}"\n'
        '        )\n'
        '\n'
        '        lineas.append("")'
    )
    new_t = (
        '        horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]\n'
        '        hora = horas[i - 1] if i <= len(horas) else ""\n'
        '        if hora:\n'
        '            lineas.append(\n'
        '                f"\U0001f550 {hora} h \u00b7 Sorteo {i} \u2192 {numero}"\n'
        '            )\n'
        '        else:\n'
        '            lineas.append(\n'
        '                f"\U0001f3b2 Sorteo {i}: {numero}"\n'
        '            )\n'
        '\n'
        '        lineas.append("")'
    )
    if old_t not in t:
        raise SystemExit(f"{fname}: TRIPLEX no encontrado")
    t = t.replace(old_t, new_t, 1)

    old_d = (
        '        lineas += [\n'
        '\n'
        '            f"\U0001f3b2 Sorteo {i}",\n'
        '\n'
        '            f"\U0001f3c6 N\u00famero premiado: {premiado}",\n'
        '\n'
        '            f"\u2b05\ufe0f Reintegro anterior: {anterior}",\n'
        '\n'
        '            f"\u27a1\ufe0f Reintegro posterior: {posterior}",\n'
        '\n'
        '            ""\n'
        '\n'
        '        ]'
    )
    new_d = (
        '        horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]\n'
        '        hora = horas[i - 1] if i <= len(horas) else ""\n'
        '        if hora:\n'
        '            lineas.append(\n'
        '                f"\U0001f550 {hora} h \u00b7 Sorteo {i}"\n'
        '            )\n'
        '        else:\n'
        '            lineas.append(\n'
        '                f"\U0001f3b2 Sorteo {i}"\n'
        '            )\n'
        '        lineas += [\n'
        '            f"\U0001f3c6 Premiado \u2192 {premiado}",\n'
        '            f"\u2b05\ufe0f Anterior {anterior}  \u00b7  \u27a1\ufe0f Posterior {posterior}",\n'
        '            ""\n'
        '        ]'
    )
    if old_d not in t:
        raise SystemExit(f"{fname}: DUPLA no encontrado")
    t = t.replace(old_d, new_d, 1)

    old_s = (
        '        lineas += [\n'
        '\n'
        '            f"\U0001f3b2 Sorteo {i}",\n'
        '\n'
        '            f"\U0001f522 {numero}",\n'
        '\n'
        '            ""\n'
        '\n'
        '        ]'
    )
    new_s = (
        '        horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]\n'
        '        hora = horas[i - 1] if i <= len(horas) else ""\n'
        '        if hora:\n'
        '            lineas.append(\n'
        '                f"\U0001f550 {hora} h \u00b7 Sorteo {i}"\n'
        '            )\n'
        '        else:\n'
        '            lineas.append(\n'
        '                f"\U0001f3b2 Sorteo {i}"\n'
        '            )\n'
        '        lineas += [\n'
        '            f"\U0001f522 {numero}",\n'
        '            ""\n'
        '        ]'
    )
    if old_s not in t:
        raise SystemExit(f"{fname}: SUPER11 no encontrado")
    t = t.replace(old_s, new_s, 1)

    p.write_text(t, encoding="utf-8")
    assert "10:00" in t
    print(f"OK {fname}")

print("Formato con horas aplicado")
