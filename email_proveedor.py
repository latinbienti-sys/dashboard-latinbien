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
    'administrativo@latinbien.com',
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


def verificar_pagos_proximos(data):
    """Verifica si hay pagos de proveedor próximos (hoy o pasados) para enviar recordatorio."""
    pp = data.get('pago_proveedor_moto', {})
    items = pp.get('items', [])
    hoy = str(date.today())
    pagos_pendientes = []
    
    for it in items:
        for p in it.get('pagos', []):
            if p.get('fecha_pago', '') <= hoy and p.get('estado') == 'pendiente':
                pagos_pendientes.append({
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
    
    return pagos_pendientes
