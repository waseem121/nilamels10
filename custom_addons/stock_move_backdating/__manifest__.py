# -*- coding: utf-8 -*-
{
    "name": "Stock Move Backdating",
    "version": "1.0",
    'author': 'Marco Dieckhoff, BREMSKERL, Agile Business Group',
    "category": "Stock Logistics",
    'website': 'www.bremskerl.com',
    'license': 'AGPL-3',
    "depends": ["stock"],
    "summary": "Allows back-dating of stock moves",
    "description": """This module allows to register old stock moves
    (with date != now).
    On stock moves, user can specify the "Actual Movement Date", that will be
    used as movement date""",
    'data': [
        "wizard/update_date_of_transfer_view.xml",
        "view/stock_move_views.xml",
        "view/stock_pack_operation_views.xml",
        "view/stock_picking_views.xml",
        "wizard/stock_immediate_transfer_views.xml",
        "wizard/stock_backorder_confirmation_views.xml",
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
