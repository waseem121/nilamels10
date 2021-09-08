{
    'name': "Pos Report",
    'author': 'odoo.com',
    'company': 'odoo.com',
    'website': 'http://www.odoo.com',
    'category': 'Reporting',
    'version': '0.2',
    'license': 'AGPL-3',
    'depends': [
        'base','point_of_sale',
    ],
    "data": [
           'views/order_analysis_report.xml',
            'wizard/order_analysis_view.xml',
        ],
}
