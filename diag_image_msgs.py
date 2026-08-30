# -*- coding: utf-8 -*-
# Diagnostico: como llegan imagenes/PDF al conector comercial (2) y que bot los procesa
import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
API = 'https://latinbien.com/web/dataset/call_kw'
def call(model, method, args, kwargs=None):
    resp = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    return resp.json().get('result')

# 1) Campos de message - ver ttype y su selection
print('=== 1) fields_get acrux.chat.message (ttype selection) ===')
fields = call('acrux.chat.message', 'fields_get', [], {'attributes': ['type', 'string', 'selection']})
if fields:
    for f in ['ttype', 'text', 'attachment_ids', 'attachments', 'message_type', 'message', 'from_me', 'contact_id', 'conversation_id', 'connector_id']:
        if f in fields:
            sel = fields[f].get('selection')
            print(f'  {f}: type={fields[f].get("type")} string={fields[f].get("string")}')
            if sel:
                print(f'    selection={sel}')
        else:
            print(f'  {f}: NO EXISTE')

# 2) Ultimos mensajes del conector 2 (comercial) - buscar no-texto
print('\n=== 2) Ultimos mensajes del conector 2 (comercial) no-texto ===')
msgs = call('acrux.chat.message', 'search_read', [[('connector_id', '=', 2)]], {
    'fields': ['id', 'text', 'ttype', 'from_me', 'create_date', 'contact_id', 'conversation_id', 'attachment_ids'],
    'order': 'create_date desc', 'limit': 30})
if msgs:
    for m in msgs:
        ttype = m.get('ttype')
        txt = str(m.get('text') or '')[:100]
        fromme = m.get('from_me')
        atch = m.get('attachment_ids') or []
        if ttype != 'text' or atch or fromme is False and not txt.strip():
            print(f"  [{m.get('create_date','')[:19]}] id={m['id']} ttype={ttype} from_me={fromme} attach={len(atch) if atch else 0}")
            print(f"      text={txt!r}")
    # resumen conteo por ttype
    print('\n  Conteo por ttype en ultimos 30:')
    from collections import Counter
    cnt = Counter((m.get('ttype') or 'text') for m in msgs)
    for t, c in cnt.items():
        print(f'    {t}: {c}')
else:
    print('  (sin resultados)')

# 3) Buscar TODOS los mensajes con attachment en las ultimas semanas, conn 2
print('\n=== 3) Mensajes conn 2 con adjuntos (imagen/pdf) ultimos 7 dias ===')
import datetime
since = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
att = call('acrux.chat.message', 'search_read', [[('connector_id', '=', 2), ('create_date', '>=', since), ('attachment_ids', '!=', False)]], {
    'fields': ['id', 'text', 'ttype', 'from_me', 'create_date', 'conversation_id', 'attachment_ids'],
    'order': 'create_date desc', 'limit': 20})
if att:
    for m in att:
        conv = m.get('conversation_id')
        print(f"  id={m['id']} [{m.get('create_date','')[:19]}] ttype={m.get('ttype')} from_me={m.get('from_me')} conv={conv[0] if conv else '?'}")
        print(f"      text={str(m.get('text') or '')[:120]!r} attach={len(m.get('attachment_ids') or [])}")
else:
    print('  (sin mensajes con adjuntos)')

# 4) Bot log recientes conn 2 - que bot responde a esos mensajes
print('\n=== 4) Ultimos bot.log conn 2 ===')
logs = call('acrux.chat.bot.log', 'search_read', [[('connector_id', '=', 2)]], {
    'fields': ['id', 'bot_log', 'create_date'],
    'order': 'id desc', 'limit': 15})
if logs:
    for lg in logs:
        print(f"  Log {lg['id']} [{lg.get('create_date','')[:19]}]")
        print(f"    {str(lg.get('bot_log') or '')[:250]}")
else:
    print('  (sin logs)')
