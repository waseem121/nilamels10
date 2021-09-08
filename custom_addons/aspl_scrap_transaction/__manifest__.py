# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': "Scrap Transactions",
    'version': '1.1',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'category': 'Uncategorized',
    'description': """
                Scrap Transaction.
            """,
    'website': "http://www.acespritech.com",
    'summary': 'This module allow to select scrap(Damage) account.',
    'depends': ['stock', 'stock_account', 'account'],
    'data': [
        'data/ir_sequences.xml',
        'views/product_view.xml',
        # 'views/pos_config_view.xml',
    ],
    "installable": True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
