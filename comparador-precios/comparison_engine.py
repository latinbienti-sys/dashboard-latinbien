"""
Motor de comparación de precios - Normaliza y compara productos entre tiendas
"""
import json
import re
from difflib import SequenceMatcher

# Productos conocidos de LatinBien con precios
LATINBIEN_PRODUCTS = [
    {"name": "iPhone 17 Pro Max 256GB eSIM", "price_usd": 2106.08, "category": "Telefonos", "brand": "Apple"},
    {"name": "iPhone 16 128GB (1SIM+eSIM)", "price_usd": 1340.09, "category": "Telefonos", "brand": "Apple"},
    {"name": "iPhone 14 eSIM 512GB", "price_usd": 1484.65, "category": "Telefonos", "brand": "Apple"},
    {"name": "Samsung Galaxy A16 5G 8GB/256GB", "price_usd": 252.73, "category": "Telefonos", "brand": "Samsung"},
    {"name": "Xiaomi 17 12GB/512GB", "price_usd": 1558.50, "category": "Telefonos", "brand": "Xiaomi"},
    {"name": "Honor X8d 6.77\" 8GB/256GB", "price_usd": 595.94, "category": "Telefonos", "brand": "Honor"},
    {"name": "Tecno Spark 50 (KN4) 4GB/256GB", "price_usd": 241.81, "category": "Telefonos", "brand": "Tecno"},
    {"name": "Infinix Hot 70 (X6895) 8GB/256GB", "price_usd": 404.05, "category": "Telefonos", "brand": "Infinix"},
    {"name": "Xiaomi Redmi Note 15 Pro+ 5G 8GB/256GB", "price_usd": 653.66, "category": "Telefonos", "brand": "Xiaomi"},
    {"name": "Aiwa 32\" HD Smart TV Google TV", "price_usd": 232.45, "category": "Televisores", "brand": "Aiwa"},
    {"name": "Aiwa 55\" QLED UHD 4K Google TV", "price_usd": 653.66, "category": "Televisores", "brand": "Aiwa"},
    {"name": "Laptop HP Pavilion 16\" 8+512GB AMD Ryzen 7", "price_usd": 1076.44, "category": "Computacion", "brand": "HP"},
    {"name": "Laptop Lenovo V14 G4 IRU Intel i7-13620H 16GB 512GB", "price_usd": 1215.28, "category": "Computacion", "brand": "Lenovo"},
    {"name": "Dell AMD Ryzen 7 7730U 16GB 1TB SSD 15.6\"", "price_usd": 1519.10, "category": "Computacion", "brand": "Dell"},
    {"name": "Laptop HP 15-fc0146dx AMD Ryzen 5 7520U 8GB 512GB", "price_usd": 1028.08, "category": "Computacion", "brand": "HP"},
    {"name": "Laptop HP 15-fd0230wm Intel i3-N305 8GB 256GB", "price_usd": 887.67, "category": "Computacion", "brand": "HP"},
    {"name": "HP 15-fd0133wm Intel i3-N305 8GB/256GB", "price_usd": 669.26, "category": "Computacion", "brand": "HP"},
    {"name": "Samsung 22\" FHD Super Slim 1920x1080", "price_usd": 216.68, "category": "Monitores", "brand": "Samsung"},
    {"name": "Samsung 28\" UR55 UHD 4K Monitor", "price_usd": 595.49, "category": "Monitores", "brand": "Samsung"},
    {"name": "Samsung 32\" Curved Monitor 1000R 75Hz", "price_usd": 466.46, "category": "Monitores", "brand": "Samsung"},
    {"name": "Nintendo Switch OLED Neon Red & Blue", "price_usd": 700.47, "category": "Consolas", "brand": "Nintendo"},
    {"name": "Microsoft Xbox Series X (USA) 1TB", "price_usd": 1071.42, "category": "Consolas", "brand": "Microsoft"},
    {"name": "Aiwa Aire Acondicionado Split Inverter 18K BTU WiFi", "price_usd": 753.51, "category": "Hogar", "brand": "Aiwa"},
    {"name": "Aire Acondicionado Aiwa 12K BTU WiFi", "price_usd": 544.46, "category": "Hogar", "brand": "Aiwa"},
    {"name": "Aiwa Congelador Horizontal 198Lt", "price_usd": 400.93, "category": "Hogar", "brand": "Aiwa"},
    {"name": "Aire acondicionado Ventana Aiwa 12000 BTU", "price_usd": 419.66, "category": "Hogar", "brand": "Aiwa"},
    {"name": "Salcar Aire Acondicionado Split 12K BTU 220V", "price_usd": 397.81, "category": "Hogar", "brand": "Salcar"},
    {"name": "Ninja Air Fryer Max XL AF161", "price_usd": 247.41, "category": "Hogar", "brand": "Ninja"},
    {"name": "Nevera Ejecutiva GPlus GP-NEJ2P 110V", "price_usd": 358.81, "category": "Refrigeracion", "brand": "GPlus"},
    {"name": "Nevera Ejecutiva GPLUS 93L Negro", "price_usd": 416.53, "category": "Refrigeracion", "brand": "GPlus"},
    {"name": "TCL Nevera Top-Mount F210TMC 210L", "price_usd": 580.34, "category": "Refrigeracion", "brand": "TCL"},
    {"name": "EcoFlow River 2 Max 512WH", "price_usd": 826.83, "category": "Estacion de carga", "brand": "Ecoflow"},
    {"name": "Bicicleta SPZ Rockhopper Sport", "price_usd": 1230.04, "category": "Deportes", "brand": "Specialized"},
    {"name": "Bicicleta SPZ Rockhopper Expert", "price_usd": 2250.08, "category": "Deportes", "brand": "Specialized"},
    {"name": "Caucho Mazzini 175/70 R13", "price_usd": 57.72, "category": "Automotriz", "brand": "Mazzini"},
    {"name": "Caucho Mazzini 195/60 R15", "price_usd": 74.88, "category": "Automotriz", "brand": "Mazzini"},
    {"name": "Fujifilm Intax Mini 12 + 30 Paper + Marcos", "price_usd": 250.56, "category": "Accesorios", "brand": "Fujifilm"},
    {"name": "Motocicleta Bel KEIKO 150", "price_usd": 1526.45, "category": "Motos", "brand": "Bel"},
    {"name": "Mindray Analizador Hemato BC10", "price_usd": 8686.39, "category": "Salud", "brand": "Mindray"},
    {"name": "Mouse Inalambrico USB 6 Botones DPI 1600", "price_usd": 9.36, "category": "Accesorios", "brand": "Astra"},
]

