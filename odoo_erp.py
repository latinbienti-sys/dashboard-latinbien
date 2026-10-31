#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consultas SOLO LECTURA a Odoo (latinbien.com / erp_production).

Cada concepto del balance tiene una función que trae su valor por empresa
(LB, GR, JV). Nunca escribe ni modifica nada en Odoo: únicamente consulta.

Requiere ODOO_USER y ODOO_PASS en el entorno (ver odoo_conn.py).
"""

from datetime import date
from typing import Dict, Any, Optional

import odoo_conn

# Mapeo empresa del balance -> compañías de Odoo que la componen.
# LB = LATINOAMERICANA DE BIENES Y SERVICIOS (1)
# GR = GERARDO JOSE RAMIREZ FERNANDEZ (3)
# JV = JUHENDIS ESTHER VALLADARES LOPEZ F.P (4)
COMPANY_MAP: Dict[str, list] = {
    "lb": [1],
    "gr": [3],
    "jv": [4],
}


# Lista blanca: cualquier otro método (write, create, unlink, action_*...) se rechaza.
METODOS_LECTURA = frozenset({"search", "search_read", "search_count", "read", "read_group", "fields_get"})


def _session():
    return odoo_conn.get_session()


def _call(s, model: str, method: str, args: Optional[list] = None,
          kwargs: Optional[dict] = None, context: Optional[dict] = None) -> Any:
    """Llamada JSON-RPC de Odoo (web session). Solo se permiten métodos de lectura."""
    if method not in METODOS_LECTURA:
        raise PermissionError(f"Método '{method}' bloqueado: este módulo solo lee de Odoo")
    params ={"model": model, "method": method, "args": args or [], "kwargs": kwargs or {}}
    if context:
        params["context"] = context
    r = s.post(f"{odoo_conn.ODOO_URL}/web/dataset/call_kw",
               json={"jsonrpc": "2.0", "method": "call", "params": params},
               timeout=60)
    r.raise_for_status()
    body = r.json()
    if body.get("error"):
        raise RuntimeError(str(body["error"]))
    return body.get("result")


def _suma_por_empresa(s, model: str, dominio_extra: list, campo_agr: str) -> Dict[str, float]:
    """Suma 'campo_agr' de un modelo agrupado por empresa.
    Devuelve {lb: X, gr: Y, jv: Z} sumando las compañías de cada entidad."""
    res = {"lb": 0.0, "gr": 0.0, "jv": 0.0}
    try:
        grupos = _call(s, model, "read_group",
                       [[], [campo_agr], ["company_id"]],
                       {"lazy": False, "domain": dominio_extra})
        por_comp: Dict[Any, float] = {}
        for g in grupos or []:
            comp = g.get("company_id")
            cid = comp[0] if isinstance(comp, (list, tuple)) else comp
            if cid:
                por_comp.setdefault(cid, 0.0)
                por_comp[cid] += float(g.get(campo_agr) or 0.0)
    except Exception:
        # Si el usuario no ve la empresa, intentar por empresa en contexto
        for ent, comps in COMPANY_MAP.items():
            for cid in comps:
                try:
                    ctx = {"allowed_company_ids": [cid]}
                    g = _call(s, model, "read_group",
                              [[], [campo_agr], []], {"lazy": False},
                              context={"allowed_company_ids": [cid]})
                    val = 0.0
                    for row in g or []:
                        val += float(row.get(campo_agr) or 0.0)
                    res[ent] = round(val, 2)
                except Exception:
                    continue
        return res

    for ent, comps in COMPANY_MAP.items():
        res[ent] = round(sum(por_comp.get(c, 0.0) for c in comps), 2)
    return res


# Almacenes que se EXCLUYEN del inventario para evitar duplicidad con otras
# compañías (stock consignado no es de la empresa que lo custodia) y averías.
_ALMACENES_EXCLUIDOS = ("CONSIGNACI", "AVERIA")


def _mapa_almacen_por_ubicacion(s) -> Dict[int, Any]:
    """Asocia cada ubicación interna con su almacén y compañía, siguiendo el
    parent_path de la ubicación y el view_location_id del almacén."""
    ctx = {"allowed_company_ids": [1, 3, 4, 6]}
    locs = _call(s, "stock.location", "search_read",
                 [[]], {"fields": ["id", "name", "usage", "parent_path"]},
                 context=ctx) or []
    internals = {l["id"]: l for l in locs if l.get("usage") == "internal"}
    ws = _call(s, "stock.warehouse", "search_read",
               [[]], {"fields": ["id", "name", "company_id", "view_location_id"]},
               context=ctx) or []
    mapa: Dict[int, Any] = {}
    for w in ws:
        comp = (w.get("company_id") or [False])[0]
        vl = w.get("view_location_id")
        vl = vl[0] if isinstance(vl, (list, tuple)) else vl
        if not comp or not vl:
            continue
        token = "/%d/" % vl
        for lid, li in internals.items():
            if token in (li.get("parent_path") or ""):
                mapa[lid] = (w["id"], w["name"], comp)
    return mapa


def _precio_estandar(s, pids, ctx) -> Dict[int, float]:
    """Costo real (standard_price) de cada producto, leído por lotes con
    search_read (más fiable que read para este campo)."""
    precios: Dict[int, float] = {}
    pids = sorted({int(p) for p in pids if p})
    B = 200
    for i in range(0, len(pids), B):
        chunk = pids[i:i + B]
        rows = _call(s, "product.product", "search_read",
                     [[("id", "in", chunk)]], {"fields": ["id", "standard_price"]},
                     context=ctx) or []
        for r in rows:
            precios[r.get("id")] = float(r.get("standard_price") or 0.0)
    return precios


def _inventario() -> Dict[str, Any]:
    """Valor del inventario por empresa = Σ (cantidad a mano × costo real)
    en los almacenes propios de cada compañía (excluye consignación y averías),
    para reproducir el informe Inventario/Informe/Stock (productos disponibles)."""
    s = _session()
    ctx = {"allowed_company_ids": [1, 3, 4, 6]}
    mapa = _mapa_almacen_por_ubicacion(s)
    # Quants a mano (location_usage internal, cantidad > 0)
    quants: list = []
    off = 0
    while True:
        batch = _call(s, "stock.quant", "search_read",
                      [[("on_hand", "=", True)]],
                      {"fields": ["product_id", "location_id", "quantity"],
                       "limit": 1000, "offset": off},
                      context=ctx) or []
        quants += batch
        if len(batch) < 1000:
            break
        off += 1000
    pids = {(q.get("product_id") or [0])[0] if isinstance(q.get("product_id"), (list, tuple))
            else q.get("product_id") for q in quants}
    precios = _precio_estandar(s, pids, ctx)

    valores = {"lb": 0.0, "gr": 0.0, "jv": 0.0}
    for q in quants:
        loc = q.get("location_id")
        loc = loc[0] if isinstance(loc, (list, tuple)) else loc
        ent = mapa.get(loc)
        if not ent:
            continue
        _, name, comp = ent
        if any(x in name.upper() for x in _ALMACENES_EXCLUIDOS):
            continue
        pid = q.get("product_id")
        pid = pid[0] if isinstance(pid, (list, tuple)) else pid
        comp_key = {1: "lb", 3: "gr", 4: "jv"}.get(comp)
        if not comp_key:
            continue
        valores[comp_key] += float(q.get("quantity") or 0.0) * precios.get(pid, 0.0)
    for k in valores:
        valores[k] = round(valores[k], 2)
    return {**valores, "fuente": "stock.quant", "indicador": "cantidad a mano * costo"}


def _inventario_transito() -> Dict[str, Any]:
    """Valor del inventario en tránsito por empresa, replicando el favorito
    INVENTRANSITO de Odoo: expediciones de almacén (stock.picking) en estado
    'assigned', valorizadas a cantidad pedida (product_uom_qty) × costo real."""
    s = _session()
    ctx = {"allowed_company_ids": [1, 3, 4, 6]}
    dom = [("state", "=", "assigned")]  # dominio del favorito INVENTRANSITO (ir.filters 305)
    pickings = _call(s, "stock.picking", "search_read",
                     [dom], {"fields": ["move_ids", "company_id"], "limit": 5000},
                     context=ctx) or []
    pck_comp = {
        p["id"]: ((p.get("company_id") or [False])[0]
                  if isinstance(p.get("company_id"), (list, tuple))
                  else p.get("company_id"))
        for p in pickings
    }
    mids = sorted({m for p in pickings for m in (p.get("move_ids") or [])})
    if not mids:
        return {"lb": 0.0, "gr": 0.0, "jv": 0.0,
                "fuente": "stock.picking", "indicador": "expediciones assigned (sin dato)"}
    moves = _call(s, "stock.move", "search_read",
                  [[("id", "in", mids)]],
                  {"fields": ["product_id", "product_uom_qty", "picking_id"],
                   "limit": 10000},
                  context=ctx) or []
    pids = {(m.get("product_id") or [0])[0] if isinstance(m.get("product_id"), (list, tuple))
            else m.get("product_id") for m in moves}
    precios = _precio_estandar(s, pids, ctx)
    valores = {"lb": 0.0, "gr": 0.0, "jv": 0.0}
    for m in moves:
        pid = m.get("product_id")
        pid = pid[0] if isinstance(pid, (list, tuple)) else pid
        pk = m.get("picking_id")
        pk = pk[0] if isinstance(pk, (list, tuple)) else pk
        comp_key = {1: "lb", 3: "gr", 4: "jv"}.get(pck_comp.get(pk))
        if not comp_key:
            continue
        valores[comp_key] += float(m.get("product_uom_qty") or 0.0) * precios.get(pid, 0.0)
    for k in valores:
        valores[k] = round(valores[k], 2)
    return {**valores, "fuente": "stock.picking", "indicador": "INVENTRANSITO (assigned) qty*costo"}


def _cuentas_por_cobrar(dominio: list, fecha: Optional[str] = None,
                        nombre: str = "CxC") -> Dict[str, Any]:
    """Suma lo adeudado (amount_residual) de facturas de clientes que cumplen
    'dominio', opcionalmente filtradas por la fecha de corte del balance.
    Solo lectura: lee account.move y account.move.line."""
    s = _session()
    ctx = {"allowed_company_ids": [1, 3, 4, 6]}
    dom = [("move_type", "in", ("out_invoice", "entry", "out_receipt"))]
    dom += list(dominio)
    if fecha:
        dom.append(("date", "<=", fecha))
    ids = _call(s, "account.move", "search", [dom], {}, context=ctx) or []
    valores = {"lb": 0.0, "gr": 0.0, "jv": 0.0}
    if not ids:
        return {**valores, "fuente": "account.move", "indicador": f"{nombre} (sin data)"}
    B = 500
    for i in range(0, len(ids), B):
        chunk = ids[i:i + B]
        movs = _call(s, "account.move", "search_read",
                     [[("id", "in", chunk)]],
                     {"fields": ["amount_residual", "company_id"]}, context=ctx) or []
        for m in movs:
            cid = (m.get("company_id") or [False])[0] \
                if isinstance(m.get("company_id"), (list, tuple)) \
                else m.get("company_id")
            comp_key = {1: "lb", 3: "gr", 4: "jv"}.get(cid)
            if not comp_key:
                continue
            valores[comp_key] += float(m.get("amount_residual") or 0.0)
    for k in valores:
        valores[k] = round(valores[k], 2)
    return {**valores, "fuente": "account.move", "indicador": nombre}


def _cxc_tecnologia(fecha: Optional[str] = None) -> Dict[str, Any]:
    """CxC Tecnología: réplica del favorito 'ANALISIS DE VENCIMIENTO CVG
    + SEGMENTOS' (account.move): x_status_operativos=6, payment_state!=paid,
    state=posted. Suma del remanente adeudado por compañía."""
    return _cuentas_por_cobrar(
        [("x_status_operativos", "=", "6"),
         ("payment_state", "!=", "paid"),
         ("state", "=", "posted")],
        fecha, "ANALISIS DE VENCIMIENTO CVG + SEGMENTOS")


def _cxc_motos(fecha: Optional[str] = None) -> Dict[str, Any]:
    """CxC Motos: lo adeudado de todo lo que pertenezca a la campaña
    CREDIMOTOS (clientes con categoría CREDIMOTO/CREDIMOTOS), facturas
    publicadas sin pagar, al día de corte indicado."""
    s = _session()
    ctx = {"allowed_company_ids": [1, 3, 4, 6]}
    part = _call(s, "res.partner", "search",
                 [[("category_id", "in", (133, 137))]], {}, context=ctx) or []
    if not part:
        return {"lb": 0.0, "gr": 0.0, "jv": 0.0,
                "fuente": "account.move", "indicador": "CxC Motos (sin clientes CREDIMOTOS)"}
    return _cuentas_por_cobrar(
        [("partner_id", "in", part),
         ("state", "=", "posted"),
         ("payment_state", "!=", "paid")],
        fecha, "CREDIMOTOS (adeudado)")


def _cuentas_por_pagar(dominio_partner: list, fecha: Optional[str],
                       nombre: str, tasa_bcv: float) -> Dict[str, Any]:
    """Suma CXP (facturas de proveedor publicadas sin pagar) de los partners que
    cumplen 'dominio_partner', en USD (convierte VEF/Bs con tasa_bcv). Solo lectura."""
    s = _session()
    ctx = {"allowed_company_ids": [1, 3, 4, 6]}
    part = _call(s, "res.partner", "search", [dominio_partner], {}, context=ctx) or []
    if not part:
        return {"lb": 0.0, "gr": 0.0, "jv": 0.0,
                "fuente": "account.move", "indicador": f"{nombre} (sin proveedores)"}
    dom = [("move_type", "in", ("in_invoice", "in_receipt")),
           ("partner_id", "in", part),
           ("state", "=", "posted"),
           ("payment_state", "in", ("not_paid", "partial"))]
    if fecha:
        dom.append(("date", "<=", fecha))
    ids = _call(s, "account.move", "search", [dom], {}, context=ctx) or []
    valores = {"lb": 0.0, "gr": 0.0, "jv": 0.0}
    if not ids:
        return {**valores, "fuente": "account.move", "indicador": f"{nombre} (sin facturas)"}
    B = 500
    for i in range(0, len(ids), B):
        chunk = ids[i:i + B]
        movs = _call(s, "account.move", "search_read",
                     [[("id", "in", chunk)]],
                     {"fields": ["amount_residual", "company_id", "currency_id"]},
                     context=ctx) or []
        for m in movs:
            cid = (m.get("company_id") or [False])[0] \
                if isinstance(m.get("company_id"), (list, tuple)) \
                else m.get("company_id")
            comp_key = {1: "lb", 3: "gr", 4: "jv"}.get(cid)
            if not comp_key:
                continue
            cur = m.get("currency_id")
            cur = cur[1] if isinstance(cur, (list, tuple)) else cur
            res = float(m.get("amount_residual") or 0.0)
            if cur and cur != "USD" and tasa_bcv:
                res = res / tasa_bcv
            valores[comp_key] += res
    for k in valores:
        valores[k] = round(valores[k], 2)
    return {**valores, "fuente": "account.move", "indicador": nombre}


def _cxp_motos(fecha: Optional[str] = None, tasa_bcv: Optional[float] = None) -> Dict[str, Any]:
    """CXP Motos: facturas sin pagar del proveedor de motos MOTO CITY PRO,
    en USD (convierte VEF/Bs con la tasa BCV del día)."""
    if tasa_bcv is None:
        try:
            import tasas
            tasa_bcv = tasas.obtener_tasa_bcv() or 875.65
        except Exception:  # noqa: BLE001
            tasa_bcv = 875.65
    return _cuentas_por_pagar(
        [("name", "ilike", "MOTO CITY PRO")],
        fecha, "CXP MOTOS (MOTO CITY PRO)", tasa_bcv)


def _cxp_tecnologia(fecha: Optional[str] = None, tasa_bcv: Optional[float] = None) -> Dict[str, Any]:
    """CXP Tecnología: facturas sin pagar de CORPORACION UNIVERSAL TECHNOLOGY,
    SERMECA y VENEPAC, en USD."""
    if tasa_bcv is None:
        try:
            import tasas
            tasa_bcv = tasas.obtener_tasa_bcv() or 875.65
        except Exception:  # noqa: BLE001
            tasa_bcv = 875.65
    return _cuentas_por_pagar(
        ["|", ("name", "ilike", "%UNIVERSAL TECHNOLOGY%"), "|",
         ("name", "ilike", "%SERMECA%"),
         ("name", "ilike", "%VENEPAC%")],
        fecha, "CXP TEC (UNIVERSAL/SERMECA/VENEPAC)", tasa_bcv)


def _anticipos_recibidos(fecha: Optional[str], tipo: str) -> Dict[str, Any]:
    """Anticipos recibidos de clientes 'al día': account.payment inbound con
    razón de pago 'ANTICIPO DE CLIENTE'. MOTO solo clientes con categoría
    CREDIMOTO/CREDIMOTOS; TEC el resto. En USD."""
    fecha = fecha or date.today().isoformat()
    s = _session()
    ctx = {"allowed_company_ids": [1, 3, 4, 6]}
    part_moto = _call(s, "res.partner", "search",
                      [[("category_id", "in", (133, 137))]], {}, context=ctx) or []
    moto_set = set(part_moto or [])
    dom = [("payment_type", "=", "inbound"),
           ("x_razonpagos", "=", "ANTICIPO DE CLIENTE"),
           ("state", "=", "posted")]
    if fecha:
        dom.append(("date", "=", fecha))
    ids = _call(s, "account.payment", "search", [dom], {}, context=ctx) or []
    valores = {"lb": 0.0, "gr": 0.0, "jv": 0.0}
    if not ids:
        return {**valores, "fuente": "account.payment",
                "indicador": f"anticipos recibidos {tipo} (sin data {fecha or 'hoy'})"}
    B = 500
    for i in range(0, len(ids), B):
        chunk = ids[i:i + B]
        pagos = _call(s, "account.payment", "search_read",
                      [[("id", "in", chunk)]],
                      {"fields": ["amount", "currency_id", "partner_id", "company_id"]},
                      context=ctx) or []
        for p in pagos:
            cur = p.get("currency_id")
            cur = cur[1] if isinstance(cur, (list, tuple)) else cur
            if cur != "USD":
                continue
            pid = p.get("partner_id")
            pid = pid[0] if isinstance(pid, (list, tuple)) else pid
            es_moto = pid in moto_set
            if (tipo == "moto" and not es_moto) or (tipo == "tec" and es_moto):
                continue
            cid = (p.get("company_id") or [False])[0] \
                if isinstance(p.get("company_id"), (list, tuple)) \
                else p.get("company_id")
            comp_key = {1: "lb", 3: "gr", 4: "jv"}.get(cid)
            if not comp_key:
                continue
            valores[comp_key] += float(p.get("amount") or 0.0)
    for k in valores:
        valores[k] = round(valores[k], 2)
    return {**valores, "fuente": "account.payment",
            "indicador": f"anticipos {fecha or date.today().isoformat()}"}


def _anticipo_tec(fecha: Optional[str] = None) -> Dict[str, Any]:
    return _anticipos_recibidos(fecha, "tec")


def _anticipo_moto(fecha: Optional[str] = None) -> Dict[str, Any]:
    return _anticipos_recibidos(fecha, "moto")


def _cuentas() -> Dict[str, Any]:
    """Plantilla para consultas contables aún sin dominio definido (ej. CxC empresas).
    Devuelve ceros."""
    return {"lb": 0.0, "gr": 0.0, "jv": 0.0, "fuente": "account.move.line",
            "indicador": "DEFINIR_DOMINIO"}


# Dispatcher: asocia cada clave del balance con su función de consulta.
QUERIES = {
    "inventario": _inventario,
    "inventario_transito": _inventario_transito,
    # Cuentas por cobrar
    "cxc_empresas": _cuentas,
    "cxc_tec": _cxc_tecnologia,
    "cxc_moto": _cxc_motos,
    # Anticipos
    "anticipo_tec": _anticipo_tec,
    "anticipo_moto": _anticipo_moto,
    # Cuentas por pagar
    "cxp_op": _cuentas,
    "cxp_tec": _cxp_tecnologia,
    "cxp_moto": _cxp_motos,
}

CONCEPTOS_SIN_CONSULTA = {
    "relacion_saldos": "WS (web service)",
    "fondo_ahorro": "WS (web service)",
    "fondo_caja": "WS (web service)",
    "saldo_td": "WS (web service)",
    "marca": "SALDO INICIAL",
    "sistema_admin": "SALDO INICIAL",
    "tdc_gr_2025": "SALDO INICIAL",
    "tdc_gr_2026": "WS (web service)",
    "prestamo_bdv": "MANUAL",
}


def consultar(key: str, fecha: Optional[str] = None) -> Dict[str, Any]:
    """Consulta un concepto del balance contra Odoo (solo lectura).
    'fecha' (ISO) es la fecha de corte para cálculos 'al día'."""
    key = (key or "").strip()
    if key in QUERIES:
        try:
            try:
                r = QUERIES[key](fecha)
            except TypeError:
                r = QUERIES[key]()
            r.update({"ok": True, "key": key, "origen": "ERP"})
            return r
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "key": key, "error": str(e)}
    if key in CONCEPTOS_SIN_CONSULTA:
        return {"ok": False, "key": key,
                "error": f"'{key}' no se consulta en ERP (fuente: {CONCEPTOS_SIN_CONSULTA[key]})"}
    return {"ok": False, "key": key,
            "error": f"Concepto '{key}' sin consulta ERP definida"}


if __name__ == "__main__":
    import json
    for k in ("inventario", "inventario_transito", "cxc_empresas"):
        print(k, "=>", json.dumps(consultar(k), ensure_ascii=False))