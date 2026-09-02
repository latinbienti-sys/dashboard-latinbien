from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Read oldest error log
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'read',
        'args': [[25706]],
        'kwargs': {'fields': ['id', 'bot_log', 'text', 'conversation_id', 'create_date']}
    }
})
r = resp.json()
if 'result' in r:
    log = r['result'][0]
    print(f'Log 25706:')
    print(f'  Date: {log.get("create_date")}')
    print(f'  Text: {str(log.get("text", ""))[:100]}')
    print(f'  Conversation: {log.get("conversation_id")}')
    print(f'  Full bot_log:')
    print(str(log.get("bot_log", "")))
print()

# Also read error 25755 (right before the first one I saw)
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'read',
        'args': [[25755]],
        'kwargs': {'fields': ['id', 'bot_log', 'text', 'create_date']}
    }
})
r2 = resp2.json()
if 'result' in r2:
    log2 = r2['result'][0]
    print(f'Log 25755:')
    print(f'  Date: {log2.get("create_date")}')
    print(f'  Text: {str(log2.get("text", ""))[:100]}')
    print(f'  bot_log:')
    print(str(log2.get("bot_log", "")))
