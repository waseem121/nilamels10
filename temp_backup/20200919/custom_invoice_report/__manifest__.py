# -*- coding: utf-8 -*-

# © 2020 Mohsin Khan
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Custom Invoice Report',
    'version': '10.0.1.0.0',
    'author': 'Mohsin Khan',
    'category': 'Accounting',
    'license': 'LGPL-3',
    'sequence': 7,
    'depends': [
        'account',
    ],
    'data': [
        'views/report_layout.xml',
        'views/invoice_report.xml',
        'views/report_invoice_custom.xml',
        'views/account_invoice_view.xml'
    ],
    'installable': True,
    'application': True,
}
