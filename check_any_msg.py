from odoo_conn import get_session

s = get_session()

sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

# Simple count query for messages
resp = s.post('https://latinbien.com/web/dataset/search_read', json={
    'jsonrpc':'2.0','method':'call',
    'params':{
        'model':'acrux.chat.message',
        'domain':[],
        'fields':['id','text','create_date','from_me','conversation_id'],
        'order':'create_date desc',
        'limit':5
    }
})
data = resp.json()
if 'error' in data:
    print("ERROR:", json.dumps(data['error']['data'], indent=2)[:3000])
else:
    records = data.get('result', {}).get('records', [])
    print(f"Found {len(records)} messages")
    for r in records:
        conv = r.get('conversation_id')
        conv_name = f"conv_{conv[0]}" if isinstance(conv, list) else str(conv)
        direction = ">>ENV" if r.get('from_me') else "<<REC"
        print(f"  [{r['create_date'][:19]}] {direction} {conv_name}: {str(r.get('text',''))[:120]}")
