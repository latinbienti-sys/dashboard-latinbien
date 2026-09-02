import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read a specific bot.log record
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'read',
        'args': [[25765]],
        'kwargs': {'fields': ['id', 'bot_log', 'text', 'conversation_id', 'create_date']}
    }
})
r = resp.json()
if 'result' in r:
    log = r['result'][0]
    print(f'Bot Log 25765:')
    print(f'  text: {str(log.get("text", ""))[:200]}')
    print(f'  bot_log: {str(log.get("bot_log", ""))[:300]}')
    print(f'  conversation_id: {log.get("conversation_id")}')
    print(f'  create_date: {log.get("create_date")}')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown')[:300])

print()

# Try reading the last 5 log entries to see if there are cobranza errors
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'bot_log', 'connector_id', 'create_date'],
            'domain': [],
            'limit': 10,
            'order': 'id desc'
        }
    }
})
r2 = resp2.json()
if 'result' in r2:
    records = r2['result']
    if isinstance(records, dict):
        records = records.get('records', [])
    for log in records:
        conn = log.get('connector_id')
        conn_name = conn[1] if conn else 'N/A'
        log_text = str(log.get('bot_log', ''))[:100]
        print(f'  Log {log["id"]}: connector={conn_name} | {log_text}')
else:
    print('Error:', r2.get('error', {}).get('message', 'unknown'))
