# -*- coding: utf-8 -*-
{
    'name': "Account Serial",

    'summary': """
        *Serial Number management for Accounts.
""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mada Solutions Pvt Ltd",
    'website': "http://www.madasolns.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','gts_coa_hierarchy_v10'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_view.xml',
    ],
    # only loaded in demonstration mode
#    'demo': [
#        'demo/demo.xml',
#    ],
}