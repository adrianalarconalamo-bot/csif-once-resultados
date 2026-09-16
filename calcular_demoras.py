import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HISTORIAL_FILE = "historial_cupones.json"
RESULTADOS_FILE = "resultados.json"
OUTPUT_DEMORAS = "demoras_texto.txt"

TELEFONO = "652 33 86 27"

def cargar_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def es_dia_laborable(dt):
    """Devuelve True si es de Lunes (0) a Viernes (4). Sábados y Domingos no cuentan."""
    return dt.weekday() < 5

def obtener_cupon_hoy():
    """Extrae el número de 5 cifras del Cupón Diario del resultados.json"""
    datos = cargar_json(RESULTADOS_FILE)
    resultados = datos.get("resultados", [])
    
    for r in resultados:
        tipo = str(r.get("tipo", "")).upper()
        if "CUPÓN" in tipo or "CUPON" in tipo:
            numero = str(r.get("numero", "")).strip()
            # Extraer solo dígitos y asegurar que tiene 5 cifras (ej: 33548)
            digitos = "".join(filter(str.isdigit, numero))
            if len(digitos) == 5:
                return digitos
    return None

def actualizar_historial(cupon_hoy, fecha_hoy_str):
    """Añade el cupón de hoy al historial persistente"""
    historial = cargar_json(HISTORIAL_FILE)
    
    # Estructura: {"DD/MM/YYYY": "33548"}
    historial[fecha_hoy_str] = cupon_hoy
    
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)
        
    return historial

def calcular_demoras_posicion(historial, posicion):
    """
    Calcula la demora en días laborables (Lunes a Viernes) para cada cifra (0 al 9)
    en una posición dada (0 para primera cifra, 4 para terminación).
    """
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    cifras_pendientes = set(range(10))
    demoras = {}  # {cifra: {"fecha": "DD/MM/YYYY", "dias": N}}
    
    # Recorremos los días hacia atrás (hasta 365 días)
    dias_laborables_contados = 0
    fecha_cursor = ahora
    
    # Convertimos las fechas del historial a un formato fácil de buscar
    # Esperamos fechas registradas o generadas en formato DD/MM/YYYY
    while cifras_pendientes and (ahora - fecha_cursor).days < 365:
        # Solo contamos si es Lunes a Viernes
        if es_dia_laborable(fecha_cursor):
            dias_laborables_contados += 1
            fecha_str = fecha_cursor.strftime("%d/%m/%Y")
            
            # Buscamos si hay un cupón guardado para esa fecha
            # Si no estuviera la fecha exacta, también busca con ceros opcionales
            cupon = historial.get(fecha_str)
            if not cupon:
                fecha_alt = f"{fecha_cursor.day}/{fecha_cursor.month}/{fecha_cursor.year}"
                cupon = historial.get(fecha_alt)
                
            if cupon and len(cupon) == 5:
                cifra_salida = int(cupon[posicion])
                if cifra_salida in cifras_pendientes:
                    demoras[cifra_salida] = {
                        "fecha": fecha_cursor.strftime("%d %b %y"),
                        "dias": dias_laborables_contados
                    }
                    cifras_pendientes.remove(cifra_salida)
                    
        fecha_cursor -= timedelta(days=1)
        
    # Asignar valor por defecto a las cifras que lleven más tiempo que el historial
    for c in cifras_pendientes:
        demoras[c] = {"fecha": "Más de 30 días", "dias": 30}
        
    # Ordenar de mayor a menor demora
    demoras_ordenadas = sorted(demoras.items(), key=lambda x: x[1]["dias"], reverse=True)
    return demoras_ordenadas

def generar_reporte_demoras():
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    cupon_hoy = obtener_cupon_hoy()
    fecha_hoy_str = ahora.strftime("%d/%m/%Y")
    
    if not cupon_hoy:
        print("⚠️ No se ha encontrado el cupón de hoy para registrar en el historial.")
        historial = cargar_json(HISTORIAL_FILE)
    else:
        print(f"✅ Cupón de hoy ({fecha_hoy_str}) registrado: {cupon_hoy}")
        historial = actualizar_historial(cupon_hoy, fecha_hoy_str)

    # 1. Demoras primera cifra (posición 0)
    demoras_primera = calcular_demoras_posicion(historial, 0)
    
    # 2. Demoras terminaciones (posición 4)
    demoras_terminaciones = calcular_demoras_posicion(historial, 4)
    
    # Maquetación exactamente igual a tu plantilla de WhatsApp
    lineas = []
    
    # Mañana o día siguiente para el título
    manana = ahora + timedelta(days=1)
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    lineas.append(f"*{manana.day}  {meses[manana.month - 1]}  {manana.year}*")
    lineas.append("")
    lineas.append("*Demora el reintegro de las primeras cifras del cupón*")
    lineas.append("Sorteo Lunes a Viernes")
    lineas.append("")
    
    for cifra, datos in demoras_primera:
        dias_txt = f"{datos['dias']:02d} días" if datos['dias'] != 1 else "01 día"
        lineas.append(f"{cifra}  {datos['fecha']}  {dias_txt}")
        
    lineas.append("")
    lineas.append(" Hola la primera cifra solo se cuenta de lunes a viernes,")
    lineas.append(" (_*el sábado y domingo no hay reintegro y esos días no se cuentan.)*")
    lineas.append("")
    lineas.append("*Demora las terminaciones*")
    lineas.append("*del cupón*")
    lineas.append("")
    
    for cifra, datos in demoras_terminaciones:
        dias_txt = f"{datos['dias']:02d} días" if datos['dias'] != 1 else "01 día"
        lineas.append(f"{cifra}  {datos['fecha']}  {dias_txt}")
        
    lineas.append("")
    lineas.append("CSIF ONCE")
    lineas.append("ESTAMOS POR TI")
    lineas.append(f"TEL: *{TELEFONO}*")
    lineas.append("*Buenas noches*")

    texto_final = "\n".join(lineas)
    
    with open(OUTPUT_DEMORAS, "w", encoding="utf-8") as f:
        f.write(texto_final)
        
    print("✅ Reporte de demoras generado con éxito.")

if __name__ == "__main__":
    generar_reporte_demoras()
