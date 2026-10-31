{
    "name": "Tablero de Pagos y Egresos por Razón",
    "version": "16.0.1.0.0",
    "category": "Reporting",
    "summary": "Analiza en qué se gastó el dinero agrupando por Razón de pagos",
    "author": "OpenCode",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "views/dashboard_menus.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "razon_pagos_dashboard/static/src/scss/dashboard.scss",
            "razon_pagos_dashboard/static/src/components/chart_donut.js",
            "razon_pagos_dashboard/static/src/components/dashboard.js",
            "razon_pagos_dashboard/static/src/components/dashboard.xml"
        ]
    },
    "installable": True,
    "application": True,
    "auto_install": False
}