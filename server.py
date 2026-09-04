#!/usr/bin/env python3
"""Servidor web dinámico — Dashboard LATINBIEN en tiempo real.
Se conecta DIRECTAMENTE a Odoo 16 (latinbien.com) vía API XML-RPC.
Sin Google Sheets, sin pasos manuales. Datos vivos desde la facturación.

Uso: python server.py
Luego abre: http://localhost:8000/"""

import os, sys, json, re
import xmlrpc.client
from collections import defaultdict, Counter
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Configuración Odoo ──────────────────────────────────────────
ODOO_URL = 'https://latinbien.com'
ODOO_DB = 'erp_production'
ODOO_USER = os.environ.get('ODOO_USER')
ODOO_PASS = os.environ.get('ODOO_PASS')
if not ODOO_USER or not ODOO_PASS:
    raise RuntimeError("ODOO_USER y ODOO_PASS deben estar definidas como variables de entorno.")

# Statuses que incluimos (Entregado, Aprobado, Cancelación Total, Congelados)
TARGET_STATUSES = ['6', '4', '8', '10', '12']

# ── Cliente Odoo ────────────────────────────────────────────────
def odoo_connect():
    """Autentica y retorna uid + models proxy (XML-RPC) + session (JSON-RPC opcional)."""
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
    if not uid:
        raise Exception('Error de autenticación en Odoo')
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    return uid, models

def json_connect():
    """Autentica vía JSON-RPC y retorna session + uid.
    JSON-RPC no sufre el bug de website_sale_wishlist en _check_credentials."""
    import requests
    sess = requests.Session()
    resp = sess.post(f'{ODOO_URL}/web/session/authenticate', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'db': ODOO_DB, 'login': ODOO_USER, 'password': ODOO_PASS},
        'id': 1
    })
    res = resp.json()
    if 'error' in res:
        raise Exception(f'Error JSON-RPC auth: {res["error"]}')
    uid = res['result']['uid']
    return sess, uid

def json_execute(sess, model, method, args=None, kwargs=None):
    """Ejecuta una llamada a Odoo vía JSON-RPC."""
    import requests
    payload = {
        'jsonrpc': '2.0', 'method': 'call',
        'params': {
            'model': model,
            'method': method,
            'args': args or [],
            'kwargs': kwargs or {},
        },
        'id': 2
    }
    resp = sess.post(f'{ODOO_URL}/web/dataset/call_kw', json=payload)
    res = resp.json()
    if 'error' in res:
        raise Exception(f'JSON-RPC error: {res["error"]}')
    return res['result']

def fetch_data():
    """Trae todas las facturas desde Odoo con los status indicados.
    Usa JSON-RPC en lugar de XML-RPC para evitar el bug de website_sale_wishlist."""
    sess, uid = json_connect()
    
    domain = [
        ['x_status_operativos', 'in', TARGET_STATUSES],
        ['move_type', '=', 'out_invoice'],
    ]
    
    fields = [
        'id', 'name', 'partner_id', 'amount_total', 'amount_residual',
        'invoice_date', 'x_status_operativos', 'x_work_profesional',
    ]
    
    ids = json_execute(sess, 'account.move', 'search', [domain])
    
    # Leer en lotes para evitar timeouts
    batch_size = 500
    all_recs = []
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        recs = json_execute(sess, 'account.move', 'read', [batch, fields])
        all_recs.extend(recs)
    
    # Procesar: extraer datos relevantes
    rows = []
    status_counter = Counter()
    for r in all_recs:
        status_key = f'{r["x_status_operativos"]}. ' + {
            '6': 'CVG - ENTREGADO',
            '4': 'SAV - APROBADO - ESPERA ENTREGA',
            '8': 'CANCELACION TOTAL',
            '10': 'CONGELADO',
            '12': 'CONGELADO',
        }.get(str(r['x_status_operativos']), str(r['x_status_operativos']))
        status_counter[status_key] += 1
        
        partner_name = ''
        if isinstance(r.get('partner_id'), list) and len(r['partner_id']) > 1:
            partner_name = r['partner_id'][1]
        
        total = float(r['amount_total'] or 0)
        residual = float(r['amount_residual'] or 0)
        pagado = total - residual
        
        rows.append({
            'cliente': partner_name,
            'total': total,
            'pagado': max(pagado, 0),
            'fecha': str(r.get('invoice_date') or ''),
            'trabajador': str(r.get('x_work_profesional') or ''),
            'status': status_key,
        })
    
    # Clasificar trabajador: muestra el valor real de Odoo, solo corrige typo
    def normalize_worker(tipo):
        tl = tipo.lower().strip() if tipo else ''
        if not tl or tl == 'vacio' or tl == 'false':
            return 'Sin clasificar'
        if tl == 'infdependiente_informal':
            return 'independiente_informal'
        return tl
    
    # Agregar por cliente
    clients_dict = defaultdict(lambda: {
        'contratos': 0, 'facturado': 0.0, 'cobrado': 0.0,
        'fechas': [], 'worker_types': Counter()
    })
    for r in rows:
        c = r['cliente']
        clients_dict[c]['contratos'] += 1
        clients_dict[c]['facturado'] += r['total']
        clients_dict[c]['cobrado'] += r['pagado']
        clients_dict[c]['fechas'].append(r['fecha'])
        clients_dict[c]['worker_types'][r['trabajador']] += 1
    
    client_list = []
    dist = Counter()
    seg_stats = defaultdict(lambda: {'clientes': 0, 'contratos': 0,
                                      'facturado': 0.0, 'cobrado': 0.0})
    for c_name, c_data in sorted(clients_dict.items(),
                                  key=lambda x: -x[1]['contratos']):
        fechas_ordenadas = sorted([f for f in c_data['fechas'] if f])
        first_date = fechas_ordenadas[0] if fechas_ordenadas else ''
        last_date = fechas_ordenadas[-1] if fechas_ordenadas else ''
        prom = round(c_data['facturado'] / c_data['contratos'], 2) \
               if c_data['contratos'] else 0
        wt = c_data['worker_types'].most_common(1)[0][0] \
             if c_data['worker_types'] else 'Sin clasificar'
        worker = normalize_worker(wt)
        dist[c_data['contratos']] += 1
        seg_stats[worker]['clientes'] += 1
        seg_stats[worker]['contratos'] += c_data['contratos']
        seg_stats[worker]['facturado'] += c_data['facturado']
        seg_stats[worker]['cobrado'] += c_data['cobrado']
        client_list.append({
            'cliente': c_name,
            'contratos': c_data['contratos'],
            'facturado': round(c_data['facturado'], 2),
            'cobrado': round(c_data['cobrado'], 2),
            'saldo': round(c_data['facturado'] - c_data['cobrado'], 2),
            'prom': prom,
            'worker_type': worker,
            'segmento': worker,
            'first_date': first_date,
            'last_date': last_date,
        })
    
    # Últimos 200
    rows.sort(key=lambda r: r['fecha'] if r['fecha'] else '', reverse=True)
    last_200 = rows[:200]
    last200_seg = Counter()
    for r in last_200:
        last200_seg[normalize_worker(r['trabajador'])] += 1
    
    # VIP (5+ contratos)
    vip_clients = [c for c in client_list if c['contratos'] >= 5]
    vip_clients.sort(key=lambda x: -x['contratos'])
    
    # Total rows (all statuses, not just our selection)
    all_ids = json_execute(sess, 'account.move', 'search_count', [[['move_type', '=', 'out_invoice']]])
    
    # Preparar facturas individuales para filtro por fecha
    invoices = []
    for r in rows:
        invoices.append({
            'fecha': r['fecha'],
            'total': r['total'],
            'pagado': r['pagado'],
            'cliente': r['cliente'],
            'status': r['status'],
            'trabajador': r['trabajador'],
        })
    
    # Plan de pagos
    payment_plan = fetch_payment_plan(sess)
    
    # Facturación Julio
    facturacion_julio = fetch_facturacion_julio(sess)
    
    # Expedientes (credit lines aprobadas)
    expedientes = fetch_expedientes(sess)

    # DSH CREDIMOTO: aislado para que un fallo en esta pestaña NUNCA rompa el
    # resto del dashboard (si falla, se muestra vacío en lugar de bloquear).
    try:
        dshbcredimoto = fetch_dshbcredimoto(sess)
    except Exception as e:
        print(f"[fetch_data] ERROR en fetch_dshbcredimoto: {e}")
        dshbcredimoto = {
            'resumen': {'total_ordenes': 0, 'total_motos': 0, 'total_producto': 0,
                        'total_gasto_admin': 0, 'total_facturado': 0,
                        'cobrado_clientes': 0, 'cuotas_pagadas': 0,
                        'cuotas_por_cobrar': 0},
            'ventas': [], 'facturas_proveedor': [],
            'proveedor_por_oc': [],
            'snapshot': {'ventas': 0, 'cobrado': 0, 'por_cobrar': 0, 'por_pagar': 0},
            'por_ciclo': {},
        }

    return {
        'status_summary': dict(status_counter.most_common()),
        'total_rows': all_ids,
        'client_count': len(client_list),
        'total_facturado': round(sum(c['facturado'] for c in client_list), 2),
        'total_cobrado': round(sum(c['cobrado'] for c in client_list), 2),
        'distribucion': [{'rango': k, 'cantidad': v}
                         for k, v in sorted(dist.items())],
        'status_counts': {
            'Entregado': status_counter.get('6. CVG - ENTREGADO', 0),
            'Aprobado': status_counter.get('4. SAV - APROBADO - ESPERA ENTREGA', 0),
            'Cancelacion Total': status_counter.get('8. CANCELACION TOTAL', 0),
            'Congelado': status_counter.get('10. CONGELADO', 0) +
                         status_counter.get('12. CONGELADO', 0),
        },
        'clients': client_list,
        'invoices': invoices,  # Para filtro por fecha preciso
        'segment_stats': {s: dict(v)
                          for s, v in sorted(seg_stats.items(),
                                             key=lambda x: -x[1]['contratos'])},
        'last200': dict(last200_seg.most_common()),
        'vip': [{'cliente': c['cliente'], 'cont': c['contratos'],
                 'first': c['first_date'], 'last': c['last_date']}
                for c in vip_clients],
        'payment_plan': payment_plan,
        'facturacion_julio': facturacion_julio,
        'facturacion_agosto': fetch_facturacion_agosto(sess),
        'expedientes': expedientes,
        'ventas_motos': fetch_ventas_motos(sess),
        'pago_proveedor_moto': fetch_pagoProveedorMoto(sess),
        'dshbcredimoto': dshbcredimoto,
        'agosto_operativo': fetch_agosto_operativo(),
    }

# ── Expedientes (Credit Lines Aprobadas) ─────────────────────────────────────
def fetch_expedientes(sess):
    """Obtiene líneas de crédito APROBADAS desde res.partner (JSON-RPC).
    Filtro: x_status_expediente = '7pre' (Línea de Crédito - Aprobada).
    Agrupa por año/mes de x_fecha_activacion y segmenta por rangos del
    límite aprobado (x_credit_limit_aprobado): <3000, 3000-6000, >6000.
    Estado de caso:
      - Usada      : usa crédito (x_credit_limit_use > 0)
      - No usada   : línes aprobada sin uso
      - Caducada   : aprobada y no usada con fecha de activación vieja (>= 365 días)
    """
    from datetime import datetime, date
    from collections import defaultdict

    FIELDS = [
        'id', 'name',
        'x_credit_limit_aprobado',   # Límite de crédito aprobado
        'x_credit_limit_available',  # Límite de crédito disponible
        'x_credit_limit_use',        # Límite de crédito usado
        'x_fecha_activacion',        # Fecha de activación (datetime)
        'x_activacion_linea',        # Línea activada (boolean)
    ]

    # Caducidad: línea aprobada que permanece SIN USO más de este número de días
    CADUCA_DAYS = 365

    try:
        ids = json_execute(sess, 'res.partner', 'search',
                           [[['x_status_expediente', '=', '7pre']]])
        if isinstance(ids, dict) and 'value' in ids:
            ids = ids['value']

        all_records = []
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i+batch_size]
            recs = json_execute(sess, 'res.partner', 'read',
                                [batch, FIELDS])
            all_records.extend(recs)

        hoy = date.today()
        month_agg = defaultdict(lambda: {
            'rango_menor_3000': 0, 'rango_3000_6000': 0, 'rango_mayor_6000': 0,
            'total_clientes': 0, 'total_monto': 0.0,
            'usadas': 0, 'no_usadas': 0, 'caducados': 0,
            'clientes': [],
        })
        total_general = {'usadas': 0, 'no_usadas': 0, 'caducados': 0,
                         'total_lineas': 0, 'total_monto': 0.0}

        for rec in all_records:
            limite = rec.get('x_credit_limit_aprobado') or 0.0
            limite = float(limite)
            usado = float(rec.get('x_credit_limit_use') or 0.0)
            es_usada = usado > 0

            fech = rec.get('x_fecha_activacion')
            dias_activos = None
            if fech:
                try:
                    fdt = datetime.strptime(str(fech)[:19], '%Y-%m-%d %H:%M:%S').date()
                    dias_activos = (hoy - fdt).days
                except Exception:
                    fdt = None
            else:
                fdt = None

            es_caducada = (not es_usada) and (dias_activos is not None) and (dias_activos >= CADUCA_DAYS)

            # Año/mes (usa fecha de activación; si no hay, "Sin activar")
            if fdt:
                key = (fdt.year, fdt.month)
            else:
                key = (-1, -1)  # sin fecha de activación

            g = month_agg[key]
            g['total_clientes'] += 1
            g['total_monto'] += limite
            if limite < 3000:
                g['rango_menor_3000'] += 1
            elif limite <= 6000:
                g['rango_3000_6000'] += 1
            else:
                g['rango_mayor_6000'] += 1

            if es_usada:
                g['usadas'] += 1
                total_general['usadas'] += 1
            else:
                g['no_usadas'] += 1
                total_general['no_usadas'] += 1
            if es_caducada:
                g['caducados'] += 1
                total_general['caducados'] += 1

            total_general['total_lineas'] += 1
            total_general['total_monto'] += limite

            g['clientes'].append({
                'name': rec.get('name') or '',
                'id': rec.get('id'),
                'limite': round(limite, 2),
                'available': round(float(rec.get('x_credit_limit_available') or 0.0), 2),
                'usado': round(usado, 2),
                'activada': bool(rec.get('x_activacion_linea')),
                'fecha_activacion': str(fech)[:10] if fech else '',
                'dias_activos': dias_activos,
                'caducado': es_caducada,
                'usada': es_usada,
                'estado': 'Usada' if es_usada else ('Caducada' if es_caducada else 'No usada'),
            })

        # Orden: grupos con fecha primero (año desc, mes desc), "Sin activar" al final
        def sort_key(item):
            if item == (-1, -1):
                return (0, 0, 0)
            return (1, -item[0], -item[1])

        grupos = []
        for k in sorted(month_agg.keys(), key=sort_key):
            g = month_agg[k]
            if k == (-1, -1):
                grupos.append(dict({
                    'year': None, 'month': None,
                    'label': 'Sin activar',
                }, **g))
            else:
                grupos.append(dict({
                    'year': k[0], 'month': k[1],
                    'label': f"{k[1]:02d}-{k[0]}",
                }, **g))

        # Totales generales como objeto adicional (lo consume el frontend)
        total_general['monto'] = round(total_general['total_monto'], 2)
        # Guardamos además el total año/mes resumido
        # Medio de conocimiento
        medios_counter = {}
        try:
            medios_data = json_execute(sess, 'res.partner', 'search_read', [
                [['x_medio', '!=', False]], ['id', 'x_medio']
            ])
            for m in medios_data:
                medio = m.get('x_medio', '')
                if medio:
                    medios_counter[medio] = medios_counter.get(medio, 0) + 1
        except Exception:
            pass

        return {
            'grupos': grupos,
            'totales': total_general,
            'medios_conocimiento': medios_counter,
        }

    except Exception as e:
        print(f"Error al buscar expedientes: {e}")
        return {
            'grupos': [],
            'totales': {'usadas': 0, 'no_usadas': 0, 'caducados': 0,
                        'total_lineas': 0, 'total_monto': 0.0, 'monto': 0.0},
        }

