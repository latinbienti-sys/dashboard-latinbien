"""Script para enviar recordatorios consolidados de pago a proveedor (GitHub Actions).
Calcula automaticamente el proximo dia de pago (5, 12, 20 o 27) y recuerda
las cuotas que vencen ese dia. Se ejecuta a las 8am y envia 1 dia antes."""
import os, sys
from datetime import date
import calendar

sys.path.insert(0, os.path.dirname(__file__))

from server import fetch_data
from email_proveedor import verificar_pagos_proximos, agrupar_por_fecha, enviar_correo_consolidado

DIAS_PAGO = [5, 12, 20, 27]


def proximo_dia_pago():
    """Devuelve la fecha 'YYYY-MM-DD' del proximo dia de pago desde hoy."""
    hoy = date.today()
    for dia in DIAS_PAGO:
        try:
            candidata = date(hoy.year, hoy.month, dia)
        except ValueError:
            candidata = date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])
        if candidata >= hoy:
            return str(candidata)
    m = hoy.month + 1
    y = hoy.year
    if m > 12:
        m = 1
        y += 1
    return str(date(y, m, DIAS_PAGO[0]))


print("Verificando pagos proximos al proveedor...")
try:
    data = fetch_data()
    fecha_objetivo = proximo_dia_pago()
    print(f"  Proximo vencimiento: {fecha_objetivo}")
    pagos = verificar_pagos_proximos(data, solo_fecha=fecha_objetivo)
    if pagos:
        grupos = agrupar_por_fecha(pagos)
        for g in grupos:
            ok, msg = enviar_correo_consolidado(
                proveedor=g['proveedor'],
                grupos=[g],
            )
            print(f"  Fecha {g['fecha_pago']} ({len(g['cuotas'])} cuotas): {msg}")
    else:
        print(f"  No hay pagos para {fecha_objetivo}.")
except Exception as e:
    print(f"  Error enviando recordatorios: {e}")
    sys.exit(1)