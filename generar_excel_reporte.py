# -*- coding: utf-8 -*-
"""Genera el reporte Excel de ventas de vehiculos LatinBienMotors 2026
a partir de datos/reporte_ventas_2026-10-30.json (descargado de Odoo, solo lectura).
Hoja por dimension. Totales con formulas. Fuente Arial."""
import json, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

BASE = os.path.dirname(os.path.abspath(__file__))
JSON_IN = os.path.join(BASE, 'datos', 'reporte_ventas_2026-10-30.json')
OUT = os.path.join(BASE, 'reporte', 'Reporte_Ventas_LatinBienMotors_2026.xlsx')

with open(JSON_IN, encoding='utf-8') as f:
    D = json.load(f)

AZUL = Font(name='Arial', size=10, color='FFFFFF', bold=True)
TEXTO = Font(name='Arial', size=10)
GRIS = Font(name='Arial', size=9, color='666666')
NEGRITA = Font(name='Arial', size=10, bold=True)
TITULO = Font(name='Arial', size=14, bold=True, color='16213E')
HEADER_FILL = PatternFill('solid', fgColor='16213E')
GRIS_FILL = PatternFill('solid', fgColor='EEF2FB')
FINO = Side(style='thin', color='D9DEE8')
BORDE = Border(bottom=FINO)
MONEY = '#,##0.00'

wb = Workbook()
wb.remove(wb.active)

def col_width(ws, anchos):
    for i, a in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(i)].width = a

def tabla(ws, start, headers, rows, total=True, money_cols=()):
    r0 = start
    for j, h in enumerate(headers, 1):
        c = ws.cell(r0, j, h); c.font = AZUL; c.fill = HEADER_FILL
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.cell(r0 - 1, 1).font = TITULO
    for i, fila in enumerate(rows, 1):
        for j, v in enumerate(fila, 1):
            c = ws.cell(r0 + i, j, v)
            c.font = TEXTO; c.border = BORDE
            if j in money_cols:
                c.number_format = MONEY; c.alignment = Alignment(horizontal='right')
        if i % 2 == 0:
            for j in range(1, len(headers) + 1):
                ws.cell(r0 + i, j).fill = GRIS_FILL
    if total:
        rt = r0 + len(rows) + 1
        c = ws.cell(rt, 1, 'TOTAL'); c.font = NEGRITA; c.fill = GRIS_FILL
        for j in range(2, len(headers) + 1):
            letra = get_column_letter(j)
            encabezado = headers[j - 1].lower()
            if encabezado.startswith('clientes'):
                cc = ws.cell(rt, j, '')  # sumar clientes no aplica
            else:
                cc = ws.cell(rt, j, f'=SUM({letra}{r0+1}:{letra}{r0+len(rows)})')
            cc.font = NEGRITA; cc.fill = GRIS_FILL
            if j in money_cols: cc.number_format = MONEY; cc.alignment = Alignment(horizontal='right')
    return r0 + len(rows) + 1

def Titulo(ws, celda, texto):
    ws[celda] = texto; ws[celda].font = TITULO

# ---------- Resumen ----------
ws = wb.create_sheet('Resumen')
Titulo(ws, 'A1', 'Reporte de Ventas - LatinBienMotors (Honda Mérida) - %d' % D['anio'])
ws['A2'] = 'Fuente: latinbienmotors.com (BD latinbien) - consulta de solo lectura'; ws['A2'].font = GRIS
ws['A3'] = 'Generado: %s' % D['generado'][:19].replace('T', ' '); ws['A3'].font = GRIS
ws['A5'] = 'Definiciones (iguales a inventariohonda):'; ws['A5'].font = NEGRITA
defs = [
    'VENDIDO: pedidos con Status Operativo = 6 (Entregado), mes por fecha de entrega (commitment_date).',
    'Unidades = líneas de producto Honda; monto = subtotal SIN IVA.',
    'RESERVADO: unidades (VIN) con stock en almacén Reservas (ubicaciones RLBM), al corte.',
    'FACTURADO NO ENTREGADO (FNE): facturadas aún en almacén FNE (informativo).',
    'FORMA DE VENTA: Contado = cliente con Oportunidad en etapa CRM "Facturado Contado" (etapa 12, 20 leads).',
    '   Crédito = el resto (facturación retail con plan de plazos SAV). 16 de los 20 contados ya están entregados.',
    'Dimensiones de cliente: género (Dama/Caballero), edad (fecha de nacimiento), departamento (state_id),',
    'profesión y actividad (ficha del contacto). Datos vacíos = sin registrar en Odoo Motors.',
]
for i, d in enumerate(defs):
    c = ws.cell(6 + i, 1, d); c.font = GRIS
