from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# First just check if messages exist for conv 33146
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.message',
        'domain':[('conversation_id','=',33146)],
        'fields':['id','text','create_date','from_me'],
        'order':'create_date asc',
        'limit':10
    }
})
print("Full response:", json.dumps(resp.json(), indent=2)[:2000])
print()
print("Result type:", type(resp.json().get('result')))
