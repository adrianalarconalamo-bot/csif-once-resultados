# csif-once-resultados

Resultados automáticos ONCE para CSIF — 21:30

## Dos canales en paralelo

| Canal     | Workflow                      | Estado                  | Secrets necesarios                  |
|-----------|-------------------------------|-------------------------|-------------------------------------|
| Telegram  | `resultados.yml`              | Activo                  | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| WhatsApp  | `resultados-whatsapp.yml`     | Activo (CallMeBot)      | `CALLMEBOT_APIKEY`, `CALLMEBOT_PHONE`   |

Ambos se ejecutan de forma independiente después de las 21:30 (hora española) y solo envían cuando están todos los resultados del día.

## Configuración de WhatsApp (CallMeBot)

1. Añade el número **+34 623 91 22 04** a contactos.
2. Envía el mensaje: `I allow callmebot to send me messages`
3. Recibirás tu APIKEY.
4. En el repositorio ve a **Settings → Secrets and variables → Actions** y crea:
   - `CALLMEBOT_APIKEY` → tu apikey
   - `CALLMEBOT_PHONE` → tu número con código de país (ej: `+34685138060`)

## Ejecución manual

En la pestaña **Actions** puedes lanzar manualmente cualquiera de los dos workflows.
