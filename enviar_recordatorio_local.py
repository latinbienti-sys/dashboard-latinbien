"""Envía recordatorio consolidado usando datos del index.html ya generado.
No necesita Odoo — lee pago_proveedor_moto del JSON embebido en index.html."""
import os, sys, json, re

# ── Leer credenciales SMTP del name.env ──
smtp_user = smtp_pass = None
with open('name.env', 'rb') as f:
    for raw in f:
        line = raw.decode('utf-8', 'replace').strip()
        if line.startswith('LATINBIEN_SMTP_USER='):
            smtp_user = line.split('=', 1)[1].strip()
        elif line.startswith('LATINBIEN_SMTP_PASS='):
            smtp_pass = line.split('=', 1)[1].strip()

if not smtp_user or not smtp_pass:
    print("ERROR: faltan LATINBIEN_SMTP_USER/PASS en name.env")
    sys.exit(1)
os.environ['LATINBIEN_SMTP_USER'] = smtp_user
os.environ['LATINBIEN_SMTP_PASS'] = smtp_pass

# ── Extraer el JSON embebido del index.html ──
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r"DATA\s*=\s*JSON\.parse\('(.*?)'\);", html, re.DOTALL)
if not m:
    # fallback: var DATA = JSON.parse('...')
    m = re.search(r"JSON\.parse\('(.*?)'\)", html, re.DOTALL)
if not m:
    print("ERROR: no se encontró DATA en index.html")
    sys.exit(1)

json_str = m.group(1)
# Desescapar la cadena JSON (el "generar_html" escapa ' y \)
json_str = json_str.replace("\\'", "'").replace('\\\\', '\\')
DATA = json.loads(json_str)

# ── Obtener pago_proveedor_moto ──
pp = DATA.get('pago_proveedor_moto', {})
items = pp.get('items', [])
if not items:
    print("No hay items en pago_proveedor_moto en index.html")
    sys.exit(1)

print(f"Órdenes en pago_proveedor_moto: {len(items)}")
for it in items:
    ciclo = it.get('ciclo')
    cls = it.get('cliente')
    print(f"  - {it.get('orden_compra')} | {cls} | ciclo {ciclo} | {it.get('modelo')}")

# ── Agrupar cuotas de la PRIMERA fecha vencida/próxima ──
from datetime import date
from email_proveedor import enviar_correo_consolidado

hoy = date.today()
# Filtrar cuotas pendientes
pendientes = []
for it in items:
    for p in it.get('pagos', []):
        if p.get('estado') == 'pendiente':
            pendientes.append({
                'proveedor': it.get('proveedor', ''),
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

print(f"\nCuotas pendientes: {len(pendientes)}")
if not pendientes:
    print("No hay cuotas pendientes para enviar recordatorio.")
    sys.exit(0)

# Agrupar por fecha
from collections import defaultdict
grupos = defaultdict(lambda: {'fecha_pago': '', 'cuotas': [], 'monto_total': 0.0, 'proveedor': ''})
for p in pendientes:
    f = p['fecha_pago']
    g = grupos[f]
    g['fecha_pago'] = f
    g['cuotas'].append(p)
    g['monto_total'] += p['monto']
    g['proveedor'] = p['proveedor']

grupos_lista = [grupos[k] for k in sorted(grupos.keys())]

# Mostrar el resumen (primer grupo)
g0 = grupos_lista[0]
print(f"\nPrimer grupo recordatorio: {g0['fecha_pago']} - {len(g0['cuotas'])} cuotas - ${g0['monto_total']:,.2f}")
for p in g0['cuotas']:
    print(f"   • {p['orden_compra']} | {p['cliente']} | cuota {p['cuota_num']} | ${p['monto']:,.2f}")

# ── Enviar a todos (destinatarios internos), como recordatorio ──
print("\nEnviando recordatorio consolidado...")
ok, msg = enviar_correo_consolidado(
    proveedor=g0['proveedor'],
    grupos=grupos_lista,  # todos los grupos, como un recordatorio general
)
print(f"Resultado: {msg}")
sys.exit(0 if ok else 1)