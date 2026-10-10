import json, os, sys, time, urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

TZ = ZoneInfo("Europe/Madrid")
AHORA = datetime.now(TZ)
HOY = AHORA.strftime("%d/%m/%Y")
APIKEY = os.getenv("CALLMEBOT_APIKEY")
PHONE = os.getenv("CALLMEBOT_PHONE")

def limpiar(v):
    return "" if v is None else str(v).strip()

def es_tipo(tipo, *nombres):
    t = limpiar(tipo).upper()
    return any(n.upper() in t for n in nombres)

def numero_sorteo(r):
    fecha = limpiar(r.get("fecha", "")).upper()
    m = "SORTEO "
    p = fecha.rfind(m)
    if p == -1:
        return 999
    try:
        return int(fecha[p+len(m):].strip())
    except ValueError:
        return 999

def formatear_dupla(valor):
    try:
        n = int(limpiar(valor))
    except ValueError:
        return valor, "—", "—"
    if not 1 <= n <= 15:
        return valor, "—", "—"
    return f"{n:02d}", f"{15 if n==1 else n-1:02d}", f"{1 if n==15 else n+1:02d}"

def separar_mi_dia(valor):
    valor = limpiar(valor)
    partes = valor.rsplit(" ", 1)
    return (partes[0].strip(), partes[1].strip()) if len(partes)==2 else (valor, "—")