# ── Pago Proveedor MOTO CITY PRO ─────────────────────────
_ciclo_field_cache = None  # Cache: nombre técnico del campo "Manejo de ciclos"

# Nombre técnico CONFIRMADO del campo "Manejo de ciclos"
# (field_get en Odoo: tenure_plan_ciclo, selection ['3y18'/'10y25'])
_CAMPO_CICLO = 'tenure_plan_ciclo'

def _descubrir_campo_ciclo(sess):
    """Verifica el nombre técnico del campo 'Manejo de ciclos' en sale.order.
    Cachea el resultado para no repetir fields_get por orden."""
    global _ciclo_field_cache
    if _ciclo_field_cache is not None:
        return _ciclo_field_cache

    try:
        so_fields = json_execute(sess, 'sale.order', 'fields_get', [],
                                 {'attributes': ['string', 'type', 'selection']})
        if _CAMPO_CICLO in so_fields:
            _ciclo_field_cache = _CAMPO_CICLO
            info = so_fields[_CAMPO_CICLO]
            print(f"[pagoProveedor] Campo '{_CAMPO_CICLO}' confirmado en sale.order "
                  f"(string: '{info.get('string')}', selection: {info.get('selection')})")
            return _CAMPO_CICLO
        # Fallback: buscar por string "Manejo de ciclos"
        for fname, finfo in so_fields.items():
            if (finfo.get('string') or '').lower() in ('manejo de ciclos', 'manejo de cicle'):
                _ciclo_field_cache = fname
                print(f"[pagoProveedor] Campo detectado por string: '{fname}' (Manejo de ciclos)")
                return fname
        print("[pagoProveedor] AVISO: No se encontró campo 'Manejo de ciclos' en sale.order")
        _ciclo_field_cache = False
        return False
    except Exception as e:
        print(f"[pagoProveedor] Error consultando sale.order.fields_get: {e}")
        _ciclo_field_cache = False
        return False


def _leer_ciclo_ov(sess, so_id):
    """Lee el campo 'Manejo de ciclos' (tenure_plan_ciclo) de una sale.order.
    Retorna '03-18', '10-25', o False si no se pudo determinar."""
    campo = _descubrir_campo_ciclo(sess)
    if not campo:
        return False

    try:
        recs = json_execute(sess, 'sale.order', 'read', [[so_id], [campo]])
        if recs:
            val = recs[0].get(campo, '')
            return _normalizar_ciclo(val)
    except Exception as e:
        print(f"[pagoProveedor] Error leyendo campo '{campo}' de OV {so_id}: {e}")

    return False


def _normalizar_ciclo(valor):
    """Normaliza el valor de tenure_plan_ciclo a '03-18' o '10-25'.
    Valores de Odoo: '3y18' (3 y 18) → 03-18, '10y25' (10 y 25) → 10-25."""
    if not valor:
        return False
    val_str = str(valor).strip().lower()
    if not val_str or val_str in ('false', 'none', 'f'):
        return False
    if '3y18' == val_str or '03y18' == val_str or '3 y 18' in val_str:
        return '03-18'
    if '10y25' == val_str or '10 y 25' in val_str:
        return '10-25'
    # Fallback flexible
    if '3' in val_str and '18' in val_str and '10' not in val_str:
        return '03-18'
    if '10' in val_str and '25' in val_str and '3' not in val_str:
        return '10-25'
    print(f"[pagoProveedor] AVISO: valor de ciclo no reconocido: '{valor}'")
    return val_str


def _fecha_ancla_cuota(sess, so_id):
    """Primera cuota REAL del cliente: línea invoice.installment.line con
    is_installment=True de las facturas de la sale.order. Devuelve la payment_date
    (date) de la primera cuota aún por pagar según el plan; si todas están pagadas,
    la más antigua. None si no se puede determinar."""
    from datetime import date as _dt_date
    try:
        so_data = json_execute(sess, 'sale.order', 'search_read', [
            [['id', '=', so_id]],
            ['id', 'invoice_ids']
        ])
        if not so_data:
            return None
        inv_ids = list(so_data[0].get('invoice_ids') or [])
        if not inv_ids:
            return None
        il_ids = json_execute(sess, 'invoice.installment.line', 'search',
                              [[['invoice_id', 'in', inv_ids], ['is_installment', '=', True]]])
        if not il_ids:
            return None
        recs = json_execute(sess, 'invoice.installment.line', 'read',
                            [il_ids, ['payment_date', 'state']])
        pendientes = []
        todas = []
        for r in recs:
            pd = str(r.get('payment_date') or '')[:10]
            if len(pd) == 10:
                todas.append(pd)
                if r.get('state') != 'paid':
                    pendientes.append(pd)
        fechas = pendientes or todas
        if not fechas:
            return None
        fechas.sort()
        return _dt_date.fromisoformat(fechas[0])
    except Exception as e:
        print(f"[pagoProveedor] AVISO: no se pudo leer fecha ancla de OV id={so_id}: {e}")
        return None


def _primera_cuota_proveedor(ciclo, ancla):
    """Asigna la cuota #1 del proveedor según el ciclo y la primera cuota real
    del cliente. Opción A (03-18): días 5/20. Opción B (10-25): días 12/27."""
    day_a, day_b = (5, 20) if ciclo == '03-18' else (12, 27)
    if ancla.day <= day_a:
        return ancla.replace(day=day_a)
    if ancla.day <= day_b:
        return ancla.replace(day=day_b)
    y, m = ancla.year, ancla.month + 1
    if m > 12:
        y, m = y + 1, 1
    return ancla.replace(year=y, month=m, day=day_a)


def _base_fallback(ciclo, hoy):
    """Cuota #1 del proveedor cuando no hay cuotas reales del cliente: siguiente
    día de pago del ciclo a partir de hoy."""
    from datetime import date as _dt_date
    day_a, day_b = (5, 20) if ciclo == '03-18' else (12, 27)
    if hoy.day <= day_a:
        return hoy.replace(day=day_a)
    if hoy.day <= day_b:
        return hoy.replace(day=day_b)
    y, m = hoy.year, hoy.month + 1
    if m > 12:
        y, m = y + 1, 1
    return _dt_date(y, m, day_a)


def fetch_pagoProveedorMoto(sess):
    """Pago a proveedor MOTO CITY PRO: 40% inicial + 60% en 8 cuotas quincenales.
    La cuota #1 se calcula desde la PRIMERA CUOTA REAL del cliente (invoice.installment.line
    con is_installment=True, 'Manejo de ciclos' de la sale.order como opción A/B)."""
    from datetime import date
    import calendar
    proveedor = "MOTO CITY PRO, C.A."

    # Precalentar el cache del campo ciclo una sola vez
    _descubrir_campo_ciclo(sess)

    purchase = json_execute(sess, 'purchase.order', 'search_read', [
        [['partner_id.name', 'ilike', 'MOTO CITY PRO'], ['state', '=', 'purchase']],
        ['id', 'name', 'partner_ref', 'date_order', 'amount_total', 'partner_id', 'state', 'order_line']
    ])
    if not purchase:
        return {"items": [], "proveedor": proveedor, "orden_compra": "", "total_ordenes": 0, "total_pagoInicial": 0, "total_financiado": 0}

    # Cache de sale.order: buscar SOLO una vez por nombre de OV
    _so_cache = {}  # orden_venta_name → {so_id, cliente}
    _ancla_cache = {}  # so_id → fecha ancla (date) o None

    items = []
    for p in purchase:
        pid = p.get('partner_id')
        proveedor_nombre = pid[1] if isinstance(pid, list) and len(pid) > 1 else proveedor
        fecha_compra = str(p.get('date_order') or '')[:10]
        monto_total_compra = float(p.get('amount_total', 0) or 0)
        orden_compra = p.get('name', '')
        orden_venta = p.get('partner_ref', '')
        cliente_venta = 'Sin asignar'
        so_id_venta = 0

        # ── Buscar la sale.order por partner_ref (una sola vez por OV) ──
        if orden_venta:
            if orden_venta in _so_cache:
                cached = _so_cache[orden_venta]
                cliente_venta = cached['cliente']
                so_id_venta = cached['so_id']
            else:
                try:
                    so_data = json_execute(sess, 'sale.order', 'search_read', [
                        [['name', '=', orden_venta]],
                        ['id', 'name', 'partner_id']
                    ])
                    if so_data:
                        so = so_data[0]
                        so_id_venta = so['id']
                        so_pid = so.get('partner_id')
                        if so_pid and isinstance(so_pid, list) and len(so_pid) > 1:
                            cliente_venta = so_pid[1]
                    _so_cache[orden_venta] = {'so_id': so_id_venta, 'cliente': cliente_venta}
                except Exception:
                    pass

        # ── Líneas de la orden de compra (precio moto + gasto admin) ──
        line_ids = p.get('order_line', [])
        precio_moto = 0
        gasto_admin = 0
        modelo = ''
        if line_ids:
            lines = json_execute(sess, 'purchase.order.line', 'read', [line_ids, ['product_id', 'price_unit', 'price_subtotal', 'name']])
            for l in lines:
                pname = l.get('name', '')
                if 'Gasto Administrativo' in pname or 'gasto' in pname.lower():
                    gasto_admin += float(l.get('price_subtotal', 0) or 0)
                else:
                    precio_moto = float(l.get('price_unit', 0) or 0)
                    prod = l.get('product_id')
                    modelo = prod[1] if isinstance(prod, list) and len(prod) > 1 else pname
        if precio_moto <= 0:
            precio_moto = monto_total_compra
        inicial_40 = round(precio_moto * 0.40, 2)
        restante_60 = round(precio_moto * 0.60, 2)
        cuota_quincenal = round(restante_60 / 8, 2)

        # ── DETECCIÓN DEL CICLO ──
        # 1) Intentar leer directo del campo 'Manejo de ciclos' en la sale.order
        ciclo_cliente = '03-18'  # Default: mayoría de clientes
        if so_id_venta:
            ciclo_ov = _leer_ciclo_ov(sess, so_id_venta)
            if ciclo_ov:
                ciclo_cliente = ciclo_ov
            else:
                print(f"[pagoProveedor] AVISO: OV {orden_venta} (id={so_id_venta}) sin 'Manejo de ciclos' definido, usando default '03-18'")
        else:
            print(f"[pagoProveedor] AVISO: OV '{orden_venta}' no encontrada, usando ciclo default '03-18'")

        # ── Calcular 8 cuotas quincenales según ciclo y FECHA ANCLA ──
        pagos = []
        day_a, day_b = (5, 20) if ciclo_cliente == '03-18' else (12, 27)
        fecha_ancla = None
        if so_id_venta:
            if so_id_venta in _ancla_cache:
                fecha_ancla = _ancla_cache[so_id_venta]
            else:
                fecha_ancla = _fecha_ancla_cuota(sess, so_id_venta)
                _ancla_cache[so_id_venta] = fecha_ancla
            if fecha_ancla:
                base = _primera_cuota_proveedor(ciclo_cliente, fecha_ancla)
                print(f"[pagoProveedor] {orden_compra}: primera cuota cliente={fecha_ancla} "
                      f"-> cuota#1 proveedor={base} (ciclo {ciclo_cliente})")
            else:
                print(f"[pagoProveedor] {orden_compra}: sin cuotas del cliente, fechas desde hoy")
                base = _base_fallback(ciclo_cliente, date.today())
        else:
            # Sin OV: fallback desde hoy con el ciclo por defecto
            print(f"[pagoProveedor] {orden_compra}: sin OV, fechas desde hoy")
            base = _base_fallback(ciclo_cliente, date.today())
        fecha_ancla_str = str(fecha_ancla)[:10] if fecha_ancla else ''

        y, m = base.year, base.month
        dia = base.day  # primer día del par (A o B)
        for cuota_num in range(1, 9):
            try:
                fecha_pago = date(y, m, dia)
            except:
                fecha_pago = date(y, m, calendar.monthrange(y, m)[1])
            pagos.append({'cuota': cuota_num, 'fecha_pago': str(fecha_pago)[:10],
                          'monto': cuota_quincenal, 'estado': 'pendiente'})
            # Alternar día: tras el primer día del par sigue el segundo en el mismo mes,
            # tras el segundo, saltar al siguiente mes con el primer día.
            if dia == day_a:
                dia = day_b
            else:
                dia = day_a
                m += 1
                if m > 12:
                    m = 1
                    y += 1

        items.append({
            'purchase_order_id': p['id'], 'orden_compra': orden_compra, 'orden_venta': orden_venta,
            'proveedor': proveedor_nombre, 'cliente': cliente_venta, 'modelo': modelo,
            'fecha_compra': fecha_compra, 'monto_total_compra': round(monto_total_compra, 2),
            'precio_moto': round(precio_moto, 2), 'gasto_admin': round(gasto_admin, 2),
            'inicial_40': inicial_40, 'restante_60': restante_60, 'cuota_quincenal': cuota_quincenal,
            'ciclo': ciclo_cliente, 'opcion': 'A' if ciclo_cliente == '03-18' else 'B',
            'fecha_ancla_cliente': fecha_ancla_str, 'pagos': pagos,
        })
    return {
        'items': items, 'proveedor': proveedor,
        'orden_compra': ', '.join(it['orden_compra'] for it in items),
        'total_ordenes': len(items),
        'total_pagoInicial': round(sum(it['inicial_40'] for it in items), 2),
        'total_financiado': round(sum(it['restante_60'] for it in items), 2),
    }


