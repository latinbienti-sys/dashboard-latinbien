from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'search_read',
        'args': [],
        'kwargs': {
            'fields': ['id', 'bot_log', 'create_date'],
            'domain': [['connector_id', '=', 17]],
            'limit': 3,
            'order': 'id desc'
        }
    }
})
r = resp.json()
if 'result' in r:
    records = r['result']
    if isinstance(records, dict): records = records.get('records', [])
    for log in records:
        lid = log['id']
        print(f'Log {lid} ({log.get("create_date")}):')
        print(str(log.get('bot_log', ''))[:500])
        print()
else:
    print('Error:', r.get('error', {}).get('message', 'unknown'))
