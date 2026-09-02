# -*- coding: utf-8 -*-
from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

API = 'https://latinbien.com/web/dataset/call_kw'
def call(model, method, args, kwargs=None):
    resp = s.post(f'{API}/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}
    })
    return resp.json().get('result')

# Conversaciones del conector 17 en status current/new (activas)
cons = call('acrux.chat.conversation', 'search_read', [[('connector_id', '=', 17)]],
            {'fields': ['id', 'name', 'status', 'create_date'], 'order': 'create_date desc', 'limit': 30})
print('=== CONVERSACIONES COBRANZA (status actual) ===')
for c in cons or []:
    print(f"  conv {c['id']} | {c['name'][:30]} | status={c.get('status')}")

# Actividades bot_thread de esas conversaciones
conv_ids = [c['id'] for c in (cons or [])]
acts = call('acrux.chat.conversation.activities', 'search_read', [[('conversation_id', 'in', conv_ids)]],
            {'fields': ['id', 'conversation_id', 'ttype', 'rec_id', 'create_date'], 'order': 'create_date desc', 'limit': 60})
print('\n=== ACTIVIDADES bot_thread COBRANZA ===')
bot_names = {b['id']: b['name'] for b in (call('acrux.chat.bot', 'search_read', [[]], {'fields': ['id', 'name']}) or [])}
for a in acts or []:
    if a.get('ttype') in ('bot_thread', 'bot_mute'):
        conv = a.get('conversation_id')
        conv_l = conv[1] if isinstance(conv, list) and conv else conv
        rec = a.get('rec_id')
        bot_l = bot_names.get(rec, rec)
        print(f"  act {a['id']} | conv={conv_l} | {a.get('ttype')} | rec={bot_l} | {a.get('create_date')}")