def fetch_dshbcredimoto(sess):
    """Dashboard CREDIMOTO: resumen de ventas, pagos de clientes y pagos a proveedor.

    Identifica órdenes CREDIMOTO por la etiqueta sale.order.tag_ids. Las cuotas del
    cliente se leen de invoice.installment.line vinculadas a la FACTURA exacta de la
    orden (sale.order.invoice_ids), no por partner ni por monto promedio. El pago
    real a proveedor sale de account.move: amount_total - amount_residual.
    El margen/costo se calcula pero NO se muestra en la pestaña (extra)."""
    from collections import defaultdict

    # ── 1. Purchase orders (proveedor MOTO CITY PRO) ──
    # Se cargan PRIMERO porque son la fuente fiable para identificar qué
    # órdenes de venta son CREDIMOTO (los partners NO siempre tienen tag "CREDIMOTO").
    po_recs = json_execute(sess, 'purchase.order', 'search_read', [
        [['partner_id.name', 'ilike', 'MOTO CITY PRO'], ['state', '=', 'purchase']],
        ['id', 'name', 'partner_ref', 'amount_total', 'partner_id', 'invoice_ids']
    ])

    po_by_ov = {}  # orden_venta_name → {po_id, po_name, monto, partner_ref, invoice_ids}
    po_all = []
    for p in po_recs:
        ov = p.get('partner_ref', '')
        po_all.append({
            'po_id': p['id'], 'po_name': p.get('name', ''),
            'monto': float(p.get('amount_total', 0) or 0),
            'invoice_ids': p.get('invoice_ids', []),
            'ov': ov,
        })
        if ov:
            po_by_ov[ov] = po_all[-1]

    # ── 2. Obtener ventas de motos y seleccionar CREDIMOTO ──
    vm = fetch_ventas_motos(sess)
    vm_items = vm.get('items', [])
    # La etiqueta "CREDIMOTO" vive en sale.order.tag_ids. Se detecta AQUÍ (solo para
    # esta pestaña) sin modificar fetch_ventas_motos ni ninguna otra pestaña.
    _ord_ids = set(it.get('orden_id') for it in vm_items if it.get('orden_id'))
    _tag_map = {}  # sale_order_id → bool
    _ord_ids_list = list(_ord_ids)
    for i in range(0, len(_ord_ids_list), 500):
        _recs = json_execute(sess, 'sale.order', 'read',
                             [_ord_ids_list[i:i + 500], ['id', 'tag_ids']])
        for _r in _recs:
            _tags = [str(t[1]) for t in (_r.get('tag_ids') or [])
                     if isinstance(t, list) and len(t) > 1]
            _tag_map[_r['id']] = any(
                'CREDIMOTO' in _tg.upper() or 'CERDIMOTO' in _tg.upper() for _tg in _tags
            )

    # Fuente principal: etiqueta CREDIMOTO en sale.order.tag_ids.
    credimoto_items = [it for it in vm_items if _tag_map.get(it.get('orden_id'))]
    # Respaldo 1: OV vinculada a una OC de MOTO CITY PRO (partner_ref).
    if po_by_ov and not credimoto_items:
        credimoto_items = [it for it in vm_items if it.get('orden') in po_by_ov]
    # Respaldo 2: ante la duda, mostrar todas las ventas de motos.
    if not credimoto_items:
        credimoto_items = vm_items
    if not credimoto_items:
        return {
            'resumen': {'total_ordenes': 0, 'total_motos': 0, 'total_producto': 0,
                        'total_gasto_admin': 0, 'total_facturado': 0,
                        'cobrado_clientes': 0, 'cuotas_pagadas': 0,
                        'cuotas_por_cobrar': 0, 'margen_bruto': 0, 'margen_pct': 0},
            'ventas': [], 'proveedor_por_oc': [],
            'snapshot': {'ventas': 0, 'cobrado': 0, 'por_cobrar': 0, 'por_pagar': 0},
            'por_ciclo': {}, 'facturas_proveedor': [],
        }

    # ── 3. Facturas EXACTAS de cada orden CREDIMOTO (sale.order.invoice_ids) ──
    # Las cuotas del cliente se vinculan a la factura de su orden (no por partner,
    # no por aproximación de monto) para evitar cuentas de otros contratos.
    so_rows = {}  # orden_name → {so_id, partner_id, invoice_ids}
    so_info = json_execute(sess, 'sale.order', 'search_read', [
        [['name', 'in', [it.get('orden', '') for it in credimoto_items]]],
        ['id', 'name', 'partner_id', 'invoice_ids']
    ])
    for s in so_info:
        pid = s.get('partner_id')
        so_rows[s['name']] = {
            'so_id': s['id'],
            'partner_id': pid[0] if isinstance(pid, list) else 0,
            'invoice_ids': list(s.get('invoice_ids') or []),
        }

    all_inv_ids = set()
    for r in so_rows.values():
        all_inv_ids.update(r['invoice_ids'])

    # Líneas del plan por factura exacta
    inv_lines = defaultdict(list)  # invoice_id → [{state, amount, payment_date, is_installment, description}]
    if all_inv_ids:
        il_ids = json_execute(sess, 'invoice.installment.line', 'search',
                              [[['invoice_id', 'in', list(all_inv_ids)]]])
        for i in range(0, len(il_ids), 2000):
            batch = il_ids[i:i + 2000]
            recs = json_execute(sess, 'invoice.installment.line', 'read',
                                [batch, ['state', 'amount', 'payment_date',
                                         'invoice_id', 'is_installment', 'description']])
            for l in recs:
                inv = l.get('invoice_id')
                iid = inv[0] if isinstance(inv, list) and len(inv) > 1 else None
                if iid:
                    inv_lines[iid].append(l)

    # ── 4. Facturas de proveedor + monto REAL pagado (account.move) ──
    all_po_inv_ids = set()
    for po in po_all:
        all_po_inv_ids.update(po.get('invoice_ids', []))

    proveedor_facturas = []
    if all_po_inv_ids:
        pf_ids = list(all_po_inv_ids)
        for i in range(0, len(pf_ids), 500):
            batch = pf_ids[i:i + 500]
            pf_recs = json_execute(sess, 'account.move', 'read',
                                   [batch, ['id', 'name', 'invoice_date', 'amount_total',
                                            'amount_residual', 'state', 'payment_state']])
            for f in pf_recs:
                total = float(f.get('amount_total', 0) or 0)
                res = f.get('amount_residual')
                pagado = round(total - float(res or 0), 2) if res is not None else 0.0
                proveedor_facturas.append({
                    'factura_id': f['id'],
                    'numero': f.get('name', ''),
                    'fecha': str(f.get('invoice_date') or '')[:10],
                    'monto': round(total, 2),
                    'pagado': round(pagado, 2),
                    'estado': f.get('state', ''),
                    'pago_estado': f.get('payment_state', ''),
                })

    # Mapear po_id → facturas de proveedor
    po_inv_map = defaultdict(list)
    for f in proveedor_facturas:
        for po in po_all:
            if f['factura_id'] in po.get('invoice_ids', []):
                po_inv_map[po['po_id']].append(f)
                break

    # ── 5. Procesar cada venta CREDIMOTO ──
    ventas = []
    total_facturado = 0.0
    total_producto = 0.0
    total_gasto_admin = 0.0
    total_motos = 0
    cobrado_clientes_total = 0.0
    cuotas_pagadas_total = 0
    cuotas_por_cobrar_total = 0
    ciclo_data = defaultdict(lambda: {'ventas': 0.0, 'cobrado': 0.0, 'clientes': set()})

    for it in credimoto_items:
        orden = it.get('orden', '')
        cliente = it.get('cliente', '')
        modelo = it.get('modelo', '')
        fecha = it.get('fecha', '')
        unidades = int(it.get('unidades', 1) or 1)
        precio_producto = float(it.get('precio_producto', 0) or 0)
        gasto_admin = float(it.get('gasto_admin', 0) or 0)
        precio_venta = float(it.get('monto_total', 0) or 0)

        total_motos += unidades
        total_producto += precio_producto
        total_gasto_admin += gasto_admin
        total_facturado += precio_venta

        so = so_rows.get(orden, {})
        so_id = so.get('so_id', 0)

        # Ciclo de la OV
        ciclo = '03-18'
        if so_id:
            ciclo_leido = _leer_ciclo_ov(sess, so_id)
            if ciclo_leido:
                ciclo = ciclo_leido

        # Cuotas del cliente: SOLO las de las facturas de esta orden
        lines = []
        for iid in so.get('invoice_ids', []):
            lines.extend(inv_lines.get(iid, []))

        paid_lines = [l for l in lines if l.get('state') == 'paid']
        cuota_lines = [l for l in lines if l.get('is_installment')]
        cuotas_pagadas = len([l for l in cuota_lines if l.get('state') == 'paid'])
        cuotas_por_cobrar = len(cuota_lines) - cuotas_pagadas
        cobrado = round(sum(float(l.get('amount', 0) or 0) for l in paid_lines), 2)
        saldo_pendiente = round(precio_venta - cobrado, 2)

        print(f"[dshcredimoto] {orden}: {len(lines)} lineas plan ({len(cuota_lines)} cuotas), "
              f"pagadas={cuotas_pagadas}, iniciales+cuotas cobrado=${cobrado}, "
              f"por cobrar=${saldo_pendiente}")

        inicial_40 = round(precio_venta * 0.40, 2)
        restante_60 = round(precio_venta * 0.60, 2)

        po_info = po_by_ov.get(orden, {})
        po_id = po_info.get('po_id', 0) if po_info else 0
        po_facturas = po_inv_map.get(po_id, []) if po_id else []
        po_facturas_out = [{
            'numero': f['numero'], 'fecha': f['fecha'],
            'monto': f['monto'], 'pagado': f['pagado'], 'estado': f['estado'],
        } for f in po_facturas]

        ventas.append({
            'orden': orden, 'cliente': cliente, 'modelo': modelo, 'ciclo': ciclo,
            'fecha': fecha, 'unidades': unidades,
            'precio_producto': round(precio_producto, 2),
            'gasto_admin': round(gasto_admin, 2),
            'precio_venta': round(precio_venta, 2),
            'inicial_40': inicial_40, 'restante_60': restante_60,
            'cobrado': cobrado, 'saldo_pendiente': saldo_pendiente,
            'cuotas_totales': len(cuota_lines), 'cuotas_pagadas': cuotas_pagadas,
            'cuotas_por_cobrar': cuotas_por_cobrar,
            'po_name': po_info.get('po_name', '') if po_info else '',
            'po_facturas': po_facturas_out,
        })

        cobrado_clientes_total += cobrado
        cuotas_pagadas_total += cuotas_pagadas
        cuotas_por_cobrar_total += cuotas_por_cobrar
        ciclo_data[ciclo]['ventas'] += precio_venta
        ciclo_data[ciclo]['cobrado'] += cobrado
        ciclo_data[ciclo]['clientes'].add(cliente)

    # ── 6. Pago real a proveedor POR ORDEN DE COMPRA ──
    proveedor_por_oc = []
    for po in po_all:
        ov = po.get('ov', '')
        cliente_oc = ''
        for it in credimoto_items:
            if it.get('orden') == ov:
                cliente_oc = it.get('cliente', '')
                break
        facturas_po = po_inv_map.get(po['po_id'], [])
        monto_fact = round(sum(f['monto'] for f in facturas_po), 2)
        pago_occ = round(sum(f['pagado'] for f in facturas_po), 2)
        proveedor_por_oc.append({
            'orden_compra': po['po_name'], 'orden_venta': ov, 'cliente': cliente_oc,
            'monto_facturado': monto_fact, 'pagado': pago_occ,
        })
    proveedor_por_oc.sort(key=lambda x: x['orden_compra'])

    compras_total = round(sum(po['monto'] for po in po_all), 2)
    total_pagado_proveedor = round(sum(f['pagado'] for f in proveedor_facturas), 2)
    por_cobrar = round(total_facturado - cobrado_clientes_total, 2)
    por_pagar = round(compras_total - total_pagado_proveedor, 2)

    # Extra (calculado, NO mostrado en la pestaña): margen sobre monto de compra
    margen_bruto = round(total_facturado - compras_total, 2)
    margen_pct = round(margen_bruto / total_facturado * 100, 1) if total_facturado else 0

    por_ciclo = {
        ciclo: {
            'ventas': round(d['ventas'], 2),
            'cobrado': round(d['cobrado'], 2),
            'pendiente': round(d['ventas'] - d['cobrado'], 2),
            'clientes_count': len(d['clientes']),
        }
        for ciclo, d in sorted(ciclo_data.items())
    }

    print(f"[dshcredimoto] RESUMEN: facturado=${total_facturado}, "
          f"cobrado_clientes=${cobrado_clientes_total}, cuotas pagadas={cuotas_pagadas_total}, "
          f"cuotas por cobrar={cuotas_por_cobrar_total}, "
          f"pago_proveedor=${total_pagado_proveedor}/{compras_total}")

    return {
        'resumen': {
            'total_ordenes': len(ventas),
            'total_motos': total_motos,
            'total_producto': round(total_producto, 2),
            'total_gasto_admin': round(total_gasto_admin, 2),
            'total_facturado': round(total_facturado, 2),
            'cobrado_clientes': round(cobrado_clientes_total, 2),
            'cuotas_pagadas': cuotas_pagadas_total,
            'cuotas_por_cobrar': cuotas_por_cobrar_total,
            'margen_bruto': margen_bruto,
            'margen_pct': margen_pct,
        },
        'ventas': sorted(ventas, key=lambda x: x['orden']),
        'proveedor_por_oc': proveedor_por_oc,
        'snapshot': {
            'ventas': round(total_facturado, 2),
            'cobrado': round(cobrado_clientes_total, 2),
            'por_cobrar': por_cobrar,
            'por_pagar': por_pagar,
        },
        'por_ciclo': por_ciclo,
        'facturas_proveedor': sorted(proveedor_facturas, key=lambda x: x['numero']),
    }


