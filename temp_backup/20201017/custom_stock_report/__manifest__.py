{
    'name': 'Custom Stock Report',
    'version': '1.0',
    'category': 'General',
    'website': 'http://www.acespritech.com',
    'description': "",
    'author': "Acespritech Solutions Pvt. Ltd.",
    'depends': ['stock', 'purchase', 'product_brand'],
    'data': [
        'views/stock_report.xml',
        'views/stock_report_lot.xml',
        'views/product_views.xml',
        'report/custom_stock_report_template.xml',
        'report/custom_stock_report_lot_template.xml'
    ],
    'installable': True,
    'auto_install': False
}
