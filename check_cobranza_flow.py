from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Read cobranza NOT FOUND (bot 45) code - this WORKS in production
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'read','args':[[45]],'kwargs':{'fields':['id','name','code','text_match','sequence']}}
})
b45 = resp.json()['result'][0]
print(f"Bot 45: {b45['name']}")
print(f"text_match={b45.get('text_match')}, sequence={b45.get('sequence')}")
print(f"Code:")
print(b45.get('code',''))

# Also check bot 40 (PAGAR Y REPORTAR) - also works
print("\n" + "="*60)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'read','args':[[40]],'kwargs':{'fields':['id','name','code']}}
})
b40 = resp.json()['result'][0]
print(f"Bot 40: {b40['name']}")
print(f"Code:")
print(b40.get('code',''))

# Check bot 34 children with their text_match/sequence
print("\n" + "="*60)
print("Children of Bot 34 (cobranza):")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot','method':'search_read',
        'args':[[('parent_id', '=', 34)]],
        'kwargs':{'fields':['id','name','text_match','sequence']}
    }
})
for b in resp.json().get('result', []):
    tm = str(b.get('text_match','') or '(empty)')[:25]
    seq = str(b.get('sequence','') or '0')
    print(f"  Bot {b['id']:>3}: {b['name'][:45]:<45} text_match={tm:<25} seq={seq}")
