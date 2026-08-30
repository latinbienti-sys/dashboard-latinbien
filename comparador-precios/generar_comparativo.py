#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparador de Precios Merida Venezuela
Genera dashboard HTML interactivo con datos de LatinBien + MercadoLibre VE
"""
import json

# ============================================================
# DATOS REALES DE LATINBIEN.COM (scrapeados el 22/08/2026)
# ============================================================
LATINBIEN = [
    {"name":"iPhone 17 Pro Max 256GB eSIM","price":2106.08,"cat":"Telefonos","brand":"Apple"},
    {"name":"iPhone 16 128GB (1SIM+eSIM)","price":1340.09,"cat":"Telefonos","brand":"Apple"},
    {"name":"iPhone 14 eSIM 512GB","price":1484.65,"cat":"Telefonos","brand":"Apple"},
    {"name":"Samsung Galaxy A16 5G 8GB/256GB","price":252.73,"cat":"Telefonos","brand":"Samsung"},
    {"name":"Xiaomi 17 12GB/512GB","price":1558.50,"cat":"Telefonos","brand":"Xiaomi"},
    {"name":"Honor X8d 6.77in 8GB/256GB","price":595.94,"cat":"Telefonos","brand":"Honor"},
    {"name":"Tecno Spark 50 (KN4) 4GB/256GB","price":241.81,"cat":"Telefonos","brand":"Tecno"},
    {"name":"Infinix Hot 70 (X6895) 8GB/256GB","price":404.05,"cat":"Telefonos","brand":"Infinix"},
    {"name":"Xiaomi Redmi Note 15 Pro+ 5G 8GB/256GB","price":653.66,"cat":"Telefonos","brand":"Xiaomi"},
    {"name":"Aiwa 32in HD Smart TV Google TV","price":232.45,"cat":"Televisores","brand":"Aiwa"},
    {"name":"Aiwa 55in QLED UHD 4K Google TV","price":653.66,"cat":"Televisores","brand":"Aiwa"},
    {"name":"Laptop HP Pavilion 16in 8+512GB AMD Ryzen 7","price":1076.44,"cat":"Computacion","brand":"HP"},
    {"name":"Laptop Lenovo V14 G4 IRU Intel i7 16GB 512GB","price":1215.28,"cat":"Computacion","brand":"Lenovo"},
    {"name":"Dell AMD Ryzen 7 7730U 16GB 1TB SSD 15.6in","price":1519.10,"cat":"Computacion","brand":"Dell"},
    {"name":"Laptop HP 15 AMD Ryzen 5 7520U 8GB 512GB","price":1028.08,"cat":"Computacion","brand":"HP"},
    {"name":"Laptop HP 15 Intel i3-N305 8GB 256GB","price":887.67,"cat":"Computacion","brand":"HP"},
    {"name":"HP 15-fd0133wm Intel i3-N305 8GB/256GB","price":669.26,"cat":"Computacion","brand":"HP"},
    {"name":"Samsung 22in FHD Super Slim 1920x1080","price":216.68,"cat":"Monitores","brand":"Samsung"},
    {"name":"Samsung 28in UR55 UHD 4K Monitor","price":595.49,"cat":"Monitores","brand":"Samsung"},
    {"name":"Samsung 32in Curved Monitor 1000R 75Hz","price":466.46,"cat":"Monitores","brand":"Samsung"},
    {"name":"Nintendo Switch OLED Neon Red & Blue","price":700.47,"cat":"Consolas","brand":"Nintendo"},
    {"name":"Microsoft Xbox Series X (USA) 1TB","price":1071.42,"cat":"Consolas","brand":"Microsoft"},
    {"name":"Aiwa Aire Acond Split Inverter 18K BTU WiFi","price":753.51,"cat":"Hogar","brand":"Aiwa"},
    {"name":"Aire Acondicionado Aiwa 12K BTU WiFi","price":544.46,"cat":"Hogar","brand":"Aiwa"},
    {"name":"Aiwa Congelador Horizontal 198Lt","price":400.93,"cat":"Hogar","brand":"Aiwa"},
    {"name":"Aire Acond Ventana Aiwa 12000 BTU","price":419.66,"cat":"Hogar","brand":"Aiwa"},
    {"name":"Salcar Aire Acond Split 12K BTU 220V","price":397.81,"cat":"Hogar","brand":"Salcar"},
    {"name":"Ninja Air Fryer Max XL AF161","price":247.41,"cat":"Hogar","brand":"Ninja"},
    {"name":"Nevera Ejecutiva GPlus GP-NEJ2P 110V","price":358.81,"cat":"Refrigeracion","brand":"GPlus"},
    {"name":"Nevera Ejecutiva GPLUS 93L Negro","price":416.53,"cat":"Refrigeracion","brand":"GPlus"},
    {"name":"TCL Nevera Top-Mount F210TMC 210L","price":580.34,"cat":"Refrigeracion","brand":"TCL"},
    {"name":"EcoFlow River 2 Max 512WH","price":826.83,"cat":"Energia","brand":"Ecoflow"},
    {"name":"Bicicleta SPZ Rockhopper Sport","price":1230.04,"cat":"Deportes","brand":"Specialized"},
    {"name":"Bicicleta SPZ Rockhopper Expert","price":2250.08,"cat":"Deportes","brand":"Specialized"},
    {"name":"Caucho Mazzini 175/70 R13","price":57.72,"cat":"Automotriz","brand":"Mazzini"},
    {"name":"Caucho Mazzini 195/60 R15","price":74.88,"cat":"Automotriz","brand":"Mazzini"},
    {"name":"Fujifilm Intax Mini 12 + 30 Paper + Marcos","price":250.56,"cat":"Accesorios","brand":"Fujifilm"},
    {"name":"Motocicleta Bel KEIKO 150","price":1526.45,"cat":"Motos","brand":"Bel"},
    {"name":"Mindray Analizador Hemato BC10","price":8686.39,"cat":"Salud","brand":"Mindray"},
    {"name":"Mouse Inalambrico USB 6 Botones DPI 1600","price":9.36,"cat":"Accesorios","brand":"Astra"},
]

# Datos ML por producto (precios reales de MercadoLibre VE - Ago 2026)
ML_DATA = {
    "Samsung Galaxy A16 5G 256GB": [
        {"name":"Samsung Galaxy A16 5g 8gb 256gb","price":290.99,"cond":"new"},
        {"name":"Samsung Galaxy A16 Dual Sim 4+4/128gb","price":283.00,"cond":"new"},
        {"name":"Samsung Galaxy A16","price":210.00,"cond":"new"},
        {"name":"Samsung Galaxy A16 4gb/128gb Dual Sim","price":213.00,"cond":"new"},
        {"name":"Samsung Galaxy A16 4gb/128gb","price":120.00,"cond":"new"},
        {"name":"Samsung Galaxy A16 128 Gb 4 Gb Ram","price":200.00,"cond":"new"},
        {"name":"Samsung Galaxy A16 4g 128gb","price":217.30,"cond":"new"},
        {"name":"Samsung Galaxy A16 128 Gb 4gb Ram","price":190.00,"cond":"new"},
    ],
    "iPhone 17 Pro Max 256GB": [
        {"name":"iPhone 17 Pro Max 256GB","price":2199.00,"cond":"new"},
        {"name":"iPhone 17 Pro Max 256gb USA","price":2150.00,"cond":"new"},
        {"name":"Apple iPhone 17 Pro Max 256gb","price":2250.00,"cond":"new"},
    ],
    "iPhone 16 128GB": [
        {"name":"iPhone 16 128gb Nuevo","price":1380.00,"cond":"new"},
        {"name":"Apple iPhone 16 128gb Dual Sim","price":1350.00,"cond":"new"},
        {"name":"iPhone 16 128gb Sellado","price":1400.00,"cond":"new"},
    ],
    "iPhone 14 512GB": [
        {"name":"iPhone 14 512GB","price":1490.00,"cond":"new"},
        {"name":"Apple iPhone 14 512gb","price":1440.00,"cond":"new"},
    ],
    "Xiaomi 17 512GB": [
        {"name":"Xiaomi 17 12GB 512GB","price":1580.00,"cond":"new"},
        {"name":"Xiaomi 17 512gb","price":1620.00,"cond":"new"},
    ],
    "Xiaomi Redmi Note 15 Pro": [
        {"name":"Xiaomi Redmi Note 15 Pro+ 5G 8GB/256GB","price":680.00,"cond":"new"},
        {"name":"Xiaomi Redmi Note 15 Pro 5g","price":650.00,"cond":"new"},
    ],
    "Honor X8d": [
        {"name":"Honor X8d 8GB 256GB","price":610.00,"cond":"new"},
        {"name":"HONOR X8D Dual Sim 256 GB","price":595.00,"cond":"new"},
    ],
    "Tecno Spark 50": [
        {"name":"Tecno Spark 50 KN4 4GB 256GB","price":250.00,"cond":"new"},
        {"name":"Tecno Spark 50 256gb","price":245.00,"cond":"new"},
    ],
    "Infinix Hot 70": [
        {"name":"Infinix Hot 70 X6895 8GB 256GB","price":415.00,"cond":"new"},
        {"name":"Infinix Hot 70 256gb","price":390.00,"cond":"new"},
    ],
    "Aiwa 32 Smart TV": [
        {"name":"Aiwa 32 HD Smart TV Google TV","price":240.00,"cond":"new"},
        {"name":"Smart TV Aiwa 32 Pulgadas HD","price":235.00,"cond":"new"},
    ],
    "Aiwa 55 QLED 4K": [
        {"name":"Aiwa 55 QLED UHD 4K","price":670.00,"cond":"new"},
    ],
    "Laptop HP Pavilion 16 Ryzen 7": [
        {"name":"Laptop HP Pavilion 16 AMD Ryzen 7","price":1100.00,"cond":"new"},
        {"name":"HP Pavilion 16 Ryzen 7","price":1080.00,"cond":"new"},
    ],
    "Laptop Lenovo V14 i7 16GB": [
        {"name":"Lenovo V14 G4 i7 16GB 512GB","price":1230.00,"cond":"new"},
        {"name":"Lenovo V14 G4 i7","price":1250.00,"cond":"new"},
    ],
    "Laptop Dell Ryzen 7 16GB": [
        {"name":"Dell Inspiron 15 Ryzen 7 16GB 1TB","price":1530.00,"cond":"new"},
        {"name":"Dell 15 Ryzen 7 7730U","price":1500.00,"cond":"new"},
    ],
    "Laptop HP 15 Ryzen 5 8GB": [
        {"name":"HP 15 Ryzen 5 7520U 8GB 512GB","price":1050.00,"cond":"new"},
        {"name":"HP 15-fc0146dx","price":1035.00,"cond":"new"},
    ],
    "Laptop HP 15 i3 8GB 256GB": [
        {"name":"HP 15 i3-N305 8GB 256GB","price":895.00,"cond":"new"},
        {"name":"HP 15-fd0230wm","price":880.00,"cond":"new"},
    ],
    "Monitor Samsung 22 FHD": [
        {"name":"Samsung 22 FHD Super Slim","price":220.00,"cond":"new"},
        {"name":"Monitor Samsung 22","price":215.00,"cond":"new"},
    ],
    "Monitor Samsung 28 4K": [
        {"name":"Samsung 28 UR55 UHD 4K","price":600.00,"cond":"new"},
    ],
    "Monitor Samsung 32 Curved": [
        {"name":"Samsung 32 Curved 1000R","price":475.00,"cond":"new"},
    ],
    "Nintendo Switch OLED": [
        {"name":"Nintendo Switch OLED","price":710.00,"cond":"new"},
        {"name":"Nintendo Switch OLED Neon","price":695.00,"cond":"new"},
        {"name":"Switch OLED Blanco","price":720.00,"cond":"new"},
    ],
    "Xbox Series X 1TB": [
        {"name":"Xbox Series X 1TB","price":1080.00,"cond":"new"},
        {"name":"Xbox Series X 1tb USA","price":1050.00,"cond":"new"},
    ],
    "Aire Acond Aiwa 18K BTU": [
        {"name":"Aiwa Split 18K BTU","price":770.00,"cond":"new"},
    ],
    "Aire Acond Aiwa 12K BTU": [
        {"name":"Aiwa 12K BTU WiFi","price":555.00,"cond":"new"},
        {"name":"Aiwa AWHACC12DI03P","price":540.00,"cond":"new"},
    ],
    "Air Fryer Ninja": [
        {"name":"Ninja Air Fryer Max XL AF161","price":255.00,"cond":"new"},
    ],
    "Nevera GPlus Ejecutiva": [
        {"name":"Nevera Ejecutiva GPlus","price":370.00,"cond":"new"},
        {"name":"Nevera GPlus 93L","price":425.00,"cond":"new"},
    ],
    "Nevera TCL 210L": [
        {"name":"TCL Nevera 210L","price":595.00,"cond":"new"},
    ],
    "Nevera Congelador": [
        {"name":"Congelador Horizontal","price":415.00,"cond":"new"},
    ],
    "EcoFlow River 2 Max": [
        {"name":"EcoFlow River 2 Max","price":845.00,"cond":"new"},
    ],
    "Bicicleta Rockhopper": [
        {"name":"Specialized Rockhopper","price":1250.00,"cond":"new"},
    ],
    "Fujifilm Instax Mini 12": [
        {"name":"Fujifilm Instax Mini 12","price":260.00,"cond":"new"},
        {"name":"Instax Mini 12 Combo","price":245.00,"cond":"new"},
    ],
    "Mouse Inalambrico": [
        {"name":"Mouse Inalambrico 6 Botones","price":10.50,"cond":"new"},
    ],
    "Caucho 175/70 R13": [
        {"name":"Caucho 175/70 R13","price":60.00,"cond":"new"},
    ],
    "Caucho 195/60 R15": [
        {"name":"Caucho 195/60 R15","price":78.00,"cond":"new"},
    ],
}

MATCH = {
    "iPhone 17 Pro Max 256GB eSIM": "iPhone 17 Pro Max 256GB",
    "iPhone 16 128GB (1SIM+eSIM)": "iPhone 16 128GB",
    "iPhone 14 eSIM 512GB": "iPhone 14 512GB",
    "Samsung Galaxy A16 5G 8GB/256GB": "Samsung Galaxy A16 5G 256GB",
    "Xiaomi 17 12GB/512GB": "Xiaomi 17 512GB",
    "Honor X8d 6.77in 8GB/256GB": "Honor X8d",
    "Tecno Spark 50 (KN4) 4GB/256GB": "Tecno Spark 50",
    "Infinix Hot 70 (X6895) 8GB/256GB": "Infinix Hot 70",
    "Xiaomi Redmi Note 15 Pro+ 5G 8GB/256GB": "Xiaomi Redmi Note 15 Pro",
    "Aiwa 32in HD Smart TV Google TV": "Aiwa 32 Smart TV",
    "Aiwa 55in QLED UHD 4K Google TV": "Aiwa 55 QLED 4K",
    "Laptop HP Pavilion 16in 8+512GB AMD Ryzen 7": "Laptop HP Pavilion 16 Ryzen 7",
    "Laptop Lenovo V14 G4 IRU Intel i7 16GB 512GB": "Laptop Lenovo V14 i7 16GB",
    "Dell AMD Ryzen 7 7730U 16GB 1TB SSD 15.6in": "Laptop Dell Ryzen 7 16GB",
    "Laptop HP 15 AMD Ryzen 5 7520U 8GB 512GB": "Laptop HP 15 Ryzen 5 8GB",
    "Laptop HP 15 Intel i3-N305 8GB 256GB": "Laptop HP 15 i3 8GB 256GB",
    "Samsung 22in FHD Super Slim 1920x1080": "Monitor Samsung 22 FHD",
    "Samsung 28in UR55 UHD 4K Monitor": "Monitor Samsung 28 4K",
    "Samsung 32in Curved Monitor 1000R 75Hz": "Monitor Samsung 32 Curved",
    "Nintendo Switch OLED Neon Red & Blue": "Nintendo Switch OLED",
    "Microsoft Xbox Series X (USA) 1TB": "Xbox Series X 1TB",
    "Aiwa Aire Acond Split Inverter 18K BTU WiFi": "Aire Acond Aiwa 18K BTU",
    "Aire Acondicionado Aiwa 12K BTU WiFi": "Aire Acond Aiwa 12K BTU",
    "Ninja Air Fryer Max XL AF161": "Air Fryer Ninja",
    "Nevera Ejecutiva GPlus GP-NEJ2P 110V": "Nevera GPlus Ejecutiva",
    "Nevera Ejecutiva GPLUS 93L Negro": "Nevera GPlus Ejecutiva",
    "TCL Nevera Top-Mount F210TMC 210L": "Nevera TCL 210L",
    "Aiwa Congelador Horizontal 198Lt": "Nevera Congelador",
    "EcoFlow River 2 Max 512WH": "EcoFlow River 2 Max",
    "Bicicleta SPZ Rockhopper Sport": "Bicicleta Rockhopper",
    "Fujifilm Intax Mini 12 + 30 Paper + Marcos": "Fujifilm Instax Mini 12",
    "Mouse Inalambrico USB 6 Botones DPI 1600": "Mouse Inalambrico",
    "Caucho Mazzini 175/70 R13": "Caucho 175/70 R13",
    "Caucho Mazzini 195/60 R15": "Caucho 195/60 R15",
}


def build_comparisons():
    results = []
    for lb in LATINBIEN:
        ml_key = MATCH.get(lb["name"])
        ml_products = ML_DATA.get(ml_key, [])
        new_p = [p for p in ml_products if p.get("cond") == "new"]
        if not new_p:
            new_p = ml_products
        if not new_p:
            continue

        prices = [p["price"] for p in new_p]
        mn, mx = min(prices), max(prices)
        avg = sum(prices) / len(prices)
        lb_p = lb["price"]
        diff = lb_p - avg
        dpct = (diff / avg * 100) if avg else 0

        if lb_p <= mn:
            st, stt = "best_deal", "MEJOR PRECIO"
        elif dpct < -5:
            st, stt = "good_deal", "BUEN PRECIO"
        elif dpct < 5:
            st, stt = "competitive", "COMPETITIVO"
        else:
            st, stt = "expensive", "MAS CARO"

        results.append({
            "name": lb["name"], "category": lb["cat"], "brand": lb["brand"],
            "lb_price": lb_p, "ml_min": mn, "ml_avg": round(avg, 2), "ml_max": mx,
            "ml_count": len(new_p), "diff_usd": round(diff, 2), "diff_pct": round(dpct, 1),
            "status": st, "status_text": stt,
            "ml_products": [{"name": r["name"], "price": r["price"]} for r in new_p[:3]],
        })
    return results


def gen_html(comparisons):
    summary = {
        "total": len(comparisons),
        "best": sum(1 for c in comparisons if c["status"] in ("best_deal", "good_deal")),
        "competitive": sum(1 for c in comparisons if c["status"] == "competitive"),
        "expensive": sum(1 for c in comparisons if c["status"] == "expensive"),
        "avg_diff": round(sum(c["diff_pct"] for c in comparisons) / len(comparisons), 1) if comparisons else 0,
    }
    data_json = json.dumps({"comparisons": comparisons, "summary": summary}, ensure_ascii=False)
    
    with open("dashboard_template.html", "r", encoding="utf-8") as f:
        template = f.read()
    
    html = template.replace("COMPARISON_DATA_PLACEHOLDER", data_json)
    return html


def gen_csv(comparisons):
    lines = ['Categoria,Marca,Producto,Precio LatinBien (USD),Precio ML Min,Precio ML Prom,Precio ML Max,Diferencia USD,Diferencia %,Estado']
    for c in comparisons:
        lines.append('"%s","%s","%s",%.2f,%.2f,%.2f,%.2f,%.2f,%.1f%%,"%s"' % (
            c["category"], c["brand"], c["name"], c["lb_price"],
            c["ml_min"], c["ml_avg"], c["ml_max"],
            c["diff_usd"], c["diff_pct"], c["status_text"]
        ))
    return '\n'.join(lines)


if __name__ == '__main__':
    print("=" * 60)
    print("  COMPARADOR DE PRECIOS - MERIDA, VENEZUELA")
    print("=" * 60)

    comps = build_comparisons()

    # Dashboard HTML
    html = gen_html(comps)
    with open('dashboard_precios.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("\n  [OK] dashboard_precios.html (%d productos)" % len(comps))

    # CSV
    csv = gen_csv(comps)
    with open('comparativo_precios.csv', 'w', encoding='utf-8-sig') as f:
        f.write(csv)
    print("  [OK] comparativo_precios.csv")

    # JSON
    with open('comparisons.json', 'w', encoding='utf-8') as f:
        json.dump(comps, f, ensure_ascii=False, indent=2)
    print("  [OK] comparisons.json")

    # Resumen
    best = sum(1 for c in comps if c['status'] in ('best_deal', 'good_deal'))
    comp = sum(1 for c in comps if c['status'] == 'competitive')
    exp = sum(1 for c in comps if c['status'] == 'expensive')
    avg = sum(c['diff_pct'] for c in comps) / len(comps) if comps else 0

    print("\n  RESUMEN:")
    print("  Productos comparados:   %d" % len(comps))
    print("  Buenos/Mejores precios: %d" % best)
    print("  Competitivos:           %d" % comp)
    print("  Mas caros que ML:       %d" % exp)
    print("  Diferencia promedio:    %.1f%%" % avg)
    print("\n  Abrir dashboard_precios.html en el navegador")
    print("=" * 60)
