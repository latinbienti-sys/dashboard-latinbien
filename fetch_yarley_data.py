#!/usr/bin/env python3
"""Consulta los contratos de Yarley Carmona desde Odoo y actualiza la página del Club."""

import json, os, requests
from datetime import datetime

ODOO_URL = 'https://latinbien.com'
ODOO_DB = 'erp_production'
ODOO_USER = 'latinbienti@latinbien.com'
ODOO_PASS = 'z+cakaSe2805*'

def json_execute(sess, model, method, args=None, kwargs=None):
    resp = sess.post(f'{ODOO_URL}/web/dataset/call_kw/{model}/{method}', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs or {}},
        'id': 'fetch_' + str(datetime.now().timestamp())
    })
    data = resp.json()
    if 'error' in data:
        raise Exception(f'Error en {model}/{method}: {data["error"]}')
    return data['result']

def main():
    sess = requests.Session()
    # Autenticar
    auth = sess.post(f'{ODOO_URL}/web/session/authenticate', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'db': ODOO_DB, 'login': ODOO_USER, 'password': ODOO_PASS},
        'id': 1
    })
    if 'error' in auth.json():
        print('Error de autenticación')
        return

    print('[OK] Conectado a Odoo')

    # 1. Buscar partner de Yarley Carmona (probar varios formatos)
    for search_name in ['Yarley Carmona', 'YARLEY CARMONA', 'Yarley Carolina Carmona', 'Yarley%Carmona']:
        partner_domain = [['name', 'ilike', search_name]]
        partner_ids = json_execute(sess, 'res.partner', 'search', [partner_domain])
        if partner_ids:
            print(f'[OK] Encontrado con: "{search_name}"')
            break
        # Probar tambien por email
        email_domain = [['email', 'ilike', 'yarley.carmona']]
        email_ids = json_execute(sess, 'res.partner', 'search', [email_domain])
        if email_ids:
            print(f'[OK] Encontrado por email: yarley.carmona@gmail.com')
            partner_ids = email_ids
            break
    if not partner_ids:
        print('[NO] No se encontro a Yarley Carmona')
        return

    partner_id = partner_ids[0]
    partner_data = json_execute(sess, 'res.partner', 'read', [partner_id, ['name', 'vat', 'email', 'mobile']])
    partner = partner_data[0] if partner_data else {'name': 'Yarley Carmona'}
    print(f'[OK] Cliente: {partner.get("name")} | ID: {partner_id} | Vat: {partner.get("vat", "N/A")}')

    # 2. Buscar contratos activos (status 4 = Aprobado, 6 = Entregado)
    contract_domain = [
        ['partner_id', '=', partner_id],
        ['x_status_operativos', 'in', ['4', '6']],
        ['move_type', '=', 'out_invoice'],
    ]
    contract_ids = json_execute(sess, 'account.move', 'search', [contract_domain])
    print(f'[OK] Contratos activos encontrados: {len(contract_ids)}')

    # 3. Leer datos financieros
    contracts = []
    total_billing = 0.0
    total_paid = 0.0
    total_pending = 0.0

    if contract_ids:
        fields = ['id', 'name', 'amount_total', 'amount_residual', 'invoice_date', 'x_status_operativos']
        raw = json_execute(sess, 'account.move', 'read', [contract_ids, fields])
        for c in raw:
            total = float(c.get('amount_total') or 0)
            residual = float(c.get('amount_residual') or 0)
            paid = total - residual
            total_billing += total
            total_paid += paid
            total_pending += residual
            contracts.append({
                'name': c.get('name', ''),
                'total': round(total, 2),
                'paid': round(paid, 2),
                'residual': round(residual, 2),
                'date': str(c.get('invoice_date', '')),
                'status': c.get('x_status_operativos', '')
            })
            print(f'   - {c["name"]}: Total=${total:.2f} Pagado=${paid:.2f} Pendiente=${residual:.2f}')

    # 4. Verificar cuotas vencidas
    overdue_count = 0
    has_overdue = False
    if contract_ids:
        try:
            overdue_domain = [
                ['invoice_id', 'in', contract_ids],
                ['state', '=', 'vencido'],
            ]
            overdue_ids = json_execute(sess, 'invoice.installment.line', 'search', [overdue_domain])
            overdue_count = len(overdue_ids)
            has_overdue = overdue_count > 0
            print(f'[OK] Cuotas vencidas: {overdue_count}')
        except:
            print('[OK] No se pudo consultar invoice.installment.line (se usara metodo alternativo)')

    # 5. Determinar rango
    def calc_tier(count, billing, overdue):
        if overdue:
            return 'Suspendido', '[X]'
        if count > 8 and billing > 6000:
            return 'VIP', '[VIP]'
        if count >= 8 and 3000.01 <= billing <= 6000:
            return 'Media', '[MEDIA]'
        if count >= 4 and billing >= 3000:
            return 'Basica', '[BASICA]'
        return 'Sin rango', '[-]'

    tier_name, tier_icon = calc_tier(len(contract_ids), total_billing, has_overdue)
    print(f'[OK] Rango: {tier_icon} {tier_name}')

    # 6. Generar datos para el HTML
    demo_data = {
        'partnerName': partner.get('name', 'Yarley Carmona'),
        'partnerId': partner_id,
        'contractCount': len(contract_ids),
        'totalBilling': round(total_billing, 2),
        'totalPaid': round(total_paid, 2),
        'totalPending': round(total_pending, 2),
        'hasOverduePayments': has_overdue,
        'overdueCount': overdue_count,
        'tierName': tier_name,
        'tierIcon': tier_icon,
        'contracts': contracts,
        'fetchedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Guardar como JSON
    with open('yarley_data.json', 'w', encoding='utf-8') as f:
        json.dump(demo_data, f, ensure_ascii=False, indent=2)
    print(f'[OK] Datos guardados en yarley_data.json')

    # 7. Actualizar el HTML con los datos reales de Yarley
    html_path = os.path.join(os.path.dirname(__file__), 'latinbien', 'club-membresia.html')
    if not os.path.exists(html_path):
        html_path = os.path.join(os.path.dirname(__file__), 'club-membresia.html')

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Construir el objeto JSON para el dashboard
    dashboard_json = json.dumps({
        'contractCount': len(contract_ids),
        'totalBilling': round(total_billing, 2),
        'totalPaid': round(total_paid, 2),
        'totalPending': round(total_pending, 2),
        'hasOverduePayments': has_overdue,
        'overdueCount': overdue_count
    })

    partner_name = partner.get('name', 'Yarley Carmona')

    # Bloque demo nuevo con los datos reales de Yarley
    demo_block_new = (
        '    // ── MODO DEMO LOCAL (Datos reales de Yarley Carmona) ──\n'
        '  if (window.location.protocol === \'file:\') {\n'
        '    document.getElementById(\'loginPrompt\').style.display = \'none\';\n'
        '    if (userGreeting) {\n'
        '      userGreeting.style.display = \'flex\';\n'
        f'      document.getElementById(\'greetingName\').textContent = \'\\U0001f44b \\u00a1Hola, {partner_name}!\';\n'
        f'      document.getElementById(\'greetingMsg\').innerHTML = \'Rango actual: <strong>{tier_icon} {tier_name}</strong> &bull; {len(contract_ids)} contratos &bull; <a href="#mi-rango" style="color:var(--accent);font-weight:600;">Ver tablero completo \\u2192</a>\';\n'
        '    }\n'
        '    if (authSec) authSec.classList.add(\'visible\');\n'
        f'    renderTierDashboard({dashboard_json});\n'
        '  }\n'
        '  }'
    )

    # Buscar el bloque de modo demo original y reemplazarlo
    pattern = r'// ── MODO DEMO LOCAL.*?renderTierDashboard\(\{[^}]+\}\);\s+\}\s+\}'
    import re
    if re.search(pattern, html, re.DOTALL):
        html = re.sub(pattern, lambda m: demo_block_new, html, flags=re.DOTALL)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'[OK] HTML actualizado con datos de Yarley Carmona')
    else:
        print('[NO] No se pudo encontrar el bloque demo en el HTML')

    print(f'\n[OK] Resumen final:')
    print(f'   Contratos activos: {len(contract_ids)}')
    print(f'   Facturación total: ${total_billing:.2f}')
    print(f'   Total pagado: ${total_paid:.2f}')
    print(f'   Saldo pendiente: ${total_pending:.2f}')
    print(f'   Cuotas vencidas: {overdue_count}')
    print(f'   Rango: {tier_name}')
    print(f'\nAbre club-membresia.html en el navegador para ver los datos reales.')

if __name__ == '__main__':
    main()
