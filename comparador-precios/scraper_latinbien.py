"""
Scraper de LatinBien.com - Extrae todos los productos con precios
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re

BASE_URL = "https://latinbien.com"
SHOP_URL = f"{BASE_URL}/shop"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-VE,es;q=0.9,en;q=0.8",
}

def scrape_page(page_num=1, order="list_price+asc"):
    """Scrape una página del shop"""
    url = f"{SHOP_URL}?page={page_num}&order={order}"
    print(f"  Fetching page {page_num}: {url}")
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  Error fetching page {page_num}: {e}")
        return [], 0
    
    soup = BeautifulSoup(resp.text, "html.parser")
    products = []
    
    # Find product cards - they contain product info
    # Looking for product links with prices
    product_cards = soup.select("a[href*='/shop/']")
    
    seen_urls = set()
    
    for card in product_cards:
        href = card.get("href", "")
        if not href or href in seen_urls or "/shop/cart" in href or "/shop/wishlist" in href or "/shop/change_pricelist" in href or "/shop/category" in href or "/shop/page" in href or "/shop?order" in href:
            continue
        
        # Try to find the product name and price
        name_el = card.select_one("h5, h4, h3, .oe_product_name, strong")
        price_text = card.get_text()
        
        # Extract price using regex
        price_match = re.search(r'\$\s*([\d.,]+)', price_text)
        
        if name_el and price_match:
            name = name_el.get_text(strip=True)
            price_str = price_match.group(1).replace(".", "").replace(",", ".")
            try:
                price = float(price_str)
            except:
                continue
            
            full_url = BASE_URL + href if href.startswith("/") else href
            
            if full_url not in seen_urls and name and price > 0:
                seen_urls.add(full_url)
                products.append({
                    "name": name,
                    "price_usd": price,
                    "url": full_url,
                    "source": "latinbien"
                })
    
    # Get total items
    total_match = re.search(r'(\d+)\s*items?\s*encontrados?', soup.get_text())
    total = int(total_match.group(1)) if total_match else 410
    
    return products, total


def scrape_all_products():
    """Scrape todas las páginas del shop"""
    all_products = []
    page = 1
    total = 410  # Known from the site
    
    print("=" * 60)
    print("SCRAPER DE LATINBIEN.COM")
    print("=" * 60)
    
    while True:
        print(f"\n📄 Página {page}...")
        products, page_total = scrape_page(page)
        
        if not products:
            print("  No more products found.")
            break
        
        all_products.extend(products)
        print(f"  ✅ {len(products)} productos extraídos (Total acumulado: {len(all_products)})")
        
        # Check if we've gotten all products (roughly 20 per page)
        if len(products) < 10:
            break
        
        page += 1
        
        if page > 25:  # Safety limit
            break
        
        time.sleep(1.5)  # Be respectful
    
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {len(all_products)} productos extraídos de LatinBien")
    print(f"{'=' * 60}")
    
    return all_products


# Known products from manual extraction (fallback)
KNOWN_PRODUCTS = [
    # Telefonos
    {"name": "iPhone 17 Pro Max 256GB eSIM", "price_usd": 2106.08, "category": "Telefonos", "brand": "Apple"},
    {"name": "iPhone 16 128GB (1SIM+eSIM)", "price_usd": 1340.09, "category": "Telefonos", "brand": "Apple"},
    {"name": "iPhone 14 eSIM 512GB", "price_usd": 1484.65, "category": "Telefonos", "brand": "Apple"},
    {"name": "Samsung Galaxy A16 5G 8GB/256GB", "price_usd": 252.73, "category": "Telefonos", "brand": "Samsung"},
    {"name": "Xiaomi 17 12GB/512GB", "price_usd": 1558.50, "category": "Telefonos", "brand": "Xiaomi"},
    {"name": "Honor X8d 6.77\" 8GB/256GB", "price_usd": 595.94, "category": "Telefonos", "brand": "Honor"},
    {"name": "Tecno Spark 50 (KN4) 4GB/256GB", "price_usd": 241.81, "category": "Telefonos", "brand": "Tecno"},
    {"name": "Infinix Hot 70 (X6895) 8GB/256GB", "price_usd": 404.05, "category": "Telefonos", "brand": "Infinix"},
    {"name": "Xiaomi Redmi Note 15 Pro+ 5G 8GB/256GB", "price_usd": 653.66, "category": "Telefonos", "brand": "Xiaomi"},
    
    # Televisores
    {"name": "Aiwa 32\" HD Smart TV Google TV", "price_usd": 232.45, "category": "Televisores", "brand": "Aiwa"},
    {"name": "Aiwa 55\" QLED UHD 4K Google TV", "price_usd": 653.66, "category": "Televisores", "brand": "Aiwa"},
    
    # Computacion - Laptops
    {"name": "Laptop HP Pavilion 16\" 8+512GB AMD Ryzen 7", "price_usd": 1076.44, "category": "Computacion", "brand": "HP"},
    {"name": "Laptop Lenovo V14 G4 IRU Intel i7-13620H 16GB 512GB", "price_usd": 1215.28, "category": "Computacion", "brand": "Lenovo"},
    {"name": "Dell AMD Ryzen 7 7730U 16GB 1TB SSD 15.6\"", "price_usd": 1519.10, "category": "Computacion", "brand": "Dell"},
    {"name": "Laptop HP 15-fc0146dx AMD Ryzen 5 7520U 8GB 512GB", "price_usd": 1028.08, "category": "Computacion", "brand": "HP"},
    {"name": "Laptop HP 15-fd0230wm Intel i3-N305 8GB 256GB", "price_usd": 887.67, "category": "Computacion", "brand": "HP"},
    {"name": "HP 15-fd0133wm Intel i3-N305 8GB/256GB", "price_usd": 669.26, "category": "Computacion", "brand": "HP"},
    
    # Monitores
    {"name": "Samsung 22\" FHD Super Slim 1920x1080", "price_usd": 216.68, "category": "Monitores", "brand": "Samsung"},
    {"name": "Samsung 28\" UR55 UHD 4K Monitor", "price_usd": 595.49, "category": "Monitores", "brand": "Samsung"},
    {"name": "Samsung 32\" Curved Monitor 1000R 75Hz", "price_usd": 466.46, "category": "Monitores", "brand": "Samsung"},
    
    # Consolas
    {"name": "Nintendo Switch OLED Neon Red & Blue", "price_usd": 700.47, "category": "Consolas", "brand": "Nintendo"},
    {"name": "Microsoft Xbox Series X (USA) 1TB", "price_usd": 1071.42, "category": "Consolas", "brand": "Microsoft"},
    
    # Hogar
    {"name": "Aiwa Aire Acondicionado Split Inverter 18K BTU WiFi", "price_usd": 753.51, "category": "Hogar", "brand": "Aiwa"},
    {"name": "Aire Acondicionado Aiwa 12K BTU WiFi", "price_usd": 544.46, "category": "Hogar", "brand": "Aiwa"},
    {"name": "Aiwa Congelador Horizontal 198Lt", "price_usd": 400.93, "category": "Hogar", "brand": "Aiwa"},
    {"name": "Aire acondicionado Ventana Aiwa 12000 BTU", "price_usd": 419.66, "category": "Hogar", "brand": "Aiwa"},
    {"name": "Salcar Aire Acondicionado Split 12K BTU 220V", "price_usd": 397.81, "category": "Hogar", "brand": "Salcar"},
    {"name": "Ninja Air Fryer Max XL AF161", "price_usd": 247.41, "category": "Hogar", "brand": "Ninja"},
    
    # Refrigeracion
    {"name": "Nevera Ejecutiva GPlus GP-NEJ2P 110V", "price_usd": 358.81, "category": "Refrigeracion", "brand": "GPlus"},
    {"name": "Nevera Ejecutiva GPLUS 93L Negro", "price_usd": 416.53, "category": "Refrigeracion", "brand": "GPlus"},
    {"name": "TCL Nevera Top-Mount F210TMC 210L", "price_usd": 580.34, "category": "Refrigeracion", "brand": "TCL"},
    
    # Estacion de carga
    {"name": "EcoFlow River 2 Max 512WH", "price_usd": 826.83, "category": "Estacion de carga", "brand": "Ecoflow"},
    
    # Deportes
    {"name": "Bicicleta SPZ Rockhopper Sport", "price_usd": 1230.04, "category": "Deportes", "brand": "Specialized"},
    {"name": "Bicicleta SPZ Rockhopper Expert", "price_usd": 2250.08, "category": "Deportes", "brand": "Specialized"},
    
    # Automotriz
    {"name": "Caucho Mazzini 175/70 R13", "price_usd": 57.72, "category": "Automotriz", "brand": "Mazzini"},
    {"name": "Caucho Mazzini 195/60 R15", "price_usd": 74.88, "category": "Automotriz", "brand": "Mazzini"},
    
    # Accesorios / Camara
    {"name": "Fujifilm Intax Mini 12 + 30 Paper + Marcos", "price_usd": 250.56, "category": "Accesorios", "brand": "Fujifilm"},
    
    # Motos
    {"name": "Motocicleta Bel KEIKO 150", "price_usd": 1526.45, "category": "Motos", "brand": "Bel"},
    
    # Medicos
    {"name": "Mindray Analizador Hemato BC10", "price_usd": 8686.39, "category": "Salud", "brand": "Mindray"},
    
    # Accesorios
    {"name": "Mouse Inalambrico USB 6 Botones DPI 1600", "price_usd": 9.36, "category": "Accesorios", "brand": "Astra"},
]


if __name__ == "__main__":
    products = scrape_all_products()
    
    # Save to JSON
    output_file = "latinbien_products.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Guardados {len(products)} productos en {output_file}")
    
    # Print summary
    categories = {}
    for p in products:
        cat = p.get("category", "Otros")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)
    
    print("\n📊 Resumen por categoría:")
    for cat, prods in sorted(categories.items()):
        print(f"  {cat}: {len(prods)} productos")