def fetch_payment_plan(sess):
    """Obtiene resumen del plan de pagos fraccionado desde invoice.installment.line.
    Usa JSON-RPC para evitar bug de website_sale_wishlist."""
    from collections import defaultdict
    
    ids = json_execute(sess, 'invoice.installment.line', 'search', [[]])
    batch_size = 2000
    all_lines = []
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        recs = json_execute(sess, 'invoice.installment.line', 'read',
                            [batch, ['state', 'amount', 'payment_date', 'invoice_id']])
        all_lines.extend(recs)

    # ── SOLO FACTURAS PUBLICADAS (posted): excluir canceladas y notas de crédito ──
    # El plan de pagos fraccionado solo debe reflejar facturas de venta publicadas.
    # Se descartan: facturas canceladas (state='cancel') y notas de crédito
    # (move_type='out_refund'/'in_refund'), que dejan cuotas 'vencido' residuales
    # e inflan la morosidad (ej: SAV/2025/00319 cancelada -> 21 cuotas fantasma).
    all_inv_ids = set()
    for l in all_lines:
        inv = l.get('invoice_id')
        inv_id = inv[0] if isinstance(inv, list) and len(inv) > 1 else None
        if inv_id:
            all_inv_ids.add(inv_id)

    partner_map = {}
    partner_id_map = {}  # invoice_id -> partner_id (para teléfono)
    partner_phone = {}  # partner_id -> teléfono
    invoice_status_map = {}
    invoice_date_map = {}
    invoice_valido = set()
    status_labels = {'6': 'Entregado', '4': 'Aprobado',
                     '8': 'Cancelación Total', '10': 'Congelado', '12': 'Congelado'}

    all_inv_list = list(all_inv_ids)
    for i in range(0, len(all_inv_list), 500):
        batch = all_inv_list[i:i+500]
        inv_data = json_execute(sess, 'account.move', 'read',
                                [batch, ['id', 'partner_id', 'name',
                                         'x_status_operativos', 'invoice_date',
                                         'state', 'move_type']])
        for inv in inv_data:
            iid = inv['id']
            pid = inv.get('partner_id')
            partner = pid[1] if isinstance(pid, list) and len(pid) > 1 else 'Desconocido'
            partner_map[iid] = partner
            partner_id_map[iid] = pid[0] if isinstance(pid, list) else 0
            partner_id_map[iid] = pid[0] if isinstance(pid, list) else 0
            raw_st = inv.get('x_status_operativos', '')
            invoice_status_map[iid] = status_labels.get(str(raw_st), '')
            invoice_date_map[iid] = str(inv.get('invoice_date') or '')[:10]
            # Solo facturas de venta PUBLICADAS (excluye canceladas, borradores y NC)
            if inv.get('state') == 'posted' and inv.get('move_type') == 'out_invoice':
                invoice_valido.add(iid)

    # Cargar teléfonos: res.partner.phone/mobile + contact_ids → chatroom number_format
    partner_ids = list(set(pid[0] for inv in inv_data if (pid := inv.get('partner_id')) and isinstance(pid, list)))
    partner_tags = {}  # partner_id -> set of tag names
    for i in range(0, len(partner_ids), 500):
        batch = partner_ids[i:i+500]
        pdata = json_execute(sess, 'res.partner', 'read',
                             [batch, ['id', 'phone', 'mobile', 'contact_ids', 'category_id']])
        for p in pdata:
            pid = p['id']
            phone = p.get('mobile') or p.get('phone') or ''
            phone_clean = str(phone).replace(' ', '').replace('-', '').replace('+', '')
            if phone_clean and not phone_clean.startswith('58'):
                phone_clean = '58' + phone_clean
            if phone_clean:
                phone_clean = '+' + phone_clean
            partner_phone[pid] = phone_clean
            # Tags del partner
            tags = p.get('category_id', [])
            partner_tags[pid] = set(t[1] for t in tags if isinstance(t, list))

            # Si no tiene phone, buscar en contact_ids (chatrooms)
            cids = p.get('contact_ids', [])
            if not partner_phone[pid] and cids:
                try:
                    chats = json_execute(sess, 'acrux.chat.conversation', 'read',
                                         [cids, ['number_format', 'number']])
                    for ch in chats:
                        nf = ch.get('number_format') or ''
                        if nf:
                            partner_phone[pid] = nf
                            break
                        n = str(ch.get('number') or '')
                        if n:
                            partner_phone[pid] = '+' + n
                            break
                except Exception:
                    pass

    # Filtrar líneas: conservar solo cuotas de facturas publicadas de venta
    def _inv_id(line):
        inv = line.get('invoice_id')
        return inv[0] if isinstance(inv, list) and len(inv) > 1 else None

    all_lines = [l for l in all_lines if _inv_id(l) in invoice_valido]

    
    # Agrupar por estado
    state_totals = defaultdict(lambda: {'monto': 0.0, 'cantidad': 0})
    vencidos = []       # lista de (invoice_id, monto, fecha, factura_name)
    debidos = []        # lista de (invoice_id, monto, fecha, factura_name)
    proyeccion = defaultdict(float)  # payment_date -> monto (solo no pagados)
    
    # Análisis por ciclo (día del mes)
    from datetime import datetime, date
    hoy = date.today()
    # ciclo_data[dia][state] = {'cantidad': N, 'monto': X, 'dias_mora': [lista]}
    ciclo_data = defaultdict(lambda: defaultdict(lambda: {'cantidad': 0, 'monto': 0.0, 'dias_mora': []}))
    # ciclo_clientes[dia][partner_name][state] = {'cantidad': N, 'monto': X}
    ciclo_clientes = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'cantidad': 0, 'monto': 0.0})))
    
    for line in all_lines:
        st = line.get('state', '')
        amt = float(line.get('amount') or 0)
        state_totals[st]['monto'] += amt
        state_totals[st]['cantidad'] += 1
        
        inv = line.get('invoice_id')
        inv_id = inv[0] if isinstance(inv, list) and len(inv) > 1 else None
        inv_name = inv[1] if isinstance(inv, list) and len(inv) > 1 else ''
        fecha = str(line.get('payment_date') or '')
        
        # Extraer día del mes para ciclo
        dia = 0
        try:
            if fecha and '-' in fecha:
                dia = int(fecha.split('-')[2])
        except (ValueError, IndexError):
            dia = 0
        
        if dia > 0:
            c = ciclo_data[dia][st]
            c['cantidad'] += 1
            c['monto'] += amt
            if st == 'vencido':
                try:
                    fd = datetime.strptime(fecha, '%Y-%m-%d').date()
                    d_mora = (hoy - fd).days
                    if d_mora > 0:
                        c['dias_mora'].append(d_mora)
                except (ValueError, TypeError):
                    pass
            # Guardar cliente a nivel de día (se asignará partner después)
            temp_cliente_key = inv_id  # lo vinculamos después con partner_map
            cc = ciclo_clientes[dia][temp_cliente_key][st]
            cc['cantidad'] += 1
            cc['monto'] += amt
        
        if st == 'vencido':
            vencidos.append({'invoice_id': inv_id, 'invoice_name': inv_name,
                             'monto': amt, 'fecha': fecha})
        elif st == 'draft':
            debidos.append({'invoice_id': inv_id, 'invoice_name': inv_name,
                            'monto': amt, 'fecha': fecha})
            if fecha:
                proyeccion[fecha] += amt
    
    # Obtener nombres de clientes desde las facturas involucradas (ya cargadas arriba)
    # partner_map / invoice_status_map / invoice_date_map ya están poblados con
    # SOLO facturas publicadas (posted + out_invoice).

    # Resolver inv_id -> partner name en ciclo_clientes (agregar por partner)
    ciclo_clientes_por_partner = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'cantidad': 0, 'monto': 0.0})))
    ciclo_partner_statuses = defaultdict(lambda: defaultdict(set))  # dia -> partner -> set de statuses
    for dia, invs in ciclo_clientes.items():
        for inv_id, states in invs.items():
            partner = partner_map.get(inv_id, 'Desconocido')
            st = invoice_status_map.get(inv_id, '')
            if st:
                ciclo_partner_statuses[dia][partner].add(st)
            for st_name, vals in states.items():
                cc = ciclo_clientes_por_partner[dia][partner][st_name]
                cc['cantidad'] += vals['cantidad']
                cc['monto'] += vals['monto']
    ciclo_clientes = ciclo_clientes_por_partner
    
    # Combinar datos de clientes en vencidos
    clientes_vencidos = defaultdict(lambda: {'monto': 0.0, 'cuotas': 0, 'facturas': [], 'statuses': set()})
    for v in vencidos:
        cliente = partner_map.get(v['invoice_id'], 'Desconocido')
        clientes_vencidos[cliente]['monto'] += v['monto']
        clientes_vencidos[cliente]['cuotas'] += 1
        if v['invoice_name'] not in clientes_vencidos[cliente]['facturas']:
            clientes_vencidos[cliente]['facturas'].append(v['invoice_name'])
        st = invoice_status_map.get(v['invoice_id'], '')
        if st:
            clientes_vencidos[cliente]['statuses'].add(st)
    
    clientes_vencidos_list = [{'cliente': k, 'monto': round(v['monto'], 2),
                                'cuotas': v['cuotas'], 'facturas': v['facturas'],
                                'statuses': list(v['statuses'])}
                              for k, v in sorted(clientes_vencidos.items(),
                                                 key=lambda x: -x[1]['monto'])]
    
    # Proyección ordenada
    proyeccion_list = [{'fecha': k, 'monto': round(v, 2)}
                       for k, v in sorted(proyeccion.items())]

    # Facturas ENTREGADAS con cuotas vencidas
    # Agrupa las cuotas vencidas por factura cuyo status operativo = 'Entregado'
    entregadas_venc = defaultdict(lambda: {
        'monto': 0.0, 'cuotas': 0, 'cliente': '', 'fecha_factura': '',
        'ultima_cuota': '', 'primer_cuota': '', 'facturas': [], 'max_dias_mora': 0
    })
    for v in vencidos:
        inv_id = v['invoice_id']
        if invoice_status_map.get(inv_id) != 'Entregado':
            continue
        f = entregadas_venc[inv_id]
        f['monto'] += v['monto']
        f['cuotas'] += 1
        f['cliente'] = partner_map.get(inv_id, 'Desconocido')
        f['fecha_factura'] = invoice_date_map.get(inv_id, '')
        fc = str(v['fecha'] or '')[:10]
        if fc:
            if not f['primer_cuota'] or fc < f['primer_cuota']:
                f['primer_cuota'] = fc
            if fc > f['ultima_cuota']:
                f['ultima_cuota'] = fc
            try:
                fd = datetime.strptime(fc, '%Y-%m-%d').date()
                d_mora = (hoy - fd).days
                if d_mora > f['max_dias_mora']:
                    f['max_dias_mora'] = d_mora
            except (ValueError, TypeError):
                pass
        if v['invoice_name'] not in f['facturas']:
            f['facturas'].append(v['invoice_name'])

    facturas_entregadas_vencidas = [{
        'invoice_id': inv_id,
        'factura': f['facturas'][0] if f['facturas'] else '',
        'cliente': f['cliente'],
        'monto': round(f['monto'], 2),
        'cuotas': f['cuotas'],
        'fecha_factura': f['fecha_factura'],
        'ultima_cuota': f['ultima_cuota'],
        'primer_cuota': f['primer_cuota'],
        'max_dias_mora': f['max_dias_mora'],
    } for inv_id, f in sorted(entregadas_venc.items(), key=lambda x: -x[1]['monto'])]

    total_entregadas_venc = {
        'facturas': len(facturas_entregadas_vencidas),
        'monto': round(sum(f['monto'] for f in facturas_entregadas_vencidas), 2),
        'cuotas': sum(f['cuotas'] for f in facturas_entregadas_vencidas),
    }

    # Construir ciclo_analysis para rangos 03-18 y 10-25
    def build_ciclo_range(dia_min, dia_max):
        """Construye datos para un rango de días de ciclo, incluyendo clientes."""
        result = {}
        for d in range(dia_min, dia_max + 1):
            entry = {}
            for st in ['draft', 'vencido', 'paid']:
                c = ciclo_data.get(d, {}).get(st, {'cantidad': 0, 'monto': 0.0, 'dias_mora': []})
                dm = c.get('dias_mora', [])
                entry[st] = {
                    'cantidad': c['cantidad'],
                    'monto': round(c['monto'], 2),
                    'dias_mora_prom': round(sum(dm)/len(dm), 1) if dm else 0,
                    'max_dias_mora': max(dm) if dm else 0
                }
            # Clientes del día (top 30 por monto draft+vencido)
            clients_by_day = ciclo_clientes.get(d, {})
            statuses_by_day = ciclo_partner_statuses.get(d, {})
            clients_list = []
            for partner, states in clients_by_day.items():
                draft_monto = states.get('draft', {}).get('monto', 0)
                venc_monto = states.get('vencido', {}).get('monto', 0)
                total = draft_monto + venc_monto
                if total > 0:
                    partner_statuses = list(statuses_by_day.get(partner, set()))
                    clients_list.append({
                        'cliente': partner,
                        'monto_draft': round(draft_monto, 2),
                        'cant_draft': states.get('draft', {}).get('cantidad', 0),
                        'monto_vencido': round(venc_monto, 2),
                        'cant_vencido': states.get('vencido', {}).get('cantidad', 0),
                        'monto_pagado': round(states.get('paid', {}).get('monto', 0), 2),
                        'cant_pagado': states.get('paid', {}).get('cantidad', 0),
                        'statuses': partner_statuses,
                    })
            clients_list.sort(key=lambda x: -(x['monto_draft'] + x['monto_vencido']))
            entry['clientes'] = clients_list[:30]
            result[str(d)] = entry
        return result
    
    ciclo_analysis = {
        '03-18': build_ciclo_range(3, 18),
        '10-25': build_ciclo_range(10, 25),
    }

    # ── Proyección por ciclo y mes: pagadas vs pendientes ──────────
    # Para cada ciclo (03-18, 10-25), por cada mes, contar cuotas
    # pagadas y pendientes (vencido + draft) y clientes únicos.
    ciclo_proj = {'03-18': defaultdict(lambda: {'pagadas': {'cuotas': 0, 'monto': 0.0, 'clientes': set()},
                                                 'pendientes': {'cuotas': 0, 'monto': 0.0, 'clientes': set()}}),
                  '10-25': defaultdict(lambda: {'pagadas': {'cuotas': 0, 'monto': 0.0, 'clientes': set()},
                                                 'pendientes': {'cuotas': 0, 'monto': 0.0, 'clientes': set()}})}

    for line in all_lines:
        st = line.get('state', '')
        amt = float(line.get('amount') or 0)
        inv = line.get('invoice_id')
        inv_id = inv[0] if isinstance(inv, list) and len(inv) > 1 else None
        if not inv_id:
            continue
        cliente = partner_map.get(inv_id, 'Desconocido')
        fecha = str(line.get('payment_date') or '')[:10]
        if not fecha or fecha < str(hoy)[:7]:
            continue  # Solo meses actuales y futuros
        try:
            parts = fecha.split('-')
            anio_mes = parts[0] + '-' + parts[1]
            dia = int(parts[2])
        except (ValueError, IndexError):
            continue

        # Asignar a ciclo
        ciclo_key = None
        if 3 <= dia <= 18:
            ciclo_key = '03-18'
        elif 10 <= dia <= 25:
            ciclo_key = '10-25'
        if not ciclo_key:
            continue

        bucket = 'pagadas' if st == 'paid' else 'pendientes'
        c = ciclo_proj[ciclo_key][anio_mes][bucket]
        c['cuotas'] += 1
        c['monto'] += amt
        c['clientes'].add(cliente)

    # Convertir sets a count para JSON
    ciclo_proj_json = {}
    for ciclo in ['03-18', '10-25']:
        ciclo_proj_json[ciclo] = {}
        for mes, data in sorted(ciclo_proj[ciclo].items()):
            pag = data['pagadas']
            pend = data['pendientes']
            ciclo_proj_json[ciclo][mes] = {
                'pagadas_cuotas': pag['cuotas'],
                'pagadas_monto': round(pag['monto'], 2),
                'pagadas_clientes': len(pag['clientes']),
                'pendientes_cuotas': pend['cuotas'],
                'pendientes_monto': round(pend['monto'], 2),
                'pendientes_clientes': len(pend['clientes']),
            }

    # ── Últimas entregas realizadas: morosidad del cliente ──────────
    # 1) Morosidad TOTAL por cliente (todas sus facturas con cuotas vencidas)
    partner_vencido = defaultdict(lambda: {'monto': 0.0, 'facturas': set(), 'cuotas': 0})
    for v in vencidos:
        cli = partner_map.get(v['invoice_id'], 'Desconocido')
        partner_vencido[cli]['monto'] += v['monto']
        partner_vencido[cli]['cuotas'] += 1
        if v['invoice_name']:
            partner_vencido[cli]['facturas'].add(v['invoice_name'])

    # 2) Últimas facturas ENTREGADAS ordenadas por fecha efectiva de entrega
    entregadas_ids = json_execute(sess, 'account.move', 'search', [[['x_status_operativos', '=', '6']]])
    entregadas_recs = []
    for i in range(0, len(entregadas_ids), 500):
        batch = entregadas_ids[i:i+500]
        recs = json_execute(sess, 'account.move', 'read', [batch, [
            'id', 'name', 'partner_id', 'invoice_date', 'x_commitment_date']])
        if recs:
            entregadas_recs.extend(recs)

    entregadas_recs.sort(key=lambda x: str(x.get('x_commitment_date') or ''), reverse=True)
    ULTIMAS_N = 60
    ultimas_entregas = []
    for inv in entregadas_recs[:ULTIMAS_N]:
        pid = inv.get('partner_id')
        cliente = pid[1] if isinstance(pid, list) and len(pid) > 1 else 'Desconocido'
        pv = partner_vencido.get(cliente, {'monto': 0.0, 'facturas': set(), 'cuotas': 0})
        ultimas_entregas.append({
            'factura': inv.get('name') or '',
            'cliente': cliente,
            'entrega': str(inv.get('x_commitment_date') or '')[:10],
            'factura_fecha': str(inv.get('invoice_date') or '')[:10],
            'vencido_cliente': round(pv['monto'], 2),
            'facturas_mora': len(pv['facturas']),
            'cuotas_mora': pv['cuotas'],
            'moroso': pv['monto'] > 0,
        })

    total_ultimas = {
        'entregas': len(ultimas_entregas),
        'morosos': sum(1 for u in ultimas_entregas if u['moroso']),
        'monto': round(sum(u['vencido_cliente'] for u in ultimas_entregas), 2),
    }

    # ── Pronto Pago: cuotas pagadas cuyo payment_date es futuro ──────
    # Clientes que pagan ANTES de la fecha de vencimiento de la cuota.
    # Cuota con state='paid' y payment_date > hoy => pronto pago.
    pronto_pago_raw = []
    for line in all_lines:
        if line.get('state') != 'paid':
            continue
        pd = str(line.get('payment_date') or '')[:10]
        if not pd or pd <= str(hoy):
            continue
        inv_id = _inv_id(line)
        if not inv_id:
            continue
        # Solo facturas con status operativo = Entregado
        if invoice_status_map.get(inv_id) != 'Entregado':
            continue
        cliente = partner_map.get(inv_id, 'Desconocido')
        inv = line.get('invoice_id')
        inv_name = inv[1] if isinstance(inv, list) and len(inv) > 1 else ''
        try:
            dias_antes = (date.fromisoformat(pd) - hoy).days
        except (ValueError, TypeError):
            dias_antes = 0
        pronto_pago_raw.append({
            'invoice_id': inv_id,
            'factura': inv_name,
            'cliente': cliente,
            'monto': float(line.get('amount') or 0),
            'payment_date': pd,
            'dias_antes': dias_antes,
        })

    # Agrupar por cliente
    pronto_cliente = defaultdict(lambda: {
        'monto': 0.0, 'cuotas': 0, 'facturas': [],
        'fecha_mas_lejana': '', 'max_dias': 0,
    })
    for p in pronto_pago_raw:
        c = pronto_cliente[p['cliente']]
        c['monto'] += p['monto']
        c['cuotas'] += 1
        inv_name = p.get('factura', '')
        inv_id = p.get('invoice_id')
        if inv_name and not any(f['name'] == inv_name for f in c['facturas']):
            c['facturas'].append({'name': inv_name, 'id': inv_id})
        if p['payment_date'] > c['fecha_mas_lejana']:
            c['fecha_mas_lejana'] = p['payment_date']
        if p['dias_antes'] > c['max_dias']:
            c['max_dias'] = p['dias_antes']

    pronto_pago_list = []
    for k, v in sorted(pronto_cliente.items(), key=lambda x: -x[1]['monto']):
        es_credimoto = False
        for iid, pn in partner_map.items():
            if pn == k:
                tags = partner_tags.get(partner_id_map.get(iid, 0), set())
                if 'CREDIMOTO' in tags or 'CERDIMOTO' in tags:
                    es_credimoto = True
                break
        pronto_pago_list.append({
            'cliente': k,
            'monto': round(v['monto'], 2),
            'cuotas': v['cuotas'],
            'facturas': v['facturas'],
            'fecha_mas_lejana': v['fecha_mas_lejana'],
            'max_dias': v['max_dias'],
            'credimoto': es_credimoto,
        })

    total_pronto_raw_monto = round(sum(p['monto'] for p in pronto_pago_raw), 2)

    # ── KPIs avanzados de Pronto Pago ────────────────────────────
    total_pagado_general = round(state_totals['paid']['monto'], 2)

    # Promedio adelantado por cliente
    monto_promedio = round(total_pronto_raw_monto / len(pronto_cliente), 2) if pronto_cliente else 0

    # Índice de anticipación PROMEDIO PONDERADO por monto
    dias_ponderado = 0
    if total_pronto_raw_monto > 0:
        sum_pond = sum(p['dias_antes'] * p['monto'] for p in pronto_pago_raw)
        dias_ponderado = round(sum_pond / total_pronto_raw_monto, 1)

    # Ratio de penetración (% de recaudación total que representa pronto pago)
    penetracion = round((total_pronto_raw_monto / total_pagado_general * 100), 2) if total_pagado_general > 0 else 0

    # Top 10 por impacto en flujo
    top10_impacto = [{
        'cliente': c['cliente'],
        'monto': c['monto'],
        'cuotas': c['cuotas'],
        'dias_max': c['max_dias'],
    } for c in pronto_pago_list[:10]]

    # ── Flags de alerta / priorización ──────────────────────────
    # Reglas de priorización:
    #   ORO  : monto >= $500 O cuotas >= 5 O max_dias >= 100
    #   PLATA: monto >= $200 O cuotas >= 3 O max_dias >= 50
    #   BRONCE: tiene pronto pago (cualquier monto)
    for c in pronto_pago_list:
        m, cu, d = c['monto'], c['cuotas'], c['max_dias']
        if m >= 500 or cu >= 5 or d >= 100:
            c['flag'] = 'oro'
            c['accion'] = 'Asignar ejecutivo preferencial + factura prioritaria + extensión de términos'
        elif m >= 200 or cu >= 3 or d >= 50:
            c['flag'] = 'plata'
            c['accion'] = 'Beneficio Non-Cash: prioridad en entregas + descuento en próximo servicio'
        else:
            c['flag'] = 'bronce'
            c['accion'] = 'Reconocimiento: correo de agradecimiento + beneficio por fidelidad'

    total_pronto = {
        'clientes': len(pronto_pago_list),
        'cuotas': len(pronto_pago_raw),
        'monto': round(total_pronto_raw_monto, 2),
        'monto_promedio': monto_promedio,
        'dias_ponderado': dias_ponderado,
        'penetracion': penetracion,
        'total_pagado': total_pagado_general,
        'oro': sum(1 for c in pronto_pago_list if c['flag'] == 'oro'),
        'plata': sum(1 for c in pronto_pago_list if c['flag'] == 'plata'),
        'bronce': sum(1 for c in pronto_pago_list if c['flag'] == 'bronce'),
    }

    # ── ALERTAS DE MOROSIDAD ───────────────────────────────────
    # Detectar clientes con cuotas vencidas que necesitan atención inmediata.
    # Severidad: CRITICO (>90 días), ALTO (30-90), MEDIO (7-30), BAJO (1-7)
    alertas_morosidad = []
    for cli, data in clientes_vencidos.items():
        if data['monto'] <= 0:
            continue
        # Buscar la cuota más antigua vencida de este cliente
        cuotas_cli = [v for v in vencidos if partner_map.get(v['invoice_id']) == cli]
        if not cuotas_cli:
            continue

        fechas_venc = []
        for v in cuotas_cli:
            f = str(v.get('fecha') or '')[:10]
            if f:
                try:
                    fd = date.fromisoformat(f)
                    dias = (hoy - fd).days
                    fechas_venc.append({'fecha': f, 'dias': dias, 'monto': v['monto'],
                                        'factura': v['invoice_name']})
                except:
                    pass

        if not fechas_venc:
            continue

        # Cuota más antigua = mayor días
        max_dias = max(cv['dias'] for cv in fechas_venc)
        cuota_antigua = max(fechas_venc, key=lambda x: x['dias'])
        total_cuotas_venc = len(cuotas_cli)

        # Severidad
        if max_dias > 90:
            severidad = 'critico'
        elif max_dias > 30:
            severidad = 'alto'
        elif max_dias > 7:
            severidad = 'medio'
        else:
            severidad = 'bajo'

        # Acción sugerida según severidad
        if severidad == 'critico':
            accion = 'Llamar HOY + enviar carta de default + ofrecer reestructuración'
        elif severidad == 'alto':
            accion = 'Contactar esta semana + ofrecer plan de pago + suspender entregas'
        elif severidad == 'medio':
            accion = 'Enviar recordatorio + verificar motivo del atraso'
        else:
            accion = 'Seguimiento suave + recordatorio de próximo vencimiento'

        # ¿Es cliente de pronto pago? (si paga adelante, puede tener problemas de flujo)
        es_pronto_pago = cli in [c['cliente'] for c in pronto_pago_list]

        alertas_morosidad.append({
            'cliente': cli,
            'severidad': severidad,
            'dias_max': max_dias,
            'monto_vencido': round(data['monto'], 2),
            'cuotas_vencidas': total_cuotas_venc,
            'facturas': list(data.get('facturas', [])),
            'cuota_mas_antigua': cuota_antigua['fecha'],
            'factura_antigua': cuota_antigua['factura'],
            'factura_antigua_id': next((v['invoice_id'] for v in cuotas_cli if v['invoice_name'] == cuota_antigua['factura']), 0),
            'accion': accion,
            'es_pronto_pago': es_pronto_pago,
        })

    alertas_morosidad.sort(key=lambda x: (-{'critico': 4, 'alto': 3, 'medio': 2, 'bajo': 1}[x['severidad']], -x['dias_max']))

    total_alertas = {
        'total': len(alertas_morosidad),
        'criticos': sum(1 for a in alertas_morosidad if a['severidad'] == 'critico'),
        'altos': sum(1 for a in alertas_morosidad if a['severidad'] == 'alto'),
        'medios': sum(1 for a in alertas_morosidad if a['severidad'] == 'medio'),
        'bajos': sum(1 for a in alertas_morosidad if a['severidad'] == 'bajo'),
        'monto_total_riesgo': round(sum(a['monto_vencido'] for a in alertas_morosidad), 2),
    }

    # ── Proyección por fecha de cobro ─────────────────────────
    # Para cada fecha específica (3, 10, 18, 25), mostrar:
    # - Monto pendiente de recibir (draft)
    # - Monto que ya pagaron antes (paid + futuro)
    # - Clientes que pagaron vs los que adeudan
    hoy_str = str(hoy)
    fecha_cobro_data = defaultdict(lambda: {
        'pendiente_monto': 0.0, 'pendiente_cuotas': 0, 'pendiente_clientes': set(),
        'pagado_monto': 0.0, 'pagado_cuotas': 0, 'pagado_clientes': set(),
    })

    for line in all_lines:
        st = line.get('state', '')
        amt = float(line.get('amount') or 0)
        fecha = str(line.get('payment_date') or '')[:10]
        if not fecha:
            continue
        try:
            dia = int(fecha.split('-')[2])
        except (ValueError, IndexError):
            continue
        inv_id = _inv_id(line)
        if not inv_id:
            continue
        if invoice_status_map.get(inv_id) != 'Entregado':
            continue
        cliente = partner_map.get(inv_id, 'Desconocido')
        mes = fecha[:7]

        fc = fecha_cobro_data[f"{mes}|{dia}"]
        if st == 'paid' and fecha > hoy_str:
            fc['pagado_monto'] += amt
            fc['pagado_cuotas'] += 1
            fc['pagado_clientes'].add(cliente)
        elif st == 'draft' and fecha >= hoy_str:
            fc['pendiente_monto'] += amt
            fc['pendiente_cuotas'] += 1
            fc['pendiente_clientes'].add(cliente)
        elif st == 'vencido' and fecha[:7] >= hoy_str[:7]:
            fc['pendiente_monto'] += amt
            fc['pendiente_cuotas'] += 1
            fc['pendiente_clientes'].add(cliente)

    fecha_cobro_json = {}
    for key, data in sorted(fecha_cobro_data.items()):
        mes, dia = key.split('|')
        # Solo meses actuales y futuros
        if mes < hoy_str[:7]:
            continue
        ciclo_key = '03-18' if 3 <= int(dia) <= 18 else '10-25'
        if mes not in fecha_cobro_json:
            fecha_cobro_json[mes] = {}
        fecha_cobro_json[mes][f"dia_{dia}"] = {
            'dia': int(dia),
            'ciclo': ciclo_key,
            'pendiente_monto': round(data['pendiente_monto'], 2),
            'pendiente_cuotas': data['pendiente_cuotas'],
            'pendiente_clientes': len(data['pendiente_clientes']),
            'pagado_monto': round(data['pagado_monto'], 2),
            'pagado_cuotas': data['pagado_cuotas'],
            'pagado_clientes': len(data['pagado_clientes']),
        }

    # ── COBRANZA VENCIDA CON COMPROMISO ────────────────────────
    compromiso_ids = json_execute(sess, 'mail.activity', 'search',
                                  [[['res_model', '=', 'account.move'],
                                    ['state', 'in', ['overdue', 'planned']]]])
    compromiso_map = {}
    for i in range(0, len(compromiso_ids), 500):
        batch = compromiso_ids[i:i+500]
        acts = json_execute(sess, 'mail.activity', 'read',
                            [batch, ['id', 'res_id', 'res_name', 'summary',
                                     'note', 'state', 'date_deadline',
                                     'activity_type_id', 'user_id']])
        for a in acts:
            inv_id = a.get('res_id')
            if not inv_id:
                continue
            if inv_id not in compromiso_map:
                compromiso_map[inv_id] = []
            tipo = a.get('activity_type_id')
            tipo_nombre = tipo[1] if isinstance(tipo, list) and len(tipo) > 1 else ''
            user = a.get('user_id')
            user_nombre = user[1] if isinstance(user, list) and len(user) > 1 else ''
            compromiso_map[inv_id].append({
                'actividad_id': a['id'],
                'summary': a.get('summary') or '',
                'note': str(a.get('note') or '')[:200],
                'state': a.get('state', ''),
                'deadline': str(a.get('date_deadline') or '')[:10],
                'tipo': tipo_nombre,
                'responsable': user_nombre,
            })

    facturas_con_compromiso = []
    seen_comp = set()
    for v in vencidos:
        inv_id = v['invoice_id']
        if inv_id in seen_comp:
            continue
        acts = compromiso_map.get(inv_id, [])
        if not acts:
            continue
        seen_comp.add(inv_id)
        cliente = partner_map.get(inv_id, 'Desconocido')
        inv_name = v.get('invoice_name', '')
        fecha_str = str(v.get('fecha', ''))[:10]
        try:
            dias = (hoy - date.fromisoformat(fecha_str)).days if fecha_str else 0
        except:
            dias = 0
        monto_venc = sum(x['monto'] for x in vencidos if x['invoice_id'] == inv_id)
        hay_overdue = any(a['state'] == 'overdue' for a in acts)
        proximo_deadline = min((a['deadline'] for a in acts if a['deadline']), default='')
        facturas_con_compromiso.append({
            'invoice_id': inv_id,
            'factura': inv_name,
            'cliente': cliente,
            'fecha_vencida': fecha_str,
            'dias_atraso': dias,
            'monto_vencido': round(monto_venc, 2),
            'actividades': acts,
            'total_actividades': len(acts),
            'compromiso_overdue': hay_overdue,
            'proximo_deadline': proximo_deadline,
        })
    facturas_con_compromiso.sort(key=lambda x: -x['dias_atraso'])
    total_compromiso = {
        'facturas': len(facturas_con_compromiso),
        'monto_total': round(sum(f['monto_vencido'] for f in facturas_con_compromiso), 2),
        'overdue': sum(1 for f in facturas_con_compromiso if f['compromiso_overdue']),
        'planned': sum(1 for f in facturas_con_compromiso if not f['compromiso_overdue']),
    }

    # ── GESTIÓN DE COBRANZA POR CICLO ─────────────────────────
    # Solo: Entregado/Aprobado + PUBLICADO + NO PAGADO
    # Sin duplicados: agrupar por cliente+factura, sumar cuotas pendientes
    ciclo_gestion_agg = defaultdict(lambda: {
        'cliente': '', 'factura': '', 'invoice_id': 0, 'ciclo': '',
        'fase': '', 'monto_total': 0.0, 'cuotas': 0, 'fecha_min': '',
        'fecha_max': '', 'status_op': '', 'phone': '',
    })
    for line in all_lines:
        inv_id = _inv_id(line)
        if not inv_id:
            continue
        # Solo no pagados
        if line.get('state') == 'paid':
            continue
        # Solo Entregado/Aprobado
        st_op = invoice_status_map.get(inv_id, '')
        if st_op not in ('Entregado', 'Aprobado'):
            continue
        # Solo facturas publicadas (ya filtrado en all_lines por invoice_valido)
        fecha = str(line.get('payment_date') or '')[:10]
        if not fecha:
            continue
        try:
            dia_pago = int(fecha.split('-')[2])
            fecha_dt = date.fromisoformat(fecha)
        except:
            continue
        if 3 <= dia_pago <= 18:
            ciclo = '03-18'
        elif 10 <= dia_pago <= 25:
            ciclo = '10-25'
        else:
            continue
        cliente = partner_map.get(inv_id, 'Desconocido')
        inv = line.get('invoice_id')
        inv_name = inv[1] if isinstance(inv, list) and len(inv) > 1 else ''
        monto = float(line.get('amount') or 0)
        diff_dias = (fecha_dt - hoy).days
        if diff_dias <= -2:
            fase = '2_dias_despues'
        elif diff_dias == -1:
            fase = '1_dia_despues'
        elif diff_dias == 0:
            fase = 'dia_ciclo'
        elif diff_dias == 1:
            fase = '1_dia_antes'
        elif diff_dias >= 2:
            fase = '2_dias_antes'
        else:
            fase = 'pasado'

        # Morosidad
        if diff_dias < -90:
            morosidad = 'critico'
        elif diff_dias < -30:
            morosidad = 'alto'
        elif diff_dias < 0:
            morosidad = 'medio'
        elif diff_dias == 0:
            morosidad = 'hoy'
        else:
            morosidad = 'pendiente'

        key = f"{inv_id}_{fecha}"
        c = ciclo_gestion_agg[key]
        c['cliente'] = cliente
        c['factura'] = inv_name
        c['invoice_id'] = inv_id
        c['ciclo'] = ciclo
        c['fase'] = fase
        c['morosidad'] = morosidad
        c['status_op'] = st_op
        c['phone'] = partner_phone.get(partner_id_map.get(inv_id, 0), '')
        c['monto_total'] += monto
        c['cuotas'] += 1
        if not c['fecha_min'] or fecha < c['fecha_min']:
            c['fecha_min'] = fecha
        if not c['fecha_max'] or fecha > c['fecha_max']:
            c['fecha_max'] = fecha
        if diff_dias < c.get('min_diff', 9999):
            c['min_diff'] = diff_dias

    ciclo_gestion_list = [{
        'cliente': v['cliente'],
        'phone': v['phone'],
        'factura': v['factura'],
        'invoice_id': v['invoice_id'],
        'ciclo': v['ciclo'],
        'fase': v['fase'],
        'morosidad': v['morosidad'],
        'status_op': v['status_op'],
        'monto': round(v['monto_total'], 2),
        'cuotas': v['cuotas'],
        'fecha_pago': v['fecha_min'],
        'diff_dias': v.get('min_diff', 0),
    } for k, v in ciclo_gestion_agg.items()]
    ciclo_gestion_list.sort(key=lambda x: x['diff_dias'])

    # Fallback: buscar teléfonos faltantes directamente de res.partner
    missing_inv_ids = set(x['invoice_id'] for x in ciclo_gestion_list if not x['phone'])
    if missing_inv_ids:
        missing_pid_set = set()
        for mid in missing_inv_ids:
            pid_val = partner_id_map.get(mid, 0)
            if pid_val and pid_val not in partner_phone:
                missing_pid_set.add(pid_val)
        if missing_pid_set:
            for i in range(0, len(list(missing_pid_set)), 500):
                batch = list(missing_pid_set)[i:i+500]
                pdata2 = json_execute(sess, 'res.partner', 'read',
                                      [batch, ['id', 'phone', 'mobile', 'contact_ids']])
                for p in pdata2:
                    pid2 = p['id']
                    phone = p.get('mobile') or p.get('phone') or ''
                    pc = str(phone).replace(' ', '').replace('-', '').replace('+', '')
                    if pc and not pc.startswith('58'):
                        pc = '58' + pc
                    if pc:
                        pc = '+' + pc
                    if not pc and p.get('contact_ids'):
                        try:
                            chats2 = json_execute(sess, 'acrux.chat.conversation', 'read',
                                                  [p['contact_ids'][:3], ['number_format', 'number']])
                            for ch2 in chats2:
                                nf = ch2.get('number_format') or ''
                                if nf:
                                    pc = nf
                                    break
                                n2 = str(ch2.get('number') or '')
                                if n2:
                                    pc = '+' + n2
                                    break
                        except Exception:
                            pass
                    partner_phone[pid2] = pc
        # Re-asignar teléfonos
        for x in ciclo_gestion_list:
            if not x['phone']:
                pid_val = partner_id_map.get(x['invoice_id'], 0)
                x['phone'] = partner_phone.get(pid_val, '')

    ciclo_gestion = {
        'items': ciclo_gestion_list,
        'resumen': {
            '03-18': {
                'total': sum(1 for x in ciclo_gestion_list if x['ciclo'] == '03-18'),
                'monto': round(sum(x['monto'] for x in ciclo_gestion_list if x['ciclo'] == '03-18'), 2),
            },
            '10-25': {
                'total': sum(1 for x in ciclo_gestion_list if x['ciclo'] == '10-25'),
                'monto': round(sum(x['monto'] for x in ciclo_gestion_list if x['ciclo'] == '10-25'), 2),
            },
        },
        'hoy': str(hoy),
    }

    return {
        'state_totals': {k: {'monto': round(v['monto'], 2), 'cantidad': v['cantidad']}
                         for k, v in sorted(state_totals.items())},
        'clientes_vencidos': clientes_vencidos_list[:100],  # Top 100
        'proyeccion': proyeccion_list,
        'total_vencido': round(state_totals['vencido']['monto'], 2),
        'total_debido': round(state_totals['draft']['monto'], 2),
        'total_pagado': round(state_totals['paid']['monto'], 2),
        'total_cuotas': len(all_lines),
        'ciclo_analysis': ciclo_analysis,
        'facturas_entregadas_vencidas': facturas_entregadas_vencidas,
        'total_entregadas_venc': total_entregadas_venc,
        'ultimas_entregas': ultimas_entregas,
        'total_ultimas': total_ultimas,
        'pronto_pago': pronto_pago_list,
        'total_pronto': total_pronto,
        'top10_impacto': top10_impacto,
        'ciclo_proj': ciclo_proj_json,
        'fecha_cobro': fecha_cobro_json,
        'alertas_morosidad': alertas_morosidad,
        'total_alertas': total_alertas,
        'facturas_con_compromiso': facturas_con_compromiso,
        'total_compromiso': total_compromiso,
        'ciclo_gestion': ciclo_gestion,
    }

