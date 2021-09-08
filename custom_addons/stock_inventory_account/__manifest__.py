# -*- coding: utf-8 -*-
{
    'name': "Inventory Adjustment Accounting",

    'summary': """
    """,

    'description': """
A new account field added in category which will be used as counter-part account when any inventory adjustment is done.
    """,

    'author': "Aasim Ahmed Ansari",
    'website': "www.linkedin.com/in/aasimansari",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Warehouse',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}