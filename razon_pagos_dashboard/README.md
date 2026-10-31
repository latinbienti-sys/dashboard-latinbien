# Tablero de Pagos y Egresos por Razón

Módulo **Odoo 16** que responde la pregunta *"¿En qué se gastó el dinero?"* agrupando por el campo
**`x_razonpagos`** en lugar de por la jerarquía Año > Mes > Día.

Es estrictamente de **solo lectura**: no crea, no modifica y no borra ningún registro.

---

## Qué incluye

| Pieza | Descripción |
|---|---|
| **Gráfico de dona** | Porcentaje y monto total por cada razón de pago. Clic en una porción = filtrar. |
| **Tabla con drill-down** | Categoría → Proveedor/Beneficiario → Documento. Subtotales en cada nivel. |
| **Barra de filtros** | Rango de fechas + estado (Publicado / Borrador / Todos) + chips por categoría. |
| **KPIs** | Total analizado, nº de registros, ticket promedio, categoría mayor. |
| **Exportar CSV** | Descarga la tabla con indentación y totales. |
| **Ver detalle** | Abre la lista de registros de Odoo filtrada, en modo no editable. |

---

## Instalación

1. Copia la carpeta `razon_pagos_dashboard` dentro de tu addon path
   (por ejemplo `/odoo/addons_custom/` o junto a tus otros addons).
2. Actualiza la lista de apps:

```bash
odoo -c odoo.conf -u razon_pagos_dashboard --stop-after-init
```

   O reinicia Odoo y ve a **Apps → Actualizar lista**.
3. Instala **"Tablero de Pagos y Egresos por Razón"**.
4. Ábrelo en **Reportes para Socios → ¿En qué se gastó el dinero?**
5. Agrégalo a **Favoritos** (ícono de estrella) como cualquier otra vista.

---

## Detección automática

El módulo **no tiene el modelo hardcodeado**. Al arrancar busca, en este orden:

| Tipo | Modelos donde busca | Campos |
|---|---|---|
| Modelo | `account.payment` → `account.move.line` → `account.move` | — |
| Razón | — | `x_razonpagos` |
| Monto | `amount`, `amount_total`, `debit`, `debit_balance`, `balance` | |
| Fecha | `payment_date`, `date`, `invoice_date` | |
| Estado | `state`, `parent_state`, `payment_state` | |
| Tipo de pago | `payment_type` | |

Como `account.payment` es el **primer** modelo que se prueba, si `x_razonpagos` vive ahí el tablero
arranca con `amount`, `payment_date` y `state` sin configurar nada.

El primer match gana. Si no encuentra nada, el tablero muestra un mensaje de error indicando
exactamente qué revisó, en vez de romperse.

### Configuración manual

Si quieres forzar un modelo o campo concreto (o usar otro nombre de campo), ve a
**Ajustes → Técnico → Parámetros del sistema** y agrega:

| Clave | Valor | Ejemplo |
|---|---|---|
| `razon_pagos_dashboard.models` | Modelos separados por coma, en orden de prioridad | `account.payment,account.move.line` |
| `razon_pagos_dashboard.reason_fields` | Campos separados por coma | `x_razonpagos` |
| `razon_pagos_dashboard.measure` | Campo de monto a sumar | `amount` |
| `razon_pagos_dashboard.date_field` | Campo de fecha del filtro | `payment_date` |
| `razon_pagos_dashboard.state_field` | Campo de estado | `state` |
| `razon_pagos_dashboard.payment_type_field` | Campo de tipo de pago | `payment_type` |

---

## Archivos

```
razon_pagos_dashboard/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── dashboard.py           # detección de modelo, dominios, read_group
├── static/src/
│   ├── scss/dashboard.scss
│   └── components/
│       ├── chart_donut.js     # Chart.js con % en cada porción
│       ├── dashboard.js       # componente OWL + acción cliente
│       └── dashboard.xml      # template
└── views/
    └── dashboard_menus.xml    # acción + menú
```

---

## Notas técnicas

- El **% del gráfico** se calcula en JavaScript con un plugin de Chart.js, porque el `graph` nativo
  de Odoo no lo muestra.
- La **tabla se construye con `read_group` encadenado**, no con `web.pivot.table`, para:
  - que el subtotal por nivel sea correcto,
  - que funcione igual en 16 que en 17,
  - evitar el origen de datos duplicado del dashboard.
- Cada fila trae su `__domain` devuelto por `read_group`, así el drill-down es exacto y el botón
  *"Ver detalle"* abre la lista real de registros, no una aproximación.
- El filtro de estado aplica por defecto **Publicado** (`posted`).
- El filtro **Tipo de pago** aparece solo en `account.payment` y arranca en **Salidas (egresos)**.
  Es importante: sin esto la donut mezclaría dinero que salió con dinero que entró, y la respuesta
  a "¿en qué se gastó?" quedaría inflada.
- Los registros sin clasificar aparecen agrupados como **"(Sin clasificar)"** — es útil para
  detectar pagos sin clasificar.