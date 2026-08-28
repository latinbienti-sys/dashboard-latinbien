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
ODOO_USER = os.environ.get('ODOO_USER', 'latinbienti@latinbien.com')
ODOO_PASS = os.environ.get('ODOO_PASS', 'z+cakaSe2805*')

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
        'expedientes': expedientes,
        'ventas_motos': fetch_ventas_motos(sess),
        'pago_proveedor_moto': fetch_pagoProveedorMoto(sess),
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
        return {
            'grupos': grupos,
            'totales': total_general,
        }

    except Exception as e:
        print(f"Error al buscar expedientes: {e}")
        return {
            'grupos': [],
            'totales': {'usadas': 0, 'no_usadas': 0, 'caducados': 0,
                        'total_lineas': 0, 'total_monto': 0.0, 'monto': 0.0},
        }

# ── Pago Proveedor MOTO CITY PRO ─────────────────────────
def fetch_pagoProveedorMoto(sess):
    """Pago a proveedor MOTO CITY PRO: 40% inicial + 60% en 8 cuotas quincenales."""
    from datetime import date, timedelta
    moto_categ_ids = [174, 167]
    prod_ids = json_execute(sess, 'product.product', 'search', [
        [['categ_id', 'in', moto_categ_ids]]
    ])
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
    orders = json_execute(sess, 'sale.order', 'read', [
        list(order_ids), ['id', 'name', 'state', 'partner_id', 'date_order', 'order_line']
    ])
    posted = [o for o in orders if o.get('state') == 'sale']
    proveedor = 'MOTO CITY PRO, C.A.'
    items = []
    for o in posted:
        oid_id = o['id']
        date_order = str(o.get('date_order') or '')[:10]
        if not date_order:
            continue
        pid = o.get('partner_id')
        cliente = pid[1] if isinstance(pid, list) and len(pid) > 1 else 'Desconocido'
        partner_id = pid[0] if isinstance(pid, list) and len(pid) > 1 else 0
        all_lines_data = json_execute(sess, 'sale.order.line', 'read',
                                      [o.get('order_line', []), ['product_id', 'price_unit', 'price_subtotal', 'name']])
        precio_moto = 0
        modelo = ''
        for l in all_lines_data:
            pname = l.get('name', '')
            if 'Gasto Administrativo' not in pname and 'gasto' not in pname.lower():
                precio_moto = float(l.get('price_unit', 0) or 0)
                prod = l.get('product_id')
                modelo = prod[1] if isinstance(prod, list) and len(prod) > 1 else pname
        if precio_moto <= 0:
            continue
        inicial_40 = round(precio_moto * 0.40, 2)
        restante_60 = round(precio_moto * 0.60, 2)
        cuota_quincenal = round(restante_60 / 8, 2)
        ciclo_cliente = '03-18'
        if partner_id:
            try:
                inst_ids = json_execute(sess, 'account.move', 'search', [
                    [['partner_id', '=', partner_id], ['state', '=', 'posted'],
                     ['move_type', '=', 'out_invoice']]
                ])
                for iid in inst_ids[:3]:
                    moves = json_execute(sess, 'account.move.line', 'search_read', [
                        [['move_id', '=', iid]], ['payment_date']
                    ])
                    for m in moves:
                        pd = str(m.get('payment_date', ''))[:10]
                        if pd:
                            try:
                                dia = int(pd.split('-')[2])
                                if 10 <= dia <= 25:
                                    ciclo_cliente = '10-25'
                                    break
                            except:
                                pass
            except:
                pass
        fecha_inicio = date.fromisoformat(date_order)
        pagos = []
        for cuota_num in range(1, 9):
            if ciclo_cliente == '03-18':
                dia_pago = 5 if cuota_num % 2 == 1 else 20
            else:
                dia_pago = 12 if cuota_num % 2 == 1 else 27
            fecha_pago = fecha_inicio + timedelta(days=14 * (cuota_num - 1))
            try:
                fecha_pago = fecha_pago.replace(day=dia_pago)
            except:
                pass
            pagos.append({
                'cuota': cuota_num,
                'fecha_pago': str(fecha_pago)[:10],
                'monto': cuota_quincenal,
                'estado': 'pendiente',
            })
        items.append({
            'orden': o.get('name', ''),
            'orden_id': oid_id,
            'cliente': cliente,
            'modelo': modelo,
            'fecha_factura': date_order,
            'precio_moto': precio_moto,
            'inicial_40': inicial_40,
            'restante_60': restante_60,
            'cuota_quincenal': cuota_quincenal,
            'ciclo': ciclo_cliente,
            'opcion': 'A' if ciclo_cliente == '03-18' else 'B',
            'pagos': pagos,
            'proveedor': proveedor,
        })
    return {
        'items': items,
        'proveedor': proveedor,
        'orden_compra': 'P01382',
        'total_ordenes': len(items),
        'total_pagoInicial': round(sum(it['inicial_40'] for it in items), 2),
        'total_financiado': round(sum(it['restante_60'] for it in items), 2),
    }

