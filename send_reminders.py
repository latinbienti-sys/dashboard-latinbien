"""Script para enviar recordatorios de pago a proveedor (ejecutado por GitHub Actions)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from server import fetch_data
from email_proveedor import verificar_pagos_proximos, enviar_correo_recordatorio

print("Verificando pagos proximos al proveedor...")
try:
    data = fetch_data()
    pagos = verificar_pagos_proximos(data)
    if pagos:
        for p in pagos:
            ok, msg = enviar_correo_recordatorio(
                proveedor=p['proveedor'],
                orden_compra=p['orden_compra'],
                cliente=p['cliente'],
                modelo=p['modelo'],
                cuota_num=p['cuota_num'],
                total_cuotas=p['total_cuotas'],
                monto=p['monto'],
                fecha_pago=p['fecha_pago'],
                ciclo=p['ciclo'],
                opcion=p['opcion']
            )
            print(f"  Cuota {p['cuota_num']}: {msg}")
    else:
        print("  No hay pagos proximos pendientes.")
except Exception as e:
    print(f"  Error enviando recordatorios: {e}")
