import json
import requests
from bs4 import BeautifulSoup

URL_RSS = "https://www.juegosonce.es/rss/sorteos2.xml"

def main():
    print(f"Descargando RSS desde: {URL_RSS}")
    response = requests.get(URL_RSS)
    response.raise_for_status()
    
    print(f"Respuesta recibida: {len(response.content)} bytes")
    
    # Parsear el XML/RSS usando BeautifulSoup
    soup = BeautifulSoup(response.content, "xml")
    items = soup.find_all("item")
    print(f"Elementos <item> encontrados: {len(items)}")
    
    resultados = []
    for item in items:
        titulo = item.title.text if item.title else ""
        descripcion = item.description.text if item.description else ""
        enlace = item.link.text if item.link else ""
        fecha = item.pubDate.text if item.pubDate else ""
        
        resultados.append({
            "titulo": titulo,
            "descripcion": descripcion,
            "enlace": enlace,
            "fecha": fecha
        })
    
    # Supongamos que procesamos/filtramos los elementos necesarios (por ejemplo, 12)
    resultados_filtrados = resultados[:12]
    print(f"Resultados procesados: {len(resultados_filtrados)}")
    
    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados_filtrados, f, ensure_ascii=False, indent=4)
        
    print("Archivo resultados.json creado correctamente.")

if __name__ == "__main__":
    main()
