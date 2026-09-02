#!/usr/bin/env python3
"""Generate a minimal test HTML with the same data (no Chart.js dependency)."""
import csv, os, json, urllib.request
from collections import defaultdict, Counter

TSV_URL = "https://docs.google.com/spreadsheets/d/1kKq4y9ZtjmdacmEgQtMX64_puRNClibBOUd0in5TB6I/export?format=tsv&gid=1961588350"
TSV_PATH = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'latinbien_raw.tsv')

print("Downloading TSV...")
urllib.request.urlretrieve(TSV_URL, TSV_PATH)

with open(TSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f, delimiter='\t')
    rows = list(reader)

headers = rows[0]
col_idx = {h: i for i, h in enumerate(headers)}

STATUS_OP = col_idx.get('Status Operativo', 42)
CLIENTE = col_idx.get('Nombre del socio a mostrar en la Factura', 29)
TOTAL = col_idx.get('Total con signo', 44)
PAGADO = col_idx.get('Total pagado', 46)
TRABAJADOR = col_idx.get('Trabajador Profesional', 48)

ACTIVE_STATUSES = {'6. CVG - ENTREGADO', '4. SAV - APROBADO - ESPERA ENTREGA', '12. CONGELADO', '11. CAMBIO DE PLAN'}

def classify_worker(tipo):
    tipo_lower = tipo.lower().strip()
    if 'independ' in tipo_lower or 'informal' in tipo_lower:
        return 'Independiente'
    if 'publico' in tipo_lower: return 'Sector p\xfablico'
    if 'privado' in tipo_lower: return 'Sector privado'
    if 'depend' in tipo_lower or 'bajo_dependencia' in tipo_lower:
        return 'Dependientes'
    return 'No clasificado'

active_rows = []
for row in rows[1:]:
    if len(row) <= max(col_idx.values()):
        continue
    status = row[STATUS_OP].strip() if STATUS_OP < len(row) else ''
    if status in ACTIVE_STATUSES:
        try:
            total_val = float(row[TOTAL].replace(',', '')) if TOTAL < len(row) and row[TOTAL].strip() else 0
        except:
            total_val = 0
        try:
            pagado_val = float(row[PAGADO].replace(',', '')) if PAGADO < len(row) and row[PAGADO].strip() else 0
        except:
            pagado_val = 0
        active_rows.append({
            'cliente': row[CLIENTE].strip() if CLIENTE < len(row) else 'N/A',
            'total': total_val,
            'pagado': pagado_val,
            'trabajador': row[TRABAJADOR].strip().lower() if TRABAJADOR < len(row) and row[TRABAJADOR].strip() else 'desconocido',
        })

print(f"Active rows: {len(active_rows)}")

clients_dict = defaultdict(lambda: {'contratos': 0, 'facturado': 0.0, 'cobrado': 0.0, 'worker_types': Counter()})
for r in active_rows:
    c = r['cliente']
    clients_dict[c]['contratos'] += 1
    clients_dict[c]['facturado'] += r['total']
    clients_dict[c]['cobrado'] += r['pagado']
    clients_dict[c]['worker_types'][r['trabajador']] += 1

client_list = []
for c, d in clients_dict.items():
    primary_wt = d['worker_types'].most_common(1)[0][0] if d['worker_types'] else 'desconocido'
    segmento = classify_worker(primary_wt)
    client_list.append({
        'cliente': c,
        'contratos': d['contratos'],
        'facturado': round(d['facturado'], 2),
        'cobrado': round(d['cobrado'], 2),
        'saldo': round(d['facturado'] - d['cobrado'], 2),
        'segmento': segmento,
    })

client_list.sort(key=lambda x: -x['contratos'])

# Generate minimal HTML
html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>TEST MINIMAL - LATINBIEN</title>
</head>
<body style="background:#f0f2f5;font-family:sans-serif;padding:20px;">
    <div style="background:#213C83;color:white;padding:20px;border-radius:12px;margin-bottom:20px;">
        <h1>TEST MINIMAL - LATINBIEN</h1>
        <p>Sin dependencia de Chart.js - solo HTML + JS puro</p>
    </div>
    <div id="status"></div>
    <script>
const DATA = ''' + json.dumps({
    'clients': client_list,
    'total_facturado': sum(c['facturado'] for c in client_list),
    'total_cobrado': sum(c['cobrado'] for c in client_list),
    'client_count': len(client_list),
}, ensure_ascii=False) + ''';

const div = document.getElementById('status');
const totalFact = DATA.total_facturado;
const totalCob = DATA.total_cobrado;
const totalPen = totalFact - totalCob;

let html = `
    <div style="background:white;padding:20px;border-radius:12px;margin-bottom:20px;">
        <h2>KPIs</h2>
        <p>Clientes activos: <strong>${DATA.client_count}</strong></p>
        <p>Total facturado: <strong>$${totalFact.toFixed(2)}</strong></p>
        <p>Total cobrado: <strong>$${totalCob.toFixed(2)}</strong></p>
        <p>Saldo pendiente: <strong>$${totalPen.toFixed(2)}</strong></p>
    </div>
    <div style="background:white;padding:20px;border-radius:12px;">
        <h2>Top 10 Clientes</h2>
        <table style="width:100%;border-collapse:collapse;">
            <tr style="background:#f0f2f7;">
                <th style="padding:8px;text-align:left;">#</th>
                <th style="padding:8px;text-align:left;">Cliente</th>
                <th style="padding:8px;text-align:right;">Contratos</th>
                <th style="padding:8px;text-align:right;">Facturado</th>
                <th style="padding:8px;text-align:left;">Segmento</th>
            </tr>
            ${DATA.clients.slice(0,10).map((c,i) => `
                <tr style="border-bottom:1px solid #f0f0f0;">
                    <td style="padding:6px;">${i+1}</td>
                    <td style="padding:6px;">${c.cliente}</td>
                    <td style="padding:6px;text-align:right;">${c.contratos}</td>
                    <td style="padding:6px;text-align:right;">$${c.facturado.toFixed(2)}</td>
                    <td style="padding:6px;">${c.segmento}</td>
                </tr>
            `).join('')}
        </table>
    </div>
`;
div.innerHTML = html;
    </script>
</body>
</html>'''

out = 'C:\\Users\\yarleyc\\Documents\\New OpenCode Project\\test_minimal_final.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written to {out}")
print(f"Size: {os.path.getsize(out)} bytes")
print("Done!")