# Mapeo de queries ML -> producto LatinBien
QUERY_TO_LATINBIEN = {
    "iPhone 17 Pro Max 256GB": "iPhone 17 Pro Max 256GB eSIM",
    "iPhone 16 128GB": "iPhone 16 128GB (1SIM+eSIM)",
    "iPhone 14 512GB": "iPhone 14 eSIM 512GB",
    "Samsung Galaxy A16 5G 256GB": "Samsung Galaxy A16 5G 8GB/256GB",
    "Xiaomi 17 512GB": "Xiaomi 17 12GB/512GB",
    "Honor X8d": "Honor X8d 6.77\" 8GB/256GB",
    "Tecno Spark 50": "Tecno Spark 50 (KN4) 4GB/256GB",
    "Infinix Hot 70": "Infinix Hot 70 (X6895) 8GB/256GB",
    "Xiaomi Redmi Note 15 Pro": "Xiaomi Redmi Note 15 Pro+ 5G 8GB/256GB",
    "Aiwa 32 pulgadas Smart TV": "Aiwa 32\" HD Smart TV Google TV",
    "Aiwa 55 QLED 4K": "Aiwa 55\" QLED UHD 4K Google TV",
    "Laptop HP Pavilion 16 Ryzen 7": "Laptop HP Pavilion 16\" 8+512GB AMD Ryzen 7",
    "Laptop Lenovo V14 i7 16GB": "Laptop Lenovo V14 G4 IRU Intel i7-13620H 16GB 512GB",
    "Laptop Dell Ryzen 7 16GB": "Dell AMD Ryzen 7 7730U 16GB 1TB SSD 15.6\"",
    "Laptop HP 15 Ryzen 5 8GB": "Laptop HP 15-fc0146dx AMD Ryzen 5 7520U 8GB 512GB",
    "Laptop HP 15 i3 8GB 256GB": "Laptop HP 15-fd0230wm Intel i3-N305 8GB 256GB",
    "Monitor Samsung 22 pulgadas FHD": "Samsung 22\" FHD Super Slim 1920x1080",
    "Monitor Samsung 28 4K UR55": "Samsung 28\" UR55 UHD 4K Monitor",
    "Monitor Samsung 32 Curved": "Samsung 32\" Curved Monitor 1000R 75Hz",
    "Nintendo Switch OLED": "Nintendo Switch OLED Neon Red & Blue",
    "Xbox Series X 1TB": "Microsoft Xbox Series X (USA) 1TB",
    "Aire acondicionado Aiwa 18000 BTU": "Aiwa Aire Acondicionado Split Inverter 18K BTU WiFi",
    "Aire acondicionado Aiwa 12000 BTU": "Aire Acondicionado Aiwa 12K BTU WiFi",
    "Air Fryer Ninja": "Ninja Air Fryer Max XL AF161",
    "Nevera ejecutiva GPlus": "Nevera Ejecutiva GPlus GP-NEJ2P 110V",
    "Nevera TCL 210 litros": "TCL Nevera Top-Mount F210TMC 210L",
    "Nevera congelador horizontal": "Aiwa Congelador Horizontal 198Lt",
    "EcoFlow River 2 Max": "EcoFlow River 2 Max 512WH",
    "Bicicleta Specialized Rockhopper": "Bicicleta SPZ Rockhopper Sport",
    "Fujifilm Instax Mini 12": "Fujifilm Intax Mini 12 + 30 Paper + Marcos",
    "Mouse inalambrico 6 botones": "Mouse Inalambrico USB 6 Botones DPI 1600",
    "Caucho 175/70 R13": "Caucho Mazzini 175/70 R13",
    "Caucho 195/60 R15": "Caucho Mazzini 195/60 R15",
    "Motocicleta Bel KEIKO 150": "Motocicleta Bel KEIKO 150",
}


def find_latinbien_product(query):
    """Encuentra el producto de LatinBien correspondiente a una query"""
    if query in QUERY_TO_LATINBIEN:
        target_name = QUERY_TO_LATINBIEN[query]
        for p in LATINBIEN_PRODUCTS:
            if p["name"] == target_name:
                return p
    return None


def build_comparisons(ml_results):
    """
    Construye comparaciones entre LatinBien y MercadoLibre
    """
    comparisons = []
    
    for query, ml_products in ml_results.items():
        lb_product = find_latinbien_product(query)
        if not lb_product:
            continue
        
        # Filter new items only and sort by price
        new_products = [p for p in ml_products if p.get("condition") == "new"]
        if not new_products:
            new_products = ml_products  # fallback to all
        
        new_products.sort(key=lambda x: x["price_usd"])
        
        if not new_products:
            continue
        
        # Calculate stats
        ml_prices = [p["price_usd"] for p in new_products]
        min_ml = min(ml_prices)
        max_ml = max(ml_prices)
        avg_ml = sum(ml_prices) / len(ml_prices)
        
        lb_price = lb_product["price_usd"]
        
        # Determine if LatinBien is cheaper
        diff_vs_min = lb_price - min_ml
        diff_vs_avg = lb_price - avg_ml
        diff_pct_vs_min = (diff_vs_min / min_ml * 100) if min_ml > 0 else 0
        diff_pct_vs_avg = (diff_vs_avg / avg_ml * 100) if avg_ml > 0 else 0
        
        # Best deal status
        if lb_price <= min_ml:
            status = "best_deal"
            status_text = "MEJOR PRECIO"
        elif diff_pct_vs_avg < -5:
            status = "good_deal"
            status_text = "BUEN PRECIO"
        elif diff_pct_vs_avg < 5:
            status = "competitive"
            status_text = "COMPETITIVO"
        else:
            status = "expensive"
            status_text = "MÁS CARO"
        
        comparison = {
            "query": query,
            "category": lb_product["category"],
            "brand": lb_product["brand"],
            "latinbien": {
                "name": lb_product["name"],
                "price_usd": lb_price,
            },
            "mercadolibre": {
                "min_price": min_ml,
                "max_price": max_ml,
                "avg_price": round(avg_ml, 2),
                "count": len(new_products),
                "top_results": new_products[:3],  # Top 3 cheapest
            },
            "comparison": {
                "diff_vs_min": round(diff_vs_min, 2),
                "diff_vs_avg": round(diff_vs_avg, 2),
                "diff_pct_vs_min": round(diff_pct_vs_min, 1),
                "diff_pct_vs_avg": round(diff_pct_vs_avg, 1),
                "status": status,
                "status_text": status_text,
            }
        }
        
        comparisons.append(comparison)
    
    return comparisons


def generate_summary(comparisons):
    """Genera resumen estadístico"""
    if not comparisons:
        return {}
    
    statuses = {}
    for c in comparisons:
        s = c["comparison"]["status"]
        if s not in statuses:
            statuses[s] = 0
        statuses[s] += 1
    
    diffs = [c["comparison"]["diff_pct_vs_avg"] for c in comparisons]
    
    return {
        "total_products": len(comparisons),
        "statuses": statuses,
        "avg_diff_pct": round(sum(diffs) / len(diffs), 1),
        "best_deals": statuses.get("best_deal", 0) + statuses.get("good_deal", 0),
        "competitive": statuses.get("competitive", 0),
        "expensive": statuses.get("expensive", 0),
    }


if __name__ == "__main__":
    # Load ML results
    try:
        with open("mercadolibre_results.json", "r", encoding="utf-8") as f:
            ml_results = json.load(f)
    except FileNotFoundError:
        print("❌ Ejecuta scraper_mercadolibre.py primero")
        exit(1)
    
    comparisons = build_comparisons(ml_results)
    summary = generate_summary(comparisons)
    
    # Save
    output = {
        "comparisons": comparisons,
        "summary": summary,
        "latinbien_products": LATINBIEN_PRODUCTS,
    }
    
    with open("comparisons.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n💾 Comparaciones guardadas en comparisons.json")
