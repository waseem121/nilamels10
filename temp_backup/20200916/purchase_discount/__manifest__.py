# -*- coding: utf-8 -*-
##############################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##############################################################################
{
    'name': "Purchase Discount",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'stock', 'purchase', 'direct_sale', 'account',
                'purchase_landed_cost'],

    'data': [
        'security/security_view.xml',
        'views/account_invoice.xml',
        'views/purchase.xml',
        'views/res_config_views.xml'
    ],
    'demo': [
    ],
}
