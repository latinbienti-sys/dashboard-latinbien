#!/usr/bin/env python3
"""Sync incremental y SOLO LECTURA desde Odoo -> cache_live.json.

Garantias:
  * Unicas llamadas a Odoo: authenticate + search_read (lectura pura;
    nunca create/write/unlink/multiproceso pesado). No afecta al ERP.
  * Filtro incremental: dominio con write_date/create_date >= ultimo sync,
    campos estrictos por modelo (CAMPOS) y limite MAX_REGS por consulta.
  * Resultado liviano: solo agregados por dia/ejecutivo en cache_live.json
    (escritura atomica: archivo temporal + os.replace). El frontend NUNCA
    consulta Odoo: solo lee este JSON local.

Uso:
    python sync_live.py             # sync incremental (ventana del ultimo sync)
    python sync_live.py --dias N    # fuerza ventana de N dias
    python sync_live.py --full      # reinicia estado y recalcula la ventana

Credenciales: variables de entorno ODOO_USER / ODOO_PASS
(opcionalmente ODOO_URL / ODOO_DB / ODOO_TZ_OFFSET / ODOO_CAT_CREDI)
o archivo name.env.

Mapeo de metricas (ventana viva; el historico estatico queda intacto):
  daily[dia][uid].c = leads creados ese dia (crm.lead.create_date)
  daily[dia][uid].a = mensajes de seguimiento ese dia (mail.message)
  daily[dia][uid].t = leads distintos con actividad ese dia
  daily[dia][uid].s = leads que entraron a etapa "Contacto Tienda"
  moves[dia][uid][etapa] = transiciones de etapa detectadas por diff de
                     snapshot local (solo lectura; sin historial en ERP)
  ventas[dia][uid]  = expected_revenue de leads que entraron a "Cierre"
Nota: en el primer run se siembra el snapshot (sin movimientos); los
movimientos/ventas se calculan a partir del segundo run.
"""
import datetime as dt
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
import xmlrpc.client

# ------------------------------------------------------------------ Rutas --
BASE = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(BASE, 'cache_live.json')
STATE_PATH = os.path.join(BASE, 'sync_state.json')
LOCK_PATH = os.path.join(BASE, 'sync.lock')

# ------------------------------------------------------------- Configuración #
ODOO_URL = os.environ.get('ODOO_URL', 'https://latinbien.com').rstrip('/')
ODOO_DB = os.environ.get('ODOO_DB', 'erp_production')
MAX_REGS = 5000          # tope estricto por consulta search_read
MAX_VENTANA = 10         # dias maximos por ventana incremental
SNAPSHOT_DIAS = 150      # retencion del snapshot local de etapas
# Odoo guarda en UTC; offset horario local para agrupar por dia (America/Caracas = -4)
TZ_OFFSET_H = int(os.environ.get('ODOO_TZ_OFFSET', '-4'))

CAMPOS = {
    'crm.lead': ['id', 'user_id', 'stage_id', 'write_date', 'create_date',
                 'expected_revenue', 'partner_id'],
    'mail.message': ['id', 'model', 'res_id', 'create_date', 'message_type',
                     'author_id'],
    'res.partner': ['id', 'name', 'user_id', 'write_date', 'create_date',
                    'category_id'],
    'res.partner.category': ['id', 'name'],
}


def log(msg):
    print('[sync_live] %s' % msg, flush=True)


# ---------------------------------------------------------- Credenciales --- #
def _leer_env_file():
    """Carga KEY=VALUE desde name.env (sin imprimir valores)."""
    for ruta in (os.path.join(BASE, 'name.env'),
                 os.path.join(os.path.dirname(BASE), 'name.env')):
        if not os.path.isfile(ruta):
            continue
        datos = {}
        with open(ruta, 'r', encoding='utf-8', errors='replace') as fh:
            for linea in fh:
                if '=' in linea and not linea.strip().startswith('#'):
                    k, v = linea.rstrip('\n').split('=', 1)
                    datos[k.strip()] = v.strip().strip('"').strip("'")
        return datos
    return {}


def credenciales():
    envfile = _leer_env_file()
    user = os.environ.get('ODOO_USER') or envfile.get('ODOO_USER')
    password = os.environ.get('ODOO_PASS') or envfile.get('ODOO_PASS')
    if not user or not password:
        raise RuntimeError(
            'Faltan credenciales: defina ODOO_USER / ODOO_PASS '
            '(variables de entorno o archivo name.env).')
    return user, password


