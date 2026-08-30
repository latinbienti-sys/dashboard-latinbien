#!/usr/bin/env python3
"""Generate a clean dashboard - NO Chart.js, NO template literals, simple JS."""
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
TRABAJADOR = col_idx.get('Trabajador Profesional', 48)

ACTIVE_STATUSES = {'6. CVG - ENTREGADO', '4. SAV - APROBADO - ESPERA ENTREGA', '12. CONGELADO', '11. CAMBIO DE PLAN'}

def classify_worker(tipo):
    tl = tipo.lower().strip()
    if 'independ' in tl or 'informal' in tl: return 'Independiente'
    if 'publico' in tl: return 'Sector publico'
    if 'privado' in tl: return 'Sector privado'
    if 'depend' in tl or 'bajo_dependencia' in tl: return 'Dependientes'
    return 'No clasificado'

active_rows = []
for row in rows[1:]:
    if len(row) <= max(col_idx.values()): continue
    status = row[STATUS_OP].strip() if STATUS_OP < len(row) else ''
    if status in ACTIVE_STATUSES:
        try:
            total_val = float(row[TOTAL].replace(',', '')) if TOTAL < len(row) and row[TOTAL].strip() else 0
        except: total_val = 0
        try:
            pagado_val = float(row[PAGADO].replace(',', '')) if PAGADO < len(row) and row[PAGADO].strip() else 0
        except: pagado_val = 0
        active_rows.append({
            'cliente': row[CLIENTE].strip() if CLIENTE < len(row) else 'N/A',
            'total': total_val,
            'pagado': pagado_val,
            'trabajador': row[TRABAJADOR].strip().lower() if TRABAJADOR < len(row) and row[TRABAJADOR].strip() else 'desconocido',
        })

clients_dict = defaultdict(lambda: {'contratos': 0, 'facturado': 0.0, 'cobrado': 0.0, 'worker_types': Counter()})
for r in active_rows:
    cid = r['cliente']
    clients_dict[cid]['contratos'] += 1
    clients_dict[cid]['facturado'] += r['total']
    clients_dict[cid]['cobrado'] += r['pagado']
    clients_dict[cid]['worker_types'][r['trabajador']] += 1

client_list = []
for cid, d in clients_dict.items():
    primary_wt = d['worker_types'].most_common(1)[0][0] if d['worker_types'] else 'desconocido'
    client_list.append({
    'cliente': cid,
    'contratos': d['contratos'],
    'facturado': round(d['facturado'], 2),
    'cobrado': round(d['cobrado'], 2),
    'saldo': round(d['facturado'] - d['cobrado'], 2),
    'segmento': classify_worker(primary_wt),
    })

client_list.sort(key=lambda x: -x['contratos'])

data = {
    'total_clientes': len(client_list),
    'total_contratos': sum(c['contratos'] for c in client_list),
    'total_facturado': round(sum(c['facturado'] for c in client_list), 2),
    'total_cobrado': round(sum(c['cobrado'] for c in client_list), 2),
    'total_saldo': round(sum(c['saldo'] for c in client_list), 2),
    'top': client_list[:5],
}
data_json = json.dumps(data, ensure_ascii=False)

# Build HTML using simple string ops - NO f-strings for template
# Write each line explicitly

lines = []
lines.append('<!DOCTYPE html>')
lines.append('<html lang="es">')
lines.append('<head>')
lines.append('<meta charset="UTF-8">')
lines.append('<title>LATINBIEN - Dashboard</title>')
lines.append('<style>')
lines.append('body { background: #f0f2f5; font-family: Arial, sans-serif; padding: 20px; }')
lines.append('.card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }')
lines.append('.header { background: #213C83; color: white; padding: 20px; border-radius: 12px; }')
lines.append('.kpi { font-size: 24px; font-weight: bold; color: #213C83; }')
lines.append('table { width: 100%; border-collapse: collapse; }')
lines.append('th { background: #f0f2f7; padding: 8px; text-align: left; font-size: 12px; }')
lines.append('td { padding: 8px; border-bottom: 1px solid #eee; font-size: 13px; }')
lines.append('</style>')
lines.append('</head>')
lines.append('<body>')

lines.append('<div class="header">')
lines.append('<h1>LATINBIEN | Analisis de Cartera</h1>')
lines.append('<p>Datos de contratos activos</p>')
lines.append('</div>')

lines.append('<div class="card">')
lines.append('<h2>Resumen</h2>')
lines.append('<p>Total de clientes activos: <span class="kpi" id="kpiClientes">0</span></p>')
lines.append('<p>Total de contratos: <span class="kpi" id="kpiContratos">0</span></p>')
lines.append('<p>Total facturado: <span class="kpi" id="kpiFacturado">$0</span></p>')
lines.append('<p>Total cobrado: <span class="kpi" id="kpiCobrado">$0</span></p>')
lines.append('<p>Saldo pendiente: <span class="kpi" id="kpiSaldo">$0</span></p>')
lines.append('</div>')

lines.append('<div class="card">')
lines.append('<h2>Top 5 Clientes</h2>')
lines.append('<table><thead><tr><th>#</th><th>Cliente</th><th>Contratos</th><th>Facturado</th><th>Segmento</th></tr></thead>')
lines.append('<tbody id="tablaBody"></tbody>')
lines.append('</table>')
lines.append('</div>')

lines.append('<div class="card" id="statusCard">')
lines.append('<p>Cargando datos de JavaScript...</p>')
lines.append('</div>')

lines.append('<script>')
lines.append('var DATA = ' + data_json + ';')
lines.append('')
lines.append('document.getElementById("kpiClientes").textContent = DATA.total_clientes;')
lines.append('document.getElementById("kpiContratos").textContent = DATA.total_contratos;')
lines.append('document.getElementById("kpiFacturado").textContent = "$" + DATA.total_facturado.toLocaleString("en-US", {minimumFractionDigits:2});')
lines.append('document.getElementById("kpiCobrado").textContent = "$" + DATA.total_cobrado.toLocaleString("en-US", {minimumFractionDigits:2});')
lines.append('document.getElementById("kpiSaldo").textContent = "$" + DATA.total_saldo.toLocaleString("en-US", {minimumFractionDigits:2});')
lines.append('')
lines.append('var tbody = document.getElementById("tablaBody");')
lines.append('var html = "";')
lines.append('for (var i = 0; i < DATA.top.length; i++) {')
lines.append('  var c = DATA.top[i];')
lines.append('  html += "<tr>";')
lines.append('  html += "<td>" + (i+1) + "</td>";')
lines.append('  html += "<td>" + c.cliente + "</td>";')
lines.append('  html += "<td>" + c.contratos + "</td>";')
lines.append('  html += "<td>$" + c.facturado.toLocaleString("en-US", {minimumFractionDigits:2}) + "</td>";')
lines.append('  html += "<td>" + c.segmento + "</td>";')
lines.append('  html += "</tr>";')
lines.append('}')
lines.append('tbody.innerHTML = html;')
lines.append('')
lines.append('document.getElementById("statusCard").innerHTML = "<p style=color:green>Datos cargados correctamente: " + DATA.total_clientes + " clientes, " + DATA.total_contratos + " contratos</p>";')
lines.append('console.log("OK: " + DATA.total_clientes + " clientes cargados");')
lines.append('</script>')

lines.append('</body>')
lines.append('</html>')

final = '\r\n'.join(lines)

out = 'C:\\Users\\yarleyc\\Documents\\New OpenCode Project\\dashboard_final.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(final)
print(f"Written: {out}")
print(f"Size: {os.path.getsize(out)} bytes")