def fetch_ventas_motos(sess):
    """Ventas de motos PUBLICADAS: precio producto + gasto admin separado.
    Usa categorías dinámicas + cache de tags CREDIMOTO + filtro temporal."""
    from datetime import date, timedelta

    # ── 1. Encontrar categorías de motos dinámicamente ──
    # Buscar categorías cuyo nombre contenga 'moto' o 'motocicleta'
    _moto_categ_cache = getattr(fetch_ventas_motos, '_categ_cache', None)
    if _moto_categ_cache is None:
        try:
            cats = json_execute(sess, 'product.category', 'search_read', [
                [], ['id', 'name']
            ])
            moto_categ_ids = [
                c['id'] for c in cats
                if 'moto' in (c.get('name') or '').lower()
            ]
            if not moto_categ_ids:
                # Fallback: categorías originales si no se encontraron por nombre
                moto_categ_ids = [174, 167]
                print("[ventasMotos] AVISO: No se encontraron categorías 'moto', usando fallback [174, 167]")
            else:
                print(f"[ventasMotos] Categorías de motos detectadas: {moto_categ_ids}")
            fetch_ventas_motos._categ_cache = moto_categ_ids
        except Exception as e:
            moto_categ_ids = [174, 167]
            print(f"[ventasMotos] Error detectando categorías: {e}, usando fallback [174, 167]")
            fetch_ventas_motos._categ_cache = moto_categ_ids
    else:
        moto_categ_ids = _moto_categ_cache

    # ── 2. Buscar productos en esas categorías ──
    prod_ids = json_execute(sess, 'product.product', 'search', [
        [['categ_id', 'in', moto_categ_ids]]
    ])
    if not prod_ids:
        return {
            'items': [], 'total_ordenes': 0, 'total_motos': 0,
            'total_producto': 0, 'total_gasto_admin': 0, 'total_monto': 0,
        }

    # ── 3. Buscar sale.order.line con esos productos ──
    sol_ids = json_execute(sess, 'sale.order.line', 'search', [
        [['product_id', 'in', prod_ids]]
    ])
    order_ids = set()
    for i in range(0, len(sol_ids), 500):
        sols = json_execute(sess, 'sale.order.line', 'read', [sol_ids[i:i+500], ['order_id']])
        for s in sols:
            oid = s.get('order_id')
            if oid and isinstance(oid, list):
                order_ids.add(oid[0])

    if not order_ids:
        return {
            'items': [], 'total_ordenes': 0, 'total_motos': 0,
            'total_producto': 0, 'total_gasto_admin': 0, 'total_monto': 0,
        }

    # ── 4. Leer órdenes de venta publicadas ──
    orders = json_execute(sess, 'sale.order', 'read', [
        list(order_ids), ['id', 'name', 'state', 'partner_id', 'date_order',
                          'order_line', 'amount_total']
    ])
    posted = [o for o in orders if o.get('state') == 'sale']

    # ── 5. Cache de tags CREDIMOTO (cargar todos los partners de una vez) ──
    partner_ids_needed = set()
    for o in posted:
        pid = o.get('partner_id')
        if isinstance(pid, list) and pid[0]:
            partner_ids_needed.add(pid[0])

    _credimoto_cache = {}  # partner_id → bool
    if partner_ids_needed:
        partner_ids_list = list(partner_ids_needed)
        for i in range(0, len(partner_ids_list), 500):
            batch = partner_ids_list[i:i+500]
            pdata = json_execute(sess, 'res.partner', 'read', [
                batch, ['id', 'category_id']
            ])
            for p in pdata:
                tags = [t[1] for t in p.get('category_id', []) if isinstance(t, list)]
                _credimoto_cache[p['id']] = any(
                    'CREDIMOTO' in t or 'CERDIMOTO' in t for t in tags
                )

    # ── 6. Procesar cada orden ──
    items = []
    for o in posted:
        oid_id = o['id']
        date_order = str(o.get('date_order') or '')[:10]  # YYYY-MM-DD completo
        mes = date_order[:7]  # YYYY-MM para agrupación
        if not date_order:
            continue

        pid = o.get('partner_id')
        partner_id = pid[0] if isinstance(pid, list) and len(pid) > 1 else 0
        cliente = pid[1] if isinstance(pid, list) and len(pid) > 1 else 'Desconocido'
        credimoto = _credimoto_cache.get(partner_id, False)

        # ── Líneas de la orden: separar moto vs gasto admin ──
        all_lines_data = json_execute(sess, 'sale.order.line', 'read',
                                      [o.get('order_line', []),
                                       ['product_id', 'price_unit', 'price_subtotal',
                                        'product_uom_qty', 'name']])
        precio_producto = 0
        gasto_admin = 0
        modelo = ''
        unidades_moto = 0
        for l in all_lines_data:
            pname = l.get('name', '')
            qty = int(l.get('product_uom_qty', 1) or 1)
            if 'Gasto Administrativo' in pname or 'gasto' in pname.lower():
                gasto_admin += float(l.get('price_subtotal', 0) or 0)
            else:
                # Tomar la línea de producto con mayor subtotal como "moto"
                subtotal = float(l.get('price_subtotal', 0) or 0)
                if subtotal > precio_producto:
                    precio_producto = float(l.get('price_unit', 0) or 0)
                    prod = l.get('product_id')
                    modelo = prod[1] if isinstance(prod, list) and len(prod) > 1 else pname
                    unidades_moto = qty

        items.append({
            'mes': mes, 'modelo': modelo, 'cliente': cliente,
            'orden': o.get('name', ''), 'orden_id': oid_id,
            'unidades': unidades_moto if unidades_moto else 1,
            'precio_producto': round(precio_producto, 2),
            'gasto_admin': round(gasto_admin, 2),
            'monto_total': round(float(o.get('amount_total', 0)), 2),
            'credimoto': credimoto,
            'fecha': date_order,
        })

    # Ordenar por fecha descendente
    items.sort(key=lambda x: x.get('fecha', ''), reverse=True)

    return {
        'items': items,
        'total_ordenes': len(items),
        'total_motos': sum(it['unidades'] for it in items),
        'total_producto': round(sum(it['precio_producto'] for it in items), 2),
        'total_gasto_admin': round(sum(it['gasto_admin'] for it in items), 2),
        'total_monto': round(sum(it['monto_total'] for it in items), 2),
    }

