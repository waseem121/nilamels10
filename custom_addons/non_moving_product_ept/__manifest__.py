{
    
     # App information
    'name': 'Non Moving Products Report',
    'version': '10.0',
    'category': 'stock',
    'license': 'OPL-1',
    'summary' : 'Non Moving Products Report gives the list of products which are in stock but doesn’t have any movement (doesn’t have sales) in specified date range. Report will be generated warehouse wise along with it’s last sales information.',
   
    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',   
    'website': 'http://www.emiprotechnologies.com/',
    
    
     # Odoo Store Specific   
    'images': ['static/description/Non-Moving-Products-Report-Cover.jpg'],
    
     # Dependencies
    'depends': ['sale', 'purchase'],
    'data': [
      'wizard/non_moving_product_wizard_views.xml'
            ],
       
    
    # Technical        
    'external_dependencies' : {'python' : ['xlwt'], },
    'installable': True,
    'auto_install': False,
    'application' : True,
    'live_test_url':'http://www.emiprotechnologies.com/free-trial?app=non-moving-product-ept&version=10', 
    'active': False,
    'price': 49.00,
    'currency': 'EUR',  

    
}
