import json
import os
import requests

def enviar_telegram(mensaje):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️ Faltan las credenciales de Telegram (TOKEN o CHAT_ID).")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Mensaje enviado a Telegram correctamente.")
    else:
        print(f"❌ Error al enviar a Telegram: {response.text}")

def main():
    if not os.path.exists("resultados.json"):
        print("⚠️ No se encontró el archivo resultados.json")
        return

    with open("resultados.json", "r", encoding="utf-8") as f:
        resultados = json.load(f)

    # Construir el texto del mensaje
    lineas = ["📢 *Últimos Resultados ONCE* 📢\n"]
    for r in resultados:
        lineas.append(f"*{r['titulo']}*\n{r['descripcion']}\n")

    texto_mensaje = "\n".join(lineas)

    # Crear el archivo whatsapp.txt
    with open("whatsapp.txt", "w", encoding="utf-8") as f:
        f.write(texto_mensaje)
    
    print("Archivo 'whatsapp.txt' creado correctamente.")
    print(f"Resultados incluidos: {len(resultados)}")

    # Enviar el mensaje a Telegram
    enviar_telegram(texto_mensaje)

if __name__ == "__main__":
    main()
