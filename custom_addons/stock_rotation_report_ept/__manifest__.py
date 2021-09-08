# -*- coding: utf-8 -*-pack
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    # App information
    'name': 'Stock Rotation Report',
    'version': '10.0',
    'category': 'Sales',
    'license': 'OPL-1',
    'summary' : 'Gives you a stock movements between specific dates for a specific or all warehouses.',
   
	# Dependencies
    'depends': ['stock'],
    
    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    
    # Views
    'data': [
                'wizard/stock_rotation_report.xml',
            ],
    'demo': [],
    
    
     # Odoo Store Specific
    'images': ['static/description/Stock-Rotation-Report-cover.jpg'], 
    
    
    
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url':'http://www.emiprotechnologies.com/free-trial?app=stock-rotation-report-ept&version=10&edition=enterprise',
    'price': '99',
    'currency': 'EUR',
}
