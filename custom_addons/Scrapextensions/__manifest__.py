# -*- coding: utf-8 -*-
{
    'name': "Scrapextensions",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','stock','stock_account'],

    'data': [
        'security/ir.model.access.csv',
        'views/scrap.xml',
    ],
    'demo': [
    ],
}