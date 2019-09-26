# -*- coding: utf-8 -*-

# Copyright 2019 Ingeniería Cloud - Pedro Baños
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': "portal cuestionarios",
    'summary': """Añade al área de usuario en portal los descargables requeridos""",
    'version': '12.0.1.1.0',
    'category': 'Other',
    'website': "https://ingenieriacloud.com",
    'author': "pjb",
    'license': 'AGPL-3',
    'installable': True,
    'depends': [
        'website',
    ],
    'data': [
        'views/templates.xml',
        'report/cuestionarios_report_templates.xml',
        'report/cuestionarios_report.xml',
    ],
}
