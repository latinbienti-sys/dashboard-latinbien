from odoo_conn import get_session

s = get_session()

from datetime import datetime, timedelta
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Get total log count for cobranza connector 17
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_count', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'search_count',
        'args': [],
        'kwargs': {'domain': [['connector_id', '=', 17]]}
    }
})
r = resp.json()
total = r.get('result', 0)
print(f'Total logs cobranza: {total}')
print()

# Get the 10 most recent logs (regardless of error/success)
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'search_read',
        'args': [],
        'kwargs': {'fields': ['id', 'bot_log', 'create_date'],
            'domain': [['connector_id', '=', 17]],
            'limit': 10,
            'order': 'id desc'}
    }
})
r2 = resp2.json()
if 'result' in r2:
    records = r2['result']
    if isinstance(records, dict): records = records.get('records', [])
    print(f'Most recent {len(records)} cobranza logs:')
    for log in records:
        lid = log['id']
        dt = log.get('create_date', '')
        logtxt = str(log.get('bot_log', ''))[:200]
        print(f'  Log {lid} | {dt} | {logtxt}')
    print()

# Get the latest 5 IDs for ALL connectors to see what's happening
resp3 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'search_read',
        'args': [],
        'kwargs': {'fields': ['id', 'connector_id', 'create_date'],
            'domain': [],
            'limit': 10,
            'order': 'id desc'}
    }
})
r3 = resp3.json()
if 'result' in r3:
    records3 = r3['result']
    if isinstance(records3, dict): records3 = records3.get('records', [])
    print('Latest 10 logs across ALL connectors:')
    for log in records3:
        lid = log['id']
        conn = log.get('connector_id')
        if isinstance(conn, (list, tuple)):
            conn = f'{conn[0]}-{conn[1]}' if conn else 'None'
        dt = log.get('create_date', '')
        print(f'  Log {lid} | Conn={conn} | {dt}')
