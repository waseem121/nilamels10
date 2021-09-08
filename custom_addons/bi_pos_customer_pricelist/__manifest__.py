# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Odoo POS Customer Pricelist",
    "version" : "10.0.0.1",
    "category" : "Point of Sale",
    "price": 39,
    "currency": 'EUR',
    "depends" : ['base','sale','point_of_sale'],
    "author": "BrowseInfo",
    'summary': 'This apps helps to manage Customer specific Pricelist on POS order',
    "description": """
    
    Purpose :- 
This Module allows you to apply pricelist on particular customer.
    POS pricelist, Point of Sale Customer pricelist, Pricelist on POS, Customer pricelist on POS, Customer pricelist on point of sale, Pricelist for customer.POS product pricelist POS item pricelist, POS partner Pricelist, POS Stock.
    """,
    "website" : "www.browseinfo.in",
    "data": [
        'views/custom_pos_view.xml',
    ],
    'qweb': [
        'static/src/xml/bi_pos_customer_pricelist.xml',
    ],
    "auto_install": False,
    'website': 'http://www.browseinfo.in',
    "installable": True,
    "images":['static/description/Banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
