{
    # Theme information
    'name' : 'Clarico Base',
    'category' : 'Website',
    'version' : '1.0',
    'summary': 'Contains Common Design Styles for Theme Clarico',
    'description': """""",

    # Dependencies
    'depends': [
        'website_sale','website_blog','website_portal_sale'
    ],

    # Views
    'data': [
        'view/clarico_setting.xml',
        'templates/assets.xml',
    ],

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',

    # Technical
    'installable': True,
    'application': False,
}
