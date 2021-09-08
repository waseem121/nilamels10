from odoo import models,fields

class extra_features_line(models.Model):
    _name="extra.features.line"
    
    extra_product_tmpl_id =  fields.Many2one('product.template', 'Product Template', required=True, ondelete='cascade')
    attribute_id = fields.Many2one('product.attribute', 'Attribute', required=True, ondelete='restrict', translate=True)
    value_ids = fields.Many2many('product.attribute.value','product_extra_features', 'line_id', 'val_id', string='Extra Features Value', translate=True)	
