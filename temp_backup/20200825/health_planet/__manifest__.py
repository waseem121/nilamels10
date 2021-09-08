# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Health Planet',
    'version': '1.0',
    'category': 'Sales',
    'sequence': 81,
    'summary': 'Manage customer requirement',
    'description': """
This module aims to fulfill Health Planet's business requirement.
==================================================
    
    * Product Form modification

       """,
    'website': 'https://www.odoo.com/',
    'depends': ['product','stock','point_of_sale','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/stock_pack_operation_view.xml',
        'views/pos_templates.xml',
        'views/stock_picking_view.xml',
        'views/res_partner_view.xml',
        'views/pos_order_view.xml',
	'views/stock_production_lot_view.xml',
	'views/sale_order_view.xml'
    ],
    'demo': [ ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'application': True,
}
