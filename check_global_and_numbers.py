from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# 1. Check root bots WITHOUT connector (global bots)
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.bot',
        'domain':[('parent_id','=',False),('connector_id','=',False)],
        'fields':['id','name','text_match','sequence','active','bot_key'],
        'limit':50
    }
})
records = resp.json().get('result', {}).get('records', [])
print("=== Root bots GLOBAL (sin connector) ===")
for b in records:
    print(f"  Bot {b['id']:>3}: {b['name'][:50]:<50} tm={str(b.get('text_match','') or '-'):<15} seq={b.get('sequence',0)} active={b.get('active')}")

# 2. Check WhatsApp numbers on connector 2
print("\n=== Números WhatsApp en conector 2 ===")
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.waba.number',
        'domain':[('connector_id','=',2)],
        'fields':['id','name','phone_number','bot_id','start_message'],
        'limit':20
    }
})
records = resp.json().get('result', {}).get('records', [])
for n in records:
    bot = n.get('bot_id')
    bot_info = f"bot_{bot[0]}" if isinstance(bot, list) else str(bot)
    print(f"  {n.get('name','')[:30]:30} tel={n.get('phone_number','')} bot={bot_info}")
    print(f"  start_message: {str(n.get('start_message',''))[:200]}")

# 3. Check ALL connectors  
print("\n=== Todos los conectores ===")
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.connector',
        'domain':[],
        'fields':['id','name','type','bot_id','message'],
        'limit':50
    }
})
records = resp.json().get('result', {}).get('records', [])
for c in records:
    bot = c.get('bot_id')
    bot_info = f"bot_{bot[0]}" if isinstance(bot, list) else str(bot)
    print(f"  Conn {c['id']:>3}: {c.get('name','')[:40]:<40} type={c.get('type','')} bot={bot_info}")
    if c.get('message'):
        print(f"    message: {str(c.get('message',''))[:150]}")
