from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

s.headers['Content-Type'] = 'application/json'

# Check text_match, sequence, bot_key for bot 61 and other root bots
bots_to_check = [61, 34, 59, 58, 84, 62]
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[('id', 'in', bots_to_check)]],
        'kwargs': {'fields': ['id', 'name', 'connector_id', 'parent_id', 'text_match', 'sequence', 'bot_key', 'active', 'apply_from', 'apply_to', 'apply_weekday']}
    }
})
print('ID   Name                                               Conn  Parent   Seq   text_match                 bot_key    Active')
print('='*100)
for b in resp.json().get('result', []):
    conn = str(b['connector_id'][0]) if b['connector_id'] else 'G'
    pid = str(b['parent_id'][0]) if b['parent_id'] else 'root'
    tm = str(b.get('text_match','') or '')[:25]
    bk = str(b.get('bot_key','') or '')[:10]
    seq = str(b.get('sequence','') or '')
    print(f"{b['id']:>4} {b['name'][:50]:<50} {conn:<5} {pid:<7} {seq:<5} {tm:<25} {bk:<10} {str(b['active']):<7}")

# Check ALL bots text_match
print("\n=== ALL bots with non-empty text_match ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/search_read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {
        'model': 'acrux.chat.bot', 'method': 'search_read',
        'args': [[('text_match', '!=', False)]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'parent_id']}
    }
})
for b in resp.json().get('result', []):
    pid = str(b['parent_id'][0]) if b['parent_id'] else 'root'
    print(f"  Bot {b['id']:>3}: {b['name'][:40]:<40} text_match='{b['text_match']}' parent={pid}")

# Check bot 62's text_match 
print("\n=== Bot 62 full ===")
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot/read', json={
    'jsonrpc': '2.0', 'method': 'call',
    'params': {'model': 'acrux.chat.bot', 'method': 'read',
        'args': [[62]],
        'kwargs': {'fields': ['id', 'name', 'text_match', 'sequence', 'bot_key']}
    }
})
print(json.dumps(resp.json().get('result', {}), indent=2))
