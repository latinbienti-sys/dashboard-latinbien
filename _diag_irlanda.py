import sys, os, json
sys.path.insert(0, r'C:\Users\yarleyc\Documents\New OpenCode Project')
sys.stdout.reconfigure(encoding='utf-8')
import server
sess, uid = server.json_connect()

print('== 1. Partner IRLANDA ==')
part = server.json_execute(sess, 'res.partner', 'search_read', [
    [['name', 'ilike', 'IRLANDA']], ['id', 'name', 'phone', 'mobile']
])
for p in part:
    print(' id:', p['id'], '|', p['name'])

print('\n== 2. Facturas del partner ==')
inv = server.json_execute(sess, 'account.move', 'search_read', [
    [['partner_id', 'in', [p['id'] for p in part]], ['move_type', '=', 'out_invoice']],
    ['id', 'name', 'amount_total', 'amount_residual', 'payment_state', 'state', 'invoice_date', 'x_status_operativos']
])
for r in inv:
    print(' ', r['id'], r['name'], '| total:', r.get('amount_total'), '| residual:', r.get('amount_residual'), '| est_pago:', r.get('payment_state'), '| state:', r.get('state'), '| x_status_op:', r.get('x_status_operativos'))

print('\n== 3. mail.activity fields_get (campos con monto/monto/importe/amount) ==')
try:
    fg = server.json_execute(sess, 'mail.activity', 'fields_get', [[], ['name', 'string', 'type', 'relation']])
    keys = sorted(k for k in fg.keys()
                  if any(t in k.lower() for t in ['monto', 'amount', 'mont', 'import', 'cuota', 'pay', 'valor', 'x_']))
    for k in keys:
        print(' ', k, '|', fg[k].get('string'), '|', fg[k].get('type'), '|', fg[k].get('relation'))
except Exception as e:
    print('ERR:', str(e)[:300])

print('\n== 4. Actividades (mail.activity) de las facturas de IRLANDA, con TODOS sus campos ==')
inv_ids = [r['id'] for r in inv]
if inv_ids:
    acts = server.json_execute(sess, 'mail.activity', 'search_read', [
        [['res_model', '=', 'account.move'], ['res_id', 'in', inv_ids]],
        []
    ])
    for a in acts:
        print('  act id:', a.get('id'), '| res_id:', a.get('res_id'), '| type:', a.get('activity_type_id'))
        for k in sorted(a.keys()):
            v = a.get(k)
            if k in ('id', 'name', 'create_uid', 'write_uid', '__last_update'):
                continue
            print('      ', k, '=', v)
        print('   ---')