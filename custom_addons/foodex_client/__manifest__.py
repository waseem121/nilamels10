# -*- coding: utf-8 -*-
{
    'name': "foodex_client",

    'summary': """
        Module for Foodex customizations
""",

    'description': """
        Nialmels customizations
    """,

    'author': "Mada Solutions Pvt Ltd",
    'website': "http://www.madasolns.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','direct_sale','foodex','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_views.xml',
        'report/sale_report.xml',
        'report/sale_report_templates.xml',
        'report/sale_report_templates_no_header.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}