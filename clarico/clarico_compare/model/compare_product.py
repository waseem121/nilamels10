from odoo import models, fields, api
 
class compare_product(models.Model):
    _name = 'compare.product'
    

    name = fields.Char('Name',required=True)
    compare_attr_id = fields.One2many('compare.product.lines', 'product_tmpl_id', 'Compare Product Lines' )
