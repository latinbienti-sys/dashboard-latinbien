# -*- coding: utf-8 -*-
"""Explora opciones de seleccion y volumen por etiqueta financiera. SOLO LECTURA."""
import json, urllib.request, http.cookiejar, os

BASE = 'https://latinbienmotors.com'
DB = os.environ['ODOO_DB']
USER = os.environ['ODOO_USER']
PWD = os.environ['ODOO_PASSWORD']

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def rpc(url, method, params):
    payload = {'jsonrpc': '2.0', 'method': 'call', 'params': params, 'id': 1}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    return json.loads(opener.open(req, timeout=90).read().decode())

def call_kw(model, method, args=None, kwargs=None):
    res = rpc(BASE + '/web/dataset/call_kw', model,
              {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs or {}})
    if 'error' in res:
        raise RuntimeError(json.dumps(res['error'], ensure_ascii=False)[:1500])
    return res['result']

r = rpc(BASE + '/web/session/authenticate', 'call',
        {'db': DB, 'login': USER, 'password': PWD})
print('UID:', r['result'].get('uid'))

# Opciones de seleccion
print('\n== Opciones de seleccion ==')
for f in ['x_plazo', 'x_bancos_cuenta', 'x_payment', 'x_indentificador_rif', 'x_productos_de_credito', 'x_demostrable_ingreso', 'x_tipo_vivienda', 'x_inicial_disponible']:
    try:
        fd = call_kw('crm.lead', 'fields_get', [[f]], {'attributes': ['string', 'type', 'selection']})[f]
        print(f, '=>', fd.get('selection') or fd.get('type'))
    except Exception as e:
        print(f, 'ERR', e)

# Etiquetas financieras
FIN_TAGS = ['ARCA', 'PIVCA', 'BANESCO', 'PROVINCIAL', 'CREDITO BANCO PROVINCIAL', 'CREDITO BANESCO']
print('\n== Etiquetas financieras ==')
tags = call_kw('crm.tag', 'search_read', [[]], {'fields': ['id', 'name']})
tag_by_name = {t['name'].strip().upper(): t['id'] for t in tags}
for name in FIN_TAGS:
    print(name, '=> id', tag_by_name.get(name.upper()))

# Volumen por etiqueta clave
mensajes = []
for nombre, pid in tag_by_name.items():
    if pid and any(k in nombre for k in ['ARCA', 'PIVCA', 'BANESCO', 'PROVINCIAL']):
        cnt = len(call_kw('crm.lead', 'search', [[['tag_ids', 'in', [pid]]]]))
        print('Tag', pid, nombre, '=> leads:', cnt)
        mensajes.append((nombre, pid, cnt))

# Total de leads
total = len(call_kw('crm.lead', 'search', [[]]))
print('\nTotal leads en CRM:', total)

# Leads con esas etiquetas
ids = []
for nombre, pid, cnt in mensajes:
    ids += call_kw('crm.lead', 'search', [[['tag_ids', 'in', [pid]]]])
print('Leads unicos con etiquetas financieras:', len(set(ids)))