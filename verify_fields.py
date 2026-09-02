# -*- coding: utf-8 -*-
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

# Campos validos del modelo acrux.chat.message
resp = s.post(f'{API}/acrux.chat.message/fields_get', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.message', 'method': 'fields_get',
               'args': [], 'kwargs': {'attributes': ['type', 'string']}}
})
fields = resp.json().get('result', {})
print('=== CAMPOS VALIDOS acrux.chat.message ===')
for f in sorted(fields):
    print(f"  {f}: {fields[f].get('type')} - {fields[f].get('string')}")
print('contact_id valido:', 'contact_id' in fields)
print('conversation_id valido:', 'conversation_id' in fields)
print('connector_id valido:', 'connector_id' in fields)

# Bots cobranza restantes: revisar campos usados
print('\n=== REVISION BOTS COBRANZA RESTANTES (42,43,44,47,59,34,46) ===')
bots = call('acrux.chat.bot', 'search_read', [[('id', 'in', [42, 43, 44, 47, 59, 34, 46])]],
            {'fields': ['id', 'name', 'code', 'body_whatsapp', 'text_match']})
for b in (bots or []):
    code = b.get('code') or ''
    print(f"Bot {b['id']} ({b['name'][:40]}) tm={b.get('text_match')} code_len={len(code)} body_len={len(b.get('body_whatsapp') or '')}")
