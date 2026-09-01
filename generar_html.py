#!/usr/bin/env python3
"""Generate index.html with all corrected data embedded (no fetch needed)."""
import csv, os, json, urllib.request
from collections import defaultdict, Counter

TSV_URL = "https://docs.google.com/spreadsheets/d/1kKq4y9ZtjmdacmEgQtMX64_puRNClibBOUd0in5TB6I/export?format=tsv&gid=1961588350"
TSV_PATH = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'latinbien_raw.tsv')

# Download TSV
print("Downloading TSV...")
urllib.request.urlretrieve(TSV_URL, TSV_PATH)

with open(TSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f, delimiter='\t')
    rows = list(reader)

print(f"Total rows: {len(rows)}")
headers = rows[0]
col_idx = {h: i for i, h in enumerate(headers)}

STATUS_OP = col_idx.get('Status Operativo', 42)
CLIENTE = col_idx.get('Nombre del socio a mostrar en la Factura', 29)
TOTAL = col_idx.get('Total con signo', 44)
PAGADO = col_idx.get('Total pagado', 46)
FECHA = col_idx.get('Fecha', 15)
TRABAJADOR = col_idx.get('Trabajador Profesional', 48)
SUCURSAL = col_idx.get('Sucursal', 43)

ACTIVE_STATUSES = {'6. CVG - ENTREGADO', '4. SAV - APROBADO - ESPERA ENTREGA'}

def classify_worker(tipo):
    tipo_lower = tipo.lower().strip()
    # Check 'independ' BEFORE 'depend' since 'independ' contains 'depend'
    if 'independ' in tipo_lower or 'informal' in tipo_lower:
        return 'Independiente'
    if 'publico' in tipo_lower: return 'Sector público'
    if 'privado' in tipo_lower: return 'Sector privado'
    if 'depend' in tipo_lower: return 'Dependientes'
    if 'bajo_dependencia' in tipo_lower:
        return 'Dependientes'
    return 'No clasificado'

# Process active rows
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

print(f"Active rows: {len(active_rows)}")

# Aggregate per client
clients_dict = defaultdict(lambda: {'contratos': 0, 'facturado': 0.0, 'cobrado': 0.0, 'fechas': [], 'worker_types': Counter()})
for r in active_rows:
    c = r['cliente']
    clients_dict[c]['contratos'] += 1
    clients_dict[c]['facturado'] += r['total']
    clients_dict[c]['cobrado'] += r['pagado']
    if r['fecha']:
        clients_dict[c]['fechas'].append(r['fecha'])
    clients_dict[c]['worker_types'][r['trabajador']] += 1

# Primary worker type
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
        'prom': round(d['facturado'] / d['contratos'], 2) if d['contratos'] else 0,
        'worker_type': primary_wt,
        'segmento': segmento,
        'first_date': fechas_sorted[0] if fechas_sorted else '',
        'last_date': fechas_sorted[-1] if fechas_sorted else '',
    })

client_list.sort(key=lambda x: -x['contratos'])

# Distribution
dist = Counter()
for c in client_list:
    dist[c['contratos']] += 1
dist_labels = sorted(dist.keys())

# Segment stats
seg_stats = defaultdict(lambda: {'clientes': 0, 'contratos': 0, 'facturado': 0.0, 'cobrado': 0.0})
for c in client_list:
    s = c['segmento']
    seg_stats[s]['clientes'] += 1
    seg_stats[s]['contratos'] += c['contratos']
    seg_stats[s]['facturado'] += c['facturado']
    seg_stats[s]['cobrado'] += c['cobrado']

# Last 200 analysis
active_rows.sort(key=lambda r: r['fecha'] if r['fecha'] else '', reverse=True)
last_200 = active_rows[:200]
last200_seg = Counter()
for r in last_200:
    last200_seg[classify_worker(r['trabajador'])] += 1

# VIP clients (5+ contracts)
vip_clients = [c for c in client_list if c['contratos'] >= 5]
vip_clients.sort(key=lambda x: -x['contratos'])

# Build embedded data
data_js = {
    'status_summary': dict(status_counter.most_common()),
    'total_rows': len(rows) - 1,
    'client_count': len(client_list),
    'total_facturado': sum(c['facturado'] for c in client_list),
    'total_cobrado': sum(c['cobrado'] for c in client_list),
    'distribucion': [{'rango': k, 'cantidad': v} for k, v in sorted(dist.items())],
    'status_counts': {
        'Entregado': status_counter.get('6. CVG - ENTREGADO', 0),
        'Aprobado': status_counter.get('4. SAV - APROBADO - ESPERA ENTREGA', 0),
        'Cancelacion Total': status_counter.get('8. CANCELACION TOTAL', 0),
        'Congelado': status_counter.get('10. CONGELADO', 0) +
                     status_counter.get('12. CONGELADO', 0),
    },
    'clients': client_list,
    'segment_stats': {s: dict(v) for s, v in sorted(seg_stats.items(), key=lambda x: -x[1]['contratos'])},
    'last200': dict(last200_seg.most_common()),
    'vip': [{
        'cliente': c['cliente'],
        'cont': c['contratos'],
        'first': c['first_date'],
        'last': c['last_date'],
    } for c in vip_clients],
}

json_str = json.dumps(data_js, ensure_ascii=True)
json_escaped = json_str.replace('\\', '\\\\').replace("'", "\\'").replace('</', '<\\/')
# For debugging: first/last 2KB of the raw JSON
json_error_preview = json_str[:2000] + '\n\n... [TRUNCATED] ...\n\n' + json_str[-2000:]
json_error_preview = json_error_preview.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
print(f"JSON data size: {len(json_str)} chars")

# Date range for VIP
all_fechas = []
for c in client_list:
    if c['first_date']: all_fechas.append(c['first_date'])
    if c['last_date']: all_fechas.append(c['last_date'])
min_date = min(all_fechas) if all_fechas else '2023-01-01'
max_date = max(all_fechas) if all_fechas else '2026-12-31'

# Relationship distribution for VIP
relacion_labels = ['1-3 meses', '3-6 meses', '6-12 meses', '12-24 meses', '24+ meses']

# Generate HTML
# I'll write the HTML with the JSON embedded
html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis de Cartera - LATINBIEN</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --primary: #213C83; --primary-dark: #1a2f66; --primary-light: #3D6194;
            --accent: #F98B10; --success: #10b981; --danger: #ef4444;
            --bg-gray: #f0f2f5; --text-dark: #1a1a2e; --white: #ffffff;
        }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg-gray); color: var(--text-dark); padding: 30px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, #0f2a5a 100%);
            color: white; padding: 30px 40px; border-radius: 16px; margin-bottom: 28px;
            box-shadow: 0 8px 25px rgba(33,60,131,0.3); position: relative; overflow: hidden;
        }}
        .header::before {{
            content: ''; position: absolute; top: -50%; right: -20%;
            width: 500px; height: 500px;
            background: radial-gradient(circle, rgba(249,139,16,0.08) 0%, transparent 70%);
            border-radius: 50%;
        }}
        .header-content {{ display: flex; align-items: center; justify-content: space-between; gap: 25px; position: relative; z-index: 1; }}
        .header-logo {{ display: flex; align-items: center; gap: 18px; }}
        .header-logo img {{ height: 50px; width: auto; }}
        .header-logo .divider {{ width: 2px; height: 40px; background: rgba(255,255,255,0.2); }}
        .header-text h1 {{ font-size: 26px; font-weight: 800; letter-spacing: -0.5px; line-height: 1.2; }}
        .header-text h1 span {{ font-weight: 300; opacity: 0.85; }}
        .header-text p {{ font-size: 13px; opacity: 0.8; margin-top: 3px; }}
        .header-meta {{ display: flex; gap: 12px; flex-wrap: wrap; }}
        .header-meta .meta-item {{ background: rgba(255,255,255,0.12); padding: 7px 14px; border-radius: 10px; text-align: center; min-width: 90px; }}
        .header-meta .meta-item strong {{ display: block; font-size: 18px; color: var(--accent); }}
        .header-meta .meta-item span {{ font-size: 9px; opacity: 0.75; text-transform: uppercase; letter-spacing: 0.3px; }}
        .header-filter {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 8px 12px; background: rgba(255,255,255,0.08); border-radius: 10px; margin-top: 6px; }}
        .header-filter label {{ font-size: 11px; color: rgba(255,255,255,0.7); font-weight: 600; }}
        .header-filter input[type=date] {{ padding: 4px 8px; border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; font-size: 11px; background: rgba(255,255,255,0.9); }}
        .header-filter .btn-filtrar {{ padding: 4px 14px; background: var(--accent); color: white; border: none; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; }}
        .header-filter .btn-filtrar:hover {{ background: #e07d00; }}
        .header-filter .btn-reset {{ padding: 4px 10px; background: rgba(255,255,255,0.15); color: rgba(255,255,255,0.8); border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; font-size: 11px; cursor: pointer; }}
        .header-filter .btn-reset:hover {{ background: rgba(255,255,255,0.25); }}
        .header-filter .btn-refresh {{ padding: 4px 14px; background: #10b981; color: white; border: none; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; margin-left: 10px; transition: background 0.2s; }}
        .header-filter .btn-refresh:hover {{ background: #059669; }}
        .header-filter .btn-refresh.loading {{ opacity: 0.6; pointer-events: none; }}
        .header-filter .filtro-info {{ font-size: 10px; color: var(--accent); font-weight: 600; }}
        .status-entregado {{ display:inline-block; font-size:10px; font-weight:700; padding:2px 8px; border-radius:10px; background:#d1fae5; color:#065f46; white-space:nowrap; }}
        .status-aprobado {{ display:inline-block; font-size:10px; font-weight:700; padding:2px 8px; border-radius:10px; background:#dbeafe; color:#1e40af; white-space:nowrap; }}
        .status-cancelado {{ display:inline-block; font-size:10px; font-weight:700; padding:2px 8px; border-radius:10px; background:#fee2e2; color:#991b1b; white-space:nowrap; }}
        .status-congelado {{ display:inline-block; font-size:10px; font-weight:700; padding:2px 8px; border-radius:10px; background:#fef3c7; color:#92400e; white-space:nowrap; }}

        .kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin-bottom: 22px; }}
        .kpi-card {{ background: var(--white); border-radius: 14px; padding: 16px 14px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); text-align: center; border-top: 4px solid var(--primary-light); transition: transform 0.2s; }}
        .kpi-card:hover {{ transform: translateY(-3px); box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .kpi-card .number {{ font-size: 24px; font-weight: 800; color: var(--primary); }}
        .kpi-card .number.money {{ font-size: 20px; }}
        .kpi-card .label {{ font-size: 10px; color: #666; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.4px; }}
        .kpi-card.accent {{ border-top-color: var(--accent); }}
        .kpi-card.accent .number {{ color: var(--accent); }}
        .kpi-card.success {{ border-top-color: var(--success); }}
        .kpi-card.success .number {{ color: var(--success); }}
        .kpi-card.danger {{ border-top-color: var(--danger); }}
        .kpi-card.danger .number {{ color: var(--danger); }}

        .charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 22px; }}
        .chart-card {{ background: var(--white); border-radius: 14px; padding: 18px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
        .chart-card h3 {{ font-size: 14px; font-weight: 700; margin-bottom: 10px; color: var(--primary); text-align: center; }}
        .chart-card .chart-container {{ position: relative; height: 350px; }}
        .chart-card.full-width {{ grid-column: 1 / -1; }}
        .chart-card.full-width .chart-container {{ height: 260px; }}

        .filtros-card {{ background: var(--white); border-radius: 14px; padding: 16px 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 22px; display: flex; flex-wrap: wrap; align-items: center; gap: 14px; }}
        .filtros-card label {{ font-size: 12px; font-weight: 600; color: var(--primary); }}
        .filtros-card input[type="date"], .filtros-card input[type="number"], .filtros-card select {{ padding: 6px 10px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 12px; transition: border-color 0.3s; }}
        .filtros-card input[type="number"] {{ width: 80px; }}
        .filtros-card input:focus, .filtros-card select:focus {{ outline: none; border-color: var(--primary-light); }}
        .filtros-card .filtro-group {{ display: flex; align-items: center; gap: 6px; }}
        .filtros-card .btn-filtrar {{ padding: 6px 16px; background: var(--primary); color: white; border: none; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; transition: background 0.2s; }}
        .filtros-card .btn-filtrar:hover {{ background: var(--primary-dark); }}
        .filtros-card .btn-reset {{ padding: 6px 12px; background: #f0f0f0; color: #666; border: none; border-radius: 8px; font-size: 12px; cursor: pointer; }}
        .filtros-card .btn-reset:hover {{ background: #e0e0e0; }}
        .filtros-card .filtro-info {{ font-size: 12px; color: #888; margin-left: auto; }}

        .table-card {{ background: var(--white); border-radius: 14px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 28px; }}
        .table-card h3 {{ font-size: 15px; font-weight: 700; margin-bottom: 12px; color: var(--primary); }}
        .table-card .controls {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; }}
        .table-card .search-box input {{ padding: 7px 14px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 13px; width: 260px; max-width: 100%; }}
        .table-card .search-box input:focus {{ outline: none; border-color: var(--primary-light); }}
        .table-card .info {{ font-size: 12px; color: #888; }}
        .table-card .pagination {{ display: flex; gap: 4px; align-items: center; }}
        .table-card .pagination button {{ padding: 5px 12px; border: 1px solid #ddd; background: var(--white); border-radius: 6px; cursor: pointer; font-size: 12px; transition: all 0.2s; }}
        .table-card .pagination button:hover:not(:disabled) {{ background: var(--primary); color: var(--white); border-color: var(--primary); }}
        .table-card .pagination button:disabled {{ opacity: 0.4; cursor: default; }}
        .table-card .page-info {{ font-size: 12px; color: #888; }}
        .ciclo-btn {{ padding: 7px 18px; border: 2px solid var(--primary-light); background: var(--white); color: var(--primary); border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; }}
        .ciclo-btn.active {{ background: var(--primary); color: var(--white); border-color: var(--primary); }}
        .ciclo-btn:hover:not(.active) {{ background: #eef1f9; }}
        .mini-kpi {{ background: var(--white); border: 1px solid #e8eaef; border-left: 3px solid var(--primary); border-radius: 8px; padding: 10px 14px; }}
        .mini-kpi .mini-val {{ font-size: 18px; font-weight: 700; color: var(--primary); }}
        .mini-kpi .mini-lbl {{ font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.3px; }}
        .mini-kpi .mini-sub {{ font-size: 12px; color: #888; margin-top: 2px; }}
        .table-wrapper {{ overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        table thead th {{ background: #f0f2f7; padding: 9px 11px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.4px; color: var(--primary); border-bottom: 2px solid #e0e4ed; cursor: pointer; user-select: none; white-space: nowrap; }}
        table thead th:hover {{ background: #e6e9f0; }}
        table thead th .sort-icon {{ margin-left: 3px; opacity: 0.3; }}
        table thead th.sorted .sort-icon {{ opacity: 1; color: var(--accent); }}
        table tbody td {{ padding: 7px 11px; border-bottom: 1px solid #f0f0f0; font-size: 12px; }}
        table tbody tr:hover {{ background: #f8f9fc; }}
        table tbody tr.top-client td {{ background: #fef8f0; }}
        table tbody tr.rank-1 {{ border-left: 4px solid #D4A017; }}
        table tbody tr.rank-2 {{ border-left: 4px solid #A8A8A8; }}
        table tbody tr.rank-3 {{ border-left: 4px solid #CD7F32; }}
        .text-right {{ text-align: right !important; }}
        .text-center {{ text-align: center !important; }}
        .badge {{ display: inline-block; padding: 2px 9px; border-radius: 20px; font-size: 10px; font-weight: 600; }}
        .badge-gold {{ background: #fff3cd; color: #856404; }}
        .badge-silver {{ background: #e9ecef; color: #495057; }}
        .badge-bronze {{ background: #ffe8d6; color: #8b4513; }}
        .badge-blue {{ background: #dbeafe; color: #1e40af; }}
        .badge-gray {{ background: #f3f4f6; color: #6b7280; }}
        .clickable {{ cursor: pointer; }}
        .clickable:hover {{ background: #f0f4ff !important; }}
        .sub-table {{ background: #f8faff; }}
        .sub-table-inner {{ width: 100%; border-collapse: collapse; margin: 4px 0; }}
        .sub-table-inner thead th {{ background: #eef3fa; padding: 5px 10px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.3px; color: #555; border-bottom: 1px solid #dce3ef; }}
        .sub-table-inner tbody td {{ padding: 4px 10px; font-size: 11px; border-bottom: 1px solid #e8ecf5; }}
        .badge-green {{ background: #d1fae5; color: #065f46; }}
        .badge-red {{ background: #fde8e8; color: #dc2626; }}

        .footer {{ text-align: center; padding: 18px; color: #aaa; font-size: 11px; }}
        .footer strong {{ color: var(--primary); }}

        .tabs {{ display: flex; flex-direction: column; gap: 4px; margin-bottom: 20px; background: #e8eaf0; border-radius: 12px; padding: 4px; max-height: 600px; overflow-y: auto; }}
        .tab-btn {{ padding: 9px 16px; border: none; background: transparent; border-radius: 10px; font-size: 12px; font-weight: 600; color: #666; cursor: pointer; transition: all 0.2s; white-space: nowrap; text-align: left; }}
        .tab-btn:hover {{ color: var(--primary); }}
        .tab-btn.active {{ background: var(--white); color: var(--primary); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        .segment-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-bottom: 22px; }}
        .segment-card {{ background: var(--white); border-radius: 14px; padding: 18px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border-left: 4px solid var(--primary); }}
        .segment-card h4 {{ font-size: 14px; font-weight: 700; color: var(--primary); margin-bottom: 8px; }}
        .segment-card .stat {{ font-size: 12px; color: #555; margin: 3px 0; }}
        .segment-card .stat strong {{ color: var(--text-dark); }}

        @media (max-width: 900px) {{
            .charts-row {{ grid-template-columns: 1fr; }}
            .header-content {{ flex-direction: column; text-align: center; }}
            .header-logo {{ justify-content: center; }}
            .header-meta {{ justify-content: center; }}
            .header {{ padding: 22px 18px; }}
            .header-text h1 {{ font-size: 20px; }}
            body {{ padding: 14px; }}
            .table-card .controls {{ flex-direction: column; align-items: stretch; }}
            .table-card .search-box input {{ width: 100%; }}
            .filtros-card {{ flex-direction: column; align-items: stretch; }}
            .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
<div class="container" id="app">

    <div class="header">
        <div class="header-content">
            <div class="header-logo">
                <img src="https://latinbien.com/web/image/website/1/logo/LATINBIEN?unique=4695b15" alt="LATINBIEN"
                     onerror="this.style.display='none'">
                <div class="divider"></div>
                <div class="header-text">
                    <h1>LATINBIEN <span>| Análisis de Cartera</span></h1>
                    <p>Distribución de contratos activos + montos históricos + segmentación por tipo de trabajador</p>
                </div>
            </div>
            <div class="header-meta">
                <div class="meta-item"><strong id="hClientes">—</strong><span>Clientes act.</span></div>
                <div class="meta-item"><strong id="hContratos">—</strong><span>Contratos act.</span></div>
                <div class="meta-item"><strong id="hFacturado">—</strong><span>Facturado</span></div>
                <div class="meta-item"><strong id="hPendiente">—</strong><span>Pendiente</span></div>
            </div>
        </div>
        <div class="header-filter">
            <label>📅 Filtrar por fecha:</label>
            <input type="date" id="filtroFechaDesde">
            <span style="color:rgba(255,255,255,0.5);font-size:11px">→</span>
            <input type="date" id="filtroFechaHasta">
            <button class="btn-filtrar" onclick="aplicarFiltroGlobal()">Aplicar</button>
            <button class="btn-reset" onclick="resetFiltroGlobal()">Limpiar</button>
            <span class="filtro-info" id="filtroInfoGlobal"></span>
            <button class="btn-refresh" onclick="actualizarDashboard(this)" title="Forzar actualización desde Odoo">🔄 Actualizar ahora</button>
            <span id="ultimaActualizacion" style="margin-left:10px;font-size:10px;color:rgba(255,255,255,0.5)"></span>
        </div>
    </div>

    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('gestion')">📋 Gestión Cobranza</button>
        <button class="tab-btn" onclick="switchTab('expedientes')">🗂️ Expedientes</button>
        <button class="tab-btn" onclick="switchTab('prontopago')">⚡ Pronto Pago</button>
        <button class="tab-btn" onclick="switchTab('ventas_motos')">🏍️ Ventas Motos</button>
        <button class="tab-btn" onclick="switchTab('pago_proveedor')">💰 Pago Proveedor</button>
        <button class="tab-btn" onclick="switchTab('resumen')">📊 Resumen</button>
        <button class="tab-btn" onclick="switchTab('pagos')">💳 Plan de Pagos</button>
        <button class="tab-btn" onclick="switchTab('ciclos')">📅 Ciclos</button>
        <button class="tab-btn" onclick="switchTab('montos')">💰 Montos</button>
        <button class="tab-btn" onclick="switchTab('segmentos')">👥 Segmentos</button>
        <button class="tab-btn" onclick="switchTab('temporal')">⏱ Temporal VIP</button>
        <button class="tab-btn" onclick="switchTab('tabla')">📋 Listado</button>
        <button class="tab-btn" onclick="switchTab('factjulio')">📋 Fact. Julio</button>
    </div>

    <!-- TAB 1: RESUMEN -->
    <div class="tab-content active" id="tab-resumen">
        <div class="kpi-row">
            <div class="kpi-card"><div class="number" id="kpi1">—</div><div class="label">Clientes 1 contrato</div></div>
            <div class="kpi-card"><div class="number" id="kpi2">—</div><div class="label">Clientes 2 contratos</div></div>
            <div class="kpi-card accent"><div class="number" id="kpi3">—</div><div class="label">Clientes 3+ contratos</div></div>
            <div class="kpi-card accent"><div class="number" id="kpi4">—</div><div class="label">Clientes 5+ (VIP)</div></div>
        </div>
        <div class="charts-row">
            <div class="chart-card"><h3>🏆 Top 20 Clientes</h3><div class="chart-container"><canvas id="chartTop20"></canvas></div></div>
            <div class="chart-card"><h3>📊 Distribución de Contratos (activos)</h3><div class="chart-container"><canvas id="chartDist"></canvas></div></div>
        </div>
        <div class="charts-row">
            <div class="chart-card full-width"><h3>📊 Facturas Emitidas por Status</h3><div class="chart-container"><canvas id="chartStatus"></canvas></div></div>
        </div>
    </div>

    <!-- TAB 2: MONTOS HISTÓRICOS -->
    <div class="tab-content" id="tab-montos">
        <div class="kpi-row">
            <div class="kpi-card"><div class="number" id="mkpiClientes">—</div><div class="label">Total Clientes</div></div>
            <div class="kpi-card"><div class="number" id="mkpiContratos">—</div><div class="label">Total Contratos</div></div>
            <div class="kpi-card accent"><div class="number money" id="mkpiFacturado">—</div><div class="label">Facturado</div></div>
            <div class="kpi-card success"><div class="number money" id="mkpiCobrado">—</div><div class="label">Cobrado</div></div>
            <div class="kpi-card danger"><div class="number money" id="mkpiPendiente">—</div><div class="label">Saldo Pendiente</div></div>
            <div class="kpi-card"><div class="number" id="mkpiPromContratos">—</div><div class="label">Prom Contratos</div></div>
            <div class="kpi-card accent"><div class="number money" id="mkpiPromMonto">—</div><div class="label">Prom $ x Cliente</div></div>
            <div class="kpi-card"><div class="number" id="mkpiMaxContratos">—</div><div class="label">Máx Contratos</div></div>
        </div>
        <div class="filtros-card">
            <label>🔍 Filtrar:</label>
            <div class="filtro-group"><span>Monto mín:</span><input type="number" id="filtroMontoMin" placeholder="0" step="100"></div>
            <div class="filtro-group"><span>Contratos mín:</span><input type="number" id="filtroContratosMin" placeholder="0" step="1"></div>
            <div class="filtro-group">
                <span>Estado:</span>
                <select id="filtroEstado"><option value="todos">Todos</option><option value="pagado">Pagado / Cancelado</option><option value="pendiente">Con saldo pendiente</option></select>
            </div>
            <button class="btn-filtrar" onclick="aplicarFiltrosMontos()">Aplicar</button>
            <button class="btn-reset" onclick="resetFiltrosMontos()">Limpiar</button>
            <span class="filtro-info" id="filtroInfoMontos">Mostrando todos</span>
        </div>
        <div class="charts-row">
            <div class="chart-card"><h3>💰 Top 20 por Monto Facturado</h3><div class="chart-container"><canvas id="chartTopMonto"></canvas></div></div>
            <div class="chart-card"><h3>📦 Top 20 por Contratos</h3><div class="chart-container"><canvas id="chartTopContratos"></canvas></div></div>
        </div>
        <div class="charts-row">
            <div class="chart-card"><h3>💵 Distribución por Monto</h3><div class="chart-container"><canvas id="chartDistMontos"></canvas></div></div>
            <div class="chart-card"><h3>🧩 Estado de Cartera</h3><div class="chart-container"><canvas id="chartCarteraPie"></canvas></div></div>
        </div>
    </div>

    <!-- TAB 3: SEGMENTOS -->
    <div class="tab-content" id="tab-segmentos">
        <div class="kpi-row" id="segmentKpis"></div>
        <div class="charts-row">
            <div class="chart-card"><h3>👥 Distribución por Segmento</h3><div class="chart-container"><canvas id="chartSegPie"></canvas></div></div>
            <div class="chart-card"><h3>💰 Facturado por Segmento</h3><div class="chart-container"><canvas id="chartSegFact"></canvas></div></div>
        </div>
        <div class="charts-row">
            <div class="chart-card full-width"><h3>📊 Últimos 200 Contratos por Tipo de Trabajador</h3><div class="chart-container"><canvas id="chartLast200"></canvas></div></div>
        </div>
        <div class="table-card" id="segmentDetalle">
            <h3>📋 Detalle por Segmento</h3>
            <div id="segmentTableWrap"></div>
        </div>
    </div>

    <!-- TAB 4: TEMPORAL VIP -->
    <div class="tab-content" id="tab-temporal">
        <div class="kpi-row">
            <div class="kpi-card accent"><div class="number" id="tmpVipCount">—</div><div class="label">Clientes VIP (5+ contratos)</div></div>
            <div class="kpi-card"><div class="number" id="tmpAvgSpan">—</div><div class="label">Promedio relación (meses)</div></div>
            <div class="kpi-card"><div class="number" id="tmpAvgFreq">—</div><div class="label">Frecuencia entre compras (días)</div></div>
            <div class="kpi-card accent"><div class="number" id="tmpMaxSpan">—</div><div class="label">Mayor antigüedad (meses)</div></div>
        </div>
        <div class="charts-row">
            <div class="chart-card"><h3>⏱ Línea de Tiempo — Clientes VIP</h3><div class="chart-container"><canvas id="chartTimeline"></canvas></div></div>
            <div class="chart-card"><h3>📆 Distribución por Tiempo de Relación</h3><div class="chart-container"><canvas id="chartRelacion"></canvas></div></div>
        </div>
        <div class="table-card">
            <h3>🏆 Top 10 VIP — Detalle Temporal</h3>
            <div class="table-wrapper">
                <table id="tablaTemporal">
                    <thead><tr><th>#</th><th>Cliente</th><th>Contratos</th><th>1ra Fecha</th><th>Últ Fecha</th><th>Días</th><th>Meses</th></tr></thead>
                    <tbody id="tbodyTemporal"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- TAB 5: LISTADO -->
    <div class="tab-content" id="tab-tabla">
        <div class="table-card">
            <h3>📋 Listado Completo de Clientes Activos</h3>
            <div class="controls">
                <div class="search-box"><input type="text" id="searchInput" placeholder="Buscar cliente..." oninput="filterTable()"></div>
                <span id="segFilterLabel" style="display:none;font-size:12px;color:var(--primary);font-weight:600;margin-left:8px"></span>
                <button id="clearSegFilter" style="display:none;font-size:11px;padding:3px 10px;border:1px solid #ccc;border-radius:5px;background:white;cursor:pointer;margin-left:4px" onclick="clearSegmentFilter()">✕ Limpiar filtro</button>
                <div class="info">Mostrando <span id="showing">0</span> de <span id="totalRows">0</span> clientes</div>
                <div class="pagination">
                    <button onclick="changePage(-1)" id="prevBtn" disabled>◀ Anterior</button>
                    <span class="page-info" id="pageInfo">Página 1 / 1</span>
                    <button onclick="changePage(1)" id="nextBtn" disabled>Siguiente ▶</button>
                </div>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)" class="sorted"># <span class="sort-icon">▲</span></th>
                            <th onclick="sortTable(1)">Cliente <span class="sort-icon">⇅</span></th>
                            <th onclick="sortTable(2)" class="sorted">Contratos <span class="sort-icon">▲</span></th>
                            <th onclick="sortTable(3)">Facturado <span class="sort-icon">⇅</span></th>
                            <th onclick="sortTable(4)">Cobrado <span class="sort-icon">⇅</span></th>
                            <th onclick="sortTable(5)">Saldo <span class="sort-icon">⇅</span></th>
                            <th onclick="sortTable(6)">Promedio <span class="sort-icon">⇅</span></th>
                            <th onclick="sortTable(7)">Segmento <span class="sort-icon">⇅</span></th>
                            <th onclick="sortTable(8)">Categoría <span class="sort-icon">⇅</span></th>
                        </tr>
                    </thead>
                    <tbody id="tableBody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- TAB 6: PLAN DE PAGOS -->
    <div class="tab-content" id="tab-pagos">
        <!-- BANNER DE ALERTAS -->
        <div id="alertasBanner" style="display:none;margin-bottom:16px;border-radius:12px;overflow:hidden">
            <div style="background:linear-gradient(135deg,#dc2626,#991b1b);color:white;padding:16px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap">
                <div style="font-size:32px">🚨</div>
                <div style="flex:1;min-width:200px">
                    <div style="font-size:18px;font-weight:700" id="alertasTitulo">ALERTAS DE MOROSIDAD</div>
                    <div style="font-size:12px;opacity:0.8;font-style:italic" id="alertasSubtitulo">Vista interna — sin acciones automáticas</div>
                </div>
                <div style="display:flex;gap:12px;flex-wrap:wrap">
                    <div style="background:rgba(255,255,255,0.2);padding:8px 14px;border-radius:8px;text-align:center">
                        <div style="font-size:22px;font-weight:800" id="alertasCriticos">0</div>
                        <div style="font-size:10px;opacity:0.8">CRÍTICOS</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.2);padding:8px 14px;border-radius:8px;text-align:center">
                        <div style="font-size:22px;font-weight:800" id="alertasAltos">0</div>
                        <div style="font-size:10px;opacity:0.8">ALTOS</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.15);padding:8px 14px;border-radius:8px;text-align:center">
                        <div style="font-size:22px;font-weight:800" id="alertasMedios">0</div>
                        <div style="font-size:10px;opacity:0.8">MEDIOS</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.15);padding:8px 14px;border-radius:8px;text-align:center">
                        <div style="font-size:22px;font-weight:800" id="alertasBajos">0</div>
                        <div style="font-size:10px;opacity:0.8">BAJOS</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.15);padding:8px 14px;border-radius:8px;text-align:center">
                        <div style="font-size:22px;font-weight:800" id="alertasMonto">—</div>
                        <div style="font-size:10px;opacity:0.8">EN RIESGO</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="kpi-row">
            <div class="kpi-card danger"><div class="number money" id="pkTotalVencido">—</div><div class="label">Total Vencido</div></div>
            <div class="kpi-card accent"><div class="number money" id="pkTotalDebido">—</div><div class="label">Total Debido (al día)</div></div>
            <div class="kpi-card success"><div class="number money" id="pkTotalPagado">—</div><div class="label">Total Pagado</div></div>
        </div>
        <div class="charts-row">
            <div class="chart-card"><h3>📊 Estado de Cuotas</h3><div class="chart-container" style="height:250px"><canvas id="chartPagosState"></canvas></div></div>
            <div class="chart-card"><h3>📅 Proyección de Cobros (Debido)</h3><div class="chart-container" style="height:250px"><canvas id="chartProyeccion"></canvas></div></div>
        </div>
            <div class="table-card">
            <h3>⚠️ Clientes con Cuotas Vencidas</h3>
            <div style="margin:8px 0;font-size:13px;color:#666">Total vencido: <strong id="pkVencidoTotal">—</strong> — <span id="pkVencidosCount">—</span> clientes afectados</div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Cliente</th>
                            <th class="text-right">Cuotas Vencidas</th>
                            <th class="text-right">Monto Vencido</th>
                            <th>Status</th>
                            <th>Facturas</th>
                        </tr>
                    </thead>
                    <tbody id="tablaVencidos"></tbody>
                </table>
            </div>
        </div>

        <!-- FACTURAS ENTREGADAS VENCIDAS -->
        <div class="table-card" style="border-color:#2563eb">
            <h3>🚚 Facturas Entregadas con Cuotas Vencidas</h3>
            <div style="margin:8px 0;font-size:13px;color:#666">Total: <strong id="evFacturasCount">—</strong> facturas · <strong id="evMontoTotal">—</strong> · <strong id="evCuotasCount">—</strong> cuotas vencidas</div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Factura</th>
                            <th>Cliente</th>
                            <th>Fecha Factura</th>
                            <th class="text-right">Cuotas Venc.</th>
                            <th class="text-right">Monto Vencido</th>
                            <th>Última Cuota</th>
                            <th class="text-right">Días Mora</th>
                        </tr>
                    </thead>
                    <tbody id="tablaEntregadasVenc"></tbody>
                </table>
            </div>
        </div>

        <!-- ÚLTIMAS ENTREGAS REALIZADAS + MOROSIDAD DEL CLIENTE -->
        <div class="table-card" style="border-color:#7c3aed">
            <h3>📦 Últimas Entregas Realizadas — ¿Quién está Moroso?</h3>
            <div style="margin:8px 0;font-size:13px;color:#666"><strong id="ueEntregas">—</strong> entregas revisadas · <strong id="ueMorosos">—</strong> clientes morosos · <strong id="ueMonto">—</strong> vencido acumulado</div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Factura</th>
                            <th>Cliente</th>
                            <th>Fecha Entrega</th>
                            <th class="text-right">Vencido del Cliente</th>
                            <th class="text-right">Facturas en Mora</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody id="tablaUltimasEntregas"></tbody>
                </table>
            </div>
            <div style="margin-top:8px;font-size:11px;color:#888">El vencido del cliente incluye TODAS sus facturas, no solo esta entrega. Resalta clientes que reciben mercancía ya teniendo deudas.</div>
        </div>

        <!-- CICLO DE PAGO (dentro del tab) -->
        <div class="table-card">
            <h3>📆 Ciclo de Pago — Análisis por Día</h3>
            <div id="cicloMañana" onclick="mostrarManana()" style="background:linear-gradient(135deg,#e8f5e9,#c8e6c9);border:2px solid #43a047;border-radius:12px;padding:16px;margin-bottom:10px;display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;cursor:pointer;transition:transform 0.15s;hover:transform:scale(1.01)">
                <div><div style="font-size:12px;color:#2e7d32;font-weight:600" id="mananaLabel">📅 MAÑANA — DÍA <span id="mananaDia">25</span></div><div style="font-size:22px;font-weight:800;color:#1b5e20" id="mananaTotal">$0</div><div style="font-size:11px;color:#555">Total a percibir — haz clic para ver clientes</div></div>
                <div><div style="font-size:12px;color:#2e7d32;font-weight:600">👥 Clientes</div><div style="font-size:22px;font-weight:800;color:#1b5e20" id="mananaClientes">0</div><div style="font-size:11px;color:#555">que deben pagar</div></div>
                <div><div style="font-size:12px;color:#c62828;font-weight:600">⚠️ Vencido</div><div style="font-size:22px;font-weight:800;color:#c62828" id="mananaVencido">$0</div><div style="font-size:11px;color:#555">arrastrado</div></div>
                <div><div style="font-size:12px;color:#1565c0;font-weight:600">✅ Histórico Cobrado</div><div style="font-size:22px;font-weight:800;color:#1565c0" id="mananaPagado">$0</div><div style="font-size:11px;color:#555">en este día</div></div>
            </div>
            <!-- RESUMEN POR CICLO -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px">
                <div id="cicloResumen0318" style="background:white;border-radius:12px;padding:14px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-left:4px solid #213C83">
                    <div style="font-size:13px;font-weight:700;color:#213C83;margin-bottom:8px">📊 Ciclo 03 – 18</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
                        <div><div style="font-size:10px;color:#888">Debido</div><div style="font-size:16px;font-weight:700;color:#10b981" id="res0318Debido">$0</div></div>
                        <div><div style="font-size:10px;color:#888">Vencido</div><div style="font-size:16px;font-weight:700;color:#ef4444" id="res0318Vencido">$0</div></div>
                        <div><div style="font-size:10px;color:#888">Pagado</div><div style="font-size:16px;font-weight:700;color:#213C83" id="res0318Pagado">$0</div></div>
                    </div>
                </div>
                <div id="cicloResumen1025" style="background:white;border-radius:12px;padding:14px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-left:4px solid #e07d00">
                    <div style="font-size:13px;font-weight:700;color:#e07d00;margin-bottom:8px">📊 Ciclo 10 – 25</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
                        <div><div style="font-size:10px;color:#888">Debido</div><div style="font-size:16px;font-weight:700;color:#10b981" id="res1025Debido">$0</div></div>
                        <div><div style="font-size:10px;color:#888">Vencido</div><div style="font-size:16px;font-weight:700;color:#ef4444" id="res1025Vencido">$0</div></div>
                        <div><div style="font-size:10px;color:#888">Pagado</div><div style="font-size:16px;font-weight:700;color:#e07d00" id="res1025Pagado">$0</div></div>
                    </div>
                </div>
            </div>
            <!-- Lista de clientes de mañana -->
            <div id="mananaClientesSection" style="margin-bottom:16px;display:none">
                <h4 style="font-size:14px;font-weight:700;color:var(--primary);margin:0 0 8px 0">📋 Clientes que pagan mañana <span id="mananaClientesSubtotal" style="font-size:12px;color:#666;font-weight:400"></span></h4>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Cliente</th>
                                <th class="text-right">$ Debido</th>
                                <th class="text-right">$ Vencido</th>
                                <th class="text-right">$ Total</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="tablaClientesManana"></tbody>
                    </table>
                </div>
            </div>
            <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
                <button class="ciclo-btn active" data-rango="03-18" onclick="renderCiclo('03-18')">Ciclo 03 – 18</button>
                <button class="ciclo-btn" data-rango="10-25" onclick="renderCiclo('10-25')">Ciclo 10 – 25</button>
            </div>
            <div id="cicloResumen" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:14px"></div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Día</th>
                            <th class="text-right">Debidas</th>
                            <th class="text-right">$ Debido</th>
                            <th class="text-right">Vencidas</th>
                            <th class="text-right">$ Vencido</th>
                            <th class="text-right">Días Mora Ø</th>
                            <th class="text-right">Pagadas</th>
                            <th class="text-right">$ Pagado</th>
                        </tr>
                    </thead>
                    <tbody id="tablaCiclo"></tbody>
                </table>
            </div>
            <div style="margin-top:18px;border-top:1px solid #e8eaef;padding-top:14px">
                <h4 id="cicloClientesTitle" style="font-size:14px;font-weight:700;color:var(--primary);margin-bottom:6px">👥 Clientes del Día</h4>
                <div id="cicloClientesResumen" style="margin-bottom:10px"></div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Cliente</th>
                                <th class="text-right">Cuotas Debidas</th>
                                <th class="text-right">$ Debido</th>
                                <th class="text-right">Vencidas</th>
                                <th class="text-right">$ Vencido</th>
                                <th class="text-right">$ Pagado</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="tablaClientesDia"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ALERTAS DE MOROSIDAD DETALLADAS -->
        <div class="results-section" id="seccionAlertas" style="display:none">
            <h3>🚨 Alertas de Morosidad — Clientes con Cuotas Atrasadas</h3>
            <p style="color:#666;margin:0 0 12px"><strong>Vista interna de consideración.</strong> No se ejecuta ninguna acción automática ni se contacta clientes. Solo fines informativos.</p>
            <p style="color:#666;margin:0 0 12px"><strong>CRÍTICO:</strong> &gt;90 días &nbsp;|&nbsp; <strong>ALTO:</strong> 30-90 días &nbsp;|&nbsp; <strong>MEDIO:</strong> 7-30 días &nbsp;|&nbsp; <strong>BAJO:</strong> 1-7 días</p>
            <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
                <button onclick="filtrarAlertas('todos')" style="padding:6px 14px;border-radius:6px;border:1px solid #ccc;background:#fff;cursor:pointer;font-size:12px" class="btn-alerta active">Todos</button>
                <button onclick="filtrarAlertas('critico')" style="padding:6px 14px;border-radius:6px;border:1px solid #dc2626;background:#fef2f2;cursor:pointer;font-size:12px;color:#dc2626">🔴 Crítico</button>
                <button onclick="filtrarAlertas('alto')" style="padding:6px 14px;border-radius:6px;border:1px solid #ea580c;background:#fff7ed;cursor:pointer;font-size:12px;color:#ea580c">🟠 Alto</button>
                <button onclick="filtrarAlertas('medio')" style="padding:6px 14px;border-radius:6px;border:1px solid #d97706;background:#fffbeb;cursor:pointer;font-size:12px;color:#d97706">🟡 Medio</button>
                <button onclick="filtrarAlertas('bajo')" style="padding:6px 14px;border-radius:6px;border:1px solid #0ea5e9;background:#f0f9ff;cursor:pointer;font-size:12px;color:#0ea5e9">🔵 Bajo</button>
            </div>
            <div class="table-container">
                <table class="data-table" id="tblAlertas">
                    <thead>
                        <tr>
                            <th>Severidad</th>
                            <th>Cliente</th>
                            <th class="text-right">Días Atraso</th>
                            <th class="text-right">$ Vencido</th>
                            <th class="text-right">Cuotas</th>
                            <th>Factura Más Antigua</th>
                            <th>Acción Sugerida</th>
                        </tr>
                    </thead>
                    <tbody id="tablaAlertas"></tbody>
                </table>
            </div>
        </div>

        <!-- COBRANZA VENCIDA CON COMPROMISO -->
        <div class="results-section" id="seccionCompromiso" style="display:none">
            <h3>📋 Facturas Vencidas con Compromiso de Pago</h3>
            <p style="color:#666;margin:0 0 12px">Facturas vencidas que tienen actividades/compromisos registrados en Odoo. Solo informativo.</p>
            <div class="kpi-row" style="margin-bottom:12px">
                <div class="kpi-card warning"><div class="number" id="compFacturas">—</div><div class="label">Facturas con Compromiso</div></div>
                <div class="kpi-card danger"><div class="number money" id="compMonto">—</div><div class="label">$ Monto Vencido</div></div>
                <div class="kpi-card danger"><div class="number" id="compOverdue">—</div><div class="label">Compromisos Vencidos</div></div>
                <div class="kpi-card success"><div class="number" id="compPlanned">—</div><div class="label">Compromisos Vigentes</div></div>
            </div>
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Estado</th>
                            <th>Factura</th>
                            <th>Cliente</th>
                            <th class="text-right">Días Atraso</th>
                            <th class="text-right">$ Vencido</th>
                            <th>Próximo Compromiso</th>
                            <th>Responsable</th>
                            <th>Detalle</th>
                        </tr>
                    </thead>
                    <tbody id="tablaCompromiso"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- TAB 7: FACTURACIÓN JULIO -->
    <div class="tab-content" id="tab-factjulio">
        <div class="kpi-row">
            <div class="kpi-card success"><div class="number money" id="fjTotalFacturado">—</div><div class="label">Total Facturado</div></div>
            <div class="kpi-card accent"><div class="number money" id="fjTotalProductos">—</div><div class="label">Total Productos</div></div>
            <div class="kpi-card warning"><div class="number money" id="fjTotalAdmin">—</div><div class="label">Gasto Admin.</div></div>
            <div class="kpi-card warning"><div class="number money" id="fjTotalAdminTotal">—</div><div class="label">Gasto Admin. (Sin Dcto)</div></div>
            <div class="kpi-card danger"><div class="number money" id="fjTotalCosto">—</div><div class="label">Costo Total</div></div>
            <div class="kpi-card success"><div class="number money" id="fjTotalMargen">—</div><div class="label">Margen Bruto</div></div>
            <div class="kpi-card"><div class="number" id="fjTotalFacturas">—</div><div class="label">Facturas</div></div>
            <div class="kpi-card"><div class="number" id="fjTotalClientes">—</div><div class="label">Clientes</div></div>
            <div class="kpi-card danger"><div class="number money" id="fjCancelacionesMonto">—</div><div class="label" id="fjCancelacionesLbl">Cancelaciones</div></div>
        </div>

        <!-- CUENTAS COLABORADORAS CON DSCTO EN GASTO ADMIN -->
        <div class="results-section">
            <h3>🤝 Cuentas Colaboradoras — Descuento 30% en Gasto Admin.</h3>
            <div style="margin:8px 0;font-size:13px;color:#666">Son las órdenes de cuentas colaboradoras que reflejan el <strong>descuento del 30%</strong> en el gasto administrativo.</div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Factura</th>
                            <th>Cliente</th>
                            <th class="text-right">Gasto Admin. (Sin Dcto)</th>
                            <th class="text-right">Dcto</th>
                            <th class="text-right">Gasto Admin. (Real)</th>
                        </tr>
                    </thead>
                    <tbody id="tablaColaboradores"></tbody>
                </table>
            </div>
        </div>

        <!-- GRAFICO RESUMEN FACT. JULIO -->
        <div class="results-section">
            <h3>📊 Resumen — Total Facturado, Productos, Gasto Admin. y Costos</h3>
            <div class="charts-row">
                <div class="chart-card full-width">
                    <h3>💰 Totales Fact. Julio 2026</h3>
                    <div class="chart-container"><canvas id="chartResumenJulio"></canvas></div>
                </div>
</div>
    </div>

    <!-- DESCUENTOS POR FACTURA -->
    <div class="results-section">
        <h3>🏷️ Descuentos aplicados por factura (Julio 2026)</h3>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Factura</th>
                        <th>Cliente</th>
                        <th class="text-right">Dcto Producto</th>
                        <th class="text-right">Dcto Gasto Admin</th>
                        <th class="text-right">Total Dcto</th>
                    </tr>
                </thead>
                <tbody id="tablaDescuentos"></tbody>
            </table>
        </div>
    </div>

    <!-- EJECUTIVOS -->
        <div class="results-section">
            <h3>👔 Desglose por Ejecutivo de Ventas</h3>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Ejecutivo</th>
                            <th class="text-right">Facturas</th>
                            <th class="text-right">Total Facturado</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody id="tablaEjecutivos"></tbody>
                </table>
            </div>
        </div>

        <!-- TOP PRODUCTOS -->
        <div class="results-section">
            <h3>🏆 Productos Más Vendidos</h3>
            <div class="charts-row">
                <div class="chart-card">
                    <h3>📦 Cantidad Vendida — Julio 2026</h3>
                    <div class="chart-container"><canvas id="chartTopProductosQty"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3>💰 Facturación por Producto — Julio 2026</h3>
                    <div class="chart-container"><canvas id="chartTopProductos"></canvas></div>
                </div>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Producto</th>
                            <th class="text-right">Cantidad</th>
                            <th class="text-right">Veces</th>
                            <th class="text-right">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody id="tablaTopProductos"></tbody>
                </table>
            </div>
        </div>

        <!-- DETALLE POR FACTURA -->
        <div class="results-section">
            <h3>📋 Detalle por Factura</h3>
            <div style="margin:8px 0;font-size:13px;color:#666">Cada factura desglosada: producto (Total − Gasto Admin), gasto administrativo, costo y margen</div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Cliente</th>
                            <th>Factura</th>
                            <th>Status Op.</th>
                            <th>Compra</th>
                            <th>Ejecutivo</th>
                            <th class="text-right">Total</th>
                            <th class="text-right">Producto</th>
                            <th class="text-right">Gasto Admin</th>
                            <th class="text-right">Costo</th>
                            <th class="text-right">Margen</th>
                        </tr>
                    </thead>
                    <tbody id="tablaFactJulio"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- TAB: FACTURACIÓN AGOSTO 2026 -->
    <div class="tab-content" id="tab-factagosto">
        <div class="kpi-row">
            <div class="kpi-card success"><div class="number money" id="faTotalFacturado">—</div><div class="label">Total Facturado</div></div>
            <div class="kpi-card accent"><div class="number money" id="faTotalProductos">—</div><div class="label">Total Productos</div></div>
            <div class="kpi-card warning"><div class="number money" id="faTotalAdmin">—</div><div class="label">Gasto Admin.</div></div>
            <div class="kpi-card danger"><div class="number money" id="faTotalCosto">—</div><div class="label">Costo Total</div></div>
            <div class="kpi-card success"><div class="number money" id="faTotalMargen">—</div><div class="label">Margen Bruto</div></div>
            <div class="kpi-card"><div class="number" id="faTotalFacturas">—</div><div class="label">Facturas</div></div>
            <div class="kpi-card"><div class="number" id="faTotalClientes">—</div><div class="label">Clientes</div></div>
            <div class="kpi-card danger"><div class="number money" id="faCancelacionesMonto">—</div><div class="label" id="faCancelacionesLbl">Cancelaciones</div></div>
        </div>
        <div class="results-section">
            <h3>📋 Detalle Facturación Agosto 2026</h3>
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Orden</th>
                            <th>Cliente</th>
                            <th>Ejecutivo</th>
                            <th class="text-right">Monto</th>
                            <th class="text-right">Costo</th>
                            <th>Fecha</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="tablaFactAgosto"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- TAB: ANÁLISIS OPERATIVO AGOSTO 2026 -->
    <div class="tab-content" id="tab-ago_operativo">
        <!-- KPIs RESUMEN -->
        <div class="kpi-row">
            <div class="kpi-card success"><div class="number" id="aoTotal">—</div><div class="label">Total Tareas</div></div>
            <div class="kpi-card accent"><div class="number" id="aoCompletadas">—</div><div class="label">Completadas</div></div>
            <div class="kpi-card warning"><div class="number" id="aoEnCurso">—</div><div class="label">En Curso</div></div>
            <div class="kpi-card danger"><div class="number" id="aoBloqueadas">—</div><div class="label">Bloqueadas</div></div>
            <div class="kpi-card"><div class="number" id="aoNoIniciadas">—</div><div class="label">No Iniciadas</div></div>
            <div class="kpi-card success"><div class="number" id="aoPctCompletadas">—</div><div class="label">% Completadas</div></div>
            <div class="kpi-card accent"><div class="number" id="aoPctEnCurso">—</div><div class="label">% En Curso</div></div>
            <div class="kpi-card danger"><div class="number" id="aoPctBloqueadas">—</div><div class="label">% Bloqueadas</div></div>
        </div>

        <!-- GRÁFICO DESEMPENO GENERAL -->
        <div class="results-section">
            <h3>📈 Informe de Desempeño — Agosto 2026</h3>
            <div class="charts-row">
                <div class="chart-card">
                    <h3>🎯 Distribución por Estado</h3>
                    <div class="chart-container"><canvas id="chartAoEstado"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3>⚡ Desempeño por Prioridad</h3>
                    <div class="chart-container"><canvas id="chartAoPrioridad"></canvas></div>
                </div>
            </div>
        </div>

        <!-- GRÁFICO PORCENTUAL DE PRIORIDAD -->
        <div class="results-section">
            <h3>📊 Relación Porcentual por Prioridad</h3>
            <div class="charts-row">
                <div class="chart-card full-width">
                    <h3>📋 % Completadas vs En Curso vs Bloqueadas por Prioridad</h3>
                    <div class="chart-container"><canvas id="chartAoPriBar"></canvas></div>
                </div>
            </div>
        </div>

        <!-- ANÁLISIS OPERATIVO DETALLADO -->
        <div class="results-section">
            <h3>🔍 Análisis Operativo Detallado</h3>
            <div style="margin:8px 0;font-size:13px;color:#666">Desglose de tareas por estado y prioridad con porcentajes de avance.</div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Prioridad</th>
                            <th class="text-right">Total</th>
                            <th class="text-right">Completadas</th>
                            <th class="text-right">% Comp.</th>
                            <th class="text-right">En Curso</th>
                            <th class="text-right">Bloqueadas</th>
                            <th class="text-right">No Iniciadas</th>
                            <th>Avance</th>
                        </tr>
                    </thead>
                    <tbody id="tablaAoPrioridad"></tbody>
                </table>
            </div>
        </div>

        <!-- LISTADO DE TAREAS -->
        <div class="results-section">
            <h3>📋 Listado de Tareas — Agosto 2026</h3>
            <div style="margin:8px 0;font-size:13px;color:#666">Todas las tareas del mes con su estado, prioridad y porcentaje de avance.</div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Tarea</th>
                            <th>Prioridad</th>
                            <th>Propietario</th>
                            <th>Estado</th>
                            <th>Inicio</th>
                            <th>Fin</th>
                            <th class="text-right">Avance</th>
                            <th>Notas</th>
                        </tr>
                    </thead>
                    <tbody id="tablaAoTareas"></tbody>
                </table>
            </div>
        </div>

        <!-- GRÁFICO LÍNEA DE TIEMPO -->
        <div class="results-section">
            <h3>📅 Línea de Tiempo — Inicios y Finalizaciones</h3>
            <div class="charts-row">
                <div class="chart-card full-width">
                    <h3>📆 Tareas por Fecha de Inicio</h3>
                    <div class="chart-container"><canvas id="chartAoTimeline"></canvas></div>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 8: EXPEDIENTES (Credit Lines Aprobadas) -->
    <div class="tab-content" id="tab-expedientes">
        <div class="kpi-row">
            <div class="kpi-card success"><div class="number" id="expTotalLineas">—</div><div class="label">Líneas Crédito</div></div>
            <div class="kpi-card accent"><div class="number money" id="expTotalMonto">—</div><div class="label">Total Monto</div></div>
            <div class="kpi-card"><div class="number" id="expUsadas">—</div><div class="label">Usadas</div></div>
            <div class="kpi-card warning"><div class="number" id="expNoUsadas">—</div><div class="label">No Usadas</div></div>
            <div class="kpi-card danger"><div class="number" id="expCaducadas">—</div><div class="label">Caducadas</div></div>
            <div class="kpi-card"><div class="number" id="expMenor3K">—</div><div class="label">&lt; $3,000</div></div>
            <div class="kpi-card"><div class="number" id="exp3K6K">—</div><div class="label">$3K-$6K</div></div>
            <div class="kpi-card"><div class="number" id="expMayor6K">—</div><div class="label">&gt; $6,000</div></div>
        </div>

        <!-- GRAFICO: Lineas por año/mes segmentado por rango -->
        <div class="results-section">
            <h3>📊 Líneas de Crédito Aprobadas por Año/Mes — Segmentado por Rango</h3>
            <div class="charts-row">
                <div class="chart-card full-width">
                    <h3>💰 Distribución por Rango y Mes</h3>
                    <div class="chart-container"><canvas id="chartExpedientes"></canvas></div>
                </div>
            </div>
        </div>

        <!-- DETALLE EXPEDIENTES: relacion por año/mes -->
        <div class="results-section">
            <h3>🗂️ Relación de Expedientes por Año/Mes</h3>
            <div style="margin:8px 0;font-size:13px;color:#666">Líneas de crédito aprobadas (Resolución final: "7. Linea de Credito Aprobada"), segmentadas por rango y con estado de uso/caducidad.</div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Año</th>
                            <th>Mes</th>
                            <th class="text-right">&lt; $3,000</th>
                            <th class="text-right">$3K-$6K</th>
                            <th class="text-right">&gt; $6,000</th>
                            <th class="text-right">Total Clientes</th>
                            <th class="text-right">Total Monto</th>
                            <th class="text-right">Usadas</th>
                            <th class="text-right">No Usadas</th>
                            <th class="text-right">Caducadas</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody id="tablaExpedientes"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ═══ TAB: PRONTO PAGO ═══ -->
    <div class="tab-content" id="tab-prontopago">
        <div class="kpi-row">
            <div class="kpi-card success"><div class="number" id="ppClientes">—</div><div class="label">Clientes</div></div>
            <div class="kpi-card accent"><div class="number money" id="ppMonto">—</div><div class="label">Total Pagado Adelantado</div></div>
            <div class="kpi-card"><div class="number" id="ppCuotas">—</div><div class="label">Cuotas Pagadas</div></div>
        </div>
        <div class="kpi-row">
            <div class="kpi-card"><div class="number money" id="ppPromedio">—</div><div class="label">Monto Promedio / Cliente</div></div>
            <div class="kpi-card accent"><div class="number" id="ppDias">—</div><div class="label">Días Anticipación (Ponderado)</div></div>
            <div class="kpi-card"><div class="number" id="ppPenetracion">—</div><div class="label">Penetración % del Total</div></div>
        </div>
        <div class="kpi-row">
            <div class="kpi-card" style="background:linear-gradient(135deg,#fef3c7,#fde68a);border:2px solid #f59e0b"><div class="number" id="ppOro">—</div><div class="label">🏆 Prioridad ORO</div></div>
            <div class="kpi-card" style="background:linear-gradient(135deg,#e5e7eb,#d1d5db);border:2px solid #9ca3af"><div class="number" id="ppPlata">—</div><div class="label">🥈 Prioridad PLATA</div></div>
            <div class="kpi-card" style="background:linear-gradient(135deg,#fed7aa,#fdba74);border:2px solid #f97316"><div class="number" id="ppBronce">—</div><div class="label">🥉 Prioridad BRONCE</div></div>
        </div>

        <!-- Top 10 Impacto en Flujo -->
        <div class="results-section">
            <h3>📊 Top 10 Clientes por Impacto en Flujo de Caja</h3>
            <div class="chart-container" style="height:320px"><canvas id="chartTop10PP"></canvas></div>
        </div>

        <!-- Tabla con flags de priorización -->
        <div class="results-section">
            <h3>⚡ Clientes Pronto Pago — Acciones de Priorización</h3>
            <p style="color:#666;margin:0 0 12px"><strong>🏆 ORO:</strong> ejecutivo preferencial + factura prioritaria + extensión de términos &nbsp;|&nbsp; <strong>🥈 PLATA:</strong> prioridad en entregas + descuento próximo servicio &nbsp;|&nbsp; <strong>🥉 BRONCE:</strong> reconocimiento + beneficio fidelidad</p>
            <div class="table-container">
                <table class="data-table" id="tblProntoPago">
                    <thead>
                        <tr>
                            <th>Prioridad</th>
                            <th>Cliente</th>
                            <th class="text-right">Cuotas</th>
                            <th class="text-right">Monto Pagado</th>
                            <th>Facturas</th>
                            <th>Fecha Más Lejana</th>
                            <th class="text-right">Días Adelantado</th>
                            <th>Acción Sugerida</th>
                        </tr>
                    </thead>
                    <tbody id="tablaProntoPago"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ═══ TAB: PROYECCIÓN POR CICLOS ═══ -->
    <div class="tab-content" id="tab-ciclos">
        <div class="kpi-row">
            <div class="kpi-card accent"><div class="number" id="ciclo0318Clientes">—</div><div class="label">Ciclo 03-18 Clientes</div></div>
            <div class="kpi-card success"><div class="number money" id="ciclo0318Pagado">—</div><div class="label">03-18 Pagado (Ago)</div></div>
            <div class="kpi-card danger"><div class="number money" id="ciclo0318Pendiente">—</div><div class="label">03-18 Pendiente (Ago)</div></div>
            <div class="kpi-card accent"><div class="number" id="ciclo1025Clientes">—</div><div class="label">Ciclo 10-25 Clientes</div></div>
            <div class="kpi-card success"><div class="number money" id="ciclo1025Pagado">—</div><div class="label">10-25 Pagado (Ago)</div></div>
            <div class="kpi-card danger"><div class="number money" id="ciclo1025Pendiente">—</div><div class="label">10-25 Pendiente (Ago)</div></div>
        </div>

        <div class="results-section">
            <h3>📅 Ciclo 03-18 — Cuotas Pagadas vs Pendientes por Mes</h3>
            <div class="chart-container" style="height:320px"><canvas id="chartCiclo0318"></canvas></div>
        </div>

        <div class="results-section">
            <h3>📅 Ciclo 10-25 — Cuotas Pagadas vs Pendientes por Mes</h3>
            <div class="chart-container" style="height:320px"><canvas id="chartCiclo1025"></canvas></div>
        </div>

        <!-- PROYECCIÓN POR FECHA DE COBRO -->
        <div class="results-section">
            <h3>💰 Proyección de Ingreso por Fecha de Cobro</h3>
            <p style="color:#666;margin:0 0 12px">Monto proyectado a recibir en cada fecha de cobro vs. lo que ya pagaron antes de la fecha.</p>
            <div class="chart-container" style="height:350px"><canvas id="chartFechaCobro"></canvas></div>
            <div class="table-container" style="margin-top:16px">
                <table class="data-table" id="tblFechaCobro">
                    <thead>
                        <tr>
                            <th>Mes</th>
                            <th>Día</th>
                            <th>Ciclo</th>
                            <th class="text-right">$ Pendiente Recibir</th>
                            <th class="text-right">Clientes Adeudan</th>
                            <th class="text-right">$ Ya Pagaron</th>
                            <th class="text-right">Clientes Pagaron</th>
                            <th class="text-right">$ Total Esperado</th>
                        </tr>
                    </thead>
                    <tbody id="tablaFechaCobro"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ═══ TAB: GESTIÓN DE COBRANZA POR CICLO ═══ -->
    <div class="tab-content" id="tab-gestion">
            <div class="kpi-row">
            <div class="kpi-card accent"><div class="number" id="gTotal0318">—</div><div class="label">Ciclo 03-18 Pendientes</div></div>
            <div class="kpi-card danger"><div class="number money" id="gPend0318">—</div><div class="label">03-18 Monto</div></div>
            <div class="kpi-card accent"><div class="number" id="gTotal1025">—</div><div class="label">Ciclo 10-25 Pendientes</div></div>
            <div class="kpi-card danger"><div class="number money" id="gPend1025">—</div><div class="label">10-25 Monto</div></div>
        </div>
        <div class="results-section">
            <h3>📋 Gestión de Cobranza por Ciclo — Segmentación por Fase</h3>
            <p style="color:#666;margin:0 0 12px">Cuotas de clientes con status <strong>Entregado</strong> y <strong>Aprobado</strong>. Segmentadas por ciclo (03-18 / 10-25), fase (2 días antes, día del ciclo, después) y estado (pagado/pendiente).</p>
            <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
                <strong>Ciclo:</strong>
                <button onclick="filtrarGestion('todos')" style="padding:6px 14px;border-radius:6px;border:1px solid #ccc;background:#fff;cursor:pointer;font-size:12px" class="btn-gestion active">Todos</button>
                <button onclick="filtrarGestion('03-18')" style="padding:6px 14px;border-radius:6px;border:1px solid #213C83;background:#dbeafe;cursor:pointer;font-size:12px;color:#213C83">03-18</button>
                <button onclick="filtrarGestion('10-25')" style="padding:6px 14px;border-radius:6px;border:1px solid #9d174d;background:#fce7f3;cursor:pointer;font-size:12px;color:#9d174d">10-25</button>
                <strong style="margin-left:12px">Estado:</strong>
                <button onclick="filtrarGestionEstado('todos')" style="padding:6px 14px;border-radius:6px;border:1px solid #ccc;background:#fff;cursor:pointer;font-size:12px" class="btn-estado active">Todos</button>
                <button onclick="filtrarGestionEstado('pendiente')" style="padding:6px 14px;border-radius:6px;border:1px solid #ef4444;background:#fef2f2;cursor:pointer;font-size:12px;color:#ef4444">Pendientes</button>
                <button onclick="filtrarGestionEstado('pagado')" style="padding:6px 14px;border-radius:6px;border:1px solid #10b981;background:#d1fae5;cursor:pointer;font-size:12px;color:#10b981">Pagados</button>
                <strong style="margin-left:12px">Fase:</strong>
                <select id="filtroFase" onchange="aplicarFiltrosGestion()" style="padding:6px 10px;border-radius:6px;border:1px solid #ccc;font-size:12px">
                    <option value="todas">Todas</option>
                    <option value="2_dias_antes">2 días antes</option>
                    <option value="1_dia_antes">1 día antes</option>
                    <option value="dia_ciclo">Día del ciclo</option>
                    <option value="1_dia_despues">1 día después</option>
                    <option value="2_dias_despues">2+ días después</option>
                </select>
                <strong style="margin-left:12px">Fecha:</strong>
                <input type="date" id="filtroFecha" onchange="aplicarFiltrosGestion()" style="padding:6px 10px;border-radius:6px;border:1px solid #ccc;font-size:12px">
                <button onclick="exportarGestionXLSX()" style="padding:6px 14px;border-radius:6px;border:1px solid #059669;background:#d1fae5;cursor:pointer;font-size:12px;color:#059669;margin-left:auto">📥 Exportar XLSX</button>
            </div>
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Ciclo</th>
                            <th>Fase</th>
                            <th>Estado</th>
                            <th>Cliente</th>
                            <th>Factura</th>
                            <th>Fecha Pago</th>
                            <th class="text-right">Monto</th>
                            <th class="text-right">Días</th>
                        </tr>
                    </thead>
                    <tbody id="tablaGestion"></tbody>
                </table>
            </div>
            <div style="margin-top:8px;color:#666;font-size:12px" id="gContador"></div>
        </div>
    </div>

    <!-- ═══ TAB: VENTAS MOTOS ═══ -->
    <div class="tab-content" id="tab-ventas_motos">
        <div class="kpi-row">
            <div class="kpi-card accent"><div class="number" id="vmTotal">—</div><div class="label">Órdenes Motos</div></div>
            <div class="kpi-card success"><div class="number money" id="vmMonto">—</div><div class="label">Monto Total Facturado</div></div>
            <div class="kpi-card"><div class="number" id="vmMotos">—</div><div class="label">Motos Vendidas</div></div>
            <div class="kpi-card accent"><div class="number money" id="vmProducto">—</div><div class="label">Precio Producto</div></div>
            <div class="kpi-card"><div class="number money" id="vmGasto">—</div><div class="label">Gasto Admin</div></div>
        </div>
        <div class="results-section">
            <h3>📋 Órdenes Publicadas de Motos</h3>
            <p style="color:#666;margin:0 0 12px">Solo órdenes de venta publicadas (state=sale). Precio producto y gasto administrativo por separado.</p>
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Orden</th>
                            <th>Cliente</th>
                            <th>CREDIMOTO</th>
                            <th>Modelo</th>
                            <th class="text-right">Precio Moto</th>
                            <th class="text-right">Gasto Admin</th>
                            <th class="text-right">Total</th>
                            <th>Mes</th>
                        </tr>
                    </thead>
                    <tbody id="tablaOrdenesMotos"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ═══ TAB: PAGO PROVEEDOR MOTO ═══ -->
    <div class="tab-content" id="tab-pago_proveedor">
        <div class="kpi-row">
            <div class="kpi-card" style="background:linear-gradient(135deg,#dbeafe,#93c5fd);border:2px solid #2563eb"><div class="number" style="font-size:18px;font-weight:800;color:#1e40af" id="ppmOrdenCompra">P01382</div><div class="label">Pedido de Compra</div></div>
            <div class="kpi-card accent"><div class="number" id="ppmProvedor">—</div><div class="label">Proveedor</div></div>
            <div class="kpi-card"><div class="number" id="ppmOrdenes">—</div><div class="label">Órdenes Venta</div></div>
            <div class="kpi-card success"><div class="number money" id="ppmInicial">—</div><div class="label">40% Inicial</div></div>
            <div class="kpi-card"><div class="number money" id="ppmFinanciado">—</div><div class="label">60% Financiado</div></div>
        </div>
        <div class="results-section">
            <h3>💰 Pedido de Compra P01382 — MOTO CITY PRO, C.A.</h3>
            <p style="color:#666;margin:0 0 12px"><strong>40% Inicial:</strong> pagadero al momento de facturación y entrega. &nbsp;|&nbsp; <strong>60% Restante:</strong> 8 cuotas quincenales según ciclo del cliente. &nbsp;|&nbsp; <strong>Opción A:</strong> días 5 y 20 &nbsp;|&nbsp; <strong>Opción B:</strong> días 12 y 27</p>
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Orden</th>
                            <th>Cliente</th>
                            <th>Modelo</th>
                            <th>Ciclo</th>
                            <th>Opción</th>
                            <th class="text-right">Precio Moto</th>
                            <th class="text-right">40% Inicial</th>
                            <th class="text-right">60% Restante</th>
                            <th class="text-right">Cuota Quincenal</th>
                        </tr>
                    </thead>
                    <tbody id="tablaPagoProveedor"></tbody>
                </table>
            </div>
        </div>
        <div class="results-section">
            <h3>📅 Cronograma de Pagos (8 cuotas quincenales)</h3>
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Orden</th>
                            <th>Cliente</th>
                            <th>Cuota</th>
                            <th>Fecha Pago</th>
                            <th class="text-right">Monto</th>
                            <th>Estado</th>
                            <th>Acción</th>
                        </tr>
                    </thead>
                    <tbody id="tablaCronograma"></tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="footer">
        <strong>LATINBIEN</strong> — Latinoamericana de Bienes y Servicios, C.A. &nbsp;·&nbsp;
        Generado el <span id="fechaGeneracion"></span>
    </div>

<script>
// ================================================================
//  DATA — EMBEDDED (no fetch needed, works with file://)
// ================================================================
var DATA;
try {{ DATA = JSON.parse('{json_escaped}'); }} catch(e) {{ DATA = null; console.error('DATA parse error:', e); }}

if (!DATA) {{
    document.write('<div style="padding:40px;font-family:sans-serif"><h2 style="color:#c00;">Error al cargar datos</h2><p>No se pudo parsear el JSON embebido. Revisa la consola (F12).</p><p style="color:#888;font-size:13px">Revisa que el archivo se haya generado correctamente o prueba con Ctrl+F5.</p></div>');
    throw new Error('DATA parse failed');
}}

// Token: lo guardas en localStorage (solo en tu navegador), nunca en el código
var GITHUB_TOKEN = localStorage.getItem('gh_token') || '';

// Global date filter via URL hash — filtra FACTURAS (no clientes)
var filteredInvoices = null; // invoices después de aplicar filtro de fecha

function getFilteredClientes() {{
    const p = new URLSearchParams(window.location.hash.replace('#',''));
    const desde = p.get('desde');
    const hasta = p.get('hasta');
    const all = DATA.clients;
    if (!desde && !hasta) {{
        filteredInvoices = null;
        return all;
    }}
    // Filtrar facturas por fecha exacta
    const invs = DATA.invoices.filter(inv => {{
        if (!inv.fecha) return false;
        if (desde && inv.fecha < desde) return false;
        if (hasta && inv.fecha > hasta) return false;
        return true;
    }});
    filteredInvoices = invs;
    
    // Reconstruir clientes desde las facturas filtradas
    const clientMap = {{}};
    invs.forEach(inv => {{
        const nom = inv.cliente || '(sin nombre)';
        if (!clientMap[nom]) {{
            clientMap[nom] = {{ contratos: 0, facturado: 0, cobrado: 0, saldo: 0, prom: 0, workers: [] }};
        }}
        clientMap[nom].contratos += 1;
        clientMap[nom].facturado += inv.total;
        clientMap[nom].cobrado += inv.pagado;
        if (inv.trabajador) clientMap[nom].workers.push(inv.trabajador);
    }});
    const result = Object.keys(clientMap).map(nom => {{
        const d = clientMap[nom];
        // Worker más frecuente para este cliente
        const freq = {{}};
        d.workers.forEach(w => {{ freq[w] = (freq[w]||0) + 1; }});
        const topWorker = Object.keys(freq).sort((a,b) => freq[b]-freq[a])[0] || '';
        return {{
            cliente: nom,
            contratos: d.contratos,
            facturado: d.facturado,
            cobrado: d.cobrado,
            saldo: d.facturado - d.cobrado,
            prom: d.facturado / d.contratos,
            worker_type: topWorker,
            segmento: topWorker,
            first_date: '',
            last_date: '',
        }};
    }});
    result.sort((a,b) => b.contratos - a.contratos);
    return result;
}}

function aplicarFiltroGlobal() {{
    const d = document.getElementById('filtroFechaDesde').value;
    const h = document.getElementById('filtroFechaHasta').value;
    const p = new URLSearchParams();
    if (d) p.set('desde', d);
    if (h) p.set('hasta', h);
    window.location.hash = p.toString();
    location.reload();
}}

function resetFiltroGlobal() {{
    window.location.hash = '';
    location.reload();
}}

function actualizarDashboard(btn) {{
    if (!GITHUB_TOKEN) {{
        const instrucciones = '👉 Para actualizar necesitas un token de GitHub.\n\n' +
            '1. Ve a: https://github.com/settings/tokens/new\n' +
            '2. Dale un nombre (ej: "dashboard-actualizar")\n' +
            '3. Marca SOLO: "workflow:write" (o Actions: Write)\n' +
            '4. Genera y copia el token\n' +
            '5. Pégalo aquí (se guarda en tu navegador, solo una vez)';
        const token = prompt(instrucciones);
        if (!token) return;
        localStorage.setItem('gh_token', token);
        GITHUB_TOKEN = token;
    }}

    btn.classList.add('loading');
    btn.textContent = '⏳ Actualizando...';

    fetch('https://api.github.com/repos/latinbienti-sys/profesional/actions/workflows/update-dashboard.yml/dispatches', {{
        method: 'POST',
        headers: {{
            'Authorization': 'Bearer ' + GITHUB_TOKEN,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }},
        body: JSON.stringify({{ ref: 'main' }})
    }})
    .then(res => {{
        if (res.status === 204) {{
            btn.textContent = '✅ Actualizando...';
            setTimeout(() => {{ location.reload(); }}, 8000);
        }} else if (res.status === 401 || res.status === 403) {{
            localStorage.removeItem('gh_token');
            GITHUB_TOKEN = '';
            btn.textContent = '❌ Token inválido';
            btn.classList.remove('loading');
            setTimeout(() => {{ btn.textContent = '🔄 Actualizar'; }}, 3000);
        }} else {{
            btn.textContent = '❌ Error ' + res.status;
            btn.classList.remove('loading');
            setTimeout(() => {{ btn.textContent = '🔄 Actualizar'; }}, 3000);
        }}
    }})
    .catch(() => {{
        btn.textContent = '❌ Sin conexión';
        btn.classList.remove('loading');
        setTimeout(() => {{ btn.textContent = '🔄 Actualizar'; }}, 3000);
    }});
}}

const fullClientes = DATA.clients;
const hashParams = new URLSearchParams(window.location.hash.replace('#',''));
if (hashParams.get('desde')) document.getElementById('filtroFechaDesde').value = hashParams.get('desde');
if (hashParams.get('hasta')) document.getElementById('filtroFechaHasta').value = hashParams.get('hasta');

let clientes = getFilteredClientes();
const statusSummary = DATA.status_summary;
const segmentStats = DATA.segment_stats;
const last200 = DATA.last200;
const distribucion = DATA.distribucion;

// ================================================================
//  HELPERS
// ================================================================
function fmtMoney(v) {{ return '$' + Number(v||0).toLocaleString('en-US', {{minimumFractionDigits:2,maximumFractionDigits:2}}); }}
function fmtNum(v) {{ return Number(v||0).toLocaleString('en-US'); }}

function getCategory(c) {{
    if (c >= 10) return {{label:'VIP ★', cls:'badge-gold'}};
    if (c >= 7) return {{label:'Premium', cls:'badge-silver'}};
    if (c >= 5) return {{label:'Frecuente', cls:'badge-bronze'}};
    if (c >= 3) return {{label:'Regular', cls:'badge-blue'}};
    return {{label:'Ocasional', cls:'badge-gray'}};
}}

// ================================================================
//  SAFETY — wrap all in try-catch so page works even if Chart.js CDN fails
// ================================================================
function safeChart(canvasId, config) {{
    try {{
        if (typeof Chart === 'undefined') {{
            console.warn('Chart.js not loaded, skipping:', canvasId);
            return null;
        }}
        // Registrar plugin datalabels (una sola vez)
        if (typeof ChartDataLabels !== 'undefined' && !Chart._datalabelsRegistered) {{
            Chart.register(ChartDataLabels);
            Chart._datalabelsRegistered = true;
        }}
        return new Chart(document.getElementById(canvasId), config);
    }} catch(e) {{
        console.error('Chart error on', canvasId, ':', e.message);
        return null;
    }}
}}

try {{
document.getElementById("fechaGeneracion").textContent =
    new Date().toLocaleDateString("es-ES", {{year:"numeric",month:"long",day:"numeric",hour:"2-digit",minute:"2-digit"}});
var ultAct = document.getElementById("ultimaActualizacion");
if (ultAct) ultAct.textContent = '⏱ ' + new Date().toLocaleDateString("es-ES", {{year:"numeric",month:"long",day:"numeric",hour:"2-digit",minute:"2-digit"}});

const totalFact = clientes.reduce((s,c) => s + c.facturado, 0);
const totalCob = clientes.reduce((s,c) => s + c.cobrado, 0);
const totalPen = totalFact - totalCob;

// Si hay filtro por fecha, mostrar facturas en vez de contratos
const hasFilter = window.location.hash.includes('desde') || window.location.hash.includes('hasta');
if (hasFilter && filteredInvoices) {{
    document.getElementById("hClientes").textContent = fmtNum(clientes.length);
    document.getElementById("hContratos").textContent = fmtNum(filteredInvoices.length) + ' facturas';
    document.getElementById("hFacturado").textContent = fmtMoney(totalFact);
    document.getElementById("hPendiente").textContent = fmtMoney(totalPen);
    document.getElementById("filtroInfoGlobal").textContent = filteredInvoices.length + ' facturas en rango';
}} else {{
    document.getElementById("hClientes").textContent = fmtNum(clientes.length);
    document.getElementById("hContratos").textContent = fmtNum(clientes.reduce((s,c) => s + c.contratos, 0));
    document.getElementById("hFacturado").textContent = fmtMoney(totalFact);
    document.getElementById("hPendiente").textContent = fmtMoney(totalPen);
}}

const c1 = clientes.filter(c => c.contratos === 1).length;
const c2 = clientes.filter(c => c.contratos === 2).length;
const c3 = clientes.filter(c => c.contratos >= 3).length;
const c5 = clientes.filter(c => c.contratos >= 5).length;
document.getElementById("kpi1").textContent = fmtNum(c1);
document.getElementById("kpi2").textContent = fmtNum(c2);
document.getElementById("kpi3").textContent = fmtNum(c3);
document.getElementById("kpi4").textContent = fmtNum(c5);

document.getElementById("mkpiClientes").textContent = fmtNum(clientes.length);
if (hasFilter && filteredInvoices) {{
    document.getElementById("mkpiContratos").textContent = fmtNum(filteredInvoices.length) + ' facturas';
    document.getElementById("filtroInfoMontos").textContent = filteredInvoices.length + ' facturas en rango';
}} else {{
    document.getElementById("mkpiContratos").textContent = fmtNum(clientes.reduce((s,c) => s + c.contratos, 0));
    document.getElementById("filtroInfoMontos").textContent = 'Mostrando todos';
}}
document.getElementById("mkpiFacturado").textContent = fmtMoney(totalFact);
document.getElementById("mkpiCobrado").textContent = fmtMoney(totalCob);
document.getElementById("mkpiPendiente").textContent = fmtMoney(totalPen);
document.getElementById("mkpiPromContratos").textContent = (clientes.reduce((s,c) => s + c.contratos, 0) / clientes.length).toFixed(1);
document.getElementById("mkpiPromMonto").textContent = fmtMoney(totalFact / clientes.length);
document.getElementById("mkpiMaxContratos").textContent = Math.max(...clientes.map(c => c.contratos));

// ================================================================
//  CHARTS — RESUMEN
// ================================================================
const brand = {{primary:'#213C83',primaryLight:'#3D6194',accent:'#F98B10',
    gradient:['#213C83','#2a4a96','#3458a8','#3D6194','#4a72a8','#5a82b8','#6a92c8','#7aa2d4','#8ab2e0','#9ac2ec']}};

// Top 20
const top20 = [...clientes].sort((a,b) => b.contratos - a.contratos).slice(0,20);
safeChart('chartTop20', {{
    type: 'bar',
    data: {{
        labels: top20.map(c => c.cliente.length > 28 ? c.cliente.substring(0,26)+'...' : c.cliente).reverse(),
        datasets: [{{data: top20.map(c => c.contratos).reverse(), backgroundColor: brand.gradient.slice(0,20).reverse(), borderWidth:0, borderRadius:4}}]
    }},
    options: {{
        indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>ctx.parsed.x+' contratos'}}}}}},
        scales:{{x:{{beginAtZero:true, grid:{{color:'rgba(0,0,0,0.05)'}}, ticks:{{stepSize:2}}}}, y:{{grid:{{display:false}}, ticks:{{font:{{size:10}}}}}}}}
    }}
}});

// Distribution
safeChart('chartDist', {{
    type:'bar',
    data:{{
        labels:distribucion.map(d=>d.rango+' contratos'),
        datasets:[{{label:'Clientes', data:distribucion.map(d=>d.cantidad),
            backgroundColor:distribucion.map(d=>d.cantidad>=50?brand.primary:d.cantidad>=10?brand.primaryLight:'#b0c4de'), borderRadius:6}}]
    }},
    options:{{
        responsive:true, maintainAspectRatio:false,
        plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>ctx.parsed.y+' clientes'}}}}}},
        scales:{{x:{{grid:{{display:false}}, ticks:{{font:{{size:10}}}}}}, y:{{beginAtZero:true, grid:{{color:'rgba(0,0,0,0.05)'}}}}}}
    }}
}});

// Status pie
const sc = DATA.status_counts;
const scTotal = sc.Entregado + sc.Aprobado + sc['Cancelacion Total'] + sc.Congelado;
safeChart('chartStatus', {{
    type:'doughnut',
    data:{{
        labels:['Entregado ('+sc.Entregado+')', 'Cancelación Total ('+sc['Cancelacion Total']+')', 'Congelado ('+sc.Congelado+')', 'Aprobado ('+sc.Aprobado+')'],
        datasets:[{{data:[sc.Entregado, sc['Cancelacion Total'], sc.Congelado, sc.Aprobado], backgroundColor:['#10b981','#ef4444','#f59e0b','#3b82f6'], borderColor:'#fff', borderWidth:3}}]
    }},
    options:{{
        responsive:true, maintainAspectRatio:false,
        plugins:{{legend:{{position:'right', labels:{{font:{{size:13}}}}}}, tooltip:{{callbacks:{{label:ctx=>ctx.label+' — '+((ctx.parsed/scTotal)*100).toFixed(1)+'%'}}}}}}
    }}
}});

// ================================================================
//  CHARTS — MONTOS
// ================================================================
let chartsMontos = {{}};
function renderChartsMontos(data) {{
    const topMonto = [...data].sort((a,b) => b.facturado - a.facturado).slice(0,20);
    chartsMontos.topMonto = safeChart('chartTopMonto', {{
        type:'bar',
        data:{{
            labels:topMonto.map(c=>c.cliente.length>28?c.cliente.substring(0,26)+'...':c.cliente).reverse(),
            datasets:[
                {{label:'Facturado', data:topMonto.map(c=>c.facturado).reverse(), backgroundColor:'rgba(33,60,131,0.85)', borderRadius:3, barPercentage:0.6}},
                {{label:'Cobrado', data:topMonto.map(c=>c.cobrado).reverse(), backgroundColor:'rgba(16,185,129,0.7)', borderRadius:3, barPercentage:0.6}}
            ]
        }},
        options:{{indexAxis:'y', responsive:true, maintainAspectRatio:false,
            plugins:{{legend:{{position:'top', labels:{{font:{{size:10}}}}}}, tooltip:{{callbacks:{{label:ctx=>ctx.dataset.label+': '+fmtMoney(ctx.parsed.x)}}}}}},
            scales:{{x:{{beginAtZero:true, grid:{{color:'rgba(0,0,0,0.05)'}}, ticks:{{callback:v=>'$'+(v>=1000?(v/1000).toFixed(0)+'k':v)}}}}, y:{{grid:{{display:false}}, ticks:{{font:{{size:10}}}}}}}}
    }}}});

    const topCont = [...data].sort((a,b) => b.contratos - a.contratos).slice(0,20);
    chartsMontos.topContratos = safeChart('chartTopContratos', {{
        type:'bar',
        data:{{
            labels:topCont.map(c=>c.cliente.length>28?c.cliente.substring(0,26)+'...':c.cliente).reverse(),
            datasets:[{{data:topCont.map(c=>c.contratos).reverse(),
                backgroundColor:topCont.map(c=>c.contratos>=10?'#D4A017':c.contratos>=7?'#A8A8A8':c.contratos>=5?'#CD7F32':'#3D6194').reverse(), borderRadius:4}}]
        }},
        options:{{indexAxis:'y', responsive:true, maintainAspectRatio:false,
            plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>ctx.parsed.x+' contratos'}}}}}},
            scales:{{x:{{beginAtZero:true, grid:{{color:'rgba(0,0,0,0.05)'}}, ticks:{{stepSize:2}}}}, y:{{grid:{{display:false}}, ticks:{{font:{{size:10}}}}}}}}
    }}}});

    const brackets = [{{label:'< $100',min:0,max:100}},{{label:'$100-$500',min:100,max:500}},{{label:'$500-$1K',min:500,max:1000}},{{label:'$1K-$5K',min:1000,max:5000}},{{label:'$5K-$10K',min:5000,max:10000}},{{label:'$10K+',min:10000,max:Infinity}}];
    const bracketCounts = brackets.map(b => data.filter(c => c.facturado >= b.min && c.facturado < b.max).length);
    chartsMontos.distMontos = safeChart('chartDistMontos', {{
        type:'bar',
        data:{{labels:brackets.map(b=>b.label), datasets:[{{label:'Clientes', data:bracketCounts, backgroundColor:['#b0c4de','#6a92c8','#3D6194','#213C83','#F98B10','#d97706'], borderRadius:6}}]}},
        options:{{responsive:true, maintainAspectRatio:false, plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>ctx.parsed.y+' clientes'}}}}}}, scales:{{x:{{grid:{{display:false}}}}, y:{{beginAtZero:true, grid:{{color:'rgba(0,0,0,0.05)'}}}}}}}}
    }});

    const pendientes = data.filter(c => c.saldo > 1).length;
    const pagados = data.filter(c => c.saldo <= 1).length;
    chartsMontos.carteraPie = safeChart('chartCarteraPie', {{
        type:'doughnut',
        data:{{labels:['Con saldo ('+fmtNum(pendientes)+')','Pagado ('+fmtNum(pagados)+')'], datasets:[{{data:[pendientes,pagados], backgroundColor:['#ef4444','#10b981'], borderColor:'#fff', borderWidth:3}}]}},
        options:{{responsive:true, maintainAspectRatio:false, plugins:{{legend:{{position:'right', labels:{{font:{{size:13}}}}}}, tooltip:{{callbacks:{{label:ctx=>ctx.label+' — '+((ctx.parsed/(pendientes+pagados))*100).toFixed(1)+'%'}}}}}}}}
    }});
}}
renderChartsMontos(clientes);

// ================================================================
//  FILTERS — MONTOS
// ================================================================
let filteredMontos = [];
function aplicarFiltrosMontos() {{
    const montoMin = parseFloat(document.getElementById('filtroMontoMin').value) || 0;
    const contMin = parseInt(document.getElementById('filtroContratosMin').value) || 0;
    const estado = document.getElementById('filtroEstado').value;
    filteredMontos = clientes.filter(c => {{
        if (c.facturado < montoMin) return false;
        if (c.contratos < contMin) return false;
        if (estado === 'pagado' && c.saldo > 1) return false;
        if (estado === 'pendiente' && c.saldo < 1) return false;
        return true;
    }});
    document.getElementById('filtroInfoMontos').textContent = filteredMontos.length === clientes.length ? 'Mostrando todos' : 'Mostrando '+filteredMontos.length+' de '+clientes.length+' clientes';
    Object.values(chartsMontos).forEach(ch => {{ if (ch) ch.destroy(); }});
    renderChartsMontos(filteredMontos);
}}
function resetFiltrosMontos() {{
    document.getElementById('filtroMontoMin').value = '';
    document.getElementById('filtroContratosMin').value = '';
    document.getElementById('filtroEstado').value = 'todos';
    filteredMontos = [];
    document.getElementById('filtroInfoMontos').textContent = 'Mostrando todos';
    Object.values(chartsMontos).forEach(ch => {{ if (ch) ch.destroy(); }});
    renderChartsMontos(clientes);
}}

// ================================================================
//  SEGMENTOS
// ================================================================
(function() {{
    const segKeys = Object.keys(segmentStats);
    const segColors = {{'bajo_dependencia':'#213C83','independiente':'#F98B10','dependiente_publico':'#10b981','independiente_formal':'#F59E0B','dependiente_privado':'#ef4444','independiente_informal':'#f97316','Sin clasificar':'#9ca3af'}};

    // KPI cards
    const kpiRow = document.getElementById('segmentKpis');
    kpiRow.innerHTML = segKeys.map(s => `
        <div class="kpi-card" style="border-top-color:${{segColors[s]||'#999'}};cursor:pointer" onclick="filterBySegment('${{s}}')" title="Ver facturas de ${{s}}">
            <div class="number">${{segmentStats[s].contratos}}</div>
            <div class="label">${{s}}</div>
            <div style="font-size:10px;color:#888;margin-top:4px">${{segmentStats[s].clientes}} clientes - ${{fmtMoney(segmentStats[s].facturado)}}</div>
        </div>
    `).join('');

    // Pie chart (facturas)
    const totalFacturas = segKeys.reduce((a,s)=>a+segmentStats[s].contratos, 0);
    safeChart('chartSegPie', {{
        type:'doughnut',
        data:{{
            labels:segKeys.map(s=>s+' ('+segmentStats[s].contratos+')'),
            datasets:[{{data:segKeys.map(s=>segmentStats[s].contratos), backgroundColor:segKeys.map(s=>segColors[s]||'#9ca3af'), borderColor:'#fff', borderWidth:3}}]
        }},
        options:{{responsive:true, maintainAspectRatio:false, plugins:{{legend:{{position:'right', labels:{{font:{{size:12}}}}}}, tooltip:{{callbacks:{{label:ctx=>ctx.label+' — '+((ctx.parsed/totalFacturas)*100).toFixed(1)+'%'}}}}}}}}
    }});

    // Facturado bar
    safeChart('chartSegFact', {{
        type:'bar',
        data:{{
            labels:segKeys,
            datasets:[{{label:'Facturado', data:segKeys.map(s=>segmentStats[s].facturado), backgroundColor:segKeys.map(s=>segColors[s]||'#9ca3af'), borderRadius:6}}]
        }},
        options:{{
            responsive:true, maintainAspectRatio:false,
            plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>fmtMoney(ctx.parsed.y)}}}}}},
            scales:{{x:{{grid:{{display:false}}}}, y:{{beginAtZero:true, grid:{{color:'rgba(0,0,0,0.05)'}}, ticks:{{callback:v=>'$'+(v>=1000?(v/1000).toFixed(0)+'k':v)}}}}}}
        }}
    }});

    // Last 200 chart
    const l200Keys = Object.keys(last200);
    safeChart('chartLast200', {{
        type:'bar',
        data:{{
            labels:l200Keys,
            datasets:[{{label:'Contratos', data:l200Keys.map(k=>last200[k]), backgroundColor:l200Keys.map(k=>segColors[k]||'#9ca3af'), borderRadius:6}}]
        }},
        options:{{
            responsive:true, maintainAspectRatio:false,
            plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>ctx.parsed.y+' contratos ('+((ctx.parsed.y/200)*100).toFixed(1)+'%)'}}}}}},
            scales:{{x:{{grid:{{display:false}}}}, y:{{beginAtZero:true, grid:{{color:'rgba(0,0,0,0.05)'}}}}}}
        }}
    }});

    // Detalle table
    const wrap = document.getElementById('segmentTableWrap');
    wrap.innerHTML = `<table>
        <thead><tr><th>Segmento</th><th>Clientes</th><th>Contratos</th><th>Facturado</th><th>Cobrado</th><th>% Cartera</th><th></th></tr></thead>
        <tbody>${{segKeys.map(s => {{
            const st = segmentStats[s];
            const pct = ((st.clientes / clientes.length) * 100).toFixed(1);
            return `<tr style="cursor:pointer" onclick="filterBySegment('${{s}}')" title="Ver clientes de ${{s}}">
                <td><strong>${{s}}</strong></td><td class="text-right">${{st.clientes}}</td><td class="text-right">${{st.contratos}}</td>
                <td class="text-right">${{fmtMoney(st.facturado)}}</td><td class="text-right">${{fmtMoney(st.cobrado)}}</td>
                <td class="text-right">${{pct}}%</td>
                <td style="font-size:11px;color:var(--primary)">Ver →</td></tr>`;
        }}).join('')}}</tbody>
    </table>`;
}})();

// ================================================================
//  TEMPORAL VIP
// ================================================================
const vipClients = DATA.vip;
let filteredVip = [...vipClients];
let timelineChart = null;

// Compute temporal metrics
function calcTemporal(vip) {{
    if (!vip.length) return {{avgSpan:0, avgFreq:0, maxSpan:0}};
    let spans = [], freqs = [];
    vip.forEach(c => {{
        if (c.first && c.last) {{
            const d1 = new Date(c.first), d2 = new Date(c.last);
            const spanD = Math.round((d2 - d1) / (86400000));
            const spanM = Math.round(spanD / 30.44 * 10) / 10;
            spans.push(spanM);
            if (c.cont > 1) freqs.push(Math.round(spanD / (c.cont - 1)));
        }}
    }});
    return {{
        avgSpan: spans.length ? spans.reduce((a,b)=>a+b,0)/spans.length : 0,
        avgFreq: freqs.length ? freqs.reduce((a,b)=>a+b,0)/freqs.length : 0,
        maxSpan: spans.length ? Math.max(...spans) : 0
    }};
}}

function buildTimelineChartData(data) {{
    if (!data.length) return {{labels:[], offsets:[], spans:[], base:new Date()}};
    const sorted = [...data].sort((a,b) => (a.first||'').localeCompare(b.first||''));
    const base = new Date(sorted[0].first);
    return {{
        labels: sorted.map(c => c.cliente.length > 25 ? c.cliente.substring(0,23)+'...' : c.cliente).reverse(),
        offsets: sorted.map(c => Math.round((new Date(c.first) - base) / 86400000)).reverse(),
        spans: sorted.map(c => Math.round((new Date(c.last) - new Date(c.first)) / 86400000)).reverse(),
        base
    }};
}}

function renderTimeline(data) {{
    const tl = buildTimelineChartData(data);
    const ctx = document.getElementById('chartTimeline');
    if (timelineChart) timelineChart.destroy();
    timelineChart = safeChart('chartTimeline', {{
        type:'bar',
        data:{{
            labels: tl.labels,
            datasets: [
                {{label:'Offset', data: tl.offsets, backgroundColor:'rgba(33,60,131,0.15)', borderRadius:0, barPercentage:0.7}},
                {{label:'Período activo', data: tl.spans, backgroundColor:'#F98B10', borderRadius:4}}
            ]
        }},
        options:{{
            indexAxis:'y', responsive:true, maintainAspectRatio:false, stacked:true,
            plugins:{{legend:{{display:false}}, tooltip:{{callbacks:{{label:ctx=>ctx.datasetIndex===0?'Inicio: '+data[data.length-1-ctx.dataIndex].first:data[data.length-1-ctx.dataIndex].first+' → '+data[data.length-1-ctx.dataIndex].last}}}}}},
            scales:{{x:{{stacked:true, title:{{display:true, text:'Días desde '+tl.base.toISOString().split('T')[0], font:{{size:10}}}}, grid:{{color:'rgba(0,0,0,0.05)'}}}}, y:{{stacked:true, grid:{{display:false}}, ticks:{{font:{{size:9}}}}}}}}
    }}}});
}}

function renderTemporalTable(data) {{
    const tbody = document.getElementById('tbodyTemporal');
    if (!data.length) {{
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:#999;">Sin datos</td></tr>';
        return;
    }}
    tbody.innerHTML = data.map((c,i) => {{
        const d1 = new Date(c.first), d2 = new Date(c.last);
        const spanD = Math.round((d2 - d1) / 86400000);
        const spanM = Math.round(spanD / 30.44 * 10) / 10;
        return `<tr class="${{i<3?'top-client':''}} ${{i===0?'rank-1':i===1?'rank-2':i===2?'rank-3':''}}">
            <td><strong>${{i+1}}</strong></td><td>${{c.cliente}}</td>
            <td class="text-right"><strong>${{c.cont}}</strong></td>
            <td>${{c.first}}</td><td>${{c.last}}</td>
            <td class="text-right">${{spanD}}</td><td class="text-right">${{spanM.toFixed(1)}}</td>
        </tr>`;
    }}).join('');
}}

function updateTemporalUI(data) {{
    const tmp = calcTemporal(data);
    document.getElementById('tmpVipCount').textContent = data.length;
    document.getElementById('tmpAvgSpan').textContent = tmp.avgSpan.toFixed(1)+' m';
    document.getElementById('tmpAvgFreq').textContent = Math.round(tmp.avgFreq)+' d';
    document.getElementById('tmpMaxSpan').textContent = tmp.maxSpan.toFixed(1)+' m';
    renderTimeline(data);
    renderTemporalTable(data);
}}

// Relationship chart
const relacionData = [
    {{label:'1-3 meses', count: vipClients.filter(c => {{const d=(new Date(c.last)-new Date(c.first))/86400000/30.44; return d>=1 && d<3;}}).length}},
    {{label:'3-6 meses', count: vipClients.filter(c => {{const d=(new Date(c.last)-new Date(c.first))/86400000/30.44; return d>=3 && d<6;}}).length}},
    {{label:'6-12 meses', count: vipClients.filter(c => {{const d=(new Date(c.last)-new Date(c.first))/86400000/30.44; return d>=6 && d<12;}}).length}},
    {{label:'12-24 meses', count: vipClients.filter(c => {{const d=(new Date(c.last)-new Date(c.first))/86400000/30.44; return d>=12 && d<24;}}).length}},
    {{label:'24+ meses', count: vipClients.filter(c => {{const d=(new Date(c.last)-new Date(c.first))/86400000/30.44; return d>=24;}}).length}}
];
safeChart('chartRelacion', {{
    type:'bar',
    data:{{labels:relacionData.map(d=>d.label), datasets:[{{label:'Clientes VIP', data:relacionData.map(d=>d.count), backgroundColor:['#b0c4de','#6a92c8','#3D6194','#213C83','#F98B10'], borderRadius:6}}]}},
    options:{{responsive:true, maintainAspectRatio:false, plugins:{{legend:{{display:false}}}}, scales:{{x:{{grid:{{display:false}}}}, y:{{beginAtZero:true, grid:{{color:'rgba(0,0,0,0.05)'}}, ticks:{{stepSize:1}}}}}}}}
}});

updateTemporalUI(vipClients);

// ================================================================
//  TABLE
// ================================================================
let currentPage = 1;
let sortColumn = 2;
let sortDesc = true;
const PAGE_SIZE = 25;
let filteredData = [...clientes];
let segmentFilter = '';

function filterTable() {{
    const term = document.getElementById('searchInput').value.toUpperCase();
    filteredData = clientes.filter(c => {{
        if (segmentFilter && c.segmento !== segmentFilter) return false;
        if (term && !c.cliente.toUpperCase().includes(term)) return false;
        return true;
    }});
    currentPage = 1;
    renderTable();
}}

function filterBySegment(seg) {{
    segmentFilter = seg;
    const searchInput = document.getElementById('searchInput');
    searchInput.value = '';
    document.getElementById('clearSegFilter').style.display = seg ? 'inline-block' : 'none';
    document.getElementById('segFilterLabel').textContent = seg ? 'Segmento: ' + seg : '';
    document.getElementById('segFilterLabel').style.display = seg ? 'inline-block' : 'none';
    filterTable();
    switchTab('tabla');
}}

function clearSegmentFilter() {{
    filterBySegment('');
}}

function sortTable(col) {{
    if (sortColumn === col) sortDesc = !sortDesc;
    else {{ sortColumn = col; sortDesc = col === 2 || col === 3; }}
    document.querySelectorAll('thead th').forEach((th,i) => {{
        th.classList.toggle('sorted', i === col);
        const icon = th.querySelector('.sort-icon');
        if (icon) icon.textContent = i === col ? (sortDesc ? '▼' : '▲') : '⇅';
    }});
    const getVal = (c, col) => {{
        switch(col) {{
            case 0: return clientes.indexOf(c);
            case 1: return c.cliente;
            case 2: return c.contratos;
            case 3: return c.facturado;
            case 4: return c.cobrado;
            case 5: return c.saldo;
            case 6: return c.prom;
            case 7: return c.segmento || '';
            case 8: return c.contratos + c.facturado;
            default: return c.contratos;
        }}
    }};
    filteredData.sort((a,b) => {{
        const va = getVal(a,col), vb = getVal(b,col);
        if (typeof va === 'string') return sortDesc ? vb.localeCompare(va) : va.localeCompare(vb);
        return sortDesc ? vb - va : va - vb;
    }});
    currentPage = 1;
    renderTable();
}}

function changePage(delta) {{
    const totalPages = Math.ceil(filteredData.length / PAGE_SIZE);
    const np = currentPage + delta;
    if (np < 1 || np > totalPages) return;
    currentPage = np;
    renderTable();
}}

function renderTable() {{
    const totalPages = Math.ceil(filteredData.length / PAGE_SIZE);
    const start = (currentPage - 1) * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, filteredData.length);
    const pageData = filteredData.slice(start, end);
    document.getElementById('totalRows').textContent = filteredData.length;
    document.getElementById('showing').textContent = filteredData.length;
    document.getElementById('pageInfo').textContent = 'Página '+currentPage+' / '+Math.max(1,totalPages);
    document.getElementById('prevBtn').disabled = currentPage <= 1;
    document.getElementById('nextBtn').disabled = currentPage >= totalPages;
    const tbody = document.getElementById('tableBody');
    if (!pageData.length) {{
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:30px;color:#999;">Sin clientes</td></tr>';
        return;
    }}
    tbody.innerHTML = pageData.map((c,i) => {{
        const ri = start + i + 1;
        const cat = getCategory(c.contratos);
        const r = ri===1?'rank-1':ri===2?'rank-2':ri===3?'rank-3':'';
        const t = ri<=3?'top-client':'';
        return `<tr class="${{r}} ${{t}}">
            <td><strong>${{ri}}</strong></td>
            <td>${{c.cliente}}</td>
            <td class="text-right"><strong>${{c.contratos}}</strong></td>
            <td class="text-right">${{fmtMoney(c.facturado)}}</td>
            <td class="text-right">${{fmtMoney(c.cobrado)}}</td>
            <td class="text-right">${{fmtMoney(c.saldo)}}</td>
            <td class="text-right">${{fmtMoney(c.prom)}}</td>
            <td><span class="badge badge-blue">${{c.segmento||'N/A'}}</span></td>
            <td><span class="badge ${{cat.cls}}">${{cat.label}}</span></td>
        </tr>`;
    }}).join('');
}}

// ================================================================
//  TABS
// ================================================================
function switchTab(tab) {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    const tabMap = {{resumen:'Resumen', montos:'Montos', segmentos:'Segmentos', temporal:'Temporal', tabla:'Listado', pagos:'Plan de Pagos', factjulio:'Fact. Julio', expedientes:'Expedientes', prontopago:'Pronto Pago', ciclos:'Ciclos', gestion:'Gestión Cobranza', ventas_motos:'Ventas Motos', pago_proveedor:'Pago Proveedor'}};

    // Arreglo de opciones del menú de navegación
    const menuItems = [
        {{ id: 'gestion', label: 'Gestión Cobranza', icon: '📋' }},
        {{ id: 'expedientes', label: 'Expedientes', icon: '📂' }},
        {{ id: 'prontopago', label: 'Pronto Pago', icon: '⚡' }},
        {{ id: 'ventas_motos', label: 'Ventas Motos', icon: '🏍️' }},
        {{ id: 'pago_proveedor', label: 'Pago Proveedor', icon: '💰' }},
        {{ id: 'resumen', label: 'Resumen', icon: '📊' }},
        {{ id: 'pagos', label: 'Plan de Pagos', icon: '💳' }},
        {{ id: 'ciclos', label: 'Ciclos', icon: '📅' }},
        {{ id: 'montos', label: 'Montos', icon: '💰' }},
        {{ id: 'segmentos', label: 'Segmentos', icon: '👥' }},
        {{ id: 'temporal', label: 'Temporal VIP', icon: '⏱️' }},
        {{ id: 'tabla', label: 'Listado', icon: '📋' }},
        {{ id: 'factjulio', label: 'Fact. Julio', icon: '📑' }},
    ];
    const btn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.textContent.includes(tabMap[tab]));
    if (btn) btn.classList.add('active');
    document.getElementById('tab-'+tab).classList.add('active');
    setTimeout(() => {{
        document.querySelectorAll('canvas').forEach(c => {{
            const ch = typeof Chart !== 'undefined' ? Chart.getChart(c) : null;
            if (ch) ch.resize();
        }});
    }}, 100);
}}

function toggleSubTable(el) {{
    var next = el.nextElementSibling;
    if (next && next.classList.contains('sub-table')) {{
        next.style.display = next.style.display === 'none' ? '' : 'none';
    }}
}}

// ================================================================
//  PLAN DE PAGOS
// ================================================================
try {{
    const pp = DATA.payment_plan;
    if (pp) {{
        document.getElementById('pkTotalVencido').textContent = fmtMoney(pp.total_vencido);
        document.getElementById('pkTotalDebido').textContent = fmtMoney(pp.total_debido);
        document.getElementById('pkTotalPagado').textContent = fmtMoney(pp.total_pagado);
        
        const vencidos = pp.clientes_vencidos || [];
        document.getElementById('pkVencidoTotal').textContent = fmtMoney(pp.total_vencido);
        document.getElementById('pkVencidosCount').textContent = vencidos.length;
        var tbody = document.getElementById('tablaVencidos');
        if (tbody) {{
            tbody.innerHTML = vencidos.slice(0,50).map(function(v) {{
                var statuses = v.statuses || [];
                var statusHtml = statuses.map(function(s) {{
                    var cls = s === 'Entregado' ? 'status-entregado' : (s === 'Cancelación Total' ? 'status-cancelado' : (s === 'Congelado' ? 'status-congelado' : 'status-aprobado'));
                    return '<span class="' + cls + '">' + s + '</span>';
                }}).join(' ');
                var factStr = v.facturas.slice(0,3).join(', ');
                if (v.facturas.length > 3) factStr += '...';
                return '<tr><td><strong>' + v.cliente + '</strong></td><td class=\"text-right\">' + v.cuotas + '</td><td class=\"text-right\" style=\"color:#ef4444;font-weight:600\">' + fmtMoney(v.monto) + '</td><td>' + statusHtml + '</td><td style=\"font-size:11px;color:#666\">' + factStr + '</td></tr>';
            }}).join('');
        }}
        // Facturas entregadas con cuotas vencidas
        var ev = pp.facturas_entregadas_vencidas || [];
        var evT = pp.total_entregadas_venc || {{facturas:0,monto:0,cuotas:0}};
        var elEvF = document.getElementById('evFacturasCount');
        var elEvM = document.getElementById('evMontoTotal');
        var elEvC = document.getElementById('evCuotasCount');
        if (elEvF) elEvF.textContent = evT.facturas.toLocaleString();
        if (elEvM) elEvM.textContent = fmtMoney(evT.monto);
        if (elEvC) elEvC.textContent = evT.cuotas.toLocaleString();
        var tevBody = document.getElementById('tablaEntregadasVenc');
        if (tevBody) {{
            tevBody.innerHTML = ev.map(function(f) {{
                var dMora = f.max_dias_mora || 0;
                var moraCls = dMora > 90 ? 'status-cancelado' : (dMora > 30 ? 'status-congelado' : 'status-aprobado');
                return '<tr>' +
                    '<td style=\"font-size:12px;color:#2563eb;font-weight:600\">' + (f.factura||'') + '</td>' +
                    '<td><strong>' + (f.cliente||'') + '</strong></td>' +
                    '<td style=\"font-size:12px\">' + (f.fecha_factura||'') + '</td>' +
                    '<td class=\"text-right\">' + f.cuotas + '</td>' +
                    '<td class=\"text-right\" style=\"color:#ef4444;font-weight:600\">' + fmtMoney(f.monto) + '</td>' +
                    '<td style=\"font-size:12px;color:#666\">' + (f.ultima_cuota||'') + '</td>' +
                    '<td class=\"text-right\"><span class=\"' + moraCls + '\">' + dMora + ' d</span></td>' +
                    '</tr>';
            }}).join('') || '<tr><td colspan="7" style="text-align:center;color:#999">Sin facturas entregadas vencidas</td></tr>';
        }}
        // Últimas entregas realizadas + morosidad del cliente
        var ue = pp.ultimas_entregas || [];
        var ueT = pp.total_ultimas || {{entregas:0,morosos:0,monto:0}};
        var elUeE = document.getElementById('ueEntregas');
        var elUeM = document.getElementById('ueMorosos');
        var elUeMo = document.getElementById('ueMonto');
        if (elUeE) elUeE.textContent = ueT.entregas.toLocaleString();
        if (elUeM) elUeM.textContent = ueT.morosos.toLocaleString();
        if (elUeMo) elUeMo.textContent = fmtMoney(ueT.monto);
        var ueBody = document.getElementById('tablaUltimasEntregas');
        if (ueBody) {{
            ueBody.innerHTML = ue.map(function(u) {{
                var cls = u.moroso ? 'status-cancelado' : 'status-entregado';
                var txt = u.moroso ? '🔴 MOROSO' : '✅ Al día';
                var vencColor = u.moroso ? '#ef4444' : '#10b981';
                return '<tr>' +
                    '<td style=\"font-size:12px;color:#7c3aed;font-weight:600\">' + (u.factura||'') + '</td>' +
                    '<td><strong>' + (u.cliente||'') + '</strong></td>' +
                    '<td style=\"font-size:12px\">' + (u.entrega||'') + '</td>' +
                    '<td class=\"text-right\" style=\"color:' + vencColor + ';font-weight:600\">' + fmtMoney(u.vencido_cliente) + '</td>' +
                    '<td class=\"text-right\">' + (u.facturas_mora||0) + '</td>' +
                    '<td><span class=\"' + cls + '\">' + txt + '</span></td>' +
                    '</tr>';
            }}).join('') || '<tr><td colspan="6" style="text-align:center;color:#999">Sin entregas recientes</td></tr>';
        }}
        renderCiclo('10-25');
        renderCicloResumen();
        renderManana();
        // Pequeño delay para asegurar que el DOM del ciclo esté listo
        setTimeout(mostrarManana, 50);
    }}
}} catch(e) {{ console.error('Payment plan error:', e); }}

// ================================================================
//  ALERTAS DE MOROSIDAD
// ================================================================
try {{
    var pp2 = DATA.payment_plan || {{}};
    var alertas = pp2.alertas_morosidad || [];
    var ta = pp2.total_alertas || {{}};

    // Banner
    if (ta.total > 0) {{
        document.getElementById('alertasBanner').style.display = 'block';
        document.getElementById('alertasTitulo').textContent = 'ALERTAS DE MOROSIDAD — ' + ta.total + ' clientes requieren atención';
        document.getElementById('alertasSubtitulo').textContent = 'Monto total en riesgo: ' + fmtMoney(ta.monto_total_riesgo) + ' | Alertas críticas: ' + ta.criticos;
        document.getElementById('alertasCriticos').textContent = ta.criticos;
        document.getElementById('alertasAltos').textContent = ta.altos;
        document.getElementById('alertasMedios').textContent = ta.medios;
        document.getElementById('alertasBajos').textContent = ta.bajos;
        document.getElementById('alertasMonto').textContent = fmtMoney(ta.monto_total_riesgo);
    }}

    // Tabla
    function renderAlertas(filtro) {{
        var filtered = filtro === 'todos' ? alertas : alertas.filter(function(a) {{ return a.severidad === filtro; }});
        var alBody = document.getElementById('tablaAlertas');
        var secc = document.getElementById('seccionAlertas');
        if (!alBody || !secc) return;
        secc.style.display = alertas.length > 0 ? 'block' : 'none';
        alBody.innerHTML = filtered.slice(0, 100).map(function(a) {{
            var sevMap = {{
                critico: {{ bg: '#fef2f2', border: '#dc2626', color: '#991b1b', label: '🔴 CRÍTICO' }},
                alto: {{ bg: '#fff7ed', border: '#ea580c', color: '#9a3412', label: '🟠 ALTO' }},
                medio: {{ bg: '#fffbeb', border: '#d97706', color: '#92400e', label: '🟡 MEDIO' }},
                bajo: {{ bg: '#f0f9ff', border: '#0ea5e9', color: '#0c4a6e', label: '🔵 BAJO' }},
            }};
            var s = sevMap[a.severidad] || sevMap.bajo;
            var ppTag = a.es_pronto_pago ? '<span style="background:#d1fae5;color:#065f46;padding:1px 6px;border-radius:4px;font-size:10px;margin-left:6px">⚡PP</span>' : '';
            var link = 'https://latinbien.com/web#id=' + (a.factura_antigua_id || 0) + '&model=account.move&view_type=form';
            return '<tr style="border-left:4px solid ' + s.border + '">' +
                '<td style="background:' + s.bg + ';color:' + s.color + ';font-weight:700;font-size:12px">' + s.label + '</td>' +
                '<td><strong>' + a.cliente + '</strong>' + ppTag + '</td>' +
                '<td class="text-right" style="font-weight:700;color:' + s.border + '">' + a.dias_max + ' días</td>' +
                '<td class="text-right" style="color:#ef4444;font-weight:600">' + fmtMoney(a.monto_vencido) + '</td>' +
                '<td class="text-right">' + a.cuotas_vencidas + '</td>' +
                '<td style="font-size:12px;color:#555">' + (a.factura_antigua || '') + '<br><span style="font-size:10px;color:#999">' + a.cuota_mas_antigua + '</span></td>' +
                '<td style="font-size:11px;color:#555;max-width:250px">' + a.accion + '</td>' +
                '</tr>';
        }}).join('') || '<tr><td colspan="7" style="text-align:center;color:#999">Sin alertas para este filtro</td></tr>';
    }}

    window.filtrarAlertas = function(filtro) {{
        document.querySelectorAll('.btn-alerta').forEach(function(b) {{ b.style.fontWeight = 'normal'; b.style.boxShadow = 'none'; }});
        event.target.style.fontWeight = '700';
        event.target.style.boxShadow = '0 0 0 2px #213C83';
        renderAlertas(filtro);
    }};

    renderAlertas('todos');
}} catch(e) {{ console.error('Alertas error:', e); }}

// ================================================================
//  COBRANZA VENCIDA CON COMPROMISO
// ================================================================
try {{
    var pp3 = DATA.payment_plan || {{}};
    var comp = pp3.facturas_con_compromiso || [];
    var tc3 = pp3.total_compromiso || {{}};

    if (comp.length > 0) {{
        document.getElementById('seccionCompromiso').style.display = 'block';
        document.getElementById('compFacturas').textContent = tc3.facturas || 0;
        document.getElementById('compMonto').textContent = fmtMoney(tc3.monto_total || 0);
        document.getElementById('compOverdue').textContent = tc3.overdue || 0;
        document.getElementById('compPlanned').textContent = tc3.planned || 0;

        var coBody = document.getElementById('tablaCompromiso');
        if (coBody) {{
            coBody.innerHTML = comp.map(function(f) {{
                var estadoHtml = f.compromiso_overdue
                    ? '<span style="background:#fef2f2;color:#991b1b;padding:2px 8px;border-radius:4px;font-weight:700;border:1px solid #dc2626">VENCIDO</span>'
                    : '<span style="background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:4px;font-weight:700;border:1px solid #10b981">VIGENTE</span>';
                var factUrl = 'https://latinbien.com/web#id=' + f.invoice_id + '&model=account.move&view_type=form';
                var acts = (f.actividades || []).map(function(a) {{
                    return '<div style="margin:2px 0;font-size:11px"><strong>' + (a.summary || '(sin resumen)') + '</strong><br>Deadline: ' + a.deadline + ' | ' + a.responsable + '</div>';
                }}).join('');
                return '<tr>' +
                    '<td>' + estadoHtml + '</td>' +
                    '<td><a href="' + factUrl + '" target="_blank" style="color:#213C83;font-weight:600;text-decoration:none;border-bottom:1px dashed #213C83">' + (f.factura||'') + '</a></td>' +
                    '<td><strong>' + f.cliente + '</strong></td>' +
                    '<td class="text-right" style="font-weight:700;color:#ef4444">' + f.dias_atraso + ' días</td>' +
                    '<td class="text-right" style="color:#ef4444;font-weight:600">' + fmtMoney(f.monto_vencido) + '</td>' +
                    '<td>' + (f.proximo_deadline || 'N/A') + '</td>' +
                    '<td style="font-size:12px">' + (f.actividades[0]?.responsable || '') + '</td>' +
                    '<td style="font-size:11px;max-width:250px">' + acts + '</td>' +
                    '</tr>';
            }}).join('') || '<tr><td colspan="8" style="text-align:center;color:#999">Sin facturas con compromiso</td></tr>';
        }}
    }}
}} catch(e) {{ console.error('Compromiso error:', e); }}

// ================================================================
//  FACTURACIÓN JULIO 2026
// ================================================================
try {{
    var fj = DATA.facturacion_julio;
    if (fj) {{
        // KPIs
        document.getElementById('fjTotalFacturado').textContent = fmtMoney(fj.total_facturado);
        document.getElementById('fjTotalProductos').textContent = fmtMoney(fj.total_productos);
        document.getElementById('fjTotalAdmin').textContent = fmtMoney(fj.total_admin);
        document.getElementById('fjTotalAdminTotal').textContent = fmtMoney(fj.total_admin_total);
        document.getElementById('fjTotalCosto').textContent = fmtMoney(fj.total_costo);
        document.getElementById('fjTotalMargen').textContent = fmtMoney(fj.total_margen);
        document.getElementById('fjTotalFacturas').textContent = fj.total_facturas.toLocaleString();
        document.getElementById('fjTotalClientes').textContent = fj.total_clientes.toLocaleString();
        document.getElementById('fjCancelacionesMonto').textContent = fmtMoney(fj.cancelaciones_monto);
        document.getElementById('fjCancelacionesLbl').textContent = fj.cancelaciones_count + ' Cancelaciones';

        // Cuentas colaboradoras con dcto en gasto admin
        var tColab = document.getElementById('tablaColaboradores');
        if (tColab && fj.colaboradores) {{
            tColab.innerHTML = fj.colaboradores.map(function(c) {{
                return '<tr>' +
                    '<td style="font-size:11px;color:#666">' + c.factura + '</td>' +
                    '<td><strong>' + c.cliente + '</strong></td>' +
                    '<td class="text-right">' + fmtMoney(c.gasto_admin_total) + '</td>' +
                    '<td class="text-right" style="color:#f59e0b;font-weight:700">' + c.descuento + '%</td>' +
                    '<td class="text-right">' + fmtMoney(c.gasto_admin) + '</td>' +
                    '</tr>';
            }}).join('');
        }}

        // Grafico resumen: Total Facturado, Productos, Gasto Admin, Costos
        try {{
            var rCanvas = document.getElementById('chartResumenJulio');
            if (rCanvas) {{
                var rLabels = ['Total Facturado', 'Total Productos', 'Gasto Admin.', 'Costos', 'Cancelaciones'];
                var rData = [fj.total_facturado, fj.total_productos, fj.total_admin, fj.total_costo, fj.cancelaciones_monto];
                var rColors = ['#213C83', '#2a4a96', '#f59e0b', '#ef4444', '#dc2626'];
                safeChart('chartResumenJulio', {{
                    type: 'bar',
                    data: {{
                        labels: rLabels,
                        datasets: [{{ data: rData, backgroundColor: rColors, borderWidth: 0, borderRadius: 6 }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{ callbacks: {{ label: function(ctx) {{ return '  ' + fmtMoney(ctx.parsed.y); }} }} }},
                            datalabels: {{
                                color: '#111',
                                font: {{ size: 12, weight: 'bold' }},
                                formatter: function(v) {{ return v.toLocaleString(undefined, {{minimumFractionDigits:2,maximumFractionDigits:2}}); }},
                                anchor: 'end',
                                align: 'top',
                                offset: 4
                            }}
                        }},
                        scales: {{
                            y: {{ beginAtZero: true, ticks: {{ callback: function(v) {{ return fmtMoney(v); }} }}, grid: {{ color: 'rgba(0,0,0,0.05)' }} }},
                            x: {{ ticks: {{ font: {{ size: 12 }}, maxRotation: 0, minRotation: 0 }}, grid: {{ display: false }} }}
                        }}
                    }}
                }});
            }}
        }} catch(e) {{ console.error('Resumen julio chart error:', e); }}

        // DESCUENTOS POR FACTURA (mostrar % de descuentos, no en dólares)
        try {{
            var dBody = document.getElementById('tablaDescuentos');
            if (dBody && fj.facturas) {{
                var rows = '';
                fj.facturas.forEach(function(f) {{
                    if (!f.lineas) return;
                    var dctoProd = 0, dctoAdmin = 0;
                    f.lineas.forEach(function(l) {{
                        if (l.tipo === 'GASTO ADMIN' && l.discount > 0) dctoAdmin += l.discount;
                        else if (l.tipo === 'PRODUCTO' && l.discount > 0) dctoProd += l.discount;
                    }});
                    if (dctoProd > 0 || dctoAdmin > 0) {{
                        var totalDcto = dctoProd + dctoAdmin;
                        rows += '<tr>' +
                            '<td style="font-size:11px;color:#666">' + f.factura + '</td>' +
                            '<td><strong>' + f.cliente + '</strong></td>' +
                            '<td class="text-right">' + dctoProd.toFixed(2) + '%</td>' +
                            '<td class="text-right">' + dctoAdmin.toFixed(2) + '%</td>' +
                            '</tr>';
                    }}
                }});
                dBody.innerHTML = rows || '<tr><td colspan="4" style="text-align:center;color:#999">Sin descuentos en facturas de julio</td></tr>';
            }}
        }} catch(e) {{ console.error('Descuentos table error:', e); }}
        
        // Ejecutivos
        var tEje = document.getElementById('tablaEjecutivos');
        if (tEje && fj.ejecutivos) {{
            tEje.innerHTML = fj.ejecutivos.map(function(e) {{
                return '<tr class="clickable" onclick="toggleSubTable(this)">' +
                    '<td><strong>' + e.nombre + '</strong></td>' +
                    '<td class="text-right">' + e.cantidad.toLocaleString() + '</td>' +
                    '<td class="text-right">' + fmtMoney(e.total) + '</td>' +
                    '<td style="font-size:11px;color:#888">▼ Ver facturas</td>' +
                    '</tr>' +
                    '<tr class="sub-table" style="display:none"><td colspan="4">' +
                    '<table class="sub-table-inner"><thead><tr>' +
                    '<th>Factura</th><th>Cliente</th><th class="text-right">Total</th><th>Status Op.</th><th>Compra</th>' +
                    '</tr></thead><tbody>' +
                    (e.facturas || []).map(function(f) {{
                        var stCls = f.status === 'Entregado' ? 'status-entregado' : (f.status === 'Cancelación Total' ? 'status-cancelado' : (f.status === 'Congelado' ? 'status-congelado' : 'status-aprobado'));
                        return '<tr><td>' + f.name + '</td><td>' + f.cliente + '</td><td class="text-right">' + fmtMoney(f.total) + '</td><td><span class="' + stCls + '">' + (f.status || '') + '</span></td><td>' + (f.compra_status || '') + '</td></tr>';
                    }}).join('') +
                    '</tbody></table></td></tr>';
            }}).join('');
        }}
        
        // Top productos
        var tProd = document.getElementById('tablaTopProductos');
        if (tProd && fj.top_productos) {{
            tProd.innerHTML = fj.top_productos.map(function(p, idx) {{
                return '<tr class="clickable" onclick="toggleSubTable(this)">' +
                    '<td>' + (idx+1) + '</td>' +
                    '<td><strong>' + p.nombre + '</strong></td>' +
                    '<td class="text-right">' + p.qty.toLocaleString() + '</td>' +
                    '<td class="text-right">' + p.veces.toLocaleString() + '</td>' +
                    '<td class="text-right">' + fmtMoney(p.subtotal) + '</td>' +
                    '</tr>' +
                    '<tr class="sub-table" style="display:none"><td colspan="5">' +
                    '<table class="sub-table-inner"><thead><tr>' +
                    '<th>Factura</th><th>Cliente</th><th class="text-right">Cant.</th><th class="text-right">Subtotal</th>' +
                    '</tr></thead><tbody>' +
                    (p.lineas || []).map(function(l) {{
                        return '<tr><td>' + l.factura + '</td><td>' + l.cliente + '</td><td class="text-right">' + l.qty.toLocaleString() + '</td><td class="text-right">' + fmtMoney(l.subtotal) + '</td></tr>';
                    }}).join('') +
                    '</tbody></table></td></tr>';
            }}).join('');
        }}
        
        // Charts: Top productos — Cantidad vendida y Facturación (top 15)
        try {{
            var colores = (['#213C83','#2a4a96','#3458a8','#3D6194','#4a72a8','#5a82b8','#6a92c8','#7aa2d4','#8ab2e0','#9ac2ec','#aad0f0','#b8daf4','#c4e2f8','#d0eafc','#dcf0ff']);
            var shortName = function(p) {{ return p.nombre.length > 34 ? p.nombre.substring(0,32)+'...' : p.nombre; }};
            var topAll = (fj.top_productos || []).slice(0, 15);

            // Gráfica 1: Cantidad vendida (de mayor a menor)
            var topQty = topAll.slice().sort(function(a,b) {{ return b.qty - a.qty; }});
            var qtyCanvas = document.getElementById('chartTopProductosQty');
            if (qtyCanvas && topQty.length) {{
                safeChart('chartTopProductosQty', {{
                    type: 'bar',
                    data: {{
                        labels: topQty.map(shortName),
                        datasets: [{{ label: 'Cantidad', data: topQty.map(function(p) {{ return p.qty; }}), backgroundColor: colores.slice(0, topQty.length), borderWidth: 0, borderRadius: 4 }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{ callbacks: {{ label: function(ctx) {{ return '  ' + ctx.parsed.y + ' unidades'; }} }} }}
                        }},
                        scales: {{
                            y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }}, grid: {{ color: 'rgba(0,0,0,0.05)' }} }},
                            x: {{ ticks: {{ font: {{ size: 10 }}, maxRotation: 45, minRotation: 0 }}, grid: {{ display: false }} }}
                        }}
                    }}
                }});
            }}

            // Gráfica 2: Facturación (subtotal, de mayor a menor)
            var topSub = topAll.slice().sort(function(a,b) {{ return b.subtotal - a.subtotal; }});
            var tpCanvas = document.getElementById('chartTopProductos');
            if (tpCanvas && topSub.length) {{
                safeChart('chartTopProductos', {{
                    type: 'bar',
                    data: {{
                        labels: topSub.map(shortName),
                        datasets: [{{ data: topSub.map(function(p) {{ return p.subtotal; }}), backgroundColor: colores.slice(0, topSub.length), borderWidth: 0, borderRadius: 4 }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{ callbacks: {{ label: function(ctx) {{ return '  ' + fmtMoney(ctx.parsed.y); }} }} }}
                        }},
                        scales: {{
                            y: {{ ticks: {{ callback: function(v) {{ return fmtMoney(v); }} }}, grid: {{ color: 'rgba(0,0,0,0.05)' }} }},
                            x: {{ ticks: {{ font: {{ size: 10 }}, maxRotation: 45, minRotation: 0 }}, grid: {{ display: false }} }}
                        }}
                    }}
                }});
            }}
        }} catch(e) {{ console.error('Top productos chart error:', e); }}
        
        // Facturas
        var tbody = document.getElementById('tablaFactJulio');
        if (tbody) {{
            tbody.innerHTML = fj.facturas.map(function(f) {{
                var margenCls = f.margen >= 0 ? 'style="color:#10b981"' : 'style="color:#ef4444"';
                var stBadge = '<span class="badge" style="background:#e8ecf5;color:#374151">' + f.status + '</span>';
                var cpBadge = '<span class="badge" style="background:#dbeafe;color:#1e40af">' + f.compra_status + '</span>';
                return '<tr class="clickable" onclick="toggleSubTable(this)">' +
                    '<td><strong>' + f.cliente + '</strong></td>' +
                    '<td style="font-size:11px;color:#666">' + f.factura + '</td>' +
                    '<td>' + stBadge + '</td>' +
                    '<td>' + cpBadge + '</td>' +
                    '<td style="font-size:12px">' + f.ejecutivo + '</td>' +
                    '<td class="text-right">' + fmtMoney(f.total) + '</td>' +
                    '<td class="text-right">' + fmtMoney(f.precio_producto) + '</td>' +
                    '<td class="text-right">' + fmtMoney(f.gasto_admin) + '</td>' +
                    '<td class="text-right">' + fmtMoney(f.costo) + '</td>' +
                    '<td class="text-right" ' + margenCls + '>' + fmtMoney(f.margen) + '</td>' +
                    '</tr>' +
                    '<tr class="sub-table" style="display:none"><td colspan="10">' +
                    '<table class="sub-table-inner"><thead><tr>' +
                    '<th>Producto</th><th>Tipo</th><th class="text-right">Cant.</th><th class="text-right">Subtotal</th><th>Categoría</th><th>Equipo</th>' +
                    '</tr></thead><tbody>' +
                    (f.lineas || []).map(function(l) {{
                        var tipoCls = l.tipo==='GASTO ADMIN' ? 'style="color:#f59e0b"' : '';
                        return '<tr><td>' + l.producto + '</td><td ' + tipoCls + '>' + l.tipo + '</td><td class="text-right">' + l.cantidad.toLocaleString() + '</td><td class="text-right">' + fmtMoney(l.subtotal) + '</td><td style="font-size:11px">' + (l.categoria || '') + '</td><td style="font-size:11px">' + (l.equipo || '') + '</td></tr>';
                    }}).join('') +
                    '</tbody></table></td></tr>';
            }}).join('');
        }}
    }}
}} catch(e) {{ console.error('Facturacion Julio error:', e); }}

function renderCiclo(rango) {{
    document.querySelectorAll('.ciclo-btn').forEach(b => b.classList.toggle('active', b.dataset.rango === rango));
    const pp = DATA.payment_plan;
    if (!pp || !pp.ciclo_analysis) return;
    const dias = pp.ciclo_analysis[rango];
    if (!dias) return;
    const claves = Object.keys(dias).sort((a,b) => parseInt(a)-parseInt(b)).filter(function(k) {{
        var d = dias[k];
        return d.draft.cantidad > 0 || d.vencido.cantidad > 0 || d.paid.cantidad > 0;
    }});
    
    // Resumen
    var totalDraft = 0, totalVenc = 0, totalPaid = 0;
    var montoDraft = 0, montoVenc = 0, montoPaid = 0;
    var diasMoraSum = 0, diasMoraCount = 0;
    claves.forEach(function(d) {{
        var e = dias[d];
        totalDraft += e.draft.cantidad; montoDraft += e.draft.monto;
        totalVenc += e.vencido.cantidad; montoVenc += e.vencido.monto;
        totalPaid += e.paid.cantidad; montoPaid += e.paid.monto;
        if (e.vencido.dias_mora_prom > 0) {{ diasMoraSum += e.vencido.dias_mora_prom; diasMoraCount++; }}
    }});
    document.getElementById('cicloResumen').innerHTML =
        '<div class=\"mini-kpi\"><div class=\"mini-val\">' + totalDraft.toLocaleString() + '</div><div class=\"mini-lbl\">Cuotas Debidas</div><div class=\"mini-sub\">$' + montoDraft.toLocaleString('en-US',{{minimumFractionDigits:2}}) + '</div></div>' +
        '<div class=\"mini-kpi\" style=\"border-left:3px solid #ef4444\"><div class=\"mini-val\" style=\"color:#ef4444\">' + totalVenc.toLocaleString() + '</div><div class=\"mini-lbl\">Cuotas Vencidas</div><div class=\"mini-sub\">$' + montoVenc.toLocaleString('en-US',{{minimumFractionDigits:2}}) + '</div></div>' +
        '<div class=\"mini-kpi\" style=\"border-left:3px solid #10b981\"><div class=\"mini-val\" style=\"color:#10b981\">' + totalPaid.toLocaleString() + '</div><div class=\"mini-lbl\">Cuotas Pagadas</div><div class=\"mini-sub\">$' + montoPaid.toLocaleString('en-US',{{minimumFractionDigits:2}}) + '</div></div>' +
        '<div class=\"mini-kpi\" style=\"border-left:3px solid #f59e0b\"><div class=\"mini-val\" style=\"color:#f59e0b\">' + (diasMoraCount>0?(diasMoraSum/diasMoraCount).toFixed(1):'0') + 'd</div><div class=\"mini-lbl\">Días Mora Promedio</div></div>';
    
    // Tabla
    var html = '';
    claves.forEach(function(d) {{
        var e = dias[d];
        var hoy = new Date().getDate();
        var hoyClass = parseInt(d) === hoy ? ' style=\"background:#eef2ff;font-weight:700\"' : '';
        html += '<tr' + hoyClass + ' data-rango=\"' + rango + '\" data-dia=\"' + d + '\" style=\"cursor:pointer\">' +
            '<td><strong>Día ' + d + '</strong>' + (parseInt(d) === hoy ? '<span style=\"color:#213C83;font-size:10px;margin-left:6px\">HOY</span>' : '') + '</td>' +
            '<td class=\"text-right\">' + e.draft.cantidad + '</td>' +
            '<td class=\"text-right\">' + fmtMoney(e.draft.monto) + '</td>' +
            '<td class=\"text-right\" style=\"color:' + (e.vencido.cantidad>0?'#ef4444':'#999') + '\">' + e.vencido.cantidad + '</td>' +
            '<td class=\"text-right\" style=\"color:' + (e.vencido.monto>0?'#ef4444':'#999') + '\">' + fmtMoney(e.vencido.monto) + '</td>' +
            '<td class=\"text-right\">' + (e.vencido.dias_mora_prom>0?e.vencido.dias_mora_prom + 'd (' + e.vencido.max_dias_mora + 'd máx)':'—') + '</td>' +
            '<td class=\"text-right\">' + e.paid.cantidad + '</td>' +
            '<td class=\"text-right\">' + fmtMoney(e.paid.monto) + '</td>' +
            '</tr>';
    }});
    var tbody = document.getElementById('tablaCiclo');
    if (tbody) tbody.innerHTML = html;
    
    // Click handler via delegación
    tbody.onclick = function(e) {{
        var tr = e.target.closest('tr');
        if (tr && tr.dataset.rango && tr.dataset.dia) {{
            mostrarClientesDia(tr.dataset.rango, parseInt(tr.dataset.dia));
        }}
    }};
    
    // Mostrar clientes del primer día o del día de hoy
    var diaInicial = claves.includes(String(hoy)) ? String(hoy) : claves[0];
    mostrarClientesDia(rango, parseInt(diaInicial));
}}

function renderCicloResumen() {{
    var pp = DATA.payment_plan;
    if (!pp || !pp.ciclo_analysis) return;
    var rangos = ['03-18', '10-25'];
    rangos.forEach(function(r) {{
        var dias = pp.ciclo_analysis[r];
        if (!dias) return;
        var totalDebido = 0, totalVencido = 0, totalPagado = 0;
        Object.keys(dias).forEach(function(d) {{
            var dd = dias[d];
            totalDebido += dd.draft.monto;
            totalVencido += dd.vencido.monto;
            totalPagado += dd.paid.monto;
        }});
        var prefix = 'res' + r.replace('-', '');
        var elDebido = document.getElementById(prefix + 'Debido');
        var elVencido = document.getElementById(prefix + 'Vencido');
        var elPagado = document.getElementById(prefix + 'Pagado');
        if (elDebido) elDebido.textContent = fmtMoney(totalDebido);
        if (elVencido) elVencido.textContent = fmtMoney(totalVencido);
        if (elPagado) elPagado.textContent = fmtMoney(totalPagado);
    }});
}}

function renderManana() {{
    var hoy = new Date().getDate();
    var pp = DATA.payment_plan;
    if (!pp || !pp.ciclo_analysis) return;
    
    // Buscar el PRÓXIMO día de pago disponible después de hoy
    // Primero busca desde mañana hasta el día 25 del mes actual
    var candidatos = [];
    var rango = null;
    
    // Generar lista de días candidatos: desde mañana hasta 25
    for (var d = hoy + 1; d <= 25; d++) {{
        if ((d >= 3 && d <= 18) || (d >= 10 && d <= 25)) candidatos.push(d);
    }}
    // Si no hay candidatos este mes, buscar al inicio del próximo ciclo (días 3-18)
    if (candidatos.length === 0) {{
        for (var d = 3; d <= 18; d++) candidatos.push(d);
    }}
    
    var found = false;
    var diaData = null;
    var diaEncontrado = null;
    
    for (var i = 0; i < candidatos.length && !found; i++) {{
        var d = candidatos[i];
        if (d >= 3 && d <= 18) rango = '03-18';
        else if (d >= 10 && d <= 25) rango = '10-25';
        var dias = pp.ciclo_analysis[rango];
        if (dias) {{
            diaData = dias[String(d)];
            if (diaData && (diaData.draft.cantidad > 0 || diaData.vencido.cantidad > 0)) {{
                found = true;
                diaEncontrado = d;
            }}
        }}
    }}
    
    if (!found) {{
        document.getElementById('mananaDia').textContent = '-';
        document.getElementById('mananaTotal').textContent = '$0';
        document.getElementById('mananaClientes').textContent = '0';
        document.getElementById('mananaVencido').textContent = '$0';
        document.getElementById('mananaPagado').textContent = '$0';
        document.getElementById('mananaClientesSection').style.display = 'none';
        return;
    }}
    
    var label = (diaEncontrado === hoy + 1) ? '📅 MAÑANA — DÍA' : '📅 PRÓXIMO PAGO — DÍA';
    document.getElementById('mananaLabel').textContent = label;
    document.getElementById('mananaDia').textContent = diaEncontrado;
    document.getElementById('mananaTotal').textContent = fmtMoney(diaData.draft.monto);
    document.getElementById('mananaClientes').textContent = (diaData.clientes||[]).length;
    document.getElementById('mananaVencido').textContent = fmtMoney(diaData.vencido.monto);
    document.getElementById('mananaPagado').textContent = fmtMoney(diaData.paid.monto);
    
    // Poblar tabla de clientes de mañana
    var cl = diaData.clientes || [];
    var tbody = document.getElementById('tablaClientesManana');
    if (tbody) {{
        var totalEsperado = 0, totalVencido = 0, totalGeneral = 0;
        tbody.innerHTML = cl.map(function(c) {{
            var debido = c.monto_draft;
            var vencido = c.monto_vencido;
            var total = debido + vencido;
            totalEsperado += debido;
            totalVencido += vencido;
            totalGeneral += total;
            var statuses = c.statuses || [];
            var statusHtml = statuses.map(function(s) {{
                var cls = s === 'Entregado' ? 'status-entregado' : (s === 'Cancelación Total' ? 'status-cancelado' : (s === 'Congelado' ? 'status-congelado' : 'status-aprobado'));
                return '<span class="' + cls + '">' + s + '</span>';
            }}).join(' ');
            return '<tr>' +
                '<td><strong>' + c.cliente + '</strong></td>' +
                '<td class=\"text-right\" style=\"color:#10b981\">' + fmtMoney(debido) + '</td>' +
                '<td class=\"text-right\" style=\"color:' + (vencido>0?'#ef4444':'#999') + '\">' + fmtMoney(vencido) + '</td>' +
                '<td class=\"text-right\" style=\"font-weight:700\">' + fmtMoney(total) + '</td>' +
                '<td>' + statusHtml + '</td>' +
                '</tr>';
        }}).join('');
        // Agregar fila de total
        tbody.innerHTML +=
            '<tr style=\"background:#f0fdf4;font-weight:700\">' +
            '<td>TOTAL</td>' +
            '<td class=\"text-right\" style=\"color:#10b981\">' + fmtMoney(totalEsperado) + '</td>' +
            '<td class=\"text-right\" style=\"color:' + (totalVencido>0?'#ef4444':'#999') + '\">' + fmtMoney(totalVencido) + '</td>' +
            '<td class=\"text-right\">' + fmtMoney(totalGeneral) + '</td>' +
            '<td></td></tr>';
    }}
    var subtotal = document.getElementById('mananaClientesSubtotal');
    if (subtotal) subtotal.textContent = '— Esperado: ' + fmtMoney(diaData.draft.monto) + ' · Vencido: ' + fmtMoney(diaData.vencido.monto);
    document.getElementById('mananaClientesSection').style.display = 'block';
}}

function mostrarManana() {{
    var hoy = new Date().getDate();
    var pp = DATA.payment_plan;
    if (!pp || !pp.ciclo_analysis) return;
    // Buscar el mismo día que renderManana encontró
    var candidatos = [];
    for (var d = hoy + 1; d <= 25; d++) {{
        if ((d >= 3 && d <= 18) || (d >= 10 && d <= 25)) candidatos.push(d);
    }}
    if (candidatos.length === 0) {{
        for (var d = 3; d <= 18; d++) candidatos.push(d);
    }}
    var encontrado = null;
    var rango = null;
    for (var i = 0; i < candidatos.length && encontrado === null; i++) {{
        var d = candidatos[i];
        if (d >= 3 && d <= 18) rango = '03-18';
        else rango = '10-25';
        var dias = pp.ciclo_analysis[rango];
        if (dias) {{
            var dd = dias[String(d)];
            if (dd && (dd.draft.cantidad > 0 || dd.vencido.cantidad > 0)) encontrado = d;
        }}
    }}
    if (encontrado === null) return;
    // Buscar la fila en la tabla y hacer clic
    var tbody = document.getElementById('tablaCiclo');
    if (tbody) {{
        var trs = tbody.querySelectorAll('tr');
        for (var i = 0; i < trs.length; i++) {{
            if (parseInt(trs[i].dataset.dia) === encontrado) {{
                trs[i].click();
                trs[i].scrollIntoView({{behavior:'smooth', block:'center'}});
                break;
            }}
        }}
    }}
}}

function mostrarClientesDia(rango, dia) {{
    document.querySelectorAll('#tablaCiclo tr').forEach(function(r) {{
        r.style.background = parseInt(r.querySelector('td').textContent.replace(/[^0-9]/g,'')) === dia ? '#eef2ff' : '';
    }});
    var dias = DATA.payment_plan.ciclo_analysis[rango];
    if (!dias) return;
    var diaData = dias[String(dia)];
    if (!diaData || !diaData.clientes) return;
    var cl = diaData.clientes;
    var title = document.getElementById('cicloClientesTitle');
    if (title) title.textContent = '👥 Clientes — Día ' + dia + ' (' + cl.length + ' clientes)';
    var resumen = document.getElementById('cicloClientesResumen');
    if (resumen) {{
        var totDraft = 0, totVenc = 0, totPaid = 0;
        cl.forEach(function(c) {{ totDraft += c.monto_draft; totVenc += c.monto_vencido; totPaid += c.monto_pagado; }});
        resumen.innerHTML =
            '<span style=\"font-size:13px;color:#666\">Esperado: <strong>$' + (totDraft+totVenc).toLocaleString('en-US',{{minimumFractionDigits:2}}) + '</strong> &nbsp;·&nbsp; Cobrado: <strong style=\"color:#10b981\">$' + totPaid.toLocaleString('en-US',{{minimumFractionDigits:2}}) + '</strong></span>';
    }}
    var tbody = document.getElementById('tablaClientesDia');
    if (!tbody) return;
    tbody.innerHTML = cl.map(function(c) {{
        var statuses = c.statuses || [];
        var statusHtml = statuses.map(function(s) {{
            var cls = s === 'Entregado' ? 'status-entregado' : (s === 'Cancelación Total' ? 'status-cancelado' : (s === 'Congelado' ? 'status-congelado' : 'status-aprobado'));
            return '<span class="' + cls + '">' + s + '</span>';
        }}).join(' ');
        return '<tr>' +
            '<td><strong>' + c.cliente + '</strong></td>' +
            '<td class=\"text-right\">' + (c.cant_draft||0) + '</td>' +
            '<td class=\"text-right\">' + fmtMoney(c.monto_draft) + '</td>' +
            '<td class=\"text-right\" style=\"color:' + (c.monto_vencido>0?'#ef4444':'#999') + '\">' + (c.cant_vencido||0) + '</td>' +
            '<td class=\"text-right\" style=\"color:' + (c.monto_vencido>0?'#ef4444':'#999') + '\">' + fmtMoney(c.monto_vencido) + '</td>' +
            '<td class=\"text-right\" style=\"color:#10b981\">' + fmtMoney(c.monto_pagado) + '</td>' +
            '<td>' + statusHtml + '</td>' +
            '</tr>';
    }}).join('');
}}

// ================================================================
//  EXPEDIENTES
// ================================================================
try {{
    var ex = DATA.expedientes;
    if (ex) {{
        // ex puede ser array (formato previo) o {grupos, totales} (nuevo)
        var exGrupos = Array.isArray(ex) ? ex : (ex.grupos || []);
        var exTot = (ex && !Array.isArray(ex) && ex.totales) ? ex.totales : null;
        // Totales
        var totLineas = 0, totMonto = 0, totUsadas = 0, totNoUsadas = 0, totCad = 0;
        var totMenor = 0, tot3K6K = 0, totMayor = 0;
        exGrupos.forEach(function(g) {{
            totLineas += g.total_clientes || 0;
            totMonto += g.total_monto || 0;
            totUsadas += g.usadas || 0;
            totNoUsadas += g.no_usadas || 0;
            totCad += g.caducados || 0;
            totMenor += g.rango_menor_3000 || 0;
            tot3K6K += g.rango_3000_6000 || 0;
            totMayor += g.rango_mayor_6000 || 0;
        }});
        if (exTot) {{
            totLineas = exTot.total_lineas || totLineas;
            totMonto = exTot.monto || exTot.total_monto || totMonto;
            totUsadas = exTot.usadas || totUsadas;
            totNoUsadas = exTot.no_usadas || totNoUsadas;
            totCad = exTot.caducados || totCad;
        }}
        document.getElementById('expTotalLineas').textContent = totLineas.toLocaleString();
        document.getElementById('expTotalMonto').textContent = fmtMoney(totMonto);
        document.getElementById('expUsadas').textContent = totUsadas.toLocaleString();
        document.getElementById('expNoUsadas').textContent = totNoUsadas.toLocaleString();
        document.getElementById('expCaducadas').textContent = totCad.toLocaleString();
        document.getElementById('expMenor3K').textContent = totMenor.toLocaleString();
        document.getElementById('exp3K6K').textContent = tot3K6K.toLocaleString();
        document.getElementById('expMayor6K').textContent = totMayor.toLocaleString();

        // Tabla de expedientes
        var teBody = document.getElementById('tablaExpedientes');
        if (teBody) {{
            var mesi = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
            teBody.innerHTML = exGrupos.map(function(g) {{
                var datosExtra = (g.clientes || []).map(function(c) {{
                    var stCls = c.usada ? 'status-entregado' : (c.caducado ? 'status-cancelado' : 'status-aprobado');
                    var stTxt = c.usada ? 'Usada' : (c.caducado ? 'Caducada' : 'No usada');
                    return '<tr><td>' + (c.name||'') + '</td><td class="text-right">' + fmtMoney(c.limite) + '</td><td>' + (c.fecha_activacion||'') + '</td><td><span class="' + stCls + '">' + stTxt + '</span></td></tr>';
                }}).join('');
                var mostAnio = g.year ? g.year : '—';
                var mostMes = g.month ? (mesi[(g.month||1)-1]) : (g.label || '—');
                return '<tr class="clickable" onclick="toggleSubTable(this)">' +
                    '<td><strong>' + mostAnio + '</strong></td>' +
                    '<td><strong>' + mostMes + '</strong></td>' +
                    '<td class="text-right">' + g.rango_menor_3000 + '</td>' +
                    '<td class="text-right">' + g.rango_3000_6000 + '</td>' +
                    '<td class="text-right">' + g.rango_mayor_6000 + '</td>' +
                    '<td class="text-right">' + g.total_clientes + '</td>' +
                    '<td class="text-right">' + fmtMoney(g.total_monto) + '</td>' +
                    '<td class="text-right" style="color:#10b981">' + (g.usadas||0) + '</td>' +
                    '<td class="text-right" style="color:#f59e0b">' + (g.no_usadas||0) + '</td>' +
                    '<td class="text-right" style="color:#ef4444">' + (g.caducados||0) + '</td>' +
                    '<td style="font-size:11px;color:#888">▼ Ver</td></tr>' +
                    '<tr class="sub-table" style="display:none"><td colspan="11">' +
                    '<table class="sub-table-inner"><thead><tr><th>Cliente</th><th class="text-right">Límite</th><th>Activación</th><th>Estado</th></tr></thead><tbody>' +
                    (datosExtra || '<tr><td colspan="4" style="text-align:center;color:#999">Sin clientes detallados</td></tr>') +
                    '</tbody></table></td></tr>';
            }}).join('') || '<tr><td colspan="11" style="text-align:center;color:#999">Sin datos</td></tr>';
        }}

        // Grafico de expedientes por mes/rango
        try {{
            var exCanvas = document.getElementById('chartExpedientes');
            if (exCanvas && exGrupos.length) {{
                var labels = exGrupos.map(function(g) {{ return g.year && g.month ? (g.year + '-' + String(g.month).padStart(2,'0')) : (g.label || 'Sin activar'); }});
                var dMenor = exGrupos.map(function(g) {{ return g.rango_menor_3000; }});
                var d3K6K = exGrupos.map(function(g) {{ return g.rango_3000_6000; }});
                var dMayor = exGrupos.map(function(g) {{ return g.rango_mayor_6000; }});
                safeChart('chartExpedientes', {{
                    type: 'bar',
                    data: {{
                        labels: labels,
                        datasets: [
                            {{ label: '< $3,000', data: dMenor, backgroundColor: '#213C83', borderWidth: 0, borderRadius: 4 }},
                            {{ label: '$3K-$6K', data: d3K6K, backgroundColor: '#F98B10', borderWidth: 0, borderRadius: 4 }},
                            {{ label: '> $6,000', data: dMayor, backgroundColor: '#10b981', borderWidth: 0, borderRadius: 4 }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ position: 'bottom' }}, tooltip: {{ mode: 'index', intersect: false }} }},
                        scales: {{
                            y: {{ beginAtZero: true, ticks: {{ precision: 0 }}, grid: {{ color: 'rgba(0,0,0,0.05)' }} }},
                            x: {{ stacked: true, grid: {{ display: false }} }}
                        }}
                    }}
                }});
            }}
        }} catch(e) {{ console.error('Expedientes chart error:', e); }}
    }}
}} catch(e) {{ console.error('Expedientes error:', e); }}

// ── Pronto Pago: clientes que pagan antes del vencimiento ──
try {{
    var pp = (DATA.payment_plan || {{}}).pronto_pago || [];
    var ppTot = (DATA.payment_plan || {{}}).total_pronto || {{}};
    var top10 = (DATA.payment_plan || {{}}).top10_impacto || [];
    document.getElementById('ppClientes').textContent = (ppTot.clientes || 0).toLocaleString();
    document.getElementById('ppMonto').textContent = fmtMoney(ppTot.monto || 0);
    document.getElementById('ppCuotas').textContent = (ppTot.cuotas || 0).toLocaleString();
    document.getElementById('ppPromedio').textContent = fmtMoney(ppTot.monto_promedio || 0);
    document.getElementById('ppDias').textContent = (ppTot.dias_ponderado || 0) + ' días';
    document.getElementById('ppPenetracion').textContent = (ppTot.penetracion || 0).toFixed(2) + '%';
    document.getElementById('ppOro').textContent = (ppTot.oro || 0);
    document.getElementById('ppPlata').textContent = (ppTot.plata || 0);
    document.getElementById('ppBronce').textContent = (ppTot.bronce || 0);

    // Gráfico Top 10 Impacto
    try {{
        var labels10 = top10.map(function(c) {{ return c.cliente.split(' ').slice(0,2).join(' '); }});
        var montos10 = top10.map(function(c) {{ return c.monto; }});
        var cuotas10 = top10.map(function(c) {{ return c.cuotas; }});
        safeChart('chartTop10PP', {{
            type: 'bar',
            data: {{
                labels: labels10,
                datasets: [
                    {{ label: 'Monto ($)', data: montos10, backgroundColor: '#213C83', borderWidth: 0, borderRadius: 4, yAxisID: 'y' }},
                    {{ label: 'Cuotas', data: cuotas10, backgroundColor: '#F98B10', borderWidth: 0, borderRadius: 4, yAxisID: 'y1' }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom' }}, tooltip: {{ mode: 'index', intersect: false }} }},
                scales: {{
                    y: {{ beginAtZero: true, position: 'left', ticks: {{ callback: function(v) {{ return '$' + v.toLocaleString(); }} }}, grid: {{ color: 'rgba(0,0,0,0.05)' }}, title: {{ display: true, text: 'Monto ($)' }} }},
                    y1: {{ beginAtZero: true, position: 'right', ticks: {{ precision: 0 }}, grid: {{ drawOnChartArea: false }}, title: {{ display: true, text: 'Cuotas' }} }},
                    x: {{ grid: {{ display: false }} }}
                }}
            }}
        }});
    }} catch(e) {{ console.error('Top10 chart error:', e); }}

    // Tabla con flags
    var ppBody = document.getElementById('tablaProntoPago');
    if (ppBody) {{
        ppBody.innerHTML = pp.map(function(c) {{
            var facts = (c.facturas || []).map(function(f) {{
                var url = 'https://latinbien.com/web#id=' + f.id + '&model=account.move&view_type=form';
                return '<a href="' + url + '" target="_blank" style="color:#213C83;text-decoration:none;border-bottom:1px dashed #213C83">' + f.name + '</a>';
            }}).join(', ');
            var flagHtml = '';
            var flagCls = '';
            if (c.flag === 'oro') {{ flagHtml = '<span style="background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:4px;font-weight:700;border:1px solid #f59e0b">🏆 ORO</span>'; flagCls = 'border-left:4px solid #f59e0b'; }}
            else if (c.flag === 'plata') {{ flagHtml = '<span style="background:#e5e7eb;color:#374151;padding:2px 8px;border-radius:4px;font-weight:700;border:1px solid #9ca3af">🥈 PLATA</span>'; flagCls = 'border-left:4px solid #9ca3af'; }}
            else {{ flagHtml = '<span style="background:#fed7aa;color:#9a3412;padding:2px 8px;border-radius:4px;font-weight:700;border:1px solid #f97316">🥉 BRONCE</span>'; flagCls = 'border-left:4px solid #f97316'; }}
            return '<tr style="' + flagCls + '">' +
                '<td>' + flagHtml + '</td>' +
                '<td><strong>' + (c.cliente || '') + '</strong></td>' +
                '<td class="text-right">' + c.cuotas + '</td>' +
                '<td class="text-right">' + fmtMoney(c.monto) + '</td>' +
                '<td style="font-size:12px;max-width:250px">' + facts + '</td>' +
                '<td>' + (c.fecha_mas_lejana || '') + '</td>' +
                '<td class="text-right"><span style="background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:4px;font-weight:600">' + c.max_dias + ' días</span></td>' +
                '<td style="font-size:11px;color:#555;max-width:280px">' + (c.accion || '') + '</td>' +
                '</tr>';
        }}).join('') || '<tr><td colspan="8" style="text-align:center;color:#999">Sin pronto pago registrado</td></tr>';
    }}
}} catch(e) {{ console.error('Pronto Pago error:', e); }}

// ── Proyección por Ciclos: pagadas vs pendientes por mes ──
try {{
    var cp = (DATA.payment_plan || {{}}).ciclo_proj || {{}};
    var mesN = {{'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun','07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'}};

    function fmtMes(m) {{
        var p = m.split('-');
        return mesN[p[1]] + ' ' + p[0];
    }}

    // KPIs de agosto
    var ago0318 = ((cp['03-18'] || {{}})['2026-08'] || {{}});
    var ago1025 = ((cp['10-25'] || {{}})['2026-08'] || {{}});
    document.getElementById('ciclo0318Clientes').textContent = ((ago0318.pagadas_clientes||0) + (ago0318.pendientes_clientes||0)).toLocaleString();
    document.getElementById('ciclo0318Pagado').textContent = fmtMoney(ago0318.pagadas_monto || 0);
    document.getElementById('ciclo0318Pendiente').textContent = fmtMoney(ago0318.pendientes_monto || 0);
    document.getElementById('ciclo1025Clientes').textContent = ((ago1025.pagadas_clientes||0) + (ago1025.pendientes_clientes||0)).toLocaleString();
    document.getElementById('ciclo1025Pagado').textContent = fmtMoney(ago1025.pagadas_monto || 0);
    document.getElementById('ciclo1025Pendiente').textContent = fmtMoney(ago1025.pendientes_monto || 0);

    // Gráficos por ciclo
    ['03-18', '10-25'].forEach(function(ciclo) {{
        var data = cp[ciclo] || {{}};
        var canvasId = ciclo === '03-18' ? 'chartCiclo0318' : 'chartCiclo1025';
        var labels = Object.keys(data).sort().map(fmtMes);
        var pagCuotas = Object.keys(data).sort().map(function(m) {{ return data[m].pagadas_cuotas; }});
        var pendCuotas = Object.keys(data).sort().map(function(m) {{ return data[m].pendientes_cuotas; }});
        var pagMonto = Object.keys(data).sort().map(function(m) {{ return data[m].pagadas_monto; }});
        var pendMonto = Object.keys(data).sort().map(function(m) {{ return data[m].pendientes_monto; }});

        try {{
            safeChart(canvasId, {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [
                        {{ label: 'Pagadas (cuotas)', data: pagCuotas, backgroundColor: '#10b981', borderWidth: 0, borderRadius: 4, yAxisID: 'y' }},
                        {{ label: 'Pendientes (cuotas)', data: pendCuotas, backgroundColor: '#ef4444', borderWidth: 0, borderRadius: 4, yAxisID: 'y' }},
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'bottom' }},
                        tooltip: {{
                            mode: 'index',
                            intersect: false,
                            callbacks: {{
                                afterBody: function(items) {{
                                    var idx = items[0].dataIndex;
                                    var mes = Object.keys(data).sort()[idx];
                                    var d = data[mes];
                                    return [
                                        '───────────',
                                        '$ Pagado: ' + fmtMoney(d.pagadas_monto),
                                        '$ Pendiente: ' + fmtMoney(d.pendientes_monto),
                                        'Clientes al día: ' + (d.pagadas_clientes||0),
                                        'Clientes adeudan: ' + (d.pendientes_clientes||0)
                                    ];
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true, ticks: {{ precision: 0 }}, grid: {{ color: 'rgba(0,0,0,0.05)' }}, title: {{ display: true, text: 'Cuotas' }} }},
                        x: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});
        }} catch(e) {{ console.error('Chart ' + canvasId + ' error:', e); }}
    }});

}} catch(e) {{ console.error('Ciclos error:', e); }}

// ── Proyección por Fecha de Cobro ──
try {{
    var fc = (DATA.payment_plan || {{}}).fecha_cobro || {{}};
    var mesN = {{'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun','07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'}};
    function fmtMesFc(m) {{ var p = m.split('-'); return mesN[p[1]] + ' ' + p[0]; }}

    // Gráfico de barras: Pendiente vs Pagado por fecha
    try {{
        var fcLabels = [];
        var fcPendiente = [];
        var fcPagado = [];
        Object.keys(fc).sort().forEach(function(mes) {{
            var dias = fc[mes];
            Object.keys(dias).sort(function(a,b) {{ return dias[a].dia - dias[b].dia; }}).forEach(function(dk) {{
                var d = dias[dk];
                fcLabels.push(fmtMesFc(mes) + ' / ' + d.dia);
                fcPendiente.push(d.pendiente_monto);
                fcPagado.push(d.pagado_monto);
            }});
        }});
        if (fcLabels.length > 0) {{
            safeChart('chartFechaCobro', {{
                type: 'bar',
                data: {{
                    labels: fcLabels,
                    datasets: [
                        {{ label: 'Pendiente Recibir ($)', data: fcPendiente, backgroundColor: '#ef4444', borderWidth: 0, borderRadius: 4 }},
                        {{ label: 'Ya Pagaron ($)', data: fcPagado, backgroundColor: '#10b981', borderWidth: 0, borderRadius: 4 }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'bottom' }},
                        tooltip: {{ mode: 'index', intersect: false, callbacks: {{ afterBody: function(items) {{ var idx = items[0].dataIndex; var total = fcPendiente[idx] + fcPagado[idx]; return ['───────────', 'Total Esperado: ' + fmtMoney(total)]; }} }} }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true, ticks: {{ callback: function(v) {{ return '$' + v.toLocaleString(); }} }}, grid: {{ color: 'rgba(0,0,0,0.05)' }}, title: {{ display: true, text: 'Monto ($)' }} }},
                        x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 45, font: {{ size: 10 }} }} }}
                    }}
                }}
            }});
        }}
    }} catch(e) {{ console.error('Chart Fecha Cobro error:', e); }}

    // Tabla
    var fcBody = document.getElementById('tablaFechaCobro');
    if (fcBody) {{
        var rows = [];
        Object.keys(fc).sort().forEach(function(mes) {{
            var dias = fc[mes];
            var mesTotal = 0;
            Object.keys(dias).forEach(function(dk) {{ mesTotal += dias[dk].pendiente_monto + dias[dk].pagado_monto; }});
            Object.keys(dias).sort(function(a,b) {{ return dias[a].dia - dias[b].dia; }}).forEach(function(dk) {{
                var d = dias[dk];
                var total = d.pendiente_monto + d.pagado_monto;
                var pct = mesTotal > 0 ? Math.round(total / mesTotal * 100) : 0;
                rows.push('<tr>' +
                    '<td><strong>' + fmtMesFc(mes) + '</strong></td>' +
                    '<td>Día ' + d.dia + '</td>' +
                    '<td>' + (d.ciclo === '03-18' ? '<span style="background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:4px;font-size:11px">03-18</span>' : '<span style="background:#fce7f3;color:#9d174d;padding:2px 8px;border-radius:4px;font-size:11px">10-25</span>') + '</td>' +
                    '<td class="text-right" style="color:#ef4444;font-weight:600">' + fmtMoney(d.pendiente_monto) + '</td>' +
                    '<td class="text-right">' + d.pendiente_clientes + '</td>' +
                    '<td class="text-right" style="color:#10b981;font-weight:600">' + fmtMoney(d.pagado_monto) + '</td>' +
                    '<td class="text-right">' + d.pagado_clientes + '</td>' +
                    '<td class="text-right" style="font-weight:700">' + fmtMoney(total) + ' <span style="color:#888;font-size:10px">(' + pct + '%)</span></td>' +
                    '</tr>');
            }});
        }});
        fcBody.innerHTML = rows.join('') || '<tr><td colspan="8" style="text-align:center;color:#999">Sin datos de proyección</td></tr>';
    }}
}} catch(e) {{ console.error('Fecha cobro error:', e); }}

// ── Gestión de Cobranza por Ciclo ──
try {{
    var gg = (DATA.payment_plan || {{}}).ciclo_gestion || {{}};
    var ggItems = gg.items || [];
    var ggRes = gg.resumen || {{}};
    var ggHoy = gg.hoy || '';

    var r0318 = ggRes['03-18'] || {{}};
    var r1025 = ggRes['10-25'] || {{}};
    document.getElementById('gTotal0318').textContent = (r0318.total||0).toLocaleString();
    document.getElementById('gPend0318').textContent = fmtMoney(r0318.monto||0);
    document.getElementById('gTotal1025').textContent = (r1025.total||0).toLocaleString();
    document.getElementById('gPend1025').textContent = fmtMoney(r1025.monto||0);

    window._gfCiclo = 'todos';
    window._gfFecha = '';

    function faseL(f) {{
        return {{'2_dias_antes':'2 días antes','1_dia_antes':'1 día antes','dia_ciclo':'Día del ciclo','1_dia_despues':'1 día después','2_dias_despues':'2+ días después','pasado':'Pasado'}}[f] || f;
    }}
    function moraColor(m) {{
        return {{'critico':'#dc2626','alto':'#ea580c','medio':'#d97706','hoy':'#0ea5e9','pendiente':'#10b981'}}[m] || '#6b7280';
    }}
    function moraLabel(m) {{
        return {{'critico':'🔴 CRÍTICO','alto':'🟠 ALTO','medio':'🟡 MEDIO','hoy':'🔵 HOY','pendiente':'🟢 PENDIENTE'}}[m] || m;
    }}

    window.filtrarGestion = function(ciclo) {{
        window._gfCiclo = ciclo;
        document.querySelectorAll('.btn-gestion').forEach(function(b) {{ b.style.fontWeight='normal'; b.style.boxShadow='none'; }});
        event.target.style.fontWeight='700';
        event.target.style.boxShadow='0 0 0 2px #213C83';
        renderGestion();
    }};
    window.aplicarFiltrosGestion = function() {{ renderGestion(); }};

    function renderGestion() {{
        var fc = document.getElementById('filtroFase').value;
        var fd = document.getElementById('filtroFecha').value;
        var filtered = ggItems.filter(function(x) {{
            if (window._gfCiclo !== 'todos' && x.ciclo !== window._gfCiclo) return false;
            if (fc !== 'todas' && x.fase !== fc) return false;
            if (fd && x.fecha_pago !== fd) return false;
            return true;
        }});
        var body = document.getElementById('tablaGestion');
        var cont = document.getElementById('gContador');
        if (!body) return;
        var html = filtered.slice(0, 500).map(function(x) {{
            var url = 'https://latinbien.com/web#id=' + x.invoice_id + '&model=account.move&view_type=form';
            var cc = x.ciclo === '03-18' ? 'background:#dbeafe;color:#1e40af' : 'background:#fce7f3;color:#9d174d';
            var mc = moraColor(x.morosidad);
            return '<tr>' +
                '<td><span style="padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;' + cc + '">' + x.ciclo + '</span></td>' +
                '<td style="color:' + mc + ';font-weight:600;font-size:12px">' + moraLabel(x.morosidad) + '</td>' +
                '<td style="font-size:12px">' + faseL(x.fase) + '</td>' +
                '<td style="font-size:11px;color:#888">' + x.status_op + '</td>' +
                '<td><strong>' + x.cliente + '</strong></td>' +
                '<td><a href="' + url + '" target="_blank" style="color:#213C83;text-decoration:none;border-bottom:1px dashed #213C83;font-size:12px">' + x.factura + '</a></td>' +
                '<td style="font-size:12px">' + x.fecha_pago + '</td>' +
                '<td class="text-right" style="font-weight:600">' + fmtMoney(x.monto) + '</td>' +
                '<td class="text-right">' + x.cuotas + '</td>' +
                '<td class="text-right" style="color:' + mc + ';font-weight:700">' + x.diff_dias + '</td>' +
                '</tr>';
        }}).join('');
        body.innerHTML = html || '<tr><td colspan="10" style="text-align:center;color:#999">Sin datos para este filtro</td></tr>';
        cont.textContent = filtered.length + ' facturas de ' + ggItems.length + ' totales' + (fd ? ' (fecha: ' + fd + ')' : '');
    }}

    window.exportarGestionXLSX = function() {{
        var fc = document.getElementById('filtroFase').value;
        var fd = document.getElementById('filtroFecha').value;
        var filtered = ggItems.filter(function(x) {{
            if (window._gfCiclo !== 'todos' && x.ciclo !== window._gfCiclo) return false;
            if (fc !== 'todas' && x.fase !== fc) return false;
            if (fd && x.fecha_pago !== fd) return false;
            return true;
        }});
        var data = [['Nombre', 'Telefono']];
        var seen = {{}};
        filtered.forEach(function(x) {{
            var phone = (x.phone || '').replace(/[^0-9+]/g, '');
            var key = x.cliente + '|' + phone;
            if (seen[key]) return;
            seen[key] = true;
            data.push([x.cliente, phone]);
        }});
        var wb = XLSX.utils.book_new();
        var ws = XLSX.utils.aoa_to_sheet(data);
        XLSX.utils.book_append_sheet(wb, ws, 'Cobranza');
        XLSX.writeFile(wb, 'gestion_cobranza_' + ggHoy + '_' + window._gfCiclo + '.xlsx');
    }};

    renderGestion();
}} catch(e) {{ console.error('Gestion cobranza error:', e); }}

// ── Ventas Motos ──
try {{
    var vm = DATA.ventas_motos || {{}};
    document.getElementById('vmTotal').textContent = (vm.total_ordenes||0).toLocaleString();
    document.getElementById('vmMonto').textContent = fmtMoney(vm.total_monto||0);
    document.getElementById('vmMotos').textContent = (vm.total_motos||0).toLocaleString();
    document.getElementById('vmProducto').textContent = fmtMoney(vm.total_producto||0);
    document.getElementById('vmGasto').textContent = fmtMoney(vm.total_gasto_admin||0);

    // Tabla órdenes
    var vmItems = vm.items || [];
    var vmOrdBody = document.getElementById('tablaOrdenesMotos');
    if (vmOrdBody && vmItems.length) {{
        vmOrdBody.innerHTML = vmItems.map(function(it) {{
            var ordUrl = 'https://latinbien.com/web#id=' + (it.orden_id||0) + '&model=sale.order&view_type=form';
            var credTag = it.credimoto ? '<span style="background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;border:1px solid #f59e0b">CREDIMOTO</span>' : '<span style="color:#ccc">—</span>';
            return '<tr>' +
                '<td><a href="' + ordUrl + '" target="_blank" style="color:#213C83;font-weight:600;text-decoration:none;border-bottom:1px dashed #213C83">' + it.orden + '</a></td>' +
                '<td><strong>' + it.cliente + '</strong></td>' +
                '<td>' + credTag + '</td>' +
                '<td>' + it.modelo + '</td>' +
                '<td class="text-right" style="font-weight:600">' + fmtMoney(it.precio_producto) + '</td>' +
                '<td class="text-right" style="color:#888">' + fmtMoney(it.gasto_admin) + '</td>' +
                '<td class="text-right" style="font-weight:700">' + fmtMoney(it.monto_total) + '</td>' +
                '<td>' + it.mes + '</td>' +
                '</tr>';
        }}).join('');
    }}
}} catch(e) {{ console.error('Ventas Motos error:', e); }}

// ── Pago Proveedor Moto ──
try {{
    var ppm = DATA.pago_proveedor_moto || {{}};
    document.getElementById('ppmOrdenCompra').textContent = ppm.orden_compra || 'P01382';
    document.getElementById('ppmProvedor').textContent = ppm.proveedor || '';
    document.getElementById('ppmOrdenes').textContent = (ppm.total_ordenes||0).toLocaleString();
    document.getElementById('ppmInicial').textContent = fmtMoney(ppm.total_pagoInicial||0);
    document.getElementById('ppmFinanciado').textContent = fmtMoney(ppm.total_financiado||0);

    var ppmItems = ppm.items || [];
    var ppmBody = document.getElementById('tablaPagoProveedor');
    if (ppmBody && ppmItems.length) {{
        ppmBody.innerHTML = ppmItems.map(function(it) {{
            var puUrl = 'https://latinbien.com/web#id=' + (it.purchase_order_id||0) + '&model=purchase.order&view_type=form';
            return '<tr>' +
                '<td><a href="' + puUrl + '" target="_blank" style="color:#213C83;font-weight:700;text-decoration:none;border-bottom:2px solid #213C83;font-size:14px">' + (it.orden_compra||'P01382') + '</a></td>' +
                '<td><strong>' + (it.cliente||'') + '</strong></td>' +
                '<td>' + (it.modelo||'') + '</td>' +
                '<td>' + (it.ciclo||'') + '</td>' +
                '<td><span style="background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">' + (it.opcion||'') + '</span></td>' +
                '<td class="text-right" style="font-weight:600">' + fmtMoney(it.precio_moto||0) + '</td>' +
                '<td class="text-right" style="color:#059669;font-weight:700">' + fmtMoney(it.inicial_40||0) + '</td>' +
                '<td class="text-right" style="color:#2563eb;font-weight:600">' + fmtMoney(it.restante_60||0) + '</td>' +
                '<td class="text-right">' + fmtMoney(it.cuota_quincenal||0) + '</td>' +
                '</tr>';
        }}).join('');
    }}

    // Cronograma
    var cronBody = document.getElementById('tablaCronograma');
    if (cronBody && ppmItems.length) {{
        var cronHtml = '';
        ppmItems.forEach(function(it) {{
            it.pagos.forEach(function(p) {{
                var hoy = new Date().toISOString().slice(0, 10);
                var esHoy = p.fecha_pago === hoy;
                var esProximo = new Date(p.fecha_pago) <= new Date(hoy);
                var btnHtml = '';
                if (esProximo) {{
                    var asunto = encodeURIComponent('Recordatorio Interno - Pago Proveedor: Cuota ' + p.cuota + '/8 - ' + it.orden_compra + ' - MOTO CITY PRO');
                    var cuerpo = encodeURIComponent('RECORDATORIO INTERNO DE PAGO A PROVEEDOR\\n\\n' +
                        'Proveedor: MOTO CITY PRO, C.A.\\n' +
                        'Orden de Compra: ' + it.orden_compra + '\\n' +
                        'Orden de Venta: ' + (it.orden_venta||'N/A') + '\\n' +
                        'Cliente: ' + (it.cliente||'') + '\\n' +
                        'Modelo: ' + (it.modelo||'') + '\\n' +
                        'Cuota: ' + p.cuota + '/8\\n' +
                        'Monto: $' + p.monto.toFixed(2) + '\\n' +
                        'Fecha de Pago: ' + p.fecha_pago + '\\n' +
                        'Ciclo: ' + (it.ciclo||'') + ' (Opción ' + (it.opcion||'') + ')\\n\\n' +
                        'Este es un recordatorio interno. Favor confirmar el pago.');
                    btnHtml = '<a href="mailto:?subject=' + asunto + '&body=' + cuerpo + '" style="display:inline-block;background:#059669;color:white;padding:3px 10px;border-radius:4px;text-decoration:none;font-size:11px;font-weight:600">📧 Recordar</a>';
                }}
                cronHtml += '<tr' + (esProximo ? ' style="background:#fef3c7"' : '') + '>' +
                    '<td>' + (it.orden_compra||'P01382') + '</td>' +
                    '<td><strong>' + (it.cliente||'') + '</strong></td>' +
                    '<td class="text-right">Cuota ' + p.cuota + '/8</td>' +
                    '<td>' + p.fecha_pago + (esHoy ? ' <strong style="color:#dc2626">HOY</strong>' : '') + '</td>' +
                    '<td class="text-right" style="font-weight:600">' + fmtMoney(p.monto) + '</td>' +
                    '<td><span style="background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:4px;font-size:11px">Pendiente</span></td>' +
                    '<td>' + btnHtml + '</td>' +
                    '</tr>';
            }});
        }});
        cronBody.innerHTML = cronHtml || '<tr><td colspan="6" style="text-align:center;color:#999">Sin cronograma</td></tr>';
    }}
}} catch(e) {{ console.error('Pago Proveedor error:', e); }}

// ── Facturación Agosto 2026 ──
try {{
    var fa = DATA.facturacion_agosto || {{}};
    document.getElementById('faTotalFacturado').textContent = fmtMoney(fa.total_facturado||0);
    document.getElementById('faTotalProductos').textContent = fmtMoney(fa.total_productos||0);
    document.getElementById('faTotalAdmin').textContent = fmtMoney(fa.total_admin||0);
    document.getElementById('faTotalCosto').textContent = fmtMoney(fa.total_costo||0);
    document.getElementById('faTotalMargen').textContent = fmtMoney(fa.total_margen||0);
    document.getElementById('faTotalFacturas').textContent = (fa.total_facturas||0).toLocaleString();
    document.getElementById('faTotalClientes').textContent = (fa.total_clientes||0).toLocaleString();
    document.getElementById('faCancelacionesMonto').textContent = fmtMoney(fa.cancelaciones_monto||0);
    document.getElementById('faCancelacionesLbl').textContent = (fa.cancelaciones_count||0) + ' Cancelaciones';

    var faBody = document.getElementById('tablaFactAgosto');
    var faFacts = fa.facturas || [];
    if (faBody && faFacts.length) {{
        faBody.innerHTML = faFacts.map(function(f) {{
            var stCls = f.status === 'Entregado' ? 'status-entregado' : (f.status === 'Cancelación Total' ? 'status-cancelado' : 'status-aprobado');
            return '<tr><td style="font-weight:600">' + (f.orden||'') + '</td>' +
                '<td>' + (f.cliente||'') + '</td>' +
                '<td>' + (f.ejecutivo||'') + '</td>' +
                '<td class="text-right">' + fmtMoney(f.monto) + '</td>' +
                '<td class="text-right">' + fmtMoney(f.costo) + '</td>' +
                '<td style="font-size:12px">' + (f.fecha||'') + '</td>' +
                '<td><span class="' + stCls + '">' + (f.status||'') + '</span></td></tr>';
        }}).join('');
    }}
}} catch(e) {{ console.error('Fact Agosto error:', e); }}

// ── Análisis Operativo Agosto 2026 (Google Sheets) ──
try {{
    var ao = DATA.agosto_operativo || {{}};
    var aoRes = ao.resumen || {{}};
    var aoPri = ao.por_prioridad || {{}};
    var aoEst = ao.por_estado || {{}};
    var aoTareas = ao.tareas || [];

    // KPIs
    document.getElementById('aoTotal').textContent = (aoRes.total||0).toLocaleString();
    document.getElementById('aoCompletadas').textContent = (aoRes.completadas||0).toLocaleString();
    document.getElementById('aoEnCurso').textContent = (aoRes.en_curso||0).toLocaleString();
    document.getElementById('aoBloqueadas').textContent = (aoRes.bloqueadas||0).toLocaleString();
    document.getElementById('aoNoIniciadas').textContent = (aoRes.no_iniciadas||0).toLocaleString();
    document.getElementById('aoPctCompletadas').textContent = (aoRes.pct_completadas||0) + '%';
    document.getElementById('aoPctEnCurso').textContent = (aoRes.pct_en_curso||0) + '%';
    document.getElementById('aoPctBloqueadas').textContent = (aoRes.pct_bloqueadas||0) + '%';

    // ── Gráfico: Distribución por Estado (Doughnut) ──
    var ctxEstado = document.getElementById('chartAoEstado');
    if (ctxEstado && typeof Chart !== 'undefined') {{
        new Chart(ctxEstado, {{
            type: 'doughnut',
            data: {{
                labels: ['Completadas', 'En Curso', 'Bloqueadas', 'No Iniciadas'],
                datasets: [{{
                    data: [aoRes.completadas||0, aoRes.en_curso||0, aoRes.bloqueadas||0, aoRes.no_iniciadas||0],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#6b7280'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ font: {{ size: 12 }} }} }},
                    datalabels: {{
                        color: '#fff',
                        font: {{ weight: 'bold', size: 14 }},
                        formatter: function(v, ctx) {{
                            var total = ctx.dataset.data.reduce(function(a,b) {{ return a+b; }}, 0);
                            var pct = total > 0 ? (v/total*100).toFixed(1) : 0;
                            return v > 0 ? pct + '%' : '';
                        }}
                    }}
                }}
            }}
        }});
    }}

    // ── Gráfico: Desempeño por Prioridad (Bar) ──
    var priLabels = Object.keys(aoPri);
    var priComp = priLabels.map(function(p) {{ return aoPri[p].completadas || 0; }});
    var priCurso = priLabels.map(function(p) {{ return aoPri[p].en_curso || 0; }});
    var priBloq = priLabels.map(function(p) {{ return aoPri[p].bloqueadas || 0; }});

    var ctxPri = document.getElementById('chartAoPrioridad');
    if (ctxPri && typeof Chart !== 'undefined' && priLabels.length) {{
        new Chart(ctxPri, {{
            type: 'bar',
            data: {{
                labels: priLabels,
                datasets: [
                    {{ label: 'Completadas', data: priComp, backgroundColor: '#10b981' }},
                    {{ label: 'En Curso', data: priCurso, backgroundColor: '#f59e0b' }},
                    {{ label: 'Bloqueadas', data: priBloq, backgroundColor: '#ef4444' }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ stacked: true }},
                    y: {{ stacked: true, beginAtZero: true }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }},
                    datalabels: {{ display: false }}
                }}
            }}
        }});
    }}

    // ── Gráfico: Relación Porcentual por Prioridad (100% Bar) ──
    var ctxPriBar = document.getElementById('chartAoPriBar');
    if (ctxPriBar && typeof Chart !== 'undefined' && priLabels.length) {{
        var priTotal = priLabels.map(function(p) {{ return aoPri[p].total || 1; }});
        var priPctComp = priLabels.map(function(p, i) {{ return Math.round((aoPri[p].completadas||0) / priTotal[i] * 100); }});
        var priPctCurso = priLabels.map(function(p, i) {{ return Math.round((aoPri[p].en_curso||0) / priTotal[i] * 100); }});
        var priPctBloq = priLabels.map(function(p, i) {{ return Math.round((aoPri[p].bloqueadas||0) / priTotal[i] * 100); }});
        var priPctNo = priLabels.map(function(p, i) {{ return Math.round((aoPri[p].no_iniciadas||0) / priTotal[i] * 100); }});

        new Chart(ctxPriBar, {{
            type: 'bar',
            data: {{
                labels: priLabels,
                datasets: [
                    {{ label: '% Completadas', data: priPctComp, backgroundColor: '#10b981' }},
                    {{ label: '% En Curso', data: priPctCurso, backgroundColor: '#f59e0b' }},
                    {{ label: '% Bloqueadas', data: priPctBloq, backgroundColor: '#ef4444' }},
                    {{ label: '% No Iniciadas', data: priPctNo, backgroundColor: '#6b7280' }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {{
                    x: {{ stacked: true, max: 100, ticks: {{ callback: function(v) {{ return v + '%'; }} }} }},
                    y: {{ stacked: true }}
                }},
                plugins: {{
                    legend: {{ position: 'bottom' }},
                    datalabels: {{
                        color: '#fff',
                        font: {{ size: 10, weight: 'bold' }},
                        formatter: function(v) {{ return v > 5 ? v + '%' : ''; }}
                    }}
                }}
            }}
        }});
    }}

    // ── Tabla: Análisis por Prioridad ──
    var aoPriBody = document.getElementById('tablaAoPrioridad');
    if (aoPriBody && priLabels.length) {{
        aoPriBody.innerHTML = priLabels.map(function(p) {{
            var d = aoPri[p];
            var pctBar = d.pct_completadas || 0;
            var barColor = pctBar >= 80 ? '#10b981' : (pctBar >= 50 ? '#f59e0b' : '#ef4444');
            return '<tr>' +
                '<td><strong>' + p + '</strong></td>' +
                '<td class="text-right">' + (d.total||0) + '</td>' +
                '<td class="text-right" style="color:#10b981;font-weight:600">' + (d.completadas||0) + '</td>' +
                '<td class="text-right" style="font-weight:700">' + (d.pct_completadas||0) + '%</td>' +
                '<td class="text-right" style="color:#f59e0b">' + (d.en_curso||0) + '</td>' +
                '<td class="text-right" style="color:#ef4444">' + (d.bloqueadas||0) + '</td>' +
                '<td class="text-right" style="color:#6b7280">' + (d.no_iniciadas||0) + '</td>' +
                '<td style="width:120px"><div style="background:#e5e7eb;border-radius:4px;height:18px;overflow:hidden">' +
                    '<div style="background:' + barColor + ';width:' + pctBar + '%;height:100%;border-radius:4px;text-align:center;color:#fff;font-size:11px;line-height:18px;font-weight:600">' + pctBar + '%</div></div></td>' +
                '</tr>';
        }}).join('');
    }}

    // ── Tabla: Listado de Tareas ──
    var aoTBody = document.getElementById('tablaAoTareas');
    if (aoTBody && aoTareas.length) {{
        aoTBody.innerHTML = aoTareas.map(function(t, i) {{
            var stCls = t.estado.toLowerCase().indexOf('completada') >= 0 ? 'status-entregado' :
                        (t.estado.toLowerCase().indexOf('bloqueada') >= 0 ? 'status-cancelado' :
                        (t.estado.toLowerCase().indexOf('en curso') >= 0 ? 'status-aprobado' : 'status-congelado'));
            var priCls = t.prioridad.indexOf('Inmediata') >= 0 ? 'background:#fef2f2;color:#991b1b' :
                         (t.prioridad.indexOf('Media') >= 0 ? 'background:#fffbeb;color:#92400e' :
                         'background:#f0fdf4;color:#166534');
            var barW = t.pct || 0;
            var barC = barW >= 100 ? '#10b981' : (barW >= 50 ? '#f59e0b' : '#6b7280');
            return '<tr>' +
                '<td style="font-size:12px;color:#888">' + (i+1) + '</td>' +
                '<td><strong style="font-size:12px">' + (t.tarea||'') + '</strong></td>' +
                '<td><span style="padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;' + priCls + '">' + (t.prioridad||'') + '</span></td>' +
                '<td style="font-size:12px">' + (t.propietario||'') + '</td>' +
                '<td><span class="' + stCls + '">' + (t.estado||'') + '</span></td>' +
                '<td style="font-size:11px;color:#666">' + (t.fecha_inicio||'') + '</td>' +
                '<td style="font-size:11px;color:#666">' + (t.fecha_fin||'') + '</td>' +
                '<td style="width:100px"><div style="background:#e5e7eb;border-radius:4px;height:16px;overflow:hidden">' +
                    '<div style="background:' + barC + ';width:' + barW + '%;height:100%;border-radius:4px;text-align:center;color:#fff;font-size:10px;line-height:16px;font-weight:600">' + barW + '%</div></div></td>' +
                '<td style="font-size:11px;color:#666;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + (t.notas||'').replace(/"/g, '&quot;') + '">' + (t.notas||'').substring(0,60) + '</td>' +
                '</tr>';
        }}).join('');
    }}

    // ── Gráfico: Timeline de Inicios ──
    var fechaMap = {{}};
    aoTareas.forEach(function(t) {{
        var f = t.fecha_inicio;
        if (f) {{
            // Extraer solo el mes/día si está en formato DD/MM/YYYY
            var parts = f.split('/');
            var key = parts.length >= 3 ? parts[0] + '/' + parts[1] : f;
            fechaMap[key] = (fechaMap[key] || 0) + 1;
        }}
    }});
    var fechaLabels = Object.keys(fechaMap).sort();
    var fechaVals = fechaLabels.map(function(k) {{ return fechaMap[k]; }});

    var ctxTimeline = document.getElementById('chartAoTimeline');
    if (ctxTimeline && typeof Chart !== 'undefined' && fechaLabels.length) {{
        new Chart(ctxTimeline, {{
            type: 'line',
            data: {{
                labels: fechaLabels,
                datasets: [{{
                    label: 'Tareas iniciadas',
                    data: fechaVals,
                    borderColor: '#213C83',
                    backgroundColor: 'rgba(33,60,131,0.1)',
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: '#F98B10',
                    pointRadius: 5,
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    datalabels: {{
                        color: '#213C83',
                        font: {{ weight: 'bold', size: 12 }},
                        anchor: 'end',
                        align: 'top'
                    }}
                }}
            }}
        }});
    }}
}} catch(e) {{ console.error('Análisis Operativo Agosto error:', e); }}

renderTable();
switchTab('gestion');
}} catch(e) {{
    console.error('Page init error:', e.message, e.stack);
    var errEl = document.getElementById('fechaGeneracion');
    if (errEl) errEl.textContent = 'Error: ' + e.message;
    var msg = document.createElement('div');
    msg.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#c00;color:#fff;padding:12px 20px;font-family:sans-serif;font-size:14px;z-index:9999';
    msg.textContent = '⚠ Error inicial: ' + e.message + ' (revisa consola F12)';
    document.body.appendChild(msg);
}}
</script>
<script src="https://cdn.sheetjs.com/xlsx-0.20.2/package/dist/xlsx.full.min.js"></script>
</body>
</html>'''

output_path = os.path.join(os.path.dirname(__file__), 'index.html')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Written to {output_path}")
print(f"File size: {os.path.getsize(output_path)} bytes")
print("Done!")
