#!/usr/bin/env python3
"""
Complete data processor for LATINBIEN dashboard.
Reads TSV from Google Sheets, filters active contracts, aggregates per client
with worker type classification, and generates embedded JSON for HTML.
"""
import csv, os, json, urllib.request
from collections import defaultdict, Counter
from datetime import datetime

TSV_URL = "https://docs.google.com/spreadsheets/d/1kKq4y9ZtjmdacmEgQtMX64_puRNClibBOUd0in5TB6I/export?format=tsv&gid=1961588350"
TSV_PATH = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'latinbien_raw.tsv')

# Download TSV
print("Downloading TSV...")
urllib.request.urlretrieve(TSV_URL, TSV_PATH)
print("Downloaded.")

# Read TSV
with open(TSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f, delimiter='\t')
    rows = list(reader)

print(f"Total rows: {len(rows)}")
headers = rows[0]
print(f"Headers ({len(headers)}): {[h for h in headers]}")

# Map column names to indices
col_idx = {h: i for i, h in enumerate(headers)}
print(f"\nColumn indices: {dict(col_idx)}")

# Key column indices
STATUS_OP_COL = col_idx.get('Status Operativo', 42)
CLIENTE_COL = col_idx.get('Nombre del socio a mostrar en la Factura', 29)
TOTAL_COL = col_idx.get('Total con signo', 44)
PAGADO_COL = col_idx.get('Total pagado', 46)
FECHA_COL = col_idx.get('Fecha', 15)
TRABAJADOR_COL = col_idx.get('Trabajador Profesional', 48)
SUCURSAL_COL = col_idx.get('Sucursal', 43)
NUMERO_COL = col_idx.get('Número', 30)
REF_COL = col_idx.get('Referencia', 37)

print(f"\nUsing columns: Status={STATUS_OP_COL}, Cliente={CLIENTE_COL}, Total={TOTAL_COL}, Pagado={PAGADO_COL}, Trabajador={TRABAJADOR_COL}")

# Active statuses (NOT cancelled)
ACTIVE_STATUSES = {
    '6. CVG - ENTREGADO',
    '4. SAV - APROBADO - ESPERA ENTREGA',
    '12. CONGELADO',
    '11. CAMBIO DE PLAN',
}
CANCELLED_STATUS = '8. CANCELACION TOTAL'

# Process data
status_counts = Counter()
active_rows = []
worker_type_values = set()

for row in rows[1:]:
    if len(row) <= max(col_idx.values()):
        continue
    
    status = row[STATUS_OP_COL].strip() if STATUS_OP_COL < len(row) else ''
    status_counts[status] += 1
    
    fecha_str = row[FECHA_COL].strip() if FECHA_COL < len(row) else ''
    
    if status in ACTIVE_STATUSES:
        active_rows.append({
            'status': status,
            'cliente': row[CLIENTE_COL].strip() if CLIENTE_COL < len(row) else 'N/A',
            'total': float(row[TOTAL_COL].replace(',', '')) if TOTAL_COL < len(row) and row[TOTAL_COL].strip() else 0,
            'pagado': float(row[PAGADO_COL].replace(',', '')) if PAGADO_COL < len(row) and row[PAGADO_COL].strip() else 0,
            'fecha': fecha_str,
            'trabajador': row[TRABAJADOR_COL].strip().lower() if TRABAJADOR_COL < len(row) and row[TRABAJADOR_COL].strip() else 'desconocido',
            'sucursal': row[SUCURSAL_COL].strip() if SUCURSAL_COL < len(row) else '',
            'numero': row[NUMERO_COL].strip() if NUMERO_COL < len(row) else '',
            'referencia': row[REF_COL].strip() if REF_COL < len(row) else '',
        })
        worker_type_values.add(active_rows[-1]['trabajador'])

print(f"\n=== Status distribution ===")
for s, c in sorted(status_counts.items(), key=lambda x: -x[1]):
    print(f"  {repr(s)}: {c}")

print(f"\n=== Active rows: {len(active_rows)} ===")
print(f"Worker types found: {sorted(worker_type_values)}")

# Worker type mapping for segmentation
WORKER_SEGMENTS = {
    'bajo_dependencia': 'Dependientes',
    'dependiente_publico': 'Sector público',
    'dependiente_privado': 'Sector privado',
    'independiente': 'Independiente',
    'independiente_formal': 'Independiente',
    'infdependiente_informal': 'Independiente',
}

# Fallback for unknown types: try to detect
def classify_worker(tipo):
    tipo_lower = tipo.lower().strip()
    if tipo_lower in WORKER_SEGMENTS:
        return WORKER_SEGMENTS[tipo_lower]
    if 'publico' in tipo_lower:
        return 'Sector público'
    if 'privado' in tipo_lower:
        return 'Sector privado'
    if 'depend' in tipo_lower:
        return 'Dependientes'
    if 'independ' in tipo_lower or 'informal' in tipo_lower:
        return 'Independiente'
    return 'No clasificado'

# Aggregate per client
clients = defaultdict(lambda: {
    'contratos': 0,
    'total_facturado': 0.0,
    'total_cobrado': 0.0,
    'fechas': [],
    'statuses': Counter(),
    'worker_types': Counter(),
    'referencias': [],
})

for r in active_rows:
    c = r['cliente']
    clients[c]['contratos'] += 1
    clients[c]['total_facturado'] += r['total']
    clients[c]['total_cobrado'] += r['pagado']
    if r['fecha']:
        clients[c]['fechas'].append(r['fecha'])
    clients[c]['statuses'][r['status']] += 1
    clients[c]['worker_types'][r['trabajador']] += 1
    clients[c]['referencias'].append(r['referencia'])

# Determine primary worker type per client
for c, data in clients.items():
    # Most common worker type among contracts
    if data['worker_types']:
        primary_wt = data['worker_types'].most_common(1)[0][0]
    else:
        primary_wt = 'desconocido'
    data['worker_type'] = primary_wt
    data['segmento'] = classify_worker(primary_wt)

# Sort clients by contract count descending
sorted_clients = sorted(clients.items(), key=lambda x: -x[1]['contratos'])

print(f"\n=== Client summary ===")
print(f"Total active clients: {len(clients)}")
print(f"Total active contracts: {sum(d['contratos'] for _, d in sorted_clients)}")
print(f"Total facturado: ${sum(d['total_facturado'] for _, d in sorted_clients):,.2f}")
print(f"Total cobrado: ${sum(d['total_cobrado'] for _, d in sorted_clients):,.2f}")

# Top 10 clients
print(f"\n=== Top 20 clients ===")
for c, d in sorted_clients[:20]:
    print(f"  {c}: {d['contratos']} contratos, ${d['total_facturado']:,.2f} fact, ${d['total_cobrado']:,.2f} cob, tipo={d['worker_type']}")

# Segment analysis
print(f"\n=== Segment analysis ===")
segment_stats = defaultdict(lambda: {'clientes': 0, 'contratos': 0, 'facturado': 0.0, 'cobrado': 0.0})
for c, d in clients.items():
    seg = d['segmento']
    segment_stats[seg]['clientes'] += 1
    segment_stats[seg]['contratos'] += d['contratos']
    segment_stats[seg]['facturado'] += d['total_facturado']
    segment_stats[seg]['cobrado'] += d['total_cobrado']

for seg, stats in sorted(segment_stats.items(), key=lambda x: -x[1]['contratos']):
    print(f"  {seg}: {stats['clientes']} clientes, {stats['contratos']} contratos, ${stats['facturado']:,.2f} fact, ${stats['cobrado']:,.2f} cob")

# Last 200 contracts analysis
print(f"\n=== Last 200 contracts by worker type ===")
# Sort active rows by fecha descending
active_rows_sorted = sorted(active_rows, key=lambda r: r['fecha'] if r['fecha'] else '', reverse=True)
last_200 = active_rows_sorted[:200]
wt_counter = Counter()
for r in last_200:
    seg = classify_worker(r['trabajador'])
    wt_counter[seg] += 1
print(f"Distribution in last 200 contracts:")
for seg, cnt in sorted(wt_counter.items(), key=lambda x: -x[1]):
    print(f"  {seg}: {cnt} ({cnt/2:.1f}%)")

# Generate the JSON data for embedding
output = {
    'status_summary': {s: c for s, c in sorted(status_counts.items(), key=lambda x: -x[1])},
    'active_count': len(active_rows),
    'cancelled_count': status_counts.get(CANCELLED_STATUS, 0),
    'total_rows': len(rows) - 1,
    'active_client_count': len(clients),
    'total_facturado': sum(d['total_facturado'] for _, d in sorted_clients),
    'total_cobrado': sum(d['total_cobrado'] for _, d in sorted_clients),
    'clients': [
        {
            'nombre': c,
            'contratos': d['contratos'],
            'facturado': round(d['total_facturado'], 2),
            'cobrado': round(d['total_cobrado'], 2),
            'worker_type': d['worker_type'],
            'segmento': d['segmento'],
            'fechas': sorted(d['fechas'])[:10] if d['fechas'] else [],
        }
        for c, d in sorted_clients
    ],
    'segment_stats': {
        seg: stats for seg, stats in sorted(segment_stats.items(), key=lambda x: -x[1]['contratos'])
    },
    'last_200': {
        'total': len(last_200),
        'by_segment': {seg: cnt for seg, cnt in sorted(wt_counter.items(), key=lambda x: -x[1])},
    },
}

# Write JSON file
json_path = os.path.join(os.path.dirname(__file__), 'dashboard_data.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\nJSON data written to {json_path}")
print(f"JSON size: {len(json.dumps(output, ensure_ascii=False))} chars")

print("\nDone!")
