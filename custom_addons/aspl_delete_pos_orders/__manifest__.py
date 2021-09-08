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
    'name': "Delete POS Order",
    'version': '1.1',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'category': 'Point of Sale',
    'description': """
                This module allow delete paid or posted Pos orders.
            """,
    'website': "http://www.acespritech.com",
    'price': 12.00,
    'currency': 'EUR',
    'summary': 'This module allow delete paid or posted POS orders.',
    'depends': ['sale', 'point_of_sale','account_cancel'],
    'data': [
             'wizard/pos_cancel_wizard.xml',
             'views/pos_config_view.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    "installable": True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: