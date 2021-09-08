{
    # Theme information
    'name' : 'Clarico Extra Features',
    'category' : 'Website',
    'version' : '1.0',
    'summary': 'Product Extra Specifications',
    'description': """""",

    # Dependencies
    'depends': [
        'clarico_product'
    ],

    # Views
    'data': [
         'security/ir.model.access.csv',
         'template/template.xml',
         'template/assets.xml',
         'views/product_template.xml'
    ],

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',

    # Technical
    'installable': True,
}