# ── Plan de Pagos (Cuotas Fraccionadas) ──────────────────────────
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
    """Ventas de motos PUBLICADAS: precio producto + gasto admin separado."""
    moto_categ_ids = [174, 167]
    prod_ids = json_execute(sess, 'product.product', 'search', [
        [['categ_id', 'in', moto_categ_ids]]
    ])
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
    orders = json_execute(sess, 'sale.order', 'read', [
        list(order_ids), ['id', 'name', 'state', 'partner_id', 'date_order', 'order_line', 'amount_total']
    ])
    posted = [o for o in orders if o.get('state') == 'sale']
    items = []
    for o in posted:
        oid_id = o['id']
        date_order = str(o.get('date_order') or '')[:7]
        if not date_order:
            continue
        pid = o.get('partner_id')
        partner_id = pid[0] if isinstance(pid, list) and len(pid) > 1 else 0
        cliente = pid[1] if isinstance(pid, list) and len(pid) > 1 else 'Desconocido'
        credimoto = False
        if partner_id:
            try:
                p_data = json_execute(sess, 'res.partner', 'read', [partner_id], ['category_id'])
                if p_data:
                    tags = [t[1] for t in p_data[0].get('category_id', []) if isinstance(t, list)]
                    credimoto = any('CREDIMOTO' in t or 'CERDIMOTO' in t for t in tags)
            except:
                pass
        all_lines_data = json_execute(sess, 'sale.order.line', 'read',
                                      [o.get('order_line', []), ['product_id', 'price_unit', 'price_subtotal', 'name']])
        precio_producto = 0
        gasto_admin = 0
        modelo = ''
        for l in all_lines_data:
            pname = l.get('name', '')
            if 'Gasto Administrativo' in pname or 'gasto' in pname.lower():
                gasto_admin += float(l.get('price_subtotal', 0) or 0)
            else:
                precio_producto = float(l.get('price_unit', 0) or 0)
                prod = l.get('product_id')
                modelo = prod[1] if isinstance(prod, list) and len(prod) > 1 else pname
        items.append({
            'mes': date_order, 'modelo': modelo, 'cliente': cliente,
            'orden': o.get('name', ''), 'orden_id': oid_id, 'unidades': 1,
            'precio_producto': round(precio_producto, 2),
            'gasto_admin': round(gasto_admin, 2),
            'monto_total': round(float(o.get('amount_total', 0)), 2),
            'credimoto': credimoto,
        })
    return {
        'items': items,
        'total_ordenes': len(items),
        'total_motos': sum(it['unidades'] for it in items),
        'total_producto': round(sum(it['precio_producto'] for it in items), 2),
        'total_gasto_admin': round(sum(it['gasto_admin'] for it in items), 2),
        'total_monto': round(sum(it['monto_total'] for it in items), 2),
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