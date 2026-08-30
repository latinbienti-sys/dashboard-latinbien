"""
Scraper de MercadoLibre Venezuela - Busca productos por nombre y extrae precios
Usa la API pública de MercadoLibre para buscar productos
"""
import requests
import json
import time
import re

API_BASE = "https://api.mercadolibre.com/sites/MLV/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


def search_product(query, limit=10):
    """
    Busca un producto en MercadoLibre Venezuela
    """
    params = {
        "q": query,
        "limit": limit,
        "sort": "relevance",
    }
    
    try:
        resp = requests.get(API_BASE, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  ⚠️ Error searching '{query}': {e}")
        return []
    
    results = []
    for item in data.get("results", []):
        title = item.get("title", "")
        price = item.get("price", 0)
        currency = item.get("currency_id", "USD")
        condition = item.get("condition", "unknown")
        seller = item.get("seller", {}).get("nickname", "N/A")
        thumbnail = item.get("thumbnail", "")
        permalink = item.get("permalink", "")
        shipping = item.get("shipping", {})
        free_shipping = shipping.get("free_shipping", False)
        
        # Only include new items with reasonable prices
        if price > 0:
            results.append({
                "name": title,
                "price_usd": price if currency == "USD" else price,  # ML VE uses USD
                "currency": currency,
                "condition": condition,
                "seller": seller,
                "url": permalink,
                "thumbnail": thumbnail,
                "free_shipping": free_shipping,
                "source": "mercadolibre_ve"
            })
    
    return results


def search_multiple_queries(queries):
    """
    Busca múltiples queries y retorna resultados agrupados
    """
    all_results = {}
    
    print("=" * 60)
    print("BUSCADOR DE MERCADOLIBRE VENEZUELA")
    print("=" * 60)
    
    for query in queries:
        print(f"\n🔍 Buscando: {query}")
        results = search_product(query, limit=5)
        all_results[query] = results
        
        if results:
            prices = [r["price_usd"] for r in results]
            print(f"  ✅ {len(results)} resultados | Precio mín: ${min(prices):.2f} | Máx: ${max(prices):.2f}")
        else:
            print(f"  ❌ Sin resultados")
        
        time.sleep(0.5)  # Rate limiting
    
    return all_results


# Queries de productos similares a LatinBien para buscar
SEARCH_QUERIES = [
    # Telefonos
    "iPhone 17 Pro Max 256GB",
    "iPhone 16 128GB",
    "iPhone 14 512GB",
    "Samsung Galaxy A16 5G 256GB",
    "Xiaomi 17 512GB",
    "Honor X8d",
    "Tecno Spark 50",
    "Infinix Hot 70",
    "Xiaomi Redmi Note 15 Pro",
    
    # Televisores
    "Aiwa 32 pulgadas Smart TV",
    "Aiwa 55 QLED 4K",
    
    # Laptops
    "Laptop HP Pavilion 16 Ryzen 7",
    "Laptop Lenovo V14 i7 16GB",
    "Laptop Dell Ryzen 7 16GB",
    "Laptop HP 15 Ryzen 5 8GB",
    "Laptop HP 15 i3 8GB 256GB",
    
    # Monitores
    "Monitor Samsung 22 pulgadas FHD",
    "Monitor Samsung 28 4K UR55",
    "Monitor Samsung 32 Curved",
    
    # Consolas
    "Nintendo Switch OLED",
    "Xbox Series X 1TB",
    
    # Hogar / Electro
    "Aire acondicionado Aiwa 18000 BTU",
    "Aire acondicionado Aiwa 12000 BTU",
    "Air Fryer Ninja",
    "Nevera ejecutiva GPlus",
    "Nevera TCL 210 litros",
    "Nevera congelador horizontal",
    
    # Energia
    "EcoFlow River 2 Max",
    
    # Deportes
    "Bicicleta Specialized Rockhopper",
    
    # Accesorios
    "Fujifilm Instax Mini 12",
    "Mouse inalambrico 6 botones",
    
    # Cauchos
    "Caucho 175/70 R13",
    "Caucho 195/60 R15",
    
    # Motos
    "Motocicleta Bel KEIKO 150",
]


if __name__ == "__main__":
    results = search_multiple_queries(SEARCH_QUERIES)
    
    # Save results
    output_file = "mercadolibre_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    total = sum(len(v) for v in results.values())
    print(f"\n{'=' * 60}")
    print(f"💾 Guardados {total} resultados en {output_file}")
    print(f"{'=' * 60}")
