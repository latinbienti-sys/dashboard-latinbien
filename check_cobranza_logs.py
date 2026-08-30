import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read all successful cobranza logs
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'bot_log', 'connector_id'],
            'domain': [['connector_id', '=', 17]],
            'limit': 50,
            'order': 'id desc'
        }
    }
})
r = resp.json()
if 'result' not in r:
    print('Error:', r.get('error', {}).get('message', 'unknown'))
    exit()

records = r['result']
if isinstance(records, dict):
    records = records.get('records', [])

print(f'=== Last {len(records)} cobranza logs ===')
has_ok = False
for log in records:
    logtxt = str(log.get('bot_log', ''))
    logid = log['id']
    if 'BOT error' in logtxt:
        print(f'  ERROR Log {logid}: crash in bot processing')
    elif 'Order' in logtxt:
        print(f'  OK    Log {logid}: {logtxt[:200]}')
        has_ok = True
    elif logtxt.strip():
        print(f'  OTHER Log {logid}: {logtxt[:200]}')
    else:
        print(f'  EMPTY Log {logid}')

if not has_ok:
    print()
    print('NO SUCCESSFUL logs found for cobranza!')
    print('ALL cobranza logs show errors or are empty.')