def fetch_facturacion_agosto(sess):
    """Facturacion mensual AGOSTO 2026 — replica de fetch_facturacion_julio."""
    ST_LABELS = {'6': 'Entregado', '8': 'Cancelación Total', '4': 'Aprobado',
                 '10': 'Congelado', '12': 'Congelado', '0': 'Sin asignar'}
    so_domain = [
        ['x_status_compra', '=', '4'],
        ['commitment_date', '>=', '2026-08-01 04:00:00'],
        ['commitment_date', '<', '2026-09-01 04:00:00'],
    ]
    so_ids = json_execute(sess, 'sale.order', 'search', [so_domain])
    if not so_ids:
        return {
            'facturas': [], 'ejecutivos': [], 'top_productos': [],
            'total_facturado': 0, 'total_facturas': 0, 'total_clientes': 0,
            'total_admin': 0, 'total_admin_total': 0,
            'total_costo': 0, 'total_margen': 0, 'total_productos': 0,
            'colaboradores': [],
            'cancelaciones_count': 0, 'cancelaciones_monto': 0,
        }
    
    ordenes = []
    for i in range(0, len(so_ids), 300):
        batch = so_ids[i:i+300]
        recs = json_execute(sess, 'sale.order', 'read', [batch, [
            'id', 'name', 'partner_id', 'commitment_date',
            'amount_total', 'amount_untaxed',
            'user_id', 'team_id', 'x_status_operativos', 'x_status_compra',
            'order_line',
        ]])
        if recs:
            ordenes.extend(recs)
    
    line_ids = []
    for so in ordenes:
        for lid in (so.get('order_line') or []):
            line_ids.append(lid)
    
    lineas = []
    if line_ids:
        for i in range(0, len(line_ids), 300):
            batch = line_ids[i:i+300]
            recs = json_execute(sess, 'sale.order.line', 'read', [batch, [
                'id', 'product_id', 'product_uom_qty', 'price_unit',
                'price_subtotal', 'price_total', 'discount', 'purchase_price',
            ]])
            if recs:
                lineas.extend(recs)
    
    lineas_por_orden = {}
    for lr in lineas:
        lid = lr['id']
        for so in ordenes:
            if lid in (so.get('order_line') or []):
                if so['id'] not in lineas_por_orden:
                    lineas_por_orden[so['id']] = []
                lineas_por_orden[so['id']].append(lr)
                break
    
    all_prod_ids = set()
    for lr in lineas:
        pid = lr.get('product_id')
        if pid and isinstance(pid, list) and len(pid) > 1:
            all_prod_ids.add(pid[0])
    
    cat_map = {}
    if all_prod_ids:
        prods = json_execute(sess, 'product.product', 'read', [
            list(all_prod_ids), ['id', 'categ_id']
        ])
        for p in prods:
            pid = p['id']
            cat = p.get('categ_id')
            cat_map[pid] = cat[1] if isinstance(cat, list) and len(cat) > 1 else 'Sin categoría'
    
    # Procesar órdenes
    facturas = []
    ejecutivo_stats = defaultdict(lambda: {'facturado': 0, 'costo': 0, 'facturas': 0, 'unidades': 0})
    prod_stats = defaultdict(lambda: {'cantidad': 0, 'monto': 0})
    cancelaciones = []
    total_admin = 0
    total_costo = 0
    clientes_set = set()
    
    for so in ordenes:
        sid = so['id']
        pid = so.get('partner_id')
        cliente = pid[1] if isinstance(pid, list) and len(pid) > 1 else 'Sin cliente'
        clientes_set.add(cliente)
        
        user = so.get('user_id')
        ejecutivo = user[1] if isinstance(user, list) and len(user) > 1 else 'Sin ejecutivo'
        
        status_code = str(so.get('x_status_operativos', '0'))
        status_label = ST_LABELS.get(status_code, status_code)
        
        monto_total = float(so.get('amount_total', 0) or 0)
        
        # Calcular costo y admin de las líneas
        orden_lineas = lineas_por_orden.get(sid, [])
        costo_total = 0
        admin_total = 0
        unidades_total = 0
        
        for l in orden_lineas:
            qty = float(l.get('product_uom_qty', 0) or 0)
            pu = float(l.get('price_unit', 0) or 0)
            pp = float(l.get('purchase_price', 0) or 0)
            desc = float(l.get('discount', 0) or 0)
            
            cat = ''
            pid2 = l.get('product_id')
            if pid2 and isinstance(pid2, list):
                cat = cat_map.get(pid2[0], '')
            
            # Gasto administrativo
            if 'Gasto Administrativo' in cat or 'gasto' in str(pid2[1] if isinstance(pid2, list) else '').lower():
                admin_total += float(l.get('price_subtotal', 0) or 0)
            else:
                costo_total += pp * qty
            
            unidades_total += int(qty)
            
            # Productos
            prod_name = pid2[1] if isinstance(pid2, list) and len(pid2) > 1 else 'Sin producto'
            prod_stats[prod_name]['cantidad'] += int(qty)
            prod_stats[prod_name]['monto'] += float(l.get('price_subtotal', 0) or 0)
        
        ejecutivo_stats[ejecutivo]['facturado'] += monto_total
        ejecutivo_stats[ejecutivo]['costo'] += costo_total
        ejecutivo_stats[ejecutivo]['facturas'] += 1
        ejecutivo_stats[ejecutivo]['unidades'] += unidades_total
        total_admin += admin_total
        total_costo += costo_total
        
        # Cancelaciones
        if status_code == '8':
            cancelaciones.append({
                'orden': so.get('name', ''),
                'cliente': cliente,
                'monto': monto_total,
            })
        
        facturas.append({
            'orden': so.get('name', ''),
            'cliente': cliente,
            'ejecutivo': ejecutivo,
            'monto': round(monto_total, 2),
            'costo': round(costo_total, 2),
            'admin': round(admin_total, 2),
            'status': status_label,
            'fecha': str(so.get('commitment_date', ''))[:10],
        })
    
    # Formatear ejecutivos
    ejecutivos = [{
        'nombre': k,
        'facturado': round(v['facturado'], 2),
        'costo': round(v['costo'], 2),
        'margen': round(v['facturado'] - v['costo'], 2),
        'facturas': v['facturas'],
        'unidades': v['unidades'],
    } for k, v in sorted(ejecutivo_stats.items(), key=lambda x: -x[1]['facturado'])]
    
    # Top productos
    top_prod = [{
        'nombre': k,
        'cantidad': v['cantidad'],
        'monto': round(v['monto'], 2),
    } for k, v in sorted(prod_stats.items(), key=lambda x: -x[1]['monto'])[:15]]
    
    total_facturado = sum(so.get('amount_total', 0) or 0 for so in ordenes)
    total_admin_total = total_admin + sum(
        sum(float(l.get('price_subtotal', 0) or 0) for l in lineas_por_orden.get(so['id'], [])
            if 'Gasto Administrativo' in (l.get('product_id') and isinstance(l.get('product_id'), list) and l['product_id'][1] or ''))
        for so in ordenes
    )
    
    return {
        'facturas': facturas,
        'ejecutivos': ejecutivos,
        'top_productos': top_prod,
        'total_facturado': round(total_facturado, 2),
        'total_facturas': len(facturas),
        'total_clientes': len(clientes_set),
        'total_admin': round(total_admin, 2),
        'total_admin_total': round(total_facturado, 2),
        'total_costo': round(total_costo, 2),
        'total_margen': round(total_facturado - total_costo, 2),
        'total_productos': sum(v['cantidad'] for v in prod_stats.values()),
        'colaboradores': ejecutivos,
        'cancelaciones_count': len(cancelaciones),
        'cancelaciones_monto': round(sum(c['monto'] for c in cancelaciones), 2),
    }

