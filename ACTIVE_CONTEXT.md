# Active Context

## New Feature: Pronto Pago Tab (⚡)
- Added new tab "⚡ Pronto Pago" to the dashboard
- Logic: cuotas with state='paid' whose payment_date is FUTURE (after today) = client paid before due date
- Data: 99 clients, 174 cuotas, $16,963 (updated with Entregado filter)
- In server.py: added `pronto_pago_raw` loop over all_lines filtering paid+future, grouped by client into `pronto_pago` list
- In server.py: added `pronto_pago` and `total_pronto` to fetch_payment_plan return dict
- In generar_html.py: added tab button, tab-content HTML, tabMap entry, and JS rendering code
- JS reads from DATA.payment_plan.pronto_pago and DATA.payment_plan.total_pronto

## Fix: Pronto Pago facturas vacías
- El campo `invoice_name` no existía en el read de installment lines
- El nombre viene en `invoice_id[1]` (campo many2one)
- Corregido: `inv_name = inv[1] if isinstance(inv, list) and len(inv) > 1 else ''`
- Ahora facturas se muestran como vinculos clickeables a Odoo

## Fix: Pronto Pago solo facturas Entregado
- Filtro `invoice_status_map.get(inv_id) != 'Entregado'` en pronto pago
- Resultado: 99 clientes, 174 cuotas, $16,963

## Feature: KPIs Avanzados Pronto Pago
- `monto_promedio`: $171.35 por cliente
- `dias_ponderado`: 13.2 días anticipación promedio ponderado por monto
- `penetracion`: 1.27% del total recaudado
- `total_pagado`: $1,335,326.42

## Feature: Flags de Priorización
- ORO (6 clientes): monto≥$500 OR cuotas≥5 OR días≥100 → ejecutivo preferencial + factura prioritaria + extensión términos
- PLATA (13 clientes): monto≥$200 OR cuotas≥3 OR días≥50 → prioridad entregas + descuento próximo servicio
- BRONCE (80 clientes): cualquier pronto pago → correo agradecimiento + beneficio fidelidad

## Feature: Top 10 Impacto en Flujo
- Gráfico de barras dual: Monto ($) + Cuotas por cliente
- Datos en `top10_impacto` del return dict
- GLENDY MARIANA CAMACHO PEREZ: $11,440 (5 cuotas, 73 días) — 67% del total

## New Feature: Pestaña 📅 Ciclos
- Proyección por ciclo 03-18 y 10-25
- Pagadas vs pendientes por mes (agosto 2026 → junio 2027)
- Ciclo 03-18 Ago: $41,136 pagado (524 clientes) / $9,418 pendiente (117 clientes)
- Ciclo 10-25 Ago: $5,027 pagado (77 clientes) / $8,062 pendiente (135 clientes)
- `ciclo_proj` en server.py return dict

## Bug Fix: Map re-initialization
- Fixed bug where `invoice_status_map` and `invoice_date_map` were re-initialized to {} at line 463-464 AFTER being filled in the filter block (lines 416-440)
- This caused facturas_entregadas_vencidas to return 0 even though 142+ facturas should pass
- After fix: 142-145 facturas entregadas vencidas, total_entregadas_venc properly populated

## Commits (this session):
- 4c9b24d fix: Plan de Pagos no borra mapas de status — entregadas vencidas solo facturas publicadas
- 50832fa regenerate: index.html tras resolver rebase (entregadas vencidas solo publicadas)
- b458366 feat: pestaña Pronto Pago — clientes que pagan antes del vencimiento
- e7f16b6 regenerate: index.html con pestaña Pronto Pago
- e6d5fab fix: pronto pago solo facturas con status operativo Entregado
- 4f2fd7c fix: pronto pago muestra números de factura con vinculo a Odoo
- 67473d9 feat: proyeccion por ciclos (03-18, 10-25) — pagadas vs pendientes por mes + graficos
- 4ec07c3 feat: pronto pago con KPIs avanzados, top 10 impacto y flags de priorizacion
- 1b690aa regenerate: index.html con KPIs pronto pago avanzados

## Feature: Alertas de Morosidad (Informativas)
- Banner rojo visible en tab Plan de Pagos con conteo por severidad
- Severidad: CRITICO (>90 días), ALTO (30-90), MEDIO (7-30), BAJO (1-7)
- Stats: 406 clientes, 315 críticos, 28 altos, 33 medios, 30 bajos, $220,192 en riesgo
- Tabla filtrable por severidad con acción sugerida
- IMPORTANTE: Solo informativo, sin acciones automáticas, sin enviar nada a clientes
- Texto claro: "Vista interna de consideración. No se ejecuta ninguna acción automática ni se contacta clientes. Solo fines informativos."
- `alertas_morosidad` y `total_alertas` en server.py return dict

## Updated Stats:
- total_vencido: $220,175.90 (only posted out_invoice)
- total_pagado: $1,335,326.42
- Entregadas vencidas: 145 facturas
- Últimas entregas: 11 morosos (from 7 earlier - data refreshes each run)
- Pronto pago: 99 clientes, 174 cuotas, $16,963
- client_count: 1,592 (from 1,577 earlier - data refreshes)
- factoras emitidas: 2,387 (from 2,358)
- Alertas morosidad: 406 clientes, $220,192 en riesgo

## Commits:
- ff7c1cf feat: alertas de morosidad internas informativas
- a26d87f regenerate: index.html con alertas morosidad informativas

## Dashboard tabs (10 total):
1. 📊 Resumen
2. 💰 Montos
3. 👥 Segmentos
4. ⏱ Temporal VIP
5. 📋 Listado
6. 💳 Plan de Pagos (con banner de alertas)
7. 📋 Fact. Julio
8. 🗂️ Expedientes
9. ⚡ Pronto Pago (KPIs, flags oro/plata/bronce, Top 10)
10. 📅 Ciclos