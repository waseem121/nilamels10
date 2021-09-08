# -*- coding: utf-8 -*-
{
    'name': "pos_anglo_saxon_accounting",

    'summary': """
        Point Of Sale COGS (Anglo-Saxon)""",

    'description': """
        Create Cost of Goods Sold moves when POS session is closed.
    """,

    'author': "Your Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','point_of_sale'],

    # always loaded
    'data': [
        'views/point_of_sale_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}