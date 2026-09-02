from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Read ALL bots' codes and look for phone numbers, asesor references
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[]],
        'kwargs': {'fields': ['id', 'name', 'connector_id', 'parent_id', 'code'],
            'order': 'id'}
    }
})
bots = resp.json().get('result', [])

# Search for phone numbers and "asesor" references
import re
print("=== Bots con números de teléfono ===")
for b in bots:
    code = b.get('code') or ''
    # Find phone numbers (Venezuelan format: 58412, 58414, 58424, etc.)
    phones = re.findall(r'584\d{7,9}', code)
    if phones:
        conn = b['connector_id'][0] if b['connector_id'] else 'GLOBAL'
        print(f"\nBot {b['id']:>3}: {b['name'][:50]:<50} connector={conn}")
        for p in set(phones):
            # Find context
            for line in code.split('\n'):
                if p in line:
                    print(f"    {line.strip()[:120]}")

print("\n\n=== Bots ASESOR (nombre contiene ASESOR) ===")
for b in bots:
    if 'ASESOR' in (b['name'] or '').upper():
        conn = b['connector_id'][0] if b['connector_id'] else 'GLOBAL'
        pid = b['parent_id'][0] if b['parent_id'] else 'root'
        print(f"  Bot {b['id']:>3}: {b['name'][:50]:<50} connector={conn:<7} parent={pid}")

# Check bot 44 and 47 (cobranza asesor) and 97-100 (comercial asesor)
print("\n\n=== Códigos de bots ASESOR ===")
for bid in [44, 47, 84, 97, 98, 99, 100]:
    resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': 'acrux.chat.bot', 'method': 'read',
            'args': [[bid]],
            'kwargs': {'fields': ['id', 'name', 'code']}
        }
    })
    if 'result' in resp2.json() and resp2.json()['result']:
        b = resp2.json()['result'][0]
        print(f"\n{'='*60}")
        print(f"Bot {bid}: {b['name']}")
        print(f"{'='*60}")
        print(b.get('code', '(empty)'))
