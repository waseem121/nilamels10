# -*- coding: utf-8 -*-
{
    'name': 'POS Fixed Amount Discount',
    'version': '10.0.1.0.1',
    'category': 'Point Of Sale',
    'sequence': 20,
    'author': 'AppJetty',
    'website': 'https://goo.gl/mFzoX9',
    'summary': 'POS Fixed Amount Discount',
    'description': """
POS Fixed Amount Discount
POS Discount Rules
POS Coupons Discount
POS Discount 
POS Discount on Product
Fixed amount discount
flat discount
point of sale
POS Global Discount
Discounts
point of sale discount
    """,
    'depends': ['point_of_sale', 'account'],
    'data': [
        'views/point_of_sale.xml',
        'views/pos_config_view.xml',
        'views/pos_view.xml',
        'views/account_invoice_view.xml',
        'views/report_invoice.xml',
        'views/report_saledetails.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'qweb': ['static/src/xml/pos.xml'],
    'images': ['static/description/splash-screen.png'],
    'price': 25.00,
    'currency': 'EUR',
    'support': 'support@appjetty.com',
}
