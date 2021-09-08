# -*- coding: utf-8 -*-
{
    'name': "Purchase Free Qty",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','account','stock','purchase','sale','direct_sale'],

    'data': [
        'security/security_view.xml',
        'views/res_config_views.xml',
        'views/purchase.xml',
        'views/account_view.xml',
        'views/sale_view.xml'
    ],
    'demo': [
    ],
}