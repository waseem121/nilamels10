##############################################################################
#    Copyright (C) 2017 oeHealth (<http://oehealth.in>). All Rights Reserved
#    oeHealth, Hospital Management Solutions
##############################################################################

{
    'name': 'POS Constraint',
    'version': '1.0',
    'author': "Odoo",
    'sequence': 85,

    'summary': 'pos',
    'depends': ['point_of_sale'],
    'description': """

    
    """,
        "website": "www.odoo.in",
        "data": [
            #'pos_template.xml',
        ],
        
        'installable': True,
        'application': True,
        'qweb': ['static/src/xml/pos.xml'],
}