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
    'name': 'Direct Invoice View',
    'version': '1',
    'category': 'Sale',
    'summary': 'Direct Invoice',
    'description': """View invoice lines with smart button""",
    'price':'' ,
    'currency': '',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'depends': ['base', 'sale'],
    "data": [
        'views/product_product.xml',
        'views/sale_order_view.xml',
        # 'views/account_view.xml',
    ],
    'images': [],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}