import urllib.request
import xml.etree.ElementTree as ET
import json
import html
import re
from datetime import datetime, timezone
from pathlib import Path

URL = "https://www.juegosonce.es/rss/sorteos2.xml"


def descargar_xml():
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/rss+xml, application/xml, text/xml"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as respuesta:
        return respuesta.read()


def limpiar_texto(texto):
    if not texto:
        return ""

    texto = html.unescape(texto)

    # Eliminar etiquetas HTML
    texto = re.sub(r"<[^>]+>", " ", texto)

    # Limpiar espacios
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def obtener_texto(elemento, nombre):
    encontrado = elemento.find(nombre)

    if encontrado is not None and encontrado.text:
        return limpiar_texto(encontrado.text)

    # Buscar también por namespace
    for hijo in elemento:
        if hijo.tag.endswith("}" + nombre):
            if hijo.text:
                return limpiar_texto(hijo.text)

    return ""


def main():
    datos = descargar_xml()

    raiz = ET.fromstring(datos)

    resultados = []

    # Buscar todos los elementos que puedan ser entradas RSS
    for elemento in raiz.iter():

        titulo = obtener_texto(elemento, "title")
        descripcion = obtener_texto(elemento, "description")
        fecha = obtener_texto(elemento, "pubDate")

        # Solo guardar elementos que realmente tengan información
        if titulo or descripcion or fecha:

            resultado = {
                "titulo": titulo,
                "fecha": fecha,
                "descripcion": descripcion
            }

            # Evitar duplicados
            if resultado not in resultados:
                resultados.append(resultado)

    # Si el RSS utiliza otro formato, buscar enlaces/items
    if not resultados:
        for elemento in raiz.iter():

            datos_elemento = {}

            for hijo in elemento:
                nombre = hijo.tag.split("}")[-1]

                if nombre in ("title", "description", "pubDate", "date"):
                    datos_elemento[nombre] = limpiar_texto(hijo.text or "")

            if any(datos_elemento.values()):

                resultado = {
                    "titulo": datos_elemento.get("title", ""),
                    "fecha": datos_elemento.get(
                        "pubDate",
                        datos_elemento.get("date", "")
                    ),
                    "descripcion": datos_elemento.get("description", "")
                }

                if resultado not in resultados:
                    resultados.append(resultado)

    # Crear resultados.json
    salida = {
        "actualizado": datetime.now(
            timezone.utc
        ).astimezone().strftime("%d/%m/%Y %H:%M"),
        "resultados": resultados
    }

    Path("resultados.json").write_text(
        json.dumps(
            salida,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    # Crear también mensaje.txt
    Path("salida").mkdir(exist_ok=True)

    texto = []
    texto.append("🍀 RESULTADOS ONCE")
    texto.append(
        datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    texto.append("")

    for resultado in resultados:
        if resultado["titulo"]:
            texto.append(resultado["titulo"])

        if resultado["fecha"]:
            texto.append(resultado["fecha"])

        if resultado["descripcion"]:
            texto.append(resultado["descripcion"])

        texto.append("")

    Path("salida/mensaje.txt").write_text(
        "\n".join(texto),
        encoding="utf-8"
    )

    print("====================================")
    print("RESULTADOS ONCE")
    print("====================================")
    print(f"Elementos encontrados: {len(resultados)}")
    print()

    for resultado in resultados:
        print("Título:", resultado["titulo"])
        print("Fecha:", resultado["fecha"])
        print("Descripción:", resultado["descripcion"])
        print("------------------------------------")

    print()
    print("Archivo resultados.json creado correctamente.")


if __name__ == "__main__":
    main()