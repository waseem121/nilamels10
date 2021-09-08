{
    # Theme information
    'name' : 'Theme Clarico',
    'category' : 'Theme/eCommerce',
    'version' : '1.0',
    'summary': 'Fully Responsive, Clean, Modern & Sectioned Odoo eCommerce Theme',
    'description': """.""",
    'license': 'OPL-1',

    # Dependencies
    'depends': [
            #'website',     
              'clarico_attribute_filter',
          	 'clarico_latest_blog',
              'clarico_brand',
               'clarico_category',
              'clarico_category_attribute',
           	 'clarico_404',
              'clarico_extra_features',
           	 'clarico_recently_viewed',
           	 'clarico_cms_blocks',
           	 'clarico_contact',
           	 'clarico_email_subscriber',
           	 'clarico_layout1',
           	 'clarico_layout2',
           	 'clarico_reset_password',
      		 'clarico_shop_left_sidebar',
              'clarico_shop_list',
               'clarico_shop_right_sidebar',
               'clarico_signin',
               'clarico_signup',
              'clarico_product_carousel_wishlist',
               'clarico_quick_view_compare',
               'clarico_quick_view_wishlist',
              'clarico_carousel_quick_view',
               'clarico_pricefilter',
               'customize_theme',
              'clarico_compare_wishlist',

                  
    ],


    # Views
    'data': [
         'data/clarico_data.xml',  
        # 'data/company_data/company_data.xml',
    ],
   
    #Odoo Store Specific

    'images': [
'static/description/main.jpg',
'static/description/main_second.jpeg'
],
    
    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Technical
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 299.00,
    'currency': 'EUR',
}
