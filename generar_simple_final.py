#!/usr/bin/env python3
"""Generate a clean simple HTML - no f-strings, minimum JS, static data baked in."""
import csv, os, json, urllib.request
from collections import defaultdict, Counter

TSV_URL = "https://docs.google.com/spreadsheets/d/1kKq4y9ZtjmdacmEgQtMX64_puRNClibBOUd0in5TB6I/export?format=tsv&gid=1961588350"
TSV_PATH = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'latinbien_raw.tsv')

print("Downloading...")
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
FECHA = col_idx.get('Fecha', 15)
TRABAJADOR = col_idx.get('Trabajador Profesional', 48)

ACTIVE_STATUSES = {'6. CVG - ENTREGADO', '4. SAV - APROBADO - ESPERA ENTREGA', '12. CONGELADO', '11. CAMBIO DE PLAN'}

def classify_worker(tipo):
    tipo_lower = tipo.lower().strip()
    if 'independ' in tipo_lower or 'informal' in tipo_lower:
        return 'Independiente'
    if 'publico' in tipo_lower: return 'Sector publico'
    if 'privado' in tipo_lower: return 'Sector privado'
    if 'depend' in tipo_lower or 'bajo_dependencia' in tipo_lower:
        return 'Dependientes'
    return 'No clasificado'

active_rows = []
status_counter = Counter()
for row in rows[1:]:
    if len(row) <= max(col_idx.values()):
        continue
    status = row[STATUS_OP].strip() if STATUS_OP < len(row) else ''
    status_counter[status] += 1
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
            'fecha': row[FECHA].strip() if FECHA < len(row) else '',
            'trabajador': row[TRABAJADOR].strip().lower() if TRABAJADOR < len(row) and row[TRABAJADOR].strip() else 'desconocido',
        })

clients_dict = defaultdict(lambda: {'contratos': 0, 'facturado': 0.0, 'cobrado': 0.0, 'fechas': [], 'worker_types': Counter()})
for r in active_rows:
    c = r['cliente']
    clients_dict[c]['contratos'] += 1
    clients_dict[c]['facturado'] += r['total']
    clients_dict[c]['cobrado'] += r['pagado']
    if r['fecha']:
        clients_dict[c]['fechas'].append(r['fecha'])
    clients_dict[c]['worker_types'][r['trabajador']] += 1

client_list = []
for c, d in clients_dict.items():
    primary_wt = d['worker_types'].most_common(1)[0][0] if d['worker_types'] else 'desconocido'
    segmento = classify_worker(primary_wt)
    fechas_sorted = sorted(d['fechas'])
    client_list.append({
        'cliente': c,
        'contratos': d['contratos'],
        'facturado': round(d['facturado'], 2),
        'cobrado': round(d['cobrado'], 2),
        'saldo': round(d['facturado'] - d['cobrado'], 2),
        'segmento': segmento,
        'first_date': fechas_sorted[0] if fechas_sorted else '',
        'last_date': fechas_sorted[-1] if fechas_sorted else '',
    })

client_list.sort(key=lambda x: -x['contratos'])

# Build JSON
data_json = json.dumps({
    'clients': client_list,
    'count': len(client_list),
    'total_facturado': sum(c['facturado'] for c in client_list),
    'total_cobrado': sum(c['cobrado'] for c in client_list),
}, ensure_ascii=False)

# Build HTML using string concatenation (NO f-strings, NO template strings)
html_parts = []
html_parts.append('<!DOCTYPE html>')
html_parts.append('<html lang="es">')
html_parts.append('<head>')
html_parts.append('    <meta charset="UTF-8">')
html_parts.append('    <title>LATINBIEN - Dashboard</title>')
html_parts.append('</head>')
html_parts.append('<body style="background:#f0f2f5;font-family:sans-serif;padding:30px;">')

# Header
html_parts.append('<div style="background:#213C83;color:white;padding:20px;border-radius:12px;margin-bottom:20px;">')
html_parts.append('    <h1>LATINBIEN | Analisis de Cartera</h1>')
html_parts.append('    <p>Contratos activos + montos + segmentacion</p>')
html_parts.append('</div>')

# Status div for JS to fill
html_parts.append('<div id="app">')
html_parts.append('    <p style="background:white;padding:20px;border-radius:12px;">')
html_parts.append('        Cargando datos...')
html_parts.append('    </p>')
html_parts.append('</div>')

# Script
html_parts.append('<script>')
html_parts.append('var DATA = ' + data_json + ';')
html_parts.append('')

# JS logic
html_parts.append('var app = document.getElementById("app");')
html_parts.append('var totalFact = DATA.total_facturado;')
html_parts.append('var totalCob = DATA.total_cobrado;')
html_parts.append('var totalPen = totalFact - totalCob;')
html_parts.append('')
html_parts.append('var html = "";')
html_parts.append('html += "<div style=\'background:white;padding:20px;border-radius:12px;margin-bottom:20px;\'">";')
html_parts.append('html += "<h2>Resumen</h2>";')
html_parts.append('html += "<p>Clientes activos: <strong>" + DATA.count + "</strong></p>";')
html_parts.append('html += "<p>Total facturado: <strong>$" + totalFact.toFixed(2) + "</strong></p>";')
html_parts.append('html += "<p>Total cobrado: <strong>$" + totalCob.toFixed(2) + "</strong></p>";')
html_parts.append('html += "<p>Saldo pendiente: <strong>$" + totalPen.toFixed(2) + "</strong></p>";')
html_parts.append('html += "</div>";')
html_parts.append('')
html_parts.append('html += "<div style=\'background:white;padding:20px;border-radius:12px;\'>";')
html_parts.append('html += "<h2>Top 10 Clientes</h2>";')
html_parts.append('html += "<table style=\'width:100%;border-collapse:collapse;\'>";')
html_parts.append('html += "<tr style=\'background:#f0f2f7;\'><th style=\'padding:8px;text-align:left;\'>#</th><th style=\'padding:8px;text-align:left;\'>Cliente</th><th style=\'padding:8px;text-align:right;\'>Contratos</th><th style=\'padding:8px;text-align:right;\'>Facturado</th><th style=\'padding:8px;text-align:left;\'>Segmento</th></tr>";')
html_parts.append('')
html_parts.append('for (var i = 0; i < Math.min(10, DATA.clients.length); i++) {')
html_parts.append('    var c = DATA.clients[i];')
html_parts.append('    html += "<tr style=\'border-bottom:1px solid #f0f0f0;\'>";')
html_parts.append('    html += "<td style=\'padding:6px;\'>" + (i+1) + "</td>";')
html_parts.append('    html += "<td style=\'padding:6px;\'>" + c.cliente + "</td>";')
html_parts.append('    html += "<td style=\'padding:6px;text-align:right;\'>" + c.contratos + "</td>";')
html_parts.append('    html += "<td style=\'padding:6px;text-align:right;\'>$" + c.facturado.toFixed(2) + "</td>";')
html_parts.append('    html += "<td style=\'padding:6px;\'>" + c.segmento + "</td>";')
html_parts.append('    html += "</tr>";')
html_parts.append('}')
html_parts.append('')
html_parts.append('html += "</table>";')
html_parts.append('html += "</div>";')
html_parts.append('')
html_parts.append('app.innerHTML = html;')
html_parts.append('console.log("Datos cargados: " + DATA.count + " clientes");')

html_parts.append('</script>')
html_parts.append('</body>')
html_parts.append('</html>')

final_html = '\n'.join(html_parts)

out = 'C:\\Users\\yarleyc\\Documents\\New OpenCode Project\\dashboard_simple.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(final_html)
print(f"Written to {out}")
print(f"Size: {os.path.getsize(out)} bytes")
print("Done!")
