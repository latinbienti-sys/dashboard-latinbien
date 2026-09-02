import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Read bot 61 ACTUAL code
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[61]],
        'kwargs': {'fields': ['id', 'name', 'code']}
    }
})
b61 = resp.json()['result'][0]
code61 = b61['code']

print(f"Bot 61: {b61['name']}")
print(f"Code length: {len(code61)}")
print(f"\n--- Full code repr ---")
print(repr(code61))
print()

# Try to compile
try:
    compile(code61, '<string>', 'exec')
    print("✅ Compiles OK")
except SyntaxError as e:
    print(f"❌ SyntaxError L{e.lineno}: {e.msg}")

# Try to compile with safe_eval restrictions (just syntax check)
# Also check for runtime issues
print("\n--- Line by line ---")
for i, line in enumerate(code61.split('\n')):
    print(f"L{i+1}: {line[:120]}")

# Also read the actual server-side error possibilities
# Check if there's an issue with the unicode escapes
print("\n--- Checking unicode escapes ---")
test_str = b61['code']
# Check for problematic surrogate pairs
if '\\ud83d' in test_str or '\\ude0a' in test_str:
    print("Contains surrogate escapes (\\ud83d etc)")
    # Try building the string Python would build
    try:
        compiled = compile(code61, '<string>', 'exec')
        print("✅ Surrogates compile OK")
    except:
        print("❌ Surrogate issue")
