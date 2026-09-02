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

# Estado de la conversacion de prueba
conv = call('acrux.chat.conversation', 'search_read', [[('id', '=', 33152)]],
            {'fields': ['id', 'name', 'number', 'connector_id', 'status', 'res_partner_id', 'agent_id', 'create_date']})
print('=== CONVERSACION 33152 ===')
for c in conv:
    print(json.dumps(c, indent=1, ensure_ascii=False))

# Actividades de bot (thread) de la conversacion
acts = call('acrux.chat.conversation.activities', 'search_read', [[('conversation_id', '=', 33152)]],
            {'fields': ['id', 'ttype', 'rec_id', 'create_date']})
print('\n=== ACTIVIDADES BOT (thread) ===')
for a in acts:
    print(json.dumps(a, ensure_ascii=False))

# Ultimos mensajes de la conversacion
msgs = call('acrux.chat.message', 'search_read', [[('contact_id', '=', 33152)]],
            {'fields': ['id', 'text', 'ttype', 'from_me', 'create_date'], 'order': 'create_date desc', 'limit': 8})
print('\n=== ULTIMOS MENSAJES ===')
for m in sorted(msgs, key=lambda x: x['create_date']):
    who = 'BOT' if m['from_me'] else 'CLI'
    print(f"[{m['create_date']}] {who}: {str(m['text'])[:150]}")

# Logs de bot recientes (errores)
logs = call('acrux.chat.bot.log', 'search_read', [[('conversation_id', '=', 33152)]],
            {'fields': ['id', 'text', 'bot_log', 'create_date'], 'order': 'create_date desc', 'limit': 6})
print('\n=== LOGS DE BOT (ultimos 6) ===')
for l in sorted(logs, key=lambda x: x['create_date']):
    print(f"[{l['create_date']}] msg={str(l.get('text'))[:40]}")
    print(f"   {str(l.get('bot_log'))[:400]}")
