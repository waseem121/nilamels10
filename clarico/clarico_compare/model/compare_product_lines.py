from odoo import models, fields, api
 
class compare_product_lines(models.Model):
    _name = 'compare.product.lines'
    
    product_tmpl_id =  fields.Many2one('compare.product','Template Compare')
    name = fields.Char('Name')
    attribute_id = fields.Many2one('product.attribute', 'Compare Product Attribute')
