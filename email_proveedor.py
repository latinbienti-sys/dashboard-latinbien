"""Módulo de envío de correos internos para recordatorios de pago a proveedor."""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = os.environ.get('LATINBIEN_SMTP_USER')
SMTP_PASS = os.environ.get('LATINBIEN_SMTP_PASS')

if not SMTP_USER or not SMTP_PASS:
    raise RuntimeError("LATINBIEN_SMTP_USER y LATINBIEN_SMTP_PASS deben estar definidas como variables de entorno.")

# Destinatarios internos
DESTINATARIOS_INTERNOS = [
    'analistadministrativo@latinbien.com',
    'osoto@latinbien.com',
    'yarley@latinbien.com',
    'presidencia@latinbien.com',
    'vicepresidencia@latinbien.com',
]

def generar_correo_recordatorio(proveedor, orden_compra, cliente, modelo, cuota_num, 
                                 total_cuotas, monto, fecha_pago, ciclo, opcion):
    """Genera el contenido del correo de recordatorio interno."""
    asunto = f'Recordatorio Interno - Pago a Proveedor: Cuota {cuota_num}/{total_cuotas} - {orden_compra}'
    
    cuerpo = f"""
RECORDATORIO INTERNO DE PAGO A PROVEEDOR
{'='*50}

Proveedor: {proveedor}
Orden de Compra: {orden_compra}
Cliente (Venta): {cliente}
Modelo: {modelo}

DETALLE DE LA CUOTA:
  Cuota: {cuota_num}/{total_cuotas}
  Monto: ${monto:,.2f}
  Fecha de Pago: {fecha_pago}
  Ciclo: {ciclo} (Opción {opcion})

{'='*50}
Este es un recordatorio interno del sistema LATINBIEN Dashboard.
Fecha de generación: {date.today()}

No responder a este correo. Es solo para referencia interna.
"""
    return asunto, cuerpo


def enviar_correo_recordatorio(proveedor, orden_compra, cliente, modelo,
                               cuota_num, total_cuotas, monto, fecha_pago, ciclo, opcion,
                               destinatarios=None, smtp_pass=None):
    """Envía correo de recordatorio interno de pago a proveedor."""
    if destinatarios is None:
        destinatarios = DESTINATARIOS_INTERNOS
    if smtp_pass is None:
        smtp_pass = SMTP_PASS
    
    asunto, cuerpo = generar_correo_recordatorio(
        proveedor, orden_compra, cliente, modelo,
        cuota_num, total_cuotas, monto, fecha_pago, ciclo, opcion
    )
    
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = ', '.join(destinatarios)
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, smtp_pass)
        server.sendmail(SMTP_USER, destinatarios, msg.as_string())
        server.quit()
        return True, f'Correo enviado a {len(destinatarios)} destinatarios'
    except Exception as e:
        return False, f'Error: {str(e)}'


def verificar_pagos_proximos(data, solo_fecha=None):
    """Verifica pagos de proveedor próximos pendientes.
    Retorna una lista de cuotas pendientes (fecha <= hoy o fecha == solo_fecha).
    Si solo_fecha se especifica, retorna solo las cuotas de ESA fecha exacta."""
    pp = data.get('pago_proveedor_moto', {})
    items = pp.get('items', [])
    hoy = str(date.today())
    pagos_pendientes = []
    
    for it in items:
        for p in it.get('pagos', []):
            f = p.get('fecha_pago', '')
            if p.get('estado') != 'pendiente':
                continue
            if solo_fecha is not None:
                if f != solo_fecha:
                    continue
            else:
                if f > hoy:
                    continue
            pagos_pendientes.append({
                'proveedor': it.get('proveedor', ''),
                'orden_compra': it.get('orden_compra', ''),
                'cliente': it.get('cliente', ''),
                'modelo': it.get('modelo', ''),
                'cuota_num': p.get('cuota', 0),
                'total_cuotas': len(it.get('pagos', [])),
                'monto': p.get('monto', 0),
                'fecha_pago': f,
                'ciclo': it.get('ciclo', ''),
                'opcion': it.get('opcion', ''),
            })
    
    return pagos_pendientes


def agrupar_por_fecha(pagos):
    """Agrupa cuotas pendientes por fecha de pago, sumando montos y contando cuotas."""
    grupos = {}
    for p in pagos:
        f = p.get('fecha_pago', '')
        g = grupos.setdefault(f, {
            'fecha_pago': f,
            'cuotas': [],
            'monto_total': 0.0,
            'proveedor': p.get('proveedor', ''),
        })
        g['cuotas'].append(p)
        g['monto_total'] += p.get('monto', 0)
    # Ordenar por fecha
    resultado = [grupos[k] for k in sorted(grupos.keys())]
    return resultado


def generar_correo_consolidado(proveedor, grupos, fecha_referencia=None):
    """Genera un correo consolidado de pagos pendientes agrupados por fecha.
    Muestra cantidad de cuotas pendientes y desglose por orden."""
    fecha_ref = fecha_referencia or date.today()
    total_general = sum(g['monto_total'] for g in grupos)
    total_cuotas = sum(len(g['cuotas']) for g in grupos)

    asunto = f'Recordatorio Interno - Pagos a Proveedor ({fecha_ref.strftime("%d/%m/%Y")}): {total_cuotas} cuotas pendientes'

    cuerpo = f"""
RECORDATORIO INTERNO DE PAGOS A PROVEEDOR
{'='*50}

Proveedor: {proveedor}
Fecha de corte: {fecha_ref.strftime('%d/%m/%Y')}

RESUMEN:
  Cuotas pendientes: {total_cuotas}
  Monto total pendiente: ${total_general:,.2f}

DETALLE POR FECHA DE PAGO:
"""
    for g in grupos:
        cuerpo += f"""
  📅 Fecha de pago: {g['fecha_pago']}  (Cuotas: {len(g['cuotas'])} | Total: ${g['monto_total']:,.2f})
  {'-'*40}"""
        for p in g['cuotas']:
            cuerpo += f"""
    • {p['orden_compra']} | Cliente: {p['cliente']} | {p['modelo']}
      Cuota {p['cuota_num']}/{p['total_cuotas']} | ${p['monto']:,.2f} | Ciclo {p['ciclo']} (Op {p['opcion']})
"""
    cuerpo += f"""
{'='*50}
Este es un recordatorio interno del sistema LATINBIEN Dashboard.
Fecha de generación: {date.today()}

No responder a este correo. Es solo para referencia interna.
"""
    return asunto, cuerpo


def enviar_correo_consolidado(proveedor, grupos, destinatarios=None,
                              smtp_user=None, smtp_pass=None, fecha_referencia=None):
    """Envía un correo consolidado de pagos pendientes a proveedor."""
    if destinatarios is None:
        destinatarios = DESTINATARIOS_INTERNOS
    if smtp_user is None:
        smtp_user = SMTP_USER
    if smtp_pass is None:
        smtp_pass = SMTP_PASS

    asunto, cuerpo = generar_correo_consolidado(proveedor, grupos, fecha_referencia)

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = ', '.join(destinatarios)
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, destinatarios, msg.as_string())
        server.quit()
        return True, f'Correo (consolidado, {sum(len(g["cuotas"]) for g in grupos)} cuotas) enviado a {len(destinatarios)} destinatarios'
    except Exception as e:
        return False, f'Error: {str(e)}'
