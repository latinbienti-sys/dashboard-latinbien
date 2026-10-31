import sys
sys.path.insert(0, r'C:\Users\yarleyc\Documents\New OpenCode Project')
sys.stdout.reconfigure(encoding='utf-8')
import server
sess, uid = server.json_connect()

# Buscar actividades con estado done
acts = server.json_execute(sess, 'mail.activity', 'search_read',
    [['state', '=', 'done'], ['id', 'res_id', 'res_name', 'summary', 'note', 'state', 'date_deadline', 'user_id']])
print('total done:', len(acts))
for a in acts[:15]:
    print(' ', a.get('res_name'), a.get('state'), a.get('summary'), str(a.get('note') or '')[:40])