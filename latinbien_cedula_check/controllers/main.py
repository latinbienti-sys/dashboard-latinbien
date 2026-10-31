import time
from collections import defaultdict, deque

from odoo import http
from odoo.http import request

_WINDOW = 60
_MAX_REQ = 20
_HITS = defaultdict(deque)


def _candidates(ident, num):
    ident = ''.join(ch for ch in str(ident or '').upper() if ch.isalpha())[:1]
    digits = ''.join(ch for ch in str(num or '') if ch.isdigit())
    if not ident or not digits:
        return []
    nz = digits.lstrip('0') or '0'
    out = {ident + nz, ident + digits}
    for w in (8, 9, 10):
        out.add(ident + nz.zfill(w))
    return list(out)


def _rate_ok(ip):
    now = time.time()
    q = _HITS[ip]
    while q and now - q[0] > _WINDOW:
        q.popleft()
    if len(q) >= _MAX_REQ:
        return False
    q.append(now)
    return True


class LatinbienCedulaCheck(http.Controller):

    @http.route('/latinbien/cedula_check', type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def cedula_check(self, ident=None, num=None, **kw):
        ip = request.httprequest.remote_addr or 'unknown'
        if not _rate_ok(ip):
            return {'estado': 'rate_limited'}
        cands = _candidates(ident, num)
        if not cands:
            return {'estado': 'no_existe'}
        partner = request.env['res.partner'].sudo().search([('vat', 'in', cands)], limit=1)
        if not partner:
            return {'estado': 'no_existe'}
        activa = bool(partner.x_activacion_linea) or (partner.x_credit_limit_aprobado or 0.0) > 0.0
        return {'estado': 'existe_con_linea' if activa else 'existe_sin_linea'}
