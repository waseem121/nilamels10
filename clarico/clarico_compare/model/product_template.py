from odoo import api, fields, models
    
    
class product_template(models.Model):
    _inherit = ["product.template"]
    
    compare_product_id = fields.Many2one('compare.product', 'Compare Product')
