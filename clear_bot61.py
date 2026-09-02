import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)
s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':'erp_production','login':'latinbienti@latinbien.com','password':'z+cakaSe2805*'}})

# Make bot 61 empty like cobranza catcher (bot 34)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[61], {'code': '\n  '}], 'kwargs': {}
    }
})
if resp.json().get('result'):
    print("✅ Bot 61: código borrado (igual que catcher cobranza)")
else:
    print("❌ Error")

# Now check: bot 62 has no text_match, so it should handle ALL messages
# If user writes "hola", bot 62 should say "Disculpa, no entendi..."
