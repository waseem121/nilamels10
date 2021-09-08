{
    # Theme information
    'name' : 'Clarico Wishlist',
    'category' : 'Website',
    'version' : '1.0',
    'summary': 'View List of Products added to Wishlist',
    'description': """""",

    # Dependencies
    'depends': [
        'clarico_shop','clarico_product'
    ],

    # Views
    'data': [
        'security/ir.model.access.csv',
        'template/theme_template.xml',
        'view/wishlist_view.xml',
        'view/wishlist_line_view.xml',
        'template/wishlist_template.xml',
        'template/assets.xml',
        'template/wishlist_list_popout.xml',
    ],

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',

    # Technical
    'installable': True,
}
