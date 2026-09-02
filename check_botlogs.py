from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Search bot logs for conversation 33152 (the test conv)
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot.log','method':'search_read',
        'args':[[('conversation_id','=',33152)]],
        'kwargs':{'fields':['id','text','bot_log','create_date','connector_id'],
            'order':'create_date asc','limit':30}
    }
})
print("=== BOT LOGS for conv 33152 ===")
for r in resp.json().get('result', []):
    print(f"[{r['create_date'][:19]}] text={r.get('text','')[:150]}")
    blog = r.get('bot_log') or ''
    print(f"  bot_log: {blog[:600]}")
    print()

# Also bot logs for cobranza conv 31368 to compare
resp = s.post('https://latinbien.com/web/dataset/call_kw/acrux.chat.bot.log/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{'model':'acrux.chat.bot.log','method':'search_read',
        'args':[[('conversation_id','=',31368)]],
        'kwargs':{'fields':['id','text','bot_log','create_date','connector_id'],
            'order':'create_date asc','limit':15}
    }
})
print("\n=== BOT LOGS for conv 31368 (cobranza) ===")
for r in resp.json().get('result', []):
    print(f"[{r['create_date'][:19]}] text={r.get('text','')[:150]}")
    blog = r.get('bot_log') or ''
    print(f"  bot_log: {blog[:600]}")
    print()