def fetch_facturacion_julio(sess):
    """Facturacion mensual desde sale.order (favorito FACTURACION MENSUAL de Odoo).
    - sale.order: unidad por orden de venta, ejecutivo = user_id (vendedor)
    - sale.order.line: productos, cantidades, subtotales y costo (purchase_price)
    Filtro igual al favorito: x_status_compra = '4', commitment_date en julio 2026.
    Nota: el favorito agrupa commitment_date:month en la zona horaria del usuario
    (America/Caracas, UTC-4 sin DST). Julio local => UTC >= 07-01 04:00:00 y
    UTC < 08-01 04:00:00, para excluir órdenes que son 1-jul en UTC pero
    todavía 30-jun en hora local (ej: LB-ORDEN-03869 de LUIS = 8 Entregado + 3 Cancelación).
    """
    ST_LABELS = {'6': 'Entregado', '8': 'Cancelación Total', '4': 'Aprobado',
                 '10': 'Congelado', '12': 'Congelado', '0': 'Sin asignar'}
    CP_LABELS = {'1': 'Cotización', '4': 'Entrega Realizada', 'False': 'Sin asignar'}
    
    # 1. Buscar órdenes de venta del favorito FACTURACION MENSUAL (julio 2026)
    so_domain = [
        ['x_status_compra', '=', '4'],
        ['commitment_date', '>=', '2026-07-01 04:00:00'],
        ['commitment_date', '<', '2026-08-01 04:00:00'],
    ]
    so_ids = json_execute(sess, 'sale.order', 'search', [so_domain])
    if not so_ids:
        return {
            'facturas': [], 'ejecutivos': [], 'top_productos': [],
            'total_facturado': 0, 'total_facturas': 0, 'total_clientes': 0,
            'total_admin': 0, 'total_admin_total': 0,
            'total_costo': 0, 'total_margen': 0, 'total_productos': 0,
            'colaboradores': [],
            'cancelaciones_count': 0, 'cancelaciones_monto': 0,
        }
    
    # 2. Leer órdenes en lotes
    ordenes = []
    for i in range(0, len(so_ids), 300):
        batch = so_ids[i:i+300]
        recs = json_execute(sess, 'sale.order', 'read', [batch, [
            'id', 'name', 'partner_id', 'commitment_date',
            'amount_total', 'amount_untaxed',
            'user_id', 'team_id', 'x_status_operativos', 'x_status_compra',
            'order_line',
        ]])
        if recs:
            ordenes.extend(recs)
    
    # 3. Recolectar líneas de orden y productos para costos
    line_ids = []
    for so in ordenes:
        for lid in (so.get('order_line') or []):
            line_ids.append(lid)
    
    lineas = []
    if line_ids:
        for i in range(0, len(line_ids), 300):
            batch = line_ids[i:i+300]
            recs = json_execute(sess, 'sale.order.line', 'read', [batch, [
                'id', 'product_id', 'product_uom_qty', 'price_unit',
                'price_subtotal', 'price_total', 'discount', 'purchase_price',
            ]])
            if recs:
                lineas.extend(recs)
    
    # Mapa de líneas por orden
    lineas_por_orden = {}
    for lr in lineas:
        lid = lr['id']
        # necesitamos mapear linea -> orden
        for so in ordenes:
            if lid in (so.get('order_line') or []):
                if so['id'] not in lineas_por_orden:
                    lineas_por_orden[so['id']] = []
                lineas_por_orden[so['id']].append(lr)
                break
    
    # 4. Recolectar categorías de productos
    all_prod_ids = set()
    for lr in lineas:
        pid = lr.get('product_id')
        if pid and isinstance(pid, list) and len(pid) > 1:
            all_prod_ids.add(pid[0])
    
    prod_categ = {}
    if all_prod_ids:
        prod_list = list(all_prod_ids)
        for i in range(0, len(prod_list), 200):
            batch = prod_list[i:i+200]
            precs = json_execute(sess, 'product.product', 'read', [batch, ['id', 'categ_id']])
            if precs:
                for pr in precs:
                    cat = pr.get('categ_id')
                    prod_categ[pr['id']] = cat[1] if isinstance(cat, list) and len(cat) > 1 else 'General'
    
    # 5. Construir datos — TODAS las órdenes se muestran y se suman
    facturas = []
    ejecutivos = {}
    productos = {}
    equipos = {}
    categorias = {}
    total_facturado = 0.0
    total_admin = 0.0
    total_admin_total = 0.0
    total_costo = 0.0
    colaboradores = []
    clientes_set = set()
    
    for so in ordenes:
        so_id = so['id']
        inv_name = so.get('name', '')
        partner = so.get('partner_id')
        partner_name = partner[1] if isinstance(partner, list) and len(partner) > 1 else 'Desconocido'
        fecha = str(so.get('commitment_date') or '')[:10]
        
        uid = so.get('user_id')
        ej_name = uid[1] if isinstance(uid, list) and len(uid) > 1 else 'Sin asignar'
        
        team = so.get('team_id')
        team_name = team[1] if isinstance(team, list) and len(team) > 1 else 'Sin equipo'
        
        raw_st = so.get('x_status_operativos')
        st_str = str(raw_st) if raw_st is not None else ''
        raw_cp = so.get('x_status_compra')
        cp_str = str(raw_cp) if raw_cp is not None else ''
        
        total = float(so.get('amount_total') or 0)
        clientes_set.add(partner_name)
        total_facturado += total
        
        lineas_orden = lineas_por_orden.get(so_id, [])
        gasto_admin = 0.0
        gasto_admin_total = 0.0
        costo_producto = 0.0
        es_colaborador = False
        pct_dscto = 0
        lineas_detalle = []
        
        for lr in lineas_orden:
            pid = lr.get('product_id')
            pname = pid[1] if isinstance(pid, list) and len(pid) > 1 else 'Producto'
            pu = float(lr.get('price_subtotal') or 0)   # precio con descuento (real)
            pu_unit = float(lr.get('price_unit') or 0)
            qty = float(lr.get('product_uom_qty') or 1)
            cost_unit = float(lr.get('purchase_price') or 0)
            dsc = float(lr.get('discount') or 0)
            
            cat_name = prod_categ.get(pid[0], 'General') if pid and isinstance(pid, list) and len(pid) > 1 else 'General'
            
            is_admin = 'gasto administrativo' in pname.lower() or 'gestion de cobranza' in pname.lower()
            
            if is_admin:
                gasto_admin += pu
                gasto_admin_total += pu_unit * qty
                total_admin += pu
                total_admin_total += pu_unit * qty
                if dsc > 0:
                    es_colaborador = True
                    pct_dscto = dsc
            else:
                costo_linea = cost_unit * qty
                costo_producto += costo_linea
                total_costo += costo_linea
                
                if pname not in productos:
                    productos[pname] = {'qty': 0, 'subtotal': 0.0, 'veces': 0, 'categoria': cat_name}
                productos[pname]['qty'] += qty
                productos[pname]['subtotal'] += pu
                productos[pname]['veces'] += 1
            
            if team_name not in equipos:
                equipos[team_name] = {'cantidad': 0, 'total_suma': 0.0, 'lineas_count': 0}
            equipos[team_name]['lineas_count'] += 1
            equipos[team_name]['cantidad'] += qty
            equipos[team_name]['total_suma'] += pu
            
            if cat_name not in categorias:
                categorias[cat_name] = {'cantidad': 0, 'total_suma': 0.0, 'lineas_count': 0}
            categorias[cat_name]['lineas_count'] += 1
            categorias[cat_name]['cantidad'] += qty
            categorias[cat_name]['total_suma'] += pu
            
            lineas_detalle.append({
                'producto': pname,
                'tipo': 'GASTO ADMIN' if is_admin else 'PRODUCTO',
                'cantidad': qty,
                'subtotal': round(pu, 2),
                'categoria': cat_name,
                'equipo': team_name,
                'price_unit': round(pu_unit, 2),
                'discount': round(dsc, 2) if dsc > 0 else (round(((pu_unit * qty - pu) / (pu_unit * qty) * 100), 2) if pu_unit > 0 and pu < pu_unit * qty else 0.0),
            })
        
        facturas.append({
            'cliente': partner_name,
            'factura': inv_name,
            'fecha': fecha,
            'ejecutivo': ej_name,
            'status': ST_LABELS.get(st_str, st_str),
            'compra_status': CP_LABELS.get(cp_str, cp_str),
            'total': round(total, 2),
            'precio_producto': round(total - gasto_admin, 2),
            'gasto_admin': round(gasto_admin, 2),
            'costo': round(costo_producto, 2),
            'margen': round((total - gasto_admin) - costo_producto, 2),
            'lineas': lineas_detalle,
        })
        
        if es_colaborador:
            colaboradores.append({
                'factura': inv_name,
                'cliente': partner_name,
                'gasto_admin_total': round(gasto_admin_total, 2),
                'gasto_admin': round(gasto_admin, 2),
                'descuento': round(pct_dscto, 0),
            })
        
        if ej_name not in ejecutivos:
            ejecutivos[ej_name] = {'cantidad': 0, 'total': 0.0, 'facturas': []}
        ejecutivos[ej_name]['cantidad'] += 1
        ejecutivos[ej_name]['total'] += total
        ejecutivos[ej_name]['facturas'].append({
            'name': inv_name,
            'cliente': partner_name,
            'total': round(total, 2),
            'status': ST_LABELS.get(st_str, st_str),
            'compra_status': CP_LABELS.get(cp_str, cp_str),
        })
    
    facturas.sort(key=lambda x: -x['total'])
    colaboradores.sort(key=lambda x: x['factura'])
    
    cancelaciones = [f for f in facturas if f['status'] == 'Cancelación Total']
    
    ej_list = [
        {'nombre': k, 'cantidad': v['cantidad'],
         'total': round(v['total'], 2), 'facturas': v['facturas']}
        for k, v in sorted(ejecutivos.items(), key=lambda x: -x[1]['total'])
    ]
    
    top_prod = sorted(productos.items(), key=lambda x: -x[1]['subtotal'])
    prod_list = [
        {'nombre': k, 'qty': v['qty'], 'subtotal': round(v['subtotal'], 2),
         'veces': v['veces'], 'categoria': v['categoria'], 'lineas': []}
        for k, v in top_prod
    ]
    
    # Equipos ordenados
    eq_list = [
        {'nombre': k, 'lineas': v['lineas_count'], 'total_suma': round(v['total_suma'], 2)}
        for k, v in sorted(equipos.items(), key=lambda x: -x[1]['total_suma'])
    ]
    
    # Categorias ordenadas
    cat_list = [
        {'nombre': k, 'lineas': v['lineas_count'], 'total_suma': round(v['total_suma'], 2)}
        for k, v in sorted(categorias.items(), key=lambda x: -x[1]['total_suma'])
    ]
    
    return {
        'facturas': facturas,
        'ejecutivos': ej_list,
        'top_productos': prod_list,
        'equipos': eq_list,
        'categorias': cat_list,
        'total_facturado': round(total_facturado, 2),
        'total_facturas': len(facturas),
        'total_clientes': len(clientes_set),
        'total_admin': round(total_admin, 2),
        'total_admin_total': round(total_admin_total, 2),
        'total_costo': round(total_costo, 2),
        'total_margen': round(total_facturado - total_admin - total_costo, 2),
        'total_productos': round(total_facturado - total_admin, 2),
        'colaboradores': colaboradores,
        'cancelaciones_count': len(cancelaciones),
        'cancelaciones_monto': round(sum(f['total'] for f in cancelaciones), 2),
    }

