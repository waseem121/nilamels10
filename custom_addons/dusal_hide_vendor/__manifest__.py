# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Dusal.net
#
##############################################################################

{
    "name" : "Hide vendors field of product",
    'summary' : "Hide vendors field, user group, selected users",
    "version" : "1.0",
    "description": """
        This module hide field vendors of product and show it to only selected user group.
        Support and contact email: almas@dusal.net Feel free to contact us.
    """,
    'author' : 'Dusal Solutions',
    'support': 'almas@dusal.net',
    'license': 'Other proprietary',
    'price': 10.00,
    'currency': 'EUR',
    'images': ['static/images/main_screenshot.png', 'static/images/screenshot.png'],
    "depends" : [
                 "product",
                 "purchase",
    ],
    "data" : [
                'dusal_product_views.xml',
                'security/product_security.xml',
                ],
    "auto_install": False,
    "installable": True,
}
