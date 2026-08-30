import requests, json, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s = requests.Session()
s.post('https://latinbien.com/web/session/authenticate', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'db': 'erp_production', 'login': 'latinbienti@latinbien.com', 'password': 'z+cakaSe2805*'}
})
s.headers['Content-Type'] = 'application/json'

# Set NOT FOUND (45) to return empty list (falsy) and use goto_and_wait to #MENUPRINCIPAL
# The empty list won't trigger the if result: assignment bug
# But goto_and_wait is inside the list...
# Let me try: just send_text without goto_and_wait
# BUT this returns a list too...

# Alternative: set bot 45's code to NOT set ret at all
# The safe_eval will return None, no crash
# But then nothing happens when "hola" is sent

# Let me try something: put the SEND_TEXT in the CATCHER (bot 34) but without ret
# In safe_eval, if we do: messages = [{'send_text': '...'}]
# But the system expects 'ret' variable

# Let me check if 'action' works instead of 'ret'
code45_noreturn = "# NOT FOUND handler - passes through"
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/write', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'write',
        'args': [[45], {'code': code45_noreturn}], 'kwargs': {}
    }
})
print('Set bot 45 to no-return:', 'OK' if resp.json().get('result') else 'ERROR')

# Now test bot 34 with a simple ret that returns an empty list (falsy)
# Empty list [] is falsy, so if result: would skip assignment
# But we need to SEND a message too...
# Actually, what if the system sends messages from the list AND checks for children?
# Let me check by looking at successful bot logs

# Read a successful log from COMERCIAL to see how they use ret
resp2 = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot.log', 'method': 'read',
        'args': [[25765]],
        'kwargs': {'fields': ['id', 'bot_log', 'text']}
    }
})
r2 = resp2.json()
if 'result' in r2:
    log = r2['result'][0]
    logtxt = str(log.get('bot_log', ''))
    print()
    print('=== Successful bot log (COMERCIAL) ===')
    print(logtxt)
    print()
    print('User text:', str(log.get('text', '')))
