from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Check all children of bot 61 with their text_match
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[('parent_id', '=', 61)]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'sequence', 'code']}
    }
})
print("Children of Bot 61:")
print(f"{'ID':>4} {'Name':<50} {'text_match':<25} {'Seq':<6} {'HasCode':<8}")
print("="*100)
for b in resp.json().get('result', []):
    tm = str(b.get('text_match','') or '(empty)')[:25]
    seq = str(b.get('sequence','') or '0')
    hascode = 'YES' if b.get('code','').strip() else 'NO'
    print(f"{b['id']:>4} {b['name'][:50]:<50} {tm:<25} {seq:<6} {hascode:<8}")

# Check bot 84 specifically
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[84]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'sequence', 'code']}
    }
})
b84 = resp2.json()['result'][0]
print(f"\nBot 84 details:")
print(f"  text_match = {repr(b84.get('text_match'))}")
print(f"  sequence = {b84.get('sequence')}")
print(f"  code = {repr(b84.get('code','')[:100])}")
