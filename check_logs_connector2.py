import requests, json, sys, datetime
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# Check recent logs for connector 2 (commercial) - errors only
today = datetime.date.today().isoformat()
print(f"=== Errors today ({today}) for connector 2 ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.logging/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'ir.logging','method':'search_read',
        'args':[[
            ('create_date', '>=', today),
            ('level', 'in', ['ERROR', 'CRITICAL', 'WARNING']),
            '|',
                ('name', 'ilike', '%bot%'),
                ('name', 'ilike', '%acrux%'),
        ]],
        'kwargs':{'fields':['name','level','message','create_date','type'],
            'order':'create_date desc',
            'limit':30}
    }
})
results = resp.json().get('result', [])
if results:
    for r in results:
        print(f"[{r['create_date'][:19]}] {r['level']}: {r['name'][:50]}")
        print(f"  {r['message'][:200]}")
        print()
else:
    print("No errors found")
    
# Also check for any recent messages on connector 2
print(f"\n=== Recent messages on connector 2 ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.message/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.message','method':'search_read',
        'args':[[
            ('create_date', '>=', today),
            ('connector_id', '=', 2),
        ]],
        'kwargs':{'fields':['id','text','create_date','from_me','conversation_id'],
            'order':'create_date desc',
            'limit':20}
    }
})
messages = resp.json().get('result', [])
if messages:
    for m in messages:
        conv = m.get('conversation_id')
        conv_name = f"conv_{conv[0]}" if conv else "?"
        direction = "ENVIADO" if m.get('from_me') else "RECIBIDO"
        print(f"[{m['create_date'][:19]}] {direction} {conv_name}: {str(m.get('text',''))[:100]}")
else:
    print("No messages found on connector 2 today")