# ------------------------------------------------------- Utilidades Odoo --- #
def conectar(user, password):
    common = xmlrpc.client.ServerProxy('%s/xmlrpc/2/common' % ODOO_URL, allow_none=True)
    uid = common.authenticate(ODOO_DB, user, password, {})
    if not uid:
        raise RuntimeError('Autenticacion rechazada por Odoo.')
    modelos = xmlrpc.client.ServerProxy('%s/xmlrpc/2/object' % ODOO_URL, allow_none=True)
    return uid, modelos


def buscar_read(uid, password, modelos, modelo, dominio, campos, limite=MAX_REGS,
                orden='write_date desc'):
    """search_read estricto: solo lectura, campos acotados y limit."""
    res = modelos.execute_kw(
        ODOO_DB, uid, password, modelo, 'search_read',
        [dominio],
        {'fields': campos, 'limit': min(limite, MAX_REGS), 'order': orden})
    truncado = len(res) >= min(limite, MAX_REGS)
    if truncado:
        log('AVISO: %s alcanzo el limite de %s registros (truncado).'
            % (modelo, min(limite, MAX_REGS)))
    return res, truncado


def a_local(fecha_odoo):
    """'YYYY-MM-DD HH:MM:SS' (UTC de Odoo) -> (fecha_local, dia_str)."""
    try:
        d = dt.datetime.strptime((fecha_odoo or '')[:19], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None, ''
    loc = d + dt.timedelta(hours=TZ_OFFSET_H)
    return loc, loc.strftime('%Y-%m-%d')


def norm_nombre(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return ' '.join(s.lower().split())


def equipo_lc_local():
    """Norms del equipo de Linea de Crédito, leídos del index.html local
    (el mismo equipo que muestra el reporte estático del embudo)."""
    try:
        with open(os.path.join(BASE, 'index.html'), 'r', encoding='utf-8',
                  errors='replace') as fh:
            html = fh.read()
        m = re.search(r'<script id="data" type="application/json">(.*?)</script>',
                      html, re.S)
        datos = json.loads(m.group(1))
        team = ((datos.get('linea_credito') or {}).get('team')) or []
        return {norm_nombre(t.get('norm') or t.get('nombre')) for t in team} - {''}
    except Exception:
        return set()


def guardar_atomico(ruta, datos):
    fd, tmp = tempfile.mkstemp(dir=BASE, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            json.dump(datos, fh, ensure_ascii=False)
        os.replace(tmp, ruta)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def leer_json(ruta, default):
    try:
        with open(ruta, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


# --------------------------------------------------------------- Lock ------ #
def tomar_lock():
    if os.path.exists(LOCK_PATH):
        try:
            if time.time() - os.path.getmtime(LOCK_PATH) < 1800:
                log('Otro sync esta corriendo (lock < 30 min). Salgo.')
                return False
            log('Lock viejo; lo reemplazo.')
        except OSError:
            pass
    with open(LOCK_PATH, 'w', encoding='utf-8') as fh:
        fh.write(str(os.getpid()))
    return True


def soltar_lock():
    try:
        os.remove(LOCK_PATH)
    except OSError:
        pass


# --------------------------------------------------------------- Ventana --- #
def calcular_ventana(state, args):
    ahora_utc = dt.datetime.utcnow()
    hoy_local = (ahora_utc + dt.timedelta(hours=TZ_OFFSET_H)).date()
    if args.full:
        state = {}
    if args.dias:
        dias = max(1, min(args.dias, MAX_VENTANA * 3))
        desde = hoy_local - dt.timedelta(days=dias - 1)
    elif state.get('desde_local'):
        # Recalcula desde el mismo punto del ultimo sync (sin huecos),
        # con tope de MAX_VENTANA dias para no pesar sobre Odoo.
        previo = dt.date.fromisoformat(state['desde_local'])
        desde = max(previo, hoy_local - dt.timedelta(days=MAX_VENTANA - 1))
    else:
        # Primer run: cubre el hueco con el cache estatico (ventana tope).
        desde = hoy_local - dt.timedelta(days=MAX_VENTANA - 1)
    iso_utc_desde = (dt.datetime.combine(desde, dt.time.min)
                     - dt.timedelta(hours=TZ_OFFSET_H)).strftime('%Y-%m-%d %H:%M:%S')
    dias = [desde + dt.timedelta(days=i)
            for i in range((hoy_local - desde).days + 1)]
    return state, desde, iso_utc_desde, dias, hoy_local


# --------------------------------------------------------------- Sync ------ #
def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

    args_dias = None
    args_full = '--full' in sys.argv
    if '--dias' in sys.argv:
        i = sys.argv.index('--dias')
        args_dias = int(sys.argv[i + 1])

    class Args(object):
        dias = args_dias
        full = args_full

    if not tomar_lock():
        return 0

    t0 = time.time()
    try:
        user, password = credenciales()
        uid, modelos = conectar(user, password)
        state = leer_json(STATE_PATH, {})
        state, desde, iso_desde, dias, hoy_local = calcular_ventana(state, Args())
        dias_set = set(d.isoformat() for d in dias)
        log('Ventana: %s -> %s (%d dias), lectura en curso...'
            % (desde.isoformat(), hoy_local.isoformat(), len(dias)))
        if len(dias) > MAX_VENTANA:
            log('AVISO: ventana mayor a MAX_VENTANA=%d por peticion --dias.' % MAX_VENTANA)

        truncado = False

        # 1) crm.lead (incremental: create_date o write_date en la ventana) --
        leads, t = buscar_read(
            uid, password, modelos, 'crm.lead',
            ['|', ('create_date', '>=', iso_desde), ('write_date', '>=', iso_desde)],
            CAMPOS['crm.lead'])
        truncado = truncado or t
        leads_por_id = {r['id']: r for r in leads}
        log('crm.lead: %d registros' % len(leads))

        # 2) mail.message de leads (seguimiento / atendidos) ---------------
        mensajes, t = buscar_read(
            uid, password, modelos, 'mail.message',
            [('model', '=', 'crm.lead'), ('create_date', '>=', iso_desde)],
            CAMPOS['mail.message'], orden='create_date desc')
        truncado = truncado or t
        log('mail.message: %d registros' % len(mensajes))

        # Leads referenciados por mensajes que no estan en la ventana:
        # se traen solo con los campos minimos para saber su ejecutivo.
        faltantes = sorted({m.get('res_id') for m in mensajes
                            if m.get('res_id') and m['res_id'] not in leads_por_id})
        for i in range(0, len(faltantes), 500):
            lote = faltantes[i:i + 500]
            extra, _ = buscar_read(
                uid, password, modelos, 'crm.lead',
                [('id', 'in', lote)],
                ['id', 'user_id', 'stage_id', 'write_date', 'create_date',
                 'partner_id'],
                orden='id desc')
            for r in extra:
                leads_por_id.setdefault(r['id'], r)

        # 3) res.partner CREDIMOTOS (gestion diaria Linea de Credito) -------
        # Categorias por defecto: nombre con "CREDIMOTO" (cubre CREDIMOTO y
        # CREDIMOTOS). Override: variable ODOO_CAT_CREDI='133,138'.
        cats_env = os.environ.get('ODOO_CAT_CREDI', '').strip()
        cat_patron = 'env' if cats_env else 'CREDIMOTO'
        if cats_env:
            cat_ids = [int(x) for x in cats_env.split(',') if x.strip()]
        elif state.get('cat_ids') and state.get('cat_patron') == cat_patron:
            cat_ids = state['cat_ids']
        else:
            cats, _ = buscar_read(
                uid, password, modelos, 'res.partner.category',
                [('name', 'ilike', 'CREDIMOTO')], CAMPOS['res.partner.category'],
                limite=50, orden='id asc')
            cat_ids = [c['id'] for c in cats]
        state['cat_patron'] = cat_patron
        if not cat_ids:
            log('Sin categoria CREDIMOTO(S) (ok si no aplica).')

        socios_lc = []
        if cat_ids:
            dominio_lc = ['&', '|',
                          ('create_date', '>=', iso_desde),
                          ('write_date', '>=', iso_desde),
                          ('category_id', 'in', cat_ids)]
            socios_lc, t = buscar_read(
                uid, password, modelos, 'res.partner', dominio_lc,
                CAMPOS['res.partner'])
            truncado = truncado or t
        log('res.partner CREDIMOTOS: %d registros' % len(socios_lc))

        # 4) Agregados por dia / ejecutivo ----------------------------------
        daily, moves, ventas = {}, {}, {}
        execs = {}

        def bucket(dia, uid_s):
            return daily.setdefault(dia, {}).setdefault(
                uid_s, {'c': 0, 't': 0, 's': 0, 'a': 0})

        def reg_exec(uid_val, nombre):
            if not uid_val:
                return None
            uid_s = str(uid_val[0] if isinstance(uid_val, (list, tuple)) else uid_val)
            nom = (uid_val[1] if isinstance(uid_val, (list, tuple)) and uid_val[1]
                   else nombre or ('UID %s' % uid_s))
            execs.setdefault(uid_s, nom)
            return uid_s

        snapshot = state.get('snapshot') or {}
        snapshot_nuevo = {}

        for r in leads:
            uid_s = reg_exec(r.get('user_id'), None)
            _, dia_c = a_local(r.get('create_date'))
            _, dia_w = a_local(r.get('write_date'))
            etapa = (r.get('stage_id') or [None, ''])[1] or 'Sin etapa'
            ingreso = float(r.get('expected_revenue') or 0)
            snapshot_nuevo[str(r['id'])] = {'stage': etapa, 'w': dia_w}
            if uid_s and dia_c in dias_set:
                bucket(dia_c, uid_s)['c'] += 1
            prev = snapshot.get(str(r['id']))
            if prev and uid_s and dia_w in dias_set and prev.get('stage') != etapa:
                mv = moves.setdefault(dia_w, {}).setdefault(uid_s, {})
                mv[etapa] = mv.get(etapa, 0) + 1
                bajo = etapa.lower()
                if 'contacto tienda' in bajo:
                    bucket(dia_w, uid_s)['s'] += 1
                if 'cierre' in bajo:
                    v = ventas.setdefault(dia_w, {})
                    v[uid_s] = v.get(uid_s, 0.0) + ingreso

        # Conserva el snapshot de leads no tocados en esta ventana.
        limite_snap = (hoy_local - dt.timedelta(days=SNAPSHOT_DIAS)).isoformat()
        for k, v in snapshot.items():
            if k not in snapshot_nuevo and v.get('w', '') >= limite_snap:
                snapshot_nuevo[k] = v

        atendidos = {}
        for m in mensajes:
            if m.get('message_type') == 'user_notification':
                continue
            lead = leads_por_id.get(m.get('res_id'))
            if not lead or not lead.get('user_id'):
                continue
            uid_s = reg_exec(lead.get('user_id'), None)
            _, dia = a_local(m.get('create_date'))
            if not uid_s or dia not in dias_set:
                continue
            bucket(dia, uid_s)['a'] += 1
            atendidos.setdefault(dia, {}).setdefault(uid_s, set()).add(m['res_id'])
        for dia, por_uid in atendidos.items():
            for uid_s, cs in por_uid.items():
                bucket(dia, uid_s)['t'] += len(cs)

        # 5) Linea de Credito: gestion diaria (por_dia / detalle_dia) --------
        lc = {'dias': [], 'por_dia': {}, 'detalle_dia': {}, 'stages': []}
        if cat_ids:
            # Senales de movimiento: (a) el contacto CREDIMOTOS cambio en la
            # ventana, (b) alguno de sus leads cambio/mensaje en la ventana.
            ids_lc = {s['id']: s for s in socios_lc}

            def _pid(reg):
                p = reg.get('partner_id')
                return p[0] if isinstance(p, (list, tuple)) and p else None

            extra_ids = sorted({pid for r in leads_por_id.values()
                                for pid in [_pid(r)]
                                if pid and pid not in ids_lc})
            for i in range(0, len(extra_ids), 500):
                lote = extra_ids[i:i + 500]
                parciales, _ = buscar_read(
                    uid, password, modelos, 'res.partner',
                    [('id', 'in', lote)], CAMPOS['res.partner'], orden='id asc')
                for p in parciales:
                    cats = p.get('category_id') or []
                    if any(c in cat_ids for c in cats):
                        ids_lc[p['id']] = p
            socios_lc = list(ids_lc.values())
            log('res.partner CREDIMOTOS (ventana + leads): %d' % len(socios_lc))
        if socios_lc:
            ids = [s['id'] for s in socios_lc]
            leads_lc = []
            for i in range(0, len(ids), 500):
                lote = ids[i:i + 500]
                parciales, t = buscar_read(
                    uid, password, modelos, 'crm.lead',
                    [('partner_id', 'in', lote)],
                    ['id', 'user_id', 'stage_id', 'write_date', 'partner_id'],
                    orden='write_date desc')
                truncado = truncado or t
                leads_lc.extend(parciales)
            por_socio = {}
            for l in leads_lc:
                pid = l.get('partner_id')
                pid = pid[0] if isinstance(pid, (list, tuple)) and pid else None
                if pid:
                    por_socio.setdefault(pid, []).append(l)

            movimientos = {}   # (dia, socio_id) -> (asesor, norm, etapa, nombre)
            equipo = equipo_lc_local()
            for s in socios_lc:
                asesor = (s.get('user_id') or [None, ''])[1] or 'Sin asesor'
                etapas = por_socio.get(s['id']) or []
                if not etapas:
                    continue  # sin lead => no cuenta como "gestionado"
                norm = norm_nombre(asesor)
                if equipo and norm not in equipo:
                    continue  # asesor fuera del equipo de Linea de Credito
                etapa_act = ((etapas[0].get('stage_id') or [None, ''])[1]
                             or 'Sin etapa')
                dias_s = {a_local(l.get('write_date'))[1] for l in etapas}
                for dia in dias_s:
                    if dia in dias_set:
                        movimientos[(dia, s['id'])] = (
                            asesor, norm, etapa_act, s.get('name') or '')
            lc_dias, lc_etapas = set(), set()
            for (dia, _sid), (asesor, norm, etapa, nombre) in sorted(movimientos.items()):
                pd = lc['por_dia'].setdefault(dia, {}).setdefault(norm, {'_total': 0})
                pd['_total'] += 1
                pd[etapa] = pd.get(etapa, 0) + 1
                lc['detalle_dia'].setdefault(dia, []).append(
                    {'nombre': nombre, 'asesor': asesor, 'etapa': etapa})
                lc_dias.add(dia)
                lc_etapas.add(etapa)
            lc['dias'] = sorted(lc_dias)
            lc['stages'] = sorted(lc_etapas)
        log('Linea de Credito: %d dias con gestion' % len(lc['dias']))

        # 6) Salida ligera ---------------------------------------------------
        # Conserva los dias del cache anterior que quedaron fuera de la
        # ventana (para que el frontend no pierda dias ya sincronizados).
        RETENER_DIAS = 60
        corte_retencion = (hoy_local - dt.timedelta(days=RETENER_DIAS)).isoformat()
        viejo = leer_json(CACHE_PATH, {})
        for e in (viejo.get('execs') or []):
            if e.get('uid'):
                execs.setdefault(str(e['uid']), e.get('nombre') or '')
        for clave, destino in (('daily', daily), ('moves', moves),
                               ('ventas', ventas)):
            for dia, val in (viejo.get(clave) or {}).items():
                if dia not in dias_set and dia >= corte_retencion:
                    destino.setdefault(dia, val)
        viejo_lc = (viejo.get('linea_credito') or {})
        for dia in (viejo_lc.get('dias') or []):
            if dia in dias_set or dia < corte_retencion:
                continue
            if dia not in lc['dias']:
                lc['dias'].append(dia)
            if dia in (viejo_lc.get('por_dia') or {}):
                lc['por_dia'].setdefault(dia, viejo_lc['por_dia'][dia])
            if dia in (viejo_lc.get('detalle_dia') or {}):
                lc['detalle_dia'].setdefault(dia, viejo_lc['detalle_dia'][dia])
        lc['dias'] = sorted(lc['dias'])

        ahora = dt.datetime.utcnow().replace(microsecond=0)
        cache = {
            'generado': ahora.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'desde': desde.isoformat(),
            'hasta': hoy_local.isoformat(),
            'dias': [d.isoformat() for d in dias],
            'truncado': truncado,
            'solo_lectura': True,
            'execs': [{'uid': u, 'nombre': n} for u, n in sorted(execs.items(),
                                                                 key=lambda x: x[1])],
            'daily': daily,
            'moves': moves,
            'ventas': ventas,
            'linea_credito': lc,
        }
        guardar_atomico(CACHE_PATH, cache)

        state.update({
            'desde_local': desde.isoformat(),
            'ultimo_sync_utc': ahora.strftime('%Y-%m-%d %H:%M:%S'),
            'cat_ids': cat_ids,
            'snapshot': snapshot_nuevo,
        })
        guardar_atomico(STATE_PATH, state)
        log('OK: cache_live.json escrito en %.1fs (solo lectura, %d leads / '
            '%d mensajes).' % (time.time() - t0, len(leads), len(mensajes)))
        return 0
    except Exception as exc:  # jamas deja rastro: el dashboard sigue sirviendo
        log('ERROR: %s' % exc)
        return 1
    finally:
        soltar_lock()


if __name__ == '__main__':
    sys.exit(main())
