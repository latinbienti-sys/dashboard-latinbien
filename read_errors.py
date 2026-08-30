import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read full bot.log details for error records
error_ids = [25761, 25760, 25758, 25757]
for eid in error_ids:
    resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot.log', 'method': 'read',
            'args': [[eid]],
            'kwargs': {'fields': ['id', 'bot_log', 'text', 'create_date']}
        }
    })
    r = resp.json()
    if 'result' in r:
        log = r['result'][0]
        print(f'=== Log {eid} ===')
        print(f'  Date: {log.get("create_date")}')
        print(f'  Text: {str(log.get("text", ""))[:100]}')
        bot_log = str(log.get("bot_log", ""))
        print(f'  Bot Log:')
        print(bot_log)
        print()
    else:
        print(f'Error reading log {eid}:', r.get('error', {}).get('message', 'unknown'))
