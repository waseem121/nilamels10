# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': 'Direct Sale',
    'version': '1.2',
    'category': 'Sale',
    'summary': 'Direct Sale Solution',
    'description': """
This module allows user to use Direct Sale Functionality.
""",
    'price':'' ,
    'currency': '',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': 'http://www.acespritech.com',
    'depends': ['base', 'sale', 'purchase', 'account', 'account_accountant', 'stock', 'stock_restrict_locations', 
            'dusal_product', 'flexiretail','account_analytic_default_siafa','account_powersports'],
    "data": [
        'security/ir.model.access.csv',
        'views/js_templates.xml',
        'views/account_view.xml',
        'views/sale_view.xml',
        'report/report_deliveryslip.xml',
        'views/res_user_view.xml',
        'views/stock_picking_views.xml',
        'views/product_pricelist_view.xml',
        'report/sale_analysis_report.xml',
        'wizard/sales_cashier_summary.xml',
        'report/report.xml',
        'report/sales_summary_report_template.xml',
        'wizard/sales_detail_report.xml',
        'report/sales_detail_report_template.xml',
        'views/account_journal_view.xml',
        'views/res_config_view.xml',
        'views/department_division_view.xml',
        'views/res_partner_view.xml',
        'views/account_payment_view.xml',
    ],
    'images': [],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
