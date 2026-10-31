import sys
sys.path.insert(0, r'C:\Users\yarleyc\Documents\New OpenCode Project')
sys.stdout.reconfigure(encoding='utf-8')
import server
sess, uid = server.json_connect()

part = server.json_execute(sess, 'res.partner', 'search_read',
    [[['name', 'ilike', 'PAOLA']], ['id', 'name']])
pids = [p['id'] for p in part]
print('partners:', [(p['id'], p['name']) for p in part])

inv = server.json_execute(sess, 'account.move', 'search_read',
    [[['partner_id', 'in', pids], ['move_type', '=', 'out_invoice']],
     ['id', 'name', 'amount_residual', 'payment_state', 'state', 'x_status_operativos']])
print('facturas:', [(r['id'], r['name'], r['payment_state'], r['state'], r['x_status_operativos']) for r in inv])
iids = [r['id'] for r in inv]

acts = server.json_execute(sess, 'mail.activity', 'search_read',
    [[['res_model', '=', 'account.move'], ['res_id', 'in', iids]], []])
for a in acts:
    print('---')
    for k in ('id', 'res_id', 'res_name', 'summary', 'note', 'state', 'date_deadline', 'activity_type_id', 'user_id'):
        print(' ', k, '=', a.get(k))