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

# ============================================================
# MENSAJE 1 — Detallado (Sueldazo + Mi Día + Triplex + Dupla)
# ============================================================

lineas1 = [
    "📢 CSIF INFORMA",
    "",
    "🎟️✨ RESULTADOS ONCE ✨",
    f"📅 {HOY}",
    "",
    "━━━━━━━━━━━━━━━━━━",
]

if sueldazo_principal or sueldazo_adicionales:
    lineas1.append("💰🌟 SUELDAZO FIN DE SEMANA")
    if sueldazo_principal:
        n = limpiar(sueldazo_principal.get("numero"))
        s = limpiar(sueldazo_principal.get("serie"))
        lineas1 += [
            "🏆 PREMIO PRINCIPAL",
            f"🔢 Número: {n}",
            f"🔖 Serie: {s}" if s else "",
            "💶 2.000 € al mes durante 10 años",
            "",
        ]
    if sueldazo_adicionales:
        lineas1.append("🎁 PREMIOS ADICIONALES")
        for r in sueldazo_adicionales:
            n = limpiar(r.get("numero"))
            s = limpiar(r.get("serie"))
            lineas1.append(f"🎁 {n} — Serie {s}" if s else f"🎁 {n}")
        lineas1.append("")
    lineas1.append("━━━━━━━━━━━━━━━━━━")

if mi_dia:
    fmd, ns = separar_mi_dia(limpiar(mi_dia.get("numero")))
    lineas1 += [
        "📅🍀 MI DÍA",
        f"📆 Fecha: {fmd}",
        f"🍀 Número de la suerte: {ns}",
        "",
        "━━━━━━━━━━━━━━━━━━",
    ]

if triplex:
    lineas1.append("🔵🎯 TRIPLEX")
    horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
    for i, r in enumerate(triplex):
        n = limpiar(r.get("numero"))
        h = horas[i] if i < len(horas) else ""
        lineas1.append(f"🕐 {h} h · Sorteo {i+1} → {n}")
    lineas1 += ["", "━━━━━━━━━━━━━━━━━━"]

if dupla:
    lineas1 += [
        "🟢🔄 DUPLA",
        "ℹ️ Números del 01 al 15",
    ]
    horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
    for i, r in enumerate(dupla):
        p, a, po = formatear_dupla(r.get("numero"))
        h = horas[i] if i < len(horas) else ""
        lineas1.append(f"🕐 {h} h · Sorteo {i+1} → {p} (Ant. {a} · Post. {po})")
    lineas1 += ["", "━━━━━━━━━━━━━━━━━━"]

lineas1 += [
    "🤝 CSIF ONCE · ESTAMOS POR TI",
    "📞 TEL: 652338627",
    "🌙 Buenas noches.",
    "CSIF, todo por todos.",
    HOY,
]

msg1 = "\n".join([l for l in lineas1 if l is not None]).strip()

# ============================================================
# MENSAJE 2 — Super 11 compacto + Demoras compactas (≤999)
# ============================================================

lineas2 = ["🔴🔥 SUPER 11"]
if super11:
    horas = ["10:00", "12:00", "14:00", "17:00", "21:15"]
    for i, r in enumerate(super11):
        n = limpiar(r.get("numero"))
        h = horas[i] if i < len(horas) else ""
        lineas2.append(f"🕐 {h}→{n}")
lineas2.append("")
lineas2.append("━━━━━━━━━━━━━━━━━━")

# Demoras compactas
if os.path.exists("demoras_texto.txt"):
    dem_raw = open("demoras_texto.txt", encoding="utf-8").read().strip()
    # Intentamos parsear de forma simple las líneas de demoras
    # Formato esperado:
    # 0 07/10/2026 02 días
    lineas2.append("*Demora primeras cifras (L-V)*")
    # Extraemos solo las líneas de números
    primeras = []
    terminaciones = []
    seccion = None
    for line in dem_raw.splitlines():
        line = line.strip()
        if "primeras cifras" in line.lower() or "reintegro de las primeras" in line.lower():
            seccion = "primeras"
            continue
        if "terminaciones" in line.lower():
            seccion = "terminaciones"
            continue
        if line and line[0].isdigit() and "/" in line:
            partes = line.split()
            if len(partes) >= 3:
                num = partes[0]
                fecha = partes[1][:5]  # dd/mm
                dias = partes[2]
                entry = f"{num} {fecha} {dias}d"
                if seccion == "primeras":
                    primeras.append(entry)
                elif seccion == "terminaciones":
                    terminaciones.append(entry)
    # Agrupar de 3 en 3
    def agrupar(lista):
        res = []
        for i in range(0, len(lista), 3):
            res.append(" · ".join(lista[i:i+3]))
        return res
    for g in agrupar(primeras):
        lineas2.append(g)
    lineas2.append("")
    lineas2.append("(sáb/dom no cuentan)")
    lineas2.append("")
    lineas2.append("*Demora terminaciones*")
    for g in agrupar(terminaciones):
        lineas2.append(g)
else:
    lineas2 += [
        "*Demora primeras cifras (L-V)*",
        "(ver demoras_texto.txt)",
        "",
        "*Demora terminaciones*",
        "(ver demoras_texto.txt)",
    ]

lineas2 += [
    "",
    "CSIF ONCE · ESTAMOS POR TI",
    "TEL: *652338627*",
    "*Buenas noches*",
]

msg2 = "\n".join(lineas2).strip()

print(f"Mensaje 1: {len(msg1)} caracteres")
print(f"Mensaje 2: {len(msg2)} caracteres")

with open("whatsapp.txt", "w", encoding="utf-8") as f:
    f.write(msg1 + "\n\n---MENSAJE 2---\n\n" + msg2)

if not APIKEY or not PHONE:
    raise SystemExit("Faltan CALLMEBOT_APIKEY o CALLMEBOT_PHONE")

def enviar(msg, etiqueta):
    if len(msg) > 999:
        print(f"⚠️ {etiqueta} tiene {len(msg)} chars (>999). Se envía igual.")
    url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={urllib.parse.quote(msg)}&apikey={APIKEY}"
    print(f"Enviando {etiqueta} ({len(msg)} chars)...")
    r = requests.get(url, timeout=30)
    print(f"  HTTP {r.status_code}: {r.text[:180]}")
    if r.status_code != 200 or ("error" in r.text.lower() and "queued" not in r.text.lower()):
        raise SystemExit(f"ERROR CallMeBot {etiqueta}: {r.text}")
    return len(msg)

c1 = enviar(msg1, "resultados-parte1")
time.sleep(3)
c2 = enviar(msg2, "resultados-parte2+demoras")

guardar_json("whatsapp_enviado.json", {
    "fecha": HOY,
    "hora": AHORA.strftime("%H:%M:%S"),
    "metodo": "callmebot",
    "caracteres_msg1": c1,
    "caracteres_msg2": c2,
    "formato": "2 mensajes detallados CSIF (≤999)",
})
print("✅ Enviado por WhatsApp (2 mensajes)")
