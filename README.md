# csif-once-resultados

Resultados automáticos ONCE para CSIF — a partir de las 21:30 (hora española)

## Workflow unificado (recomendado)

| Canal              | Workflow                         | Secrets necesarios                                      |
|--------------------|----------------------------------|---------------------------------------------------------|
| Telegram + WhatsApp| `resultados-unificado.yml`       | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `CALLMEBOT_APIKEY`, `CALLMEBOT_PHONE` |

Este workflow envía **a los dos canales en la misma ejecución**.
Solo envía cuando están todos los resultados del día y a partir de las 21:30.

### Cómo lanzarlo manualmente

1. Ve a la pestaña **Actions**
2. Selecciona **"Resultados ONCE (Telegram + WhatsApp)"**
3. Pulsa **Run workflow**

### Configuración de WhatsApp (CallMeBot)

1. Añade el número **+34 623 91 22 04** a contactos.
2. Envía el mensaje: `I allow callmebot to send me messages`
3. Recibirás tu APIKEY.
4. En el repositorio ve a **Settings → Secrets and variables → Actions** y crea:
   - `CALLMEBOT_APIKEY` → tu apikey
   - `CALLMEBOT_PHONE` → tu número con código de país (ej: `+34685138060`)

### Workflows antiguos (opcional)

Los workflows antiguos (`resultados.yml` y `resultados-whatsapp.yml`) siguen existiendo por compatibilidad.
Puedes desactivarlos en la pestaña Actions si quieres usar solo el unificado.

---

**Nota sobre fiabilidad de GitHub Actions:**  
Los workflows programados (`schedule`) de GitHub pueden retrasarse o no ejecutarse bajo carga. Si un día no llega el mensaje automático, lanza el workflow unificado manualmente.
