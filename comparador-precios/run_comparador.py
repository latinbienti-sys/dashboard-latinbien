"""
Script principal - Genera el comparativo de precios completo
Ejecuta scrapers, compara precios y genera dashboard HTML
"""
import json
import sys
import os

# Importar módulos
from comparison_engine import LATINBIEN_PRODUCTS, build_comparisons, generate_summary, QUERY_TO_LATINBIEN
from scraper_mercadolibre import search_multiple_queries, SEARCH_QUERIES


def main():
    print("=" * 70)
    print("  COMPARADOR DE PRECIOS - MÉRIDA, VENEZUELA")
    print("  LatinBien vs MercadoLibre VE vs Tiendas Locales")
    print("=" * 70)
    
    # Paso 1: Buscar productos en MercadoLibre
    print("\n📡 Paso 1: Buscando productos en MercadoLibre Venezuela...")
    ml_results = search_multiple_queries(SEARCH_QUERIES)
    
    # Guardar resultados ML
    with open("mercadolibre_results.json", "w", encoding="utf-8") as f:
        json.dump(ml_results, f, ensure_ascii=False, indent=2)
    
    total_ml = sum(len(v) for v in ml_results.values())
    print(f"\n✅ {total_ml} resultados de ML obtenidos")
    
    # Paso 2: Construir comparaciones
    print("\n📊 Paso 2: Construyendo comparaciones...")
    comparisons = build_comparisons(ml_results)
    summary = generate_summary(comparisons)
    
    # Guardar comparaciones
    output = {
        "comparisons": comparisons,
        "summary": summary,
        "latinbien_products": LATINBIEN_PRODUCTS,
    }
    with open("comparisons.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Paso 3: Generar dashboard HTML
    print("\n🎨 Paso 3: Generando dashboard interactivo...")
    generate_dashboard(comparisons, summary)
    
    # Paso 4: Generar CSV para Excel
    print("\n📋 Paso 4: Generando CSV para análisis...")
    generate_csv(comparisons)
    
    # Resumen final
    print("\n" + "=" * 70)
    print("  RESUMEN DEL ANÁLISIS")
    print("=" * 70)
    print(f"  Total productos comparados: {summary['total_products']}")
    print(f"  Buenos/Mejores precios:     {summary['best_deals']}")
    print(f"  Precios competitivos:       {summary['competitive']}")
    print(f"  Más caros que ML:           {summary['expensive']}")
    print(f"  Diferencia promedio:        {summary['avg_diff_pct']}%")
    print("=" * 70)
    print("\n  Archivos generados:")
    print("  📄 dashboard_precios.html    → Dashboard interactivo")
    print("  📄 comparativo_precios.csv   → Para Excel/Google Sheets")
    print("  📄 comparisons.json          → Datos completos JSON")
    print("  📄 mercadolibre_results.json → Resultados crudos ML")
    print("=" * 70)


def generate_dashboard(comparisons, summary):
    """Genera el dashboard HTML final"""
    
    # Preparar datos para JavaScript
    js_data = json.dumps({
        "comparisons": comparisons,
        "summary": summary,
        "latinbien_products": LATINBIEN_PRODUCTS,
    }, ensure_ascii=False)
    
    # Leer template
    with open("dashboard_template.html", "r", encoding="utf-8") as f:
        template = f.read()
    
    # Reemplazar placeholder con datos reales
    html = template.replace("COMPARISON_DATA_PLACEHOLDER", js_data)
    
    # Escribir dashboard final
    with open("dashboard_precios.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("  ✅ dashboard_precios.html generado")


def generate_csv(comparisons):
    """Genera CSV para análisis en Excel"""
    import csv
    
    with open("comparativo_precios.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "Categoría", "Marca", "Producto LatinBien",
            "Precio LatinBien (USD)", "Precio ML Mín (USD)", "Precio ML Prom (USD)",
            "Precio ML Máx (USD)", "Diferencia vs Prom (USD)", "Diferencia %",
            "Estado", "# Ofertas ML", "URL LatinBien", "URL Mejor Precio ML"
        ])
        
        # Rows
        for c in comparisons:
            cmp = c["comparison"]
            ml = c["mercadolibre"]
            lb = c["latinbien"]
            
            best_ml_url = ml["top_results"][0]["url"] if ml["top_results"] else ""
            
            writer.writerow([
                c["category"], c["brand"], lb["name"],
                f"{lb['price_usd']:.2f}", f"{ml['min_price']:.2f}",
                f"{ml['avg_price']:.2f}", f"{ml['max_price']:.2f}",
                f"{cmp['diff_vs_avg']:.2f}", f"{cmp['diff_pct_vs_avg']:.1f}%",
                cmp["status_text"], ml["count"],
                "", best_ml_url
            ])
    
    print("  ✅ comparativo_precios.csv generado")


if __name__ == "__main__":
    main()
