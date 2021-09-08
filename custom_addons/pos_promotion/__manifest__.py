# -*- coding: utf-8 -*-
{
    'name': 'POS Promotions',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 0,
    'author': 'TL Technology',
    'price': '77.92',
    'website': 'http://bruce-nguyen.com',
    'currency': 'USD',
    'depends': ['point_of_sale'],
    'description': "When we're sale product, we'll need promotions running \n"
                   "By 100 USD percent 10% \n"
                   "By Product x gift product y \n"
                   "...or something like that",
    'data': [
        'security/ir.model.access.csv',
        'data/parameter.xml',
        '__import__/template.xml',
        'view/pos_promotion_view.xml',
        'view/pos_config_view.xml',
        'view/pos_order.xml',
        'view/company_view.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'application': True,
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
    'support': 'thanhchatvn@gmail.com'
}
