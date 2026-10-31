import sys
sys.path.insert(0, r'C:\Users\yarleyc\Documents\New OpenCode Project')
sys.stdout.reconfigure(encoding='utf-8')
import server
sess, uid = server.json_connect()

# Buscar actividades cuya nota/resumen contenga 10.76
acts = server.json_execute(sess, 'mail.activity', 'search_read',
    [['|', ['note', 'ilike', '10.76'], ['summary', 'ilike', '10.76']],
     ['id', 'res_model', 'res_id', 'res_name', 'summary', 'note', 'state', 'date_deadline', 'activity_type_id', 'user_id']])
print('actividades con 10.76:', len(acts))
for a in acts:
    for k in ('id', 'res_model', 'res_id', 'res_name', 'summary', 'note', 'state', 'date_deadline', 'user_id'):
        print(' ', k, '=', a.get(k))
    print('---')

# Si ninguna, buscar por partner PAOLA MARGARITA sus actividades en otros modelos
print('\n== todas las actividades de facturas de PAOLA MARGARITA (55691) ==')
inv = server.json_execute(sess, 'account.move', 'search_read',
    [[['partner_id', '=', 55691]], ['id', 'name']])
iids = [r['id'] for r in inv]
print('facturas:', [(r['id'], r['name']) for r in inv])
acts2 = server.json_execute(sess, 'mail.activity', 'search_read',
    [[['res_id', 'in', iids]], ['id', 'res_model', 'res_name', 'summary', 'note', 'state', 'date_deadline']])
print('actividades:', len(acts2))
for a in acts2:
    print(' ', a.get('id'), a.get('res_model'), a.get('res_name'), '|', a.get('summary'), '|', a.get('note'), '|', a.get('state'), '|', a.get('date_deadline'))