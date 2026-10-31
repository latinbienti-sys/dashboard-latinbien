{
    'name': 'Latinbien - Verificación de Cédula',
    'version': '16.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Consulta en solo lectura si una cédula existe y tiene línea de crédito activa.',
    'description': 'Endpoint de solo lectura + script del sitio para orientar al cliente al inicio del formulario.',
    'depends': ['website', 'crm'],
    'data': [],
    'assets': {
        'web.assets_frontend': [
            'latinbien_cedula_check/static/src/js/cedula_check.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
