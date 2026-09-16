import json
import html
from pathlib import Path

INPUT_FILE = "resultados.json"
OUTPUT_FILE = "whatsapp.txt"


def limpiar_texto(texto):
    if not texto:
        return ""

    # Convertir entidades HTML:
    # &oacute; -> ó
    # &eacute; -> é
    # &aacute; -> á
    # etc.
    return html.unescape(str(texto)).strip()


def formatear_resultado(resultado):
    tipo = limpiar_texto(resultado.get("tipo", ""))
    fecha = limpiar_texto(resultado.get("fecha", ""))
    numero = limpiar_texto(resultado.get("numero", ""))
    serie = limpiar_texto(resultado.get("serie", ""))
    importebote = limpiar_texto(resultado.get("importebote", ""))
    adic = limpiar_texto(resultado.get("adic", ""))

    texto = []

    if tipo:
        texto.append(tipo)

    if fecha:
        texto.append(fecha)

    if numero:
        texto.append(f"Número: {numero}")

    if serie:
        texto.append(f"Serie: {serie}")

    if importebote and importebote != "0":
        try:
            bote = int(importebote)
            texto.append(f"Bote: {bote:,} €".replace(",", "."))
        except ValueError:
            texto.append(f"Bote: {importebote} €")

    if adic:
        texto.append(f"Adicionales: {adic}")

    return "\n".join(texto)


def generar_whatsapp():
    ruta = Path(INPUT_FILE)

    if not ruta.exists():
        print(f"ERROR: No existe el archivo {INPUT_FILE}")
        return

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR leyendo {INPUT_FILE}: {e}")
        return

    resultados = data.get("resultados", [])

    if not resultados:
        print("AVISO: resultados.json no contiene resultados.")
        return

    actualizado = limpiar_texto(data.get("actualizado", ""))

    lineas = []

    lineas.append("🎟️ RESULTADOS ONCE")
    lineas.append("")

    if actualizado:
        lineas.append(f"Actualizado: {actualizado}")

    lineas.append("")
    lineas.append("━━━━━━━━━━━━━━━━━━")
    lineas.append("")

    for resultado in resultados:
        texto = formatear_resultado(resultado)

        if texto:
            lineas.append(texto)
            lineas.append("")
            lineas.append("━━━━━━━━━━━━━━━━━━")
            lineas.append("")

    texto_final = "\n".join(lineas).strip() + "\n"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(texto_final)

    print(f"Archivo '{OUTPUT_FILE}' creado correctamente.")
    print(f"Resultados incluidos: {len(resultados)}")


if __name__ == "__main__":
    generar_whatsapp()