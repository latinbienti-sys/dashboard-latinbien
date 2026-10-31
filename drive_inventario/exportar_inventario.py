#!/usr/bin/env python3
"""Exporta inventario, precios, proveedores y rotación desde Odoo a CSV.

Genera archivos numerados y listos para subir a Google Drive y analizar con
ChatGPT (conector de Google Drive).

Uso:
    python drive_inventario/exportar_inventario.py

Requiere: name.env con ODOO_USER y ODOO_PASS (en la raíz del proyecto).
"""
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

import requests

try:
    from dotenv import dotenv_values
except ImportError:
    def dotenv_values(path):
        vals = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
        return vals

ODOO_URL = "https://latinbien.com"
ODOO_DB = "erp_production"
BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
HOY = datetime.now()
CORTE_12M = (HOY - timedelta(days=365)).strftime("%Y-%m-%d")
CORTE_24M = (HOY - timedelta(days=730)).strftime("%Y-%m-%d")
MERCANCIA = [["type", "in", ["product", "consu"]]]


def sesion():
    cfg = dotenv_values(os.path.join(ROOT, "name.env"))
    user, pw = cfg.get("ODOO_USER"), cfg.get("ODOO_PASS")
    if not user or not pw:
        sys.exit("Falta ODOO_USER/ODOO_PASS en name.env")
    s = requests.Session()
    r = s.post(f"{ODOO_URL}/web/session/authenticate", json={
        "jsonrpc": "2.0", "method": "call",
        "params": {"db": ODOO_DB, "login": user, "password": pw}, "id": 1,
    }, timeout=60)
    if not r.json().get("result", {}).get("uid"):
        sys.exit("Fallo de autenticación en Odoo")
    s.headers["Content-Type"] = "application/json"
    print("[OK] Conectado a Odoo")
    return s


def call(s, model, method, args=None, kwargs=None):
    r = s.post(f"{ODOO_URL}/web/dataset/call_kw/{model}/{method}", json={
        "jsonrpc": "2.0", "method": "call",
        "params": {"model": model, "method": method,
                   "args": args or [], "kwargs": kwargs or {}},
        "id": 1,
    }, timeout=180)
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"{model}.{method}: {j['error']['data'].get('message')}")
    return j["result"]


def leer(s, model, domain, fields, order=None, limit=100000):
    kw = {"fields": fields, "limit": limit}
    if order:
        kw["order"] = order
    return call(s, model, "search_read", [domain], kw)


def por_chunks(lst, n=800):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def nombre(x):
    return x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else (x or "")


def escrito(fname, header, rows):
    path = os.path.join(BASE, fname)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"[OK] {fname}: {len(rows)} filas")


def fnum(v):
    return round(float(v or 0), 2)