# ── Análisis Operativo Agosto 2026 (Google Sheets) ──────────────────────────
def fetch_agosto_operativo():
    """Descarga y procesa tareas de agosto 2026 desde Google Sheets (CSV).
    Genera estadísticas de desempeño: % completadas, por prioridad, por estado."""
    import csv as _csv
    import io
    try:
        import urllib.request
        url = 'https://docs.google.com/spreadsheets/d/14YvQPXEqqqnioc5chfAxWqpGe8jnXneYnHq82Vs2iR4/export?format=csv&gid=1881944744'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read().decode('utf-8-sig')
        reader = _csv.DictReader(io.StringIO(raw))
        rows = list(reader)
    except Exception as e:
        print(f'Error descargando Google Sheets agosto operativo: {e}', file=sys.stderr)
        return {'tareas': [], 'resumen': {}, 'por_prioridad': {}, 'por_estado': {}, 'total': 0}

    if not rows:
        return {'tareas': [], 'resumen': {}, 'por_prioridad': {}, 'por_estado': {}, 'total': 0}

    total = len(rows)
    completadas = 0
    en_curso = 0
    bloqueadas = 0
    no_iniciadas = 0
    por_prioridad = {}
    por_estado = {}
    tareas = []

    for r in rows:
        tarea = r.get('Tarea', '').strip()
        prioridad = r.get('Prioridad', '').strip()
        estado = r.get('Estado', '').strip()
        propietario = r.get('Propietario', '').strip()
        fecha_inicio = r.get('Fecha de inicio', '').strip()
        fecha_fin = r.get('Fecha de finalización', '').strip()
        notas = r.get('Notas', '').strip()
        en_curso_pct = r.get('% en curso', '').strip().replace('%', '')
        hito = r.get('Hito', '').strip()
        distribuible = r.get('Distribuible', '').strip()

        # Parse % en curso
        try:
            pct = float(en_curso_pct) if en_curso_pct else 0
        except:
            pct = 0

        # Clasificar estado
        estado_lower = estado.lower()
        if 'completada' in estado_lower:
            completadas += 1
        elif 'en curso' in estado_lower:
            en_curso += 1
        elif 'bloqueada' in estado_lower:
            bloqueadas += 1
        elif 'no iniciada' in estado_lower:
            no_iniciadas += 1

        # Contar por prioridad
        if prioridad:
            if prioridad not in por_prioridad:
                por_prioridad[prioridad] = {'total': 0, 'completadas': 0, 'en_curso': 0, 'bloqueadas': 0, 'no_iniciadas': 0}
            por_prioridad[prioridad]['total'] += 1
            if 'completada' in estado_lower:
                por_prioridad[prioridad]['completadas'] += 1
            elif 'en curso' in estado_lower:
                por_prioridad[prioridad]['en_curso'] += 1
            elif 'bloqueada' in estado_lower:
                por_prioridad[prioridad]['bloqueadas'] += 1
            elif 'no iniciada' in estado_lower:
                por_prioridad[prioridad]['no_iniciadas'] += 1

        # Contar por estado
        if estado:
            por_estado[estado] = por_estado.get(estado, 0) + 1

        tareas.append({
            'tarea': tarea,
            'prioridad': prioridad,
            'propietario': propietario,
            'estado': estado,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'notas': notas,
            'pct': pct,
            'hito': hito,
            'distribuible': distribuible,
        })

    # Calcular porcentajes de desempeño
    resumen = {
        'total': total,
        'completadas': completadas,
        'en_curso': en_curso,
        'bloqueadas': bloqueadas,
        'no_iniciadas': no_iniciadas,
        'pct_completadas': round(completadas / total * 100, 1) if total else 0,
        'pct_en_curso': round(en_curso / total * 100, 1) if total else 0,
        'pct_bloqueadas': round(bloqueadas / total * 100, 1) if total else 0,
        'pct_no_iniciadas': round(no_iniciadas / total * 100, 1) if total else 0,
    }

    # Agregar % a por_prioridad
    for pri in por_prioridad:
        p = por_prioridad[pri]
        p['pct_completadas'] = round(p['completadas'] / p['total'] * 100, 1) if p['total'] else 0

    return {
        'tareas': tareas,
        'resumen': resumen,
        'por_prioridad': por_prioridad,
        'por_estado': por_estado,
        'total': total,
    }

def build_html(data):
    script_path = os.path.join(os.path.dirname(__file__), 'generar_html.py')
    with open(script_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    start = source.find("html = f'''")
    if start < 0:
        raise Exception('No se encontró la plantilla HTML')
    
    prefix = source[start:start+11]
    rest = source[start+len(prefix):]
    end = rest.find("'''")
    if end < 0:
        raise Exception('No se encontró el cierre de la plantilla')
    tpl = rest[:end]
    
    json_str = json.dumps(data, ensure_ascii=False)
    json_escaped = json_str.replace('\\', '\\\\').replace("'", "\\'")
    
    # Primero desescapar {{ y }} del template (f-string literal braces)
    tpl_unescaped = tpl.replace('{{', '{').replace('}}', '}')
    # Luego insertar el JSON (para que no se dañe si contiene }} o {{)
    html = tpl_unescaped.replace('{json_escaped}', json_escaped)
    return html

# ── Cache ────────────────────────────────────────────────────────
DATA_CACHE = None
HTML_CACHE = None

def get_dashboard():
    global DATA_CACHE, HTML_CACHE
    try:
        data = fetch_data()
        DATA_CACHE = data
        HTML_CACHE = build_html(data)
        return HTML_CACHE
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        if HTML_CACHE:
            print('Sirviendo cache anterior...', file=sys.stderr)
            return HTML_CACHE
        raise

# ── Servidor HTTP ────────────────────────────────────────────────
class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            try:
                html = get_dashboard()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            except Exception as e:
                self.send_error(500, f'Error: {e}')
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        print(f'[{self.address_string()}] {format % args}', file=sys.stderr)

if __name__ == '__main__':
    # Modo --generate: solo genera index.html y sale (para GitHub Actions)
    if '--generate' in sys.argv:
        OUTPUT = os.path.join(os.path.dirname(__file__), 'index.html')
        print(f'Generando {OUTPUT}...')
        try:
            data = fetch_data()
            html = build_html(data)
            with open(OUTPUT, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f'OK - {data["client_count"]} clientes, '
                  f'{sum(data["status_counts"].values())} facturas emitidas')
            print(f'Escrito: {OUTPUT} ({os.path.getsize(OUTPUT)} bytes)')
        except Exception as e:
            print(f'ERROR: {e}')
            sys.exit(1)
        sys.exit(0)
    
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    print('='*55)
    print('  LATINBIEN - Dashboard en Tiempo Real')
    print('  Conectado directo a Odoo 16')
    print('='*55)
    print()
    print('  Cargando datos desde Odoo...')
    try:
        data = fetch_data()
        DATA_CACHE = data
        HTML_CACHE = build_html(data)
        print(f'  OK - {data["client_count"]} clientes, '
              f'{sum(data["status_counts"].values())} facturas emitidas')
    except Exception as e:
        print(f'  ERROR: {e}')
        sys.exit(1)
    
    print()
    print(f'  Abre esta URL en tu navegador:')
    print(f'  http://localhost:{PORT}/')
    print()
    print('  Los datos vienen DIRECTAMENTE desde latinbien.com')
    print('  Cada visita obtiene los datos mas recientes.')
    print('  Presiona Ctrl+C para detener.')
    print()
    
    server = HTTPServer(('0.0.0.0', PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Servidor detenido.')
        server.server_close()