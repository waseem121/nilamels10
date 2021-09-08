# -*- coding: utf-8 -*-
{
    'name': "account_report_xls",

    'summary': """
    """,

    'description': """
        Account Report XLS
    """,

    'author': "Jayesh Joshi",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account','report_xls','ledgers_filter_custom'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_report_xls_view.xml',
        'wizard/account_financial_report_view.xml',
        'wizard/report_aged_partner_balance_view.xml',
        'wizard/account_report_print_journal_view.xml',
        'wizard/account_report_general_ledger_view.xml',
        'wizard/account_report_trial_balance_view.xml',
        'wizard/partner_ledger_report_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}