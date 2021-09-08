# -*- coding: utf-8 -*-
{
    'name': "foodex",

    'summary': """
        Foodex customizations
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Mada Solutions Pvt Ltd",
    'website': "http://www.madasolns.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','account','direct_sale','account_powersports','multiple_uom_pricelist','stock','stock_account'],

    # always loaded
    'data': [
        'security/security_view.xml',    
        'security/ir.model.access.csv',
        'data/account_data.xml',
        'views/account_invoice_view.xml',
        'views/account_payment_view.xml',
        'views/res_users_view.xml',
        'views/stock_picking_views.xml',
        'report/report.xml',
        'report/collection_report_template.xml',
        'report/custom_stock_report_van_template.xml',
        'wizard/wizard_collection_report.xml',
        'wizard/stock_report_van_view.xml',
        'wizard/manual_reconcile_custom_view.xml',
        'wizard/change_customer_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}