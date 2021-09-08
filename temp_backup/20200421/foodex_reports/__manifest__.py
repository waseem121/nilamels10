# -*- coding: utf-8 -*-
{
    'name': "FOODEX REPORTS",

    'summary': """
        Foodex customizations
        """,

    'description': """
        Long description of module's purpose
    """,

    'category': '',
    'version': '0.1',

    'depends': ['base','sale','account','direct_sale','stock'],

    'data': [
        'report/template_purchase_register.xml',
        'views/purchase_register.xml',
        'views/itemwise_sale.xml',
        'report/itemwise_sale_template.xml',
        'views/invoice_datewise.xml',
        'report/invoice_datewise_template.xml',
        'views/sale_return.xml',
        'report/sale_report_template.xml',
        'views/salesman_report.xml',
        'report/salesman_report_template.xml',
        'views/cash_payment_report.xml',
        'report/cash_payment_report_template.xml',
        'views/bank_payment_report.xml',
        'report/bank_payment_report_template.xml',
        'views/supplier_sale.xml',
        'report/supplier_register_template.xml',
        'views/item_details_report.xml',
        'report/item_details_report_temlate.xml',
        'views/stock_move_report.xml',
        'report/stock_move_report_template.xml',
        'views/pending_transfer.xml',
        'report/pending_transfer_template.xml',
        'views/vander_sales.xml',
        'report/vendor_sale_template.xml'
    ],
}