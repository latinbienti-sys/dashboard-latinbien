"""Script para enviar recordatorios consolidados de pago a proveedor (GitHub Actions).
Recuerda SOLO la (o las) cuota(s) que vencen el próximo día 05 del mes:
patrón ciclo 03-18 (cuotas impares vencen el día 05, pares el 20).
Agrupa por fecha y envía UN correo con el conteo total."""
import os, sys
from datetime import date

import calendar
sys.path.insert(0, os.path.dirname(__file__))

from server import fetch_data
from email_proveedor import verificar_pagos_proximos, agrupar_por_fecha, enviar_correo_consolidado


def proximo_dia(dia=5):
    """Devuelve la fecha 'YYYY-MM-DD' del próximo día 'dia' (hoy o siguientes meses)."""
    hoy = date.today()
    try:
        cand = date(hoy.year, hoy.month, dia)
    except ValueError:
        cand = date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])
    if cand < hoy:
        # El día ya pasó este mes → saltar al mes siguiente
        m = hoy.month + 1
        y = hoy.year
        if m > 12:
            m = 1
            y += 1
        try:
            cand = date(y, m, dia)
        except ValueError:
            cand = date(y, m, calendar.monthrange(y, m)[1])
    return str(cand)


print("Verificando pagos que vencen el proximo dia 05 al proveedor...")
try:
    data = fetch_data()
    dia = 5
    fecha_objetivo = proximo_dia(dia)
    print(f"  Fecha objetivo de vencimiento: {fecha_objetivo}")
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
        print("  No hay pagos programados para el proximo dia 05.")
except Exception as e:
    print(f"  Error enviando recordatorios: {e}")
    sys.exit(1)