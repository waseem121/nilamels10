# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name" : " multi UOM pricelist",
    "version" : "10.0.0.1",
    "category" : "",
    'summary': 'Brief description of the module',
    "description": """
    
   Description of the module. 
    
    """,
    "author": "BrowseInfo",
    "website" : "www.browseinfo.in",
    "price": 000,
    "currency": 'EUR',
    "depends" : ['base','sale','stock','direct_sale'],
    "data": [
        'views/product_template_inherited.xml',
        'views/product_pricelist.xml',
    ],
    'qweb': [
    ],
    "auto_install": False,
    "installable": True,
    "live_test_url":'youtube link',
    "images":["static/description/Banner.png"],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
