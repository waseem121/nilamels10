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
    'name': "Account Customization Powersports",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Aasim Ahmed Ansari",
    'website': "http://aasimania.wordpress.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['account', 'account_voucher'],
    'data': [
        'account_report.xml',
        'account_view.xml',
        'views/report_accountvoucher.xml',
        'views/report_accountvoucher_account_move.xml',
        'views/report_trialbalance.xml',
        'views/report_agedpartnerbalance.xml',
        'res_company_view.xml'
    ],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: