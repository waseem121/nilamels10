# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Dusal.net
#
##############################################################################

{
    "name" : "Hide cost price of product",
    'summary' : "Hide cost price, hide standard price, sale price, user group, selected users",
    "version" : "2.2",
    "description": """
        This module hide product cost and sale price of product and show it to only selected user group.
        Support and contact email: almas@dusal.net Feel free to contact us.
    """,
    'author' : 'Dusal Solutions',
    'support': 'almas@dusal.net',
    'license': 'Other proprietary',
    'price': 10.00,
    'currency': 'EUR',
    'images': ['static/images/main_screenshot.png', 'static/images/screenshot0.png', 'static/images/screenshot.png', 'static/images/screenshot1.png'],
    "depends" : [
                 "product",
    ],
    "data" : [
                'dusal_product_views.xml',
                'security/product_security.xml',
                ],
    "auto_install": False,
    "installable": True,
}