ws['A14'] = 'Resumen'; ws['A14'].font = NEGRITA
kpi = [('Unidades entregadas 2026', float(D['total']['unidades'])),
       ('Monto entregado sin IVA ($)', D['total']['monto']),
       ('Pedidos entregados', D['total']['pedidos']),
       ('Reservadas al corte (%s)' % D['reservado']['alCorte'], D['reservado']['unidades']),
       ('Facturadas no entregadas (FNE)', D['facturadoNoEntregado']['unidades'])]
for i, (k, v) in enumerate(kpi):
    ws.cell(15 + i, 1, k).font = TEXTO
    c = ws.cell(15 + i, 2, v); c.font = NEGRITA; c.number_format = MONEY if i == 1 else '0'
col_width(ws, [46, 18])

def sheet_dim(nombre, titulo, filas, headers=('Dimensión', 'Unidades', 'Monto sin IVA ($)', 'Pedidos', 'Clientes')):
    w = wb.create_sheet(nombre)
    Titulo(w, 'A1', titulo)
    filas_f = [[f['llave'], f['unidades'], f['monto'], f['pedidos'], f['clientes']] for f in filas]
    tabla(w, 3, list(headers), filas_f, money_cols=(3,))
    col_width(w, [34, 12, 20, 11, 11])
    return w

sheet_dim('Por Mes', 'Vendido por MES (%d) - unidades y monto' % D['anio'], D['porMes'])
sheet_dim('Forma de venta', 'Por FORMA DE VENTA', D['porForma'])
sheet_dim('Dama-Caballero', 'Por GÉNERO', D['porGenero'])
sheet_dim('Edad', 'Por EDAD (rangos)', D['porEdad'])
sheet_dim('Departamento', 'Por ESTADO / DEPARTAMENTO', D['porEstado'])
sheet_dim('Actividad', 'Por ACTIVIDAD del cliente', D['porActividad'])
sheet_dim('Profesión', 'Por PROFESIÓN declarada', D['porProfesion'])

# ---------- Reservado ----------
w = wb.create_sheet('Reservado')
Titulo(w, 'A1', 'RESERVADO al corte %s (almacén Reservas RLBM)' % D['reservado']['alCorte'])
hdr = ['VIN', 'Modelo', 'Cliente', 'Género', 'Edad', 'Departamento', 'Profesión', 'Actividad']
rows = [[r['vin'], r['modelo'], r['cliente'], r['genero'], r['edad'] if r['edad'] is not None else '(sin dato)',
         r['estado'], r['profesion'], r['actividad']] for r in D['reservado']['detalle']]
tabla(w, 3, hdr, rows, total=False)
w.cell(3 + len(rows) + 1, 1, 'TOTAL unidades reservadas').font = NEGRITA
w.cell(3 + len(rows) + 1, 2, f'=SUM(B4:B{3 + len(rows)})').font = NEGRITA
w['A12'] = 'FACTURADO NO ENTREGADO (FNE), informativo:'; w['A12'].font = NEGRITA
hdr2 = ['Modelo', 'Unidades']
rows2 = [[u['modelo'], u['unidades']] for u in D['facturadoNoEntregado']['detalle']]
tabla(w, 13, hdr2, rows2, total=False)
col_width(w, [22, 42, 36, 12, 9, 16, 24, 26])

# ---------- Detalle Vendido ----------
w = wb.create_sheet('Detalle Vendido')
Titulo(w, 'A1', 'Detalle vendido %d (una fila por unidad Honda)' % D['anio'])
hdr = ['Mes', 'Fecha entrega', 'Pedido', 'Cliente', 'Modelo', 'Unid.', 'Monto sin IVA ($)', 'Forma de venta',
       'Ejecutivo', 'Género', 'Edad', 'Departamento', 'Profesión', 'Actividad']
rows = [[d['mes'], d['fechaStr'][:10], d['pedido'], d['cliente'], d['modelo'], d['unidades'], d['montoSinIva'],
         d['forma'], d['ejecutivo'], d['genero'], d['edad'] if d['edad'] is not None else '(sin dato)',
         d['estado'], d['profesion'], d['actividad']] for d in D['detalle']]
tabla(w, 3, hdr, rows, total=True, money_cols=(7,))
col_width(w, [9, 12, 16, 34, 40, 7, 18, 18, 24, 12, 9, 16, 22, 24])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
print('OK ->', OUT)