def main():
    s = sesion()

    # ── Productos (solo mercancía; servicios/gastos excluidos) ───────────
    productos = leer(s, "product.product", MERCANCIA, [
        "id", "default_code", "name", "barcode", "product_tmpl_id",
        "categ_id", "uom_id", "list_price", "standard_price",
        "qty_available",
    ])
    print(f"[OK] Productos mercancía: {len(productos)}")
    prod = {p["id"]: p for p in productos}
    for p in productos:
        p["almacen_set"] = set()

    # ── Ventas 12 meses (base de precios reales y rotación) ──────────────
    orders = leer(s, "sale.order", [
        ["date_order", ">", CORTE_12M],
        ["state", "in", ["sale", "done"]],
    ], ["id", "date_order", "currency_id"])
    o_map = {o["id"]: o for o in orders}
    monedas = {nombre(o.get("currency_id")) for o in orders}
    lines = []
    for ch in por_chunks(list(o_map)):
        lines += leer(s, "sale.order.line", [["order_id", "in", ch]], [
            "product_id", "product_uom_qty", "price_subtotal", "order_id",
        ])
    print(f"[OK] Líneas de venta 12m: {len(lines)} (monedas: {monedas})")

    corte_90 = (HOY - timedelta(days=90)).strftime("%Y-%m-%d")
    corte_30 = (HOY - timedelta(days=30)).strftime("%Y-%m-%d")
    met = defaultdict(lambda: {
        "u12": 0.0, "i12": 0.0, "u90": 0.0, "u30": 0.0,
        "u_usd": 0.0, "ult": "", "n": 0,
    })
    for l in lines:
        if not l.get("product_id"):
            continue
        o = o_map.get(l["order_id"][0])
        if not o:
            continue
        fecha = (o.get("date_order") or "")[:10]
        pid = l["product_id"][0]
        m = met[pid]
        u = fnum(l.get("product_uom_qty"))
        m["u12"] += u
        m["n"] += 1
        es_usd = nombre(o.get("currency_id")) == "USD"
        if es_usd:
            m["i12"] += fnum(l.get("price_subtotal"))
            m["u_usd"] += u
        if fecha >= corte_90:
            m["u90"] += u
        if fecha >= corte_30:
            m["u30"] += u
        if fecha > m["ult"]:
            m["ult"] = fecha

    def precio_ref(pid):
        """Precio de venta de referencia: promedio 12m, si no, lista si es real."""
        m = met.get(pid)
        if m and m["u_usd"] > 0:
            return fnum(m["i12"] / m["u_usd"]), "promedio_12m"
        p = prod.get(pid)
        if p and fnum(p.get("list_price")) > 1:
            return fnum(p["list_price"]), "lista"
        return "", "sin_dato"

    # ── Existencias por almacén (stock.quant) ────────────────────────────
    quants = leer(s, "stock.quant", [
        ["location_id.usage", "=", "internal"], ["quantity", "!=", 0],
    ], ["product_id", "location_id", "quantity"])
    stock_alm = defaultdict(float)  # (pid, almacen) -> cantidad
    for q in quants:
        if not q.get("product_id") or not q.get("location_id"):
            continue
        pid = q["product_id"][0]
        if pid not in prod:
            continue
        almacen = nombre(q["location_id"]).split("/")[0]
        stock_alm[(pid, almacen)] += fnum(q.get("quantity"))
    filas_alm = []
    for (pid, almacen), cant in sorted(
            stock_alm.items(), key=lambda x: (prod[x[0][0]].get("default_code") or "", x[0][1])):
        p = prod[pid]
        p["almacen_set"].add(almacen)
        filas_alm.append([
            p.get("default_code") or "", p["name"], nombre(p.get("categ_id")),
            almacen, fnum(cant),
        ])
    escrito("01_existencias_por_almacen.csv",
            ["codigo", "producto", "categoria", "almacen", "cantidad"],
            filas_alm)

    # ── Inventario total valorizado ──────────────────────────────────────
    filas_inv, valor_costo = [], 0.0
    for p in productos:
        stock = fnum(p.get("qty_available"))
        costo, venta = fnum(p.get("standard_price")), fnum(p.get("list_price"))
        valor_costo += stock * costo
        filas_inv.append([
            p.get("default_code") or "", p["name"], nombre(p.get("categ_id")),
            nombre(p.get("uom_id")), stock, costo, venta,
            fnum(stock * costo), fnum(stock * venta),
            "; ".join(sorted(p["almacen_set"])),
        ])
    filas_inv.sort(key=lambda r: -r[7])
    escrito("02_inventario_total.csv", [
        "codigo", "producto", "categoria", "unidad", "stock_actual",
        "costo_unitario", "precio_lista", "valor_a_costo",
        "valor_a_precio_lista", "almacenes",
    ], filas_inv)
    print(f"[OK] Valor inventario a costo: ${valor_costo:,.2f}")

    # ── Lista de precios de proveedores (product.supplierinfo) ───────────
    supinfo = leer(s, "product.supplierinfo", [], [
        "partner_id", "product_tmpl_id", "product_code", "product_name",
        "min_qty", "price", "date_start", "date_end", "currency_id",
    ])
    print(f"[OK] Precios de proveedor: {len(supinfo)}")
    tmpl_a_prod = {}
    for p in productos:
        tmpl_a_prod.setdefault(p["product_tmpl_id"][0], p)
    prov_min = {}   # tmpl_id -> (precio, partner)
    filas_lista = []
    for r in supinfo:
        prov = nombre(r.get("partner_id"))
        tmpl = r.get("product_tmpl_id") and r["product_tmpl_id"][0]
        precio = fnum(r.get("price"))
        p = tmpl_a_prod.get(tmpl)
        filas_lista.append([
            prov, (p.get("default_code") if p else "") or "",
            p["name"] if p else nombre(r.get("product_tmpl_id")),
            r.get("product_code") or "", r.get("product_name") or "",
            precio, fnum(r.get("min_qty")),
            r.get("date_start") or "", r.get("date_end") or "",
            nombre(r.get("currency_id")),
        ])
        if precio > 0 and tmpl and (tmpl not in prov_min or precio < prov_min[tmpl][0]):
            prov_min[tmpl] = (precio, prov)
    filas_lista.sort(key=lambda r: (r[0], r[1]))
    escrito("05_lista_precios_proveedor.csv", [
        "proveedor", "codigo", "producto", "codigo_proveedor",
        "descripcion_proveedor", "precio_proveedor", "cantidad_minima",
        "vigente_desde", "vigente_hasta", "moneda",
    ], filas_lista)

    # ── Precios actuales: lista vs precio real vs costo vs proveedor ─────
    filas_precios = []
    sin_precio = 0
    for p in productos:
        pid = p["id"]
        costo = fnum(p.get("standard_price"))
        lista = fnum(p.get("list_price"))
        prom, fuente = precio_ref(pid)
        ultimo = fnum(met[pid]["i12"] / met[pid]["u_usd"]) if met.get(pid, {}).get("u_usd") else ""
        margen_prom = round((prom - costo) / prom * 100, 1) if prom and costo > 0 else ""
        tmpl = p["product_tmpl_id"][0]
        pmin, prov = prov_min.get(tmpl, (None, ""))
        if lista <= 1:
            sin_precio += 1
        filas_precios.append([
            p.get("default_code") or "", p["name"], nombre(p.get("categ_id")),
            fnum(p.get("qty_available")), lista,
            "SI" if lista > 1 else "NO",
            prom, fuente, ultimo, costo, margen_prom,
            fnum(pmin) if pmin else "", prov,
        ])
    filas_precios.sort(key=lambda r: r[0])
    escrito("03_precios_actuales.csv", [
        "codigo", "producto", "categoria", "stock_actual", "precio_lista",
        "precio_lista_confiable", "precio_venta_prom_12m",
        "fuente_precio_venta", "precio_venta_ultimo_12m", "costo",
        "margen_sobre_precio_prom_pct", "precio_proveedor_min", "proveedor_min",
    ], filas_precios)
    if sin_precio:
        print(f"[AVISO] {sin_precio} productos con precio de lista <= 1 "
              f"(usar precio_venta_prom_12m)")

    # ── Proveedores ──────────────────────────────────────────────────────
    partners = leer(s, "res.partner", [["supplier_rank", ">", 0]], [
        "id", "name", "email", "phone", "mobile", "city",
    ])
    print(f"[OK] Proveedores: {len(partners)}")
    prov_nombre = {p["id"]: p["name"] for p in partners}

    # ── Compras 24 meses (purchase.order.line) ───────────────────────────
    pos = leer(s, "purchase.order", [
        ["date_order", ">", CORTE_24M],
        ["state", "in", ["purchase", "done"]],
    ], ["id", "date_order", "partner_id", "currency_id"])
    po_map = {o["id"]: o for o in pos}
    pol = []
    for ch in por_chunks(list(po_map)):
        pol += leer(s, "purchase.order.line", [["order_id", "in", ch]], [
            "product_id", "product_qty", "price_unit", "price_subtotal",
            "order_id", "partner_id",
        ])
    print(f"[OK] Líneas de compra 24m: {len(pol)}")

    compras = defaultdict(list)          # (pid, pvid) -> [(fecha, precio, cant)]
    compras_por_prod = defaultdict(float)   # pid -> unidades compradas
    compras_por_prov = defaultdict(lambda: [0, 0.0, ""])  # pvid -> [lineas, unidades, ultima]
    for l in pol:
        o = po_map.get(l["order_id"][0])
        if not o or not l.get("product_id"):
            continue
        pid = l["product_id"][0]
        if pid not in prod:
            continue
        pvid = (l.get("partner_id") or o.get("partner_id"))[0]
        fecha = (o.get("date_order") or "")[:10]
        cant = fnum(l.get("product_qty"))
        compras[(pid, pvid)].append((fecha, fnum(l.get("price_unit")), cant))
        compras_por_prod[pid] += cant
        cp = compras_por_prov[pvid]
        cp[0] += 1
        cp[1] += cant
        if fecha > cp[2]:
            cp[2] = fecha
    for k in compras:
        compras[k].sort(key=lambda x: x[0])

    # ── Cambios de precio de proveedor ───────────────────────────────────
    filas_cambio = []
    for (pid, pvid), hist in compras.items():
        p = prod[pid]
        tmpl = p["product_tmpl_id"][0]
        precio_lista_prov = prov_min.get(tmpl, (None, ""))[0]
        costo = fnum(p.get("standard_price"))
        ref, fuente_ref = precio_ref(pid)
        prev = None
        for fecha, precio, cant in hist:
            cambio, estado = "", "PRIMERA COMPRA"
            if prev is not None and prev > 0:
                delta = (precio - prev) / prev * 100
                cambio = round(delta, 1)
                estado = ("SUBIO" if delta > 0.01 else
                          "BAJO" if delta < -0.01 else "SIN CAMBIO")
            filas_cambio.append([
                p.get("default_code") or "", p["name"],
                prov_nombre.get(pvid, ""), fecha, cant, precio,
                prev if prev is not None else "", cambio, estado,
                fnum(precio_lista_prov) if precio_lista_prov else "",
                costo, ref, fuente_ref,
                round((precio - ref) / ref * 100, 1) if ref else "",
            ])
            prev = precio
    filas_cambio.sort(key=lambda r: (r[0], r[3]))
    escrito("06_cambios_precio_proveedor.csv", [
        "codigo", "producto", "proveedor", "fecha_compra", "cantidad",
        "precio_unitario", "precio_anterior", "cambio_pct", "estado",
        "precio_lista_proveedor_actual", "nuestro_costo",
        "nuestro_precio_venta_ref", "fuente_precio_venta",
        "precio_proveedor_vs_nuestro_precio_pct",
    ], filas_cambio)

    # ── Proveedores (contactos + actividad) ──────────────────────────────
    surten = defaultdict(set)
    for r in supinfo:
        surten[r["partner_id"][0]].add(r["product_tmpl_id"][0])
    filas_prov = []
    for p in partners:
        acts = compras_por_prov.get(p["id"], [0, 0, ""])
        filas_prov.append([
            p["name"], p.get("email") or "", p.get("phone") or "",
            p.get("mobile") or "", p.get("city") or "",
            len(surten.get(p["id"], ())), acts[0], fnum(acts[1]), acts[2],
        ])
    filas_prov.sort(key=lambda r: (-r[6], -r[5], r[0]))
    escrito("04_proveedores.csv", [
        "proveedor", "email", "telefono", "whatsapp", "ciudad",
        "productos_en_lista", "compras_24m_lineas", "unidades_compradas_24m",
        "ultima_compra",
    ], filas_prov)

    # ── Rotación 12 meses / ABC ──────────────────────────────────────────
    items = []
    for pid, m in met.items():
        if pid not in prod:
            continue
        p = prod[pid]
        items.append({"p": p, "m": m, "stock": fnum(p.get("qty_available")),
                      "compras": compras_por_prod.get(pid, 0.0)})
    items.sort(key=lambda x: -x["m"]["i12"])
    ingresos_total = sum(x["m"]["i12"] for x in items) or 1
    acum = 0.0
    filas_rot = []
    for it in items:
        p, m = it["p"], it["m"]
        acum += m["i12"] / ingresos_total
        clase = "A" if acum <= 0.80 else "B" if acum <= 0.95 else "C"
        dias_sin = (HOY - datetime.strptime(m["ult"], "%Y-%m-%d")).days if m["ult"] else ""
        ritmo = m["u12"] / 365
        cobertura = round(it["stock"] / ritmo) if ritmo > 0 and it["stock"] > 0 else ""
        filas_rot.append([
            p.get("default_code") or "", p["name"], nombre(p.get("categ_id")),
            it["stock"], round(m["u12"]), fnum(m["i12"]), round(m["u90"]),
            round(m["u30"]), m["ult"], dias_sin, m["n"],
            round(it["compras"]), cobertura, clase,
        ])
    escrito("07_rotacion_ventas_12m.csv", [
        "codigo", "producto", "categoria", "stock_actual", "unidades_vendidas_12m",
        "ingresos_usd_12m", "unidades_90d", "unidades_30d", "ultima_venta",
        "dias_desde_ultima_venta", "lineas_venta", "unidades_compradas_24m",
        "dias_cobertura_stock", "clase_ABC",
    ], filas_rot)

    print("\n[RESUMEN]")
    print(f"  Productos mercancía: {len(productos)} | con stock: "
          f"{sum(1 for p in productos if p.get('qty_available'))}")
    print(f"  Proveedores: {len(partners)} | precios proveedor: {len(supinfo)}")
    print(f"  Cambios de precio registrados: {len(filas_cambio)}")
    print(f"  Productos vendidos 12m: {len(filas_rot)}")
    print(f"\nArchivos en: {BASE}")


if __name__ == "__main__":
    main()
