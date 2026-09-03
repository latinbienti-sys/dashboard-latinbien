"""Conexión compartida a Odoo para scripts de diagnóstico.

Uso:
    from odoo_conn import get_session
    s = get_session()
    # luego hacer calls con s.post(...)

Requiere variables de entorno ODOO_USER y ODOO_PASS.
"""
import os
import requests

ODOO_URL = 'https://latinbien.com'
ODOO_DB = 'erp_production'


def get_session():
    """Retorna una sesión JSON-RPC autenticada contra Odoo."""
    user = os.environ.get('ODOO_USER')
    password = os.environ.get('ODOO_PASS')
    if not user or not password:
        raise RuntimeError(
            "ODOO_USER y ODOO_PASS deben estar definidas como variables de entorno."
        )
    s = requests.Session()
    s.post(f'{ODOO_URL}/web/session/authenticate', json={
        'jsonrpc': '2.0', 'method': 'call',
        'params': {'db': ODOO_DB, 'login': user, 'password': password}
    })
    s.headers['Content-Type'] = 'application/json'
    return s
