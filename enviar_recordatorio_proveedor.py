"""Recordatorio de pago a proveedor por la PRÓXIMA fecha de pago (la primera del mes).

Modo por defecto: PRUEBA EN SECO (dry-run) — solo imprime el resumen y el cuerpo del correo.
Para enviar de verdad:  python enviar_recordatorio_proveedor.py --send
  (requiere LATINBIEN_SMTP_USER y LATINBIEN_SMTP_PASS en name.env o variables de entorno)

Opcional: indicar fecha exacta:  python enviar_recordatorio_proveedor.py --fecha 2026-09-20

Lee pago_proveedor_moto del JSON embebido en index.html (no necesita Odoo),
totaliza el monto a cancelar por las cuotas de esa fecha y arma el correo.
"""
import os, sys, json, re
from datetime import date, timedelta

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

ENVIAR = '--send' in sys.argv
FECHA_OBJETIVO = None
for i, a in enumerate(sys.argv):
    if a == '--fecha' and i + 1 < len(sys.argv):
        FECHA_OBJETIVO = sys.argv[i + 1]

# ── Credenciales SMTP (SOLO se cargan si se va a enviar) ──
smtp_user = smtp_pass = None
if ENVIAR:
    with open('name.env', 'rb') as f:
        for raw in f:
            line = raw.decode('utf-8', 'replace').strip()
            if line.startswith('LATINBIEN_SMTP_USER='):
                smtp_user = line.split('=', 1)[1].strip()
            elif line.startswith('LATINBIEN_SMTP_PASS='):
                smtp_pass = line.split('=', 1)[1].strip()
    if not smtp_user or not smtp_pass:
        print("ERROR: para enviar necesitas LATINBIEN_SMTP_USER/PASS en name.env")
        sys.exit(1)
    os.environ['LATINBIEN_SMTP_USER'] = smtp_user
    os.environ['LATINBIEN_SMTP_PASS'] = smtp_pass

# ── Extraer el JSON embebido del index.html ──
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r"DATA\s*=\s*JSON\.parse\('(.*?)'\);", html, re.DOTALL)
if not m:
    m = re.search(r"JSON\.parse\('(.*?)'\)", html, re.DOTALL)
if not m:
    print("ERROR: no se encontró DATA en index.html")
    sys.exit(1)

json_str = m.group(1)
json_str = json_str.replace("\\'", "'").replace('\\\\', '\\')
DATA = json.loads(json_str)

# ── Obtener pago_proveedor_moto ──
pp = DATA.get('pago_proveedor_moto', {})
items = pp.get('items', [])
if not items:
    print("No hay items en pago_proveedor_moto en index.html")
    sys.exit(1)

proveedor = pp.get('proveedor', 'MOTO CITY PRO, C.A.')

# ── Recolectar cuotas pendientes ──
pendientes = []
for it in items:
    for p in it.get('pagos', []):
        if p.get('estado') != 'pendiente':
            continue
        pendientes.append({
            'proveedor': proveedor,
            'orden_compra': it.get('orden_compra', ''),
            'cliente': it.get('cliente', ''),
            'modelo': it.get('modelo', ''),
            'cuota_num': p.get('cuota', 0),
            'total_cuotas': len(it.get('pagos', [])),
            'monto': p.get('monto', 0),
            'fecha_pago': p.get('fecha_pago', ''),
            'ciclo': it.get('ciclo', ''),
            'opcion': it.get('opcion', ''),
        })

if not pendientes:
    print("No hay cuotas pendientes a proveedor.")
    sys.exit(0)

# ── Agrupar por fecha y elegir la próxima ──
hoy = date.today().isoformat()
if FECHA_OBJETIVO:
    fechas = sorted({c['fecha_pago'] for c in pendientes})
    if FECHA_OBJETIVO not in set(fechas):
        print(f"ERROR: la fecha {FECHA_OBJETIVO} no aparece en las cuotas pendientes.")
        print(f"Fechas disponibles: {', '.join(fechas)}")
        sys.exit(1)
    fecha_seleccionada = FECHA_OBJETIVO
else:
    proximas = sorted({c['fecha_pago'] for c in pendientes if c['fecha_pago'] >= hoy})
    fecha_seleccionada = proximas[0] if proximas else sorted({c['fecha_pago'] for c in pendientes})[0]

cuotas_fecha = [c for c in pendientes if c['fecha_pago'] == fecha_seleccionada]
cuotas_fecha.sort(key=lambda c: (c['orden_compra'], c['cuota_num']))
monto_total = sum(c['monto'] for c in cuotas_fecha)

# ── Mostrar resumen (prueba en seco) ──
print("=" * 70)
print(f"RECORDATORIO PAGO A PROVEEDOR — {proveedor}")
print(f"Fecha de pago (próxima): {fecha_seleccionada}")
print(f"Cuotas a cancelar: {len(cuotas_fecha)}")
print(f"TOTAL A CANCELAR: ${monto_total:,.2f}")
print("=" * 70)
for c in cuotas_fecha:
    print(f"  • {c['orden_compra']} | {c['cliente']} | {c['modelo']}"
          f" | cuota {c['cuota_num']}/{c['total_cuotas']} | ${c['monto']:,.2f}"
          f" | ciclo {c['ciclo']} (Op {c['opcion']})")

# ── Armar el correo ──
if ENVIAR:
    from email_proveedor import generar_correo_totalizado_por_fecha, enviar_correo_totalizado_por_fecha
    asunto, cuerpo = generar_correo_totalizado_por_fecha(proveedor, fecha_seleccionada, cuotas_fecha, monto_total)
else:
    # Preview local idéntico al que se enviaría (sin requerir SMTP)
    asunto = (f'💵 Recordatorio Pago a Proveedor {fecha_seleccionada} — '
              f'{len(cuotas_fecha)} cuotas | Total ${monto_total:,.2f}')
    cuerpo = f"""
RECORDATORIO INTERNO DE PAGO A PROVEEDOR — TOTAL POR FECHA
{'='*55}

Proveedor: {proveedor}
Fecha de Pago: {fecha_seleccionada}
Cuotas a cancelar: {len(cuotas_fecha)}
TOTAL A CANCELAR: ${monto_total:,.2f}

DETALLE DE LAS CUOTAS ({fecha_seleccionada}):
"""
    for c in cuotas_fecha:
        cuerpo += (
            f"\n  • {c['orden_compra']} | Cliente: {c['cliente']} | {c['modelo']}"
            f"\n    Cuota {c['cuota_num']}/{c['total_cuotas']} | ${c['monto']:,.2f}"
            f" | Ciclo {c['ciclo']} (Op {c['opcion']})"
        )
    cuerpo += f"""
{'='*55}
TOTAL POR ESTA FECHA: ${monto_total:,.2f} en {len(cuotas_fecha)} cuotas.

Este es un recordatorio interno del sistema LATINBIEN Dashboard.
Fecha de generación: {date.today()}

No responder a este correo. Es solo para referencia interna.
    """

print("\n──────────────────────────────────────────────")
print("ASUNTO: " + asunto)
print("CUERPO DEL CORREO (prueba en seco):")
print(cuerpo)

if ENVIAR:
    print("\nEnviando correo real...")
    ok, msg = enviar_correo_totalizado_por_fecha(proveedor, fecha_seleccionada,
                                                 cuotas_fecha, monto_total)
    print(f"Resultado: {msg}")
    sys.exit(0 if ok else 1)
else:
    print("\n[PRUEBA EN SECO] No se envió ningún correo.")
    print("Para ENVIAR de verdad ejecuta:  python enviar_recordatorio_proveedor.py --send")
    sys.exit(0)