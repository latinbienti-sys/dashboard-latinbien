# Dashboard Hub

Biblioteca visual estática para centralizar accesos a tableros de LATINBIEN y HONDA.

El catálogo actual contiene siete accesos de LATINBIEN: Ventas, Finanzas, Soporte, Inventario, CRM, Clientes y Cobranza. Todos los accesos de LATINBIEN abren el tablero público general en `https://latinbienti-sys.github.io/dashboard-latinbien/`, que incluye las pestañas Resumen, Gestión Cobranza, Montos, Segmentos, Listado, Plan de Pagos y Ciclos, entre otras. HONDA mantiene Inventario y CRM como accesos de ejemplo hasta recibir sus URLs.

## Ejecutar

El proyecto no requiere dependencias. Desde esta carpeta, ejecuta:

```bash
python3 -m http.server 3000 --bind 0.0.0.0
```

Luego abre la ruta raíz en el Preview del proyecto.

## Personalizar

Edita el arreglo `dashboards` al inicio de `app.js`. Cada objeto acepta `name`, `category`, `icon`, `color`, `description`, `keywords` y `url`. Para enlaces reales, cambia `url` por la URL del dashboard y elimina `example: true`.

Los favoritos se guardan en `localStorage` del navegador, sin backend, para mantener la experiencia rápida y simple.
