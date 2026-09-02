# -*- coding: utf-8 -*-
# Dump completo bots cobranza rotos + logs recientes conector 17
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

print('=== CODIGO COMPLETO BOTS COBRANZA ROTOS ===')
for bid in [40, 41, 45, 34, 46]:
    bots = call('acrux.chat.bot', 'search_read', [[('id', '=', bid)]],
                {'fields': ['id', 'name', 'bot_key', 'text_match', 'code', 'body_whatsapp', 'child_ids']})
    if not bots: continue
    b = bots[0]
    print('='*80)
    print(f"BOT {b['id']} | {b['name']} | key={b.get('bot_key')} | tm={b.get('text_match')} | childs={len(b.get('child_ids') or [])}")
    print("--- body_whatsapp ---")
    print(repr(b.get('body_whatsapp') or ''))
    print("--- code ---")
    print(b.get('code') or '(empty)')
    print()

# 2. Conversaciones del conector 17 con actividad reciente
cons = call('acrux.chat.conversation', 'search_read', [[('connector_id', '=', 17)]],
            {'fields': ['id', 'name', 'number', 'status', 'create_date', 'last_message_date'],
             'order': 'create_date desc', 'limit': 12})
print('=== CONVERSACIONES CONECTOR 17 ===')
for c in cons:
    print(f"  conv {c['id']} | {c['name']} | status={c.get('status')} | last={c.get('last_message_date')}")

# 3. Logs de bot recientes del conector 17
print('\n=== LOGS DE BOT RECIENTES (conector 17) ===')
logs = call('acrux.chat.bot.log', 'search_read', [[]],
            {'fields': ['id', 'text', 'bot_log', 'conversation_id', 'create_date'],
             'order': 'create_date desc', 'limit': 15})
for l in logs:
    conv_id = l.get('conversation_id')
    conv_label = conv_id[1] if isinstance(conv_id, list) and conv_id else conv_id
    is_err = 'error' in str(l.get('bot_log')).lower()
    prefix = '❌' if is_err else '  '
    print(f"{prefix}[{l['create_date']}] conv={conv_label} msg={str(l.get('text'))[:40]}")
    print(f"   {str(l.get('bot_log'))[:350]}")
