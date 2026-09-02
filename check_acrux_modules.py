from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Check installed acrux modules
resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.module.module/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'ir.module.module','method':'search_read',
        'args':[[('name','ilike','acrux')]],
        'kwargs':{'fields':['name','state','version'], 'limit':30}
    }
})
print("=== ACRUX MODULES ===")
for r in resp.json().get('result', []):
    print(f"  {r['name']}: state={r['state']} version={r.get('version','')}")

# Check all models in acrux.chat domain
resp = s.post('https://latinbien.com/web/dataset/call_kw/ir.model/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'ir.model','method':'search_read',
        'args':[[('model','ilike','acrux.chat')]],
        'kwargs':{'fields':['model','name'], 'limit':50}
    }
})
print("\n=== ACRUX CHAT MODELS ===")
for r in resp.json().get('result', []):
    print(f"  {r['model']}: {r['name']}")
