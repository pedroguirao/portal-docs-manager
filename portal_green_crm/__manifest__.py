# -*- coding: utf-8 -*-

# Copyright 2019 Ingeniería Cloud - Pedro Baños
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': "portal green crm",
    'summary': """Añade al área de usuario los elementos requeridos
    -DI
    -NT
    -CT
    -Autorizaciones
    """,
    'version': '11.0.5.0.0',
    'category': 'Other',
    'website': "https://ingenieriacloud.com",
    'author': "Ingenieriacloud",
    'license': 'AGPL-3',
    'installable': True,
    'depends': [
       
    ],
    'data': [
        'views/templates.xml',
        'views/templates_ct.xml',
        'views/templates_nt.xml',
        'views/templates_au.xml',
    ],
}
