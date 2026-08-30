import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})

# 1) Find recent conversations on cobranza connector (17) and commercial (2)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[('connector_id','=',17)]],
        'kwargs':{'fields':['id','number','status','write_date','last_message_date'],
            'order':'write_date desc','limit':6}
    }
})
print("=== COBRANZA (conn 17) conversations ===")
for r in resp.json().get('result', []):
    print(f"  ID {r['id']}: {r['number']} status={r['status']} write={str(r.get('write_date',''))[:19]}")

resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.conversation/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.conversation','method':'search_read',
        'args':[[('connector_id','=',2)]],
        'kwargs':{'fields':['id','number','status','write_date','last_message_date'],
            'order':'write_date desc','limit':6}
    }
})
print("\n=== COMERCIAL (conn 2) conversations ===")
for r in resp.json().get('result', []):
    print(f"  ID {r['id']}: {r['number']} status={r['status']} write={str(r.get('write_date',''))[:19]}")
