import csv, os, json
from collections import defaultdict, Counter

temp_dir = os.environ['TEMP']
path = os.path.join(temp_dir, 'latinbien_raw.csv')

with open(path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

client_col = 'Nombre del socio a mostrar en la Factura'
total_col = 'Total con signo'
pagado_col = 'Total pagado'
status_op_col = 'Status Operativo'
fecha_col = 'Fecha'
ejecutivo_col = 'ejecutivo de ventas'
equipo_col = 'Equipo de ventas'

# Active statuses
active_statuses = {'6. CVG - ENTREGADO', '4. SAV - APROBADO - ESPERA ENTREGA', '12. CONGELADO', '11. CAMBIO DE PLAN'}

actual_rows = [r for r in rows if r.get(client_col, '').strip() and r.get(status_op_col, '').strip()]
print(f'Actual rows with status: {len(actual_rows)}')

# Active rows only
active_rows = [r for r in actual_rows if r.get(status_op_col, '') in active_statuses]
print(f'Active rows: {len(active_rows)}')

# Aggregate by client for ACTIVE rows
client_data = defaultdict(lambda: {'contratos': 0, 'total': 0.0, 'pagado': 0.0, 'fechas': []})

for r in active_rows:
    name = r.get(client_col, '').strip().upper()
    if not name: continue
    t_str = r.get(total_col, '0').replace(',', '').replace('"', '').strip()
    p_str = r.get(pagado_col, '0').replace(',', '').replace('"', '').strip()
    try: tv = float(t_str) if t_str else 0.0
    except: tv = 0.0
    try: pv = float(p_str) if p_str else 0.0
    except: pv = 0.0
    fech = r.get(fecha_col, '').strip()
    d = client_data[name]
    d['contratos'] += 1
    d['total'] += tv
    d['pagado'] += pv
    if fech:
        d['fechas'].append(fech)

print(f'Total active clients: {len(client_data)}')
print(f'Total active contracts: {sum(d["contratos"] for d in client_data.values())}')

# Build all clients sorted by contratos
by_contracts = sorted(client_data.items(), key=lambda x: x[1]['contratos'], reverse=True)

# Distribution
dist = Counter()
for name, d in client_data.items():
    c = d['contratos']
    if c >= 10: dist['10+'] += 1
    else: dist[str(c)] += 1

# Top 20
top20 = []
for i, (name, d) in enumerate(by_contracts[:20]):
    fechas = sorted(d['fechas'])
    first_date = fechas[0] if fechas else ''
    last_date = fechas[-1] if fechas else ''
    span_d = (__import__('datetime').datetime.strptime(last_date, '%Y-%m-%d') - __import__('datetime').datetime.strptime(first_date, '%Y-%m-%d')).days if first_date and last_date else 0
    span_m = round(span_d / 30.44, 1) if span_d else 0
    freq = round(span_d / (d['contratos'] - 1)) if d['contratos'] > 1 and span_d else 0
    pag_pct = round((d['pagado'] / d['total']) * 100, 1) if d['total'] else 0
    top20.append({
        'cliente': name,
        'contratos': d['contratos'],
        'total': round(d['total'], 2),
        'pagado': round(d['pagado'], 2),
        'saldo': round(d['total'] - d['pagado'], 2),
        'prom': round(d['total'] / d['contratos'], 2) if d['contratos'] else 0,
        'first': first_date,
        'last': last_date,
        'spanM': span_m,
        'freq': freq,
        'pagPct': pag_pct
    })

# Global stats
total_clientes = len(client_data)
total_contratos = sum(d['contratos'] for d in client_data.values())
total_facturado = sum(d['total'] for d in client_data.values())
total_cobrado = sum(d['pagado'] for d in client_data.values())
total_pendiente = total_facturado - total_cobrado

print(f'\n=== GLOBAL STATS (ACTIVE ONLY) ===')
print(f'Clientes: {total_clientes}')
print(f'Contratos activos: {total_contratos}')
print(f'Facturado: ${total_facturado:,.2f}')
print(f'Cobrado: ${total_cobrado:,.2f}')
print(f'Pendiente: ${total_pendiente:,.2f}')

print(f'\n=== DISTRIBUTION ===')
for k in sorted(dist.keys(), key=lambda x: int(x.replace('+', '')) if x != '10+' else 10):
    print(f'  {k} contrato(s): {dist[k]}')

print(f'\n=== TOP 20 ACTIVE ===')
for i, c in enumerate(top20):
    print(f'{i+1}. {c["cliente"][:45]}: {c["contratos"]} contratos, ${c["total"]:,.2f}, pagado {c["pagPct"]}%')

# Output JSON
output = {
    'totalClientes': total_clientes,
    'totalContratos': total_contratos,
    'totalFacturado': round(total_facturado, 2),
    'totalCobrado': round(total_cobrado, 2),
    'totalPendiente': round(total_pendiente, 2),
    'promedioContratos': round(total_contratos / total_clientes, 1),
    'promedioMonto': round(total_facturado / total_clientes, 2),
    'maxContratos': max(d['contratos'] for d in client_data.values()),
    'distribucion': sorted([{'rango': k, 'cantidad': v} for k, v in dist.items()], key=lambda x: int(x['rango'].replace('+', '')) if x['rango'] != '10+' else 10),
    'top20': top20,
    'allClients': []
}

# Add all clients (sorted by contratos desc)
for i, (name, d) in enumerate(by_contracts):
    fechas = sorted(d['fechas'])
    first_date = fechas[0] if fechas else ''
    last_date = fechas[-1] if fechas else ''
    span_d = (__import__('datetime').datetime.strptime(last_date, '%Y-%m-%d') - __import__('datetime').datetime.strptime(first_date, '%Y-%m-%d')).days if first_date and last_date else 0
    span_m = round(span_d / 30.44, 1) if span_d else 0
    freq = round(span_d / (d['contratos'] - 1)) if d['contratos'] > 1 and span_d else 0
    output['allClients'].append({
        'cliente': name,
        'contratos': d['contratos'],
        'total': round(d['total'], 2),
        'pagado': round(d['pagado'], 2),
        'saldo': round(d['total'] - d['pagado'], 2),
        'prom': round(d['total'] / d['contratos'], 2) if d['contratos'] else 0,
        'first': first_date,
        'last': last_date,
        'spanM': span_m,
        'freq': freq
    })

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clientes_data_activos.json'), 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\nJSON saved with {len(output["allClients"])} clients')
