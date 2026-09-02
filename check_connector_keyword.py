from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Read ALL fields of connector 2
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.connector','method':'read',
        'args':[[2]],
        'kwargs':{'fields':['id','name','keyword','message','bot_log','thread_minutes','time_to_done',
                           'ca_status','active','sequence','source','connector_type',
                           'allowed_user_ids','team_id','company_id']}
    }
})
print("Connector 2 full data:")
for c in resp.json().get('result', []):
    for k,v in c.items():
        if isinstance(v, list) and len(v) > 1:
            print(f"  {k}: [{v[0]}, '{v[1]}']")
        elif isinstance(v, bool):
            print(f"  {k}: {v}")
        elif v:
            print(f"  {k}: {str(v)[:150]}")

# Also check if there's a 'keyword' or 'trigger' in the fields
print("\n\n=== Checking ALL connector fields ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.connector/fields_get', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.connector','method':'fields_get',
        'args':[[]],'kwargs':{'attributes':['string','type','help']}
    }
})
for fname, finfo in sorted(resp.json().get('result', {}).items()):
    if 'keyword' in fname.lower() or 'trigger' in fname.lower() or 'filter' in fname.lower() or 'domain' in fname.lower() or 'start' in fname.lower():
        print(f"  {fname}: {finfo.get('string','?')} ({finfo.get('type','?')}) - {finfo.get('help','')[:100]}")
