{
    # Theme information
    'name' : 'Clarico Compare',
    'category' : 'Website',
    'version' : '1.0',
    'summary': 'Add Products into Compare from Category & Product Page',
    'description': """""",

    # Dependencies
    'depends': [
        'clarico_shop','clarico_extra_features'
    ],

    # Views
    'data': [
        'security/ir.model.access.csv',
        'template/compare_theme_template.xml',
        'view/compare_product.xml',
        'view/product_templat_compare.xml',
        'template/compare_page.xml',
        'template/assets.xml',
        'template/compare_list_popout.xml',
    ],

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',

    # Technical
    'installable': True,
}
