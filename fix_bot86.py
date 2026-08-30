import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read bot 86
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[86]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
bot = resp.json()['result'][0]
code = bot['code']

print(f"Bot 86: {bot['name']}")
print(f"Code length: {len(code)}")

# Find all ret = [ patterns
for i, line in enumerate(code.split('\n')):
    if 'ret = [{' in line:
        print(f'L{i+1}: {repr(line[:120])}')
    if 'ret = env' in line:
        print(f'L{i+1}: {repr(line[:120])}')

# The two remaining f-string patterns need to be replaced
# Pattern 1: ret = [{'send_text': f"\ud83d\uded1 No encontr\u00e9...}]
# Pattern 2: ret = [{'send_text': f"\ud83d\uded1 *Error al validar...}]