def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_json(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

datos = cargar_json("resultados.json")
resultados = datos.get("resultados", [])
if not resultados:
    print("resultados vacíos"); sys.exit(0)

resultados_hoy = [r for r in resultados if HOY in limpiar(r.get("fecha", ""))]
print(f"Resultados hoy ({HOY}): {len(resultados_hoy)}")
if not resultados_hoy:
    print("Sin resultados de hoy"); sys.exit(0)

cupon_diario = cuponazo = sueldazo_principal = mi_dia = eurojackpot = None
sueldazo_adicionales, triplex, dupla, super11 = [], [], [], []
for r in resultados_hoy:
    t = limpiar(r.get("tipo", ""))
    if es_tipo(t, "CUPÓN DIARIO", "CUPON DIARIO"): cupon_diario = r
    elif es_tipo(t, "CUPONAZO"): cuponazo = r
    elif es_tipo(t, "SUELDAZO ADICIONAL"): sueldazo_adicionales.append(r)
    elif es_tipo(t, "SUELDAZO"): sueldazo_principal = r
    elif es_tipo(t, "MI DÍA", "MI DIA"): mi_dia = r
    elif es_tipo(t, "TRIPLEX"): triplex.append(r)
    elif es_tipo(t, "DUPLA"): dupla.append(r)
    elif es_tipo(t, "SUPER 11", "SUPERONCE"): super11.append(r)
    elif es_tipo(t, "EUROJACKPOT"): eurojackpot = r

triplex.sort(key=numero_sorteo)
dupla.sort(key=numero_sorteo)
super11.sort(key=numero_sorteo)

DIA = AHORA.weekday()
faltan = []
if len(triplex) < 5: faltan.append(f"Triplex ({len(triplex)}/5)")
if len(dupla) < 5: faltan.append(f"Dupla ({len(dupla)}/5)")
if len(super11) < 5: faltan.append(f"Super 11 ({len(super11)}/5)")
if mi_dia is None: faltan.append("Mi Día")
if DIA <= 3 and cupon_diario is None: faltan.append("Cupón Diario")
if DIA == 4 and cuponazo is None: faltan.append("Cuponazo")
if DIA in (1, 4) and eurojackpot is None: faltan.append("Eurojackpot")
if DIA in (5, 6):
    if sueldazo_principal is None: faltan.append("Sueldazo principal")
    if len(sueldazo_adicionales) < 4: faltan.append(f"Sueldazo adic ({len(sueldazo_adicionales)}/4)")

if AHORA.hour < 21 or (AHORA.hour == 21 and AHORA.minute < 30):
    print(f"[{AHORA.strftime('%H:%M')}] Antes de 21:30"); sys.exit(0)
if faltan:
    print("Incompleto:", ", ".join(faltan)); sys.exit(0)

try:
    est = cargar_json("whatsapp_enviado.json")
except Exception:
    est = {}
if isinstance(est, dict) and est.get("fecha") == HOY:
    print(f"[{HOY}] Ya enviado hoy"); sys.exit(0)

lineas = ["📢 CSIF INFORMA · RESULTADOS ONCE", f"📅 {HOY}", "━━━━━━━━━━━━━━━━━━"]
if cupon_diario:
    n, s = limpiar(cupon_diario.get("numero")), limpiar(cupon_diario.get("serie"))
    lineas += ["🎫 CUPÓN DIARIO", f"🔢 {n} · Serie {s}" if s else f"🔢 {n}", "━━━━━━━━━━━━━━━━━━"]
if cuponazo:
    n, s = limpiar(cuponazo.get("numero")), limpiar(cuponazo.get("serie"))
    lineas += ["🎟️ CUPONAZO", f"🔢 {n} · Serie {s}" if s else f"🔢 {n}", "━━━━━━━━━━━━━━━━━━"]
if sueldazo_principal or sueldazo_adicionales:
    lineas.append("💰 SUELDAZO FIN DE SEMANA")
    if sueldazo_principal:
        n, s = limpiar(sueldazo_principal.get("numero")), limpiar(sueldazo_principal.get("serie"))
        lineas.append(f"🏆 Principal: {n} · Serie {s}" if s else f"🏆 Principal: {n}")
    if sueldazo_adicionales:
        extras = []
        for r in sueldazo_adicionales:
            n, s = limpiar(r.get("numero")), limpiar(r.get("serie"))
            extras.append(f"{n}/{s}" if s else n)
        lineas.append("🎁 Adic: " + " · ".join(extras))
    lineas.append("━━━━━━━━━━━━━━━━━━")
if eurojackpot:
    n, s = limpiar(eurojackpot.get("numero")), limpiar(eurojackpot.get("serie"))
    b = limpiar(eurojackpot.get("importebote", ""))
    lineas.append("🇪🇺 EUROJACKPOT")
    ej = f"🔢 {n}"
    if s: ej += f" · ☀️ {s}"
    if b and b not in ("", "0", "0.0", "1000000"):
        try:
            bn = int(float(b))
            ej += f" · Bote {bn//1_000_000}M€" if bn >= 1_000_000 else f" · Bote {b}€"
        except ValueError:
            ej += f" · Bote {b}€"
    lineas += [ej, "━━━━━━━━━━━━━━━━━━"]
if mi_dia:
    fmd, ns = separar_mi_dia(limpiar(mi_dia.get("numero")))
    lineas += [f"📅 MI DÍA: {fmd} · 🍀 {ns}", "━━━━━━━━━━━━━━━━━━"]
if triplex:
    lineas.append("🔵 TRIPLEX")
    horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
    items = [f"{horas[i]}→{limpiar(r.get('numero'))}" for i, r in enumerate(triplex)]
    lineas.append("  ".join(items[:3]))
    if len(items) > 3: lineas.append("  ".join(items[3:]))
    lineas.append("━━━━━━━━━━━━━━━━━━")
if dupla:
    lineas.append("🟢 DUPLA (01-15)")
    horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
    items = []
    for i, r in enumerate(dupla):
        p, a, po = formatear_dupla(r.get("numero"))
        items.append(f"{horas[i]}→{p} ant{a}/pos{po}")
    for j in range(0, len(items), 2):
        lineas.append(" · ".join(items[j:j+2]))
    lineas.append("━━━━━━━━━━━━━━━━━━")
if super11:
    lineas.append("🔴 SUPER 11")
    horas = ["10h", "12h", "14h", "17h", "21h"]
    for i, r in enumerate(super11):
        n = limpiar(r.get("numero"))
        while "  " in n: n = n.replace("  ", " ")
        lineas.append(f"{horas[i]}: {n}")
    lineas.append("━━━━━━━━━━━━━━━━━━")
lineas += ["🤝 CSIF ONCE · ESTAMOS POR TI", "📞 TEL: 652338627 · 🌙 Buenas noches"]
texto = "\n".join(lineas).strip()
if len(texto) > 999:
    texto = texto[:996] + "..."
print(f"Longitud principal: {len(texto)}")
with open("whatsapp.txt", "w", encoding="utf-8") as f:
    f.write(texto)
print(texto)

if not APIKEY or not PHONE:
    raise SystemExit("Faltan CALLMEBOT_APIKEY o CALLMEBOT_PHONE")

def enviar(msg, etiqueta):
    if len(msg) > 999:
        msg = msg[:996] + "..."
    url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
    print(f"Enviando {etiqueta} ({len(msg)} chars)...")
    r = requests.get(url, timeout=30)
    print(f"  HTTP {r.status_code}: {r.text[:180]}")
    if r.status_code != 200 or ("error" in r.text.lower() and "queued" not in r.text.lower()):
        raise SystemExit(f"ERROR CallMeBot {etiqueta}: {r.text}")
    return len(msg)

c1 = enviar(texto, "resultados")
c2 = 0
dem = ""
if os.path.exists("demoras_texto.txt"):
    dem = open("demoras_texto.txt", encoding="utf-8").read().strip()
if dem:
    time.sleep(4)
    c2 = enviar(dem, "demoras")
else:
    print("Sin demoras_texto.txt")

guardar_json("whatsapp_enviado.json", {
    "fecha": HOY, "hora": AHORA.strftime("%H:%M:%S"), "metodo": "callmebot",
    "caracteres_resultados": c1, "caracteres_demoras": c2, "demoras_enviadas": bool(dem),
})
print("✅ Enviado por WhatsApp")
