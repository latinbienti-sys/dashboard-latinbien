import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Get ALL recent logs
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'search_read',
        'args': [],
        'kwargs': {'fields': ['id', 'bot_log', 'connector_id', 'create_date'],
            'domain': [['id', '>', 25761]],
            'limit': 20, 'order': 'id asc'}
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    if records:
        print(f'Found {len(records)} new logs since ID 25761:')
        for log in records:
            lid = log['id']
            conn = log.get('connector_id')
            if isinstance(conn, (list, tuple)):
                conn = f'{conn[0]}-{conn[1]}' if conn else 'None'
            dt = log.get('create_date', '')
            logtxt = str(log.get('bot_log', ''))[:150]
            print(f'  Log {lid} | Conn={conn} | {dt}')
            print(f'    {logtxt}')
            print()
    else:
        print('No new logs since ID 25761')
else:
    print('Error:', r.get('error', {}).get('message', 'unknown'))
