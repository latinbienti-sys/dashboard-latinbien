# -*- coding: utf-8 -*-
# Diagnostico global: logs conector 17 + TODOS los bots con conversation_id/active_bot_id
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

# Conversaciones del conector 17 (campos validos)
cons = call('acrux.chat.conversation', 'search_read', [[('connector_id', '=', 17)]],
            {'fields': ['id', 'name', 'number', 'status', 'create_date'],
             'order': 'create_date desc', 'limit': 15})
print('=== CONVERSACIONES CONECTOR 17 ===')
for c in cons or []:
    print(f"  conv {c['id']} | {c['name']} | status={c.get('status')} | created={c.get('create_date')}")

# Logs de bot recientes (buscar errores en cobranza)
print('\n=== LOGS DE BOT RECIENTES (ultimos 20) ===')
logs = call('acrux.chat.bot.log', 'search_read', [[]],
            {'fields': ['id', 'text', 'bot_log', 'conversation_id', 'create_date'],
             'order': 'create_date desc', 'limit': 20})
for l in logs or []:
    conv_id = l.get('conversation_id')
    conv_label = conv_id[1] if isinstance(conv_id, list) and conv_id else conv_id
    is_err = 'error' in str(l.get('bot_log')).lower()
    prefix = '❌' if is_err else '  '
    print(f"{prefix}[{l['create_date']}] conv={conv_label} msg={str(l.get('text'))[:45]}")
    print(f"   {str(l.get('bot_log'))[:300]}")

# TODOS los bots con conversation_id / active_bot_id
print('\n=== TODOS LOS BOTS CON conversation_id / active_bot_id ===')
bots = call('acrux.chat.bot', 'search_read', [[]],
            {'fields': ['id', 'name', 'connector_id', 'text_match', 'bot_key', 'code']})
for b in bots or []:
    code = b.get('code') or ''
    flags = []
    if 'conversation_id' in code: flags.append('conversation_id')
    if 'active_bot_id' in code: flags.append('active_bot_id')
    if flags:
        conn = b.get('connector_id')
        conn_label = conn[1] if isinstance(conn, list) and conn else conn
        print(f"  Bot {b['id']} | {b['name'][:45]} | conn={conn_label} | {'+'.join(flags)}")
