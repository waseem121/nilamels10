# -*- coding: utf-8 -*-
{
    'name': 'POS Session Report',
    'summary': 'Allow to Print Current Session Report',
    'description': """
    Module Developed for Session Report.
    """,
    'category': 'Point of Sale',
    'version': '1.0',
    'author': 'TechnoSquare',
    'website': 'http://technosquare.in',
    'depends': ['point_of_sale'],
    'data': [
        'views/templates.xml',
        'views/pos_config.xml',
        'report/report_pos_session.xml',
    ],
    'qweb': [
        'static/src/xml/session_report.xml',
    ],
    'images': ['static/description/banner.png'],
    'price': 20,
    'currency': "EUR",
    "auto_install": False,
    "installable": True,
}
