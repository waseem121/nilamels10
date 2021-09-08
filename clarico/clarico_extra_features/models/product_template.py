from odoo import api, fields, models
    
    
class product_template(models.Model):
    _inherit = ["product.template"]
    
    extra_features_sort_description = fields.Text('Short Description', translate=True)
    extra_features_id = fields.One2many('extra.features.line','extra_product_tmpl_id','Extra Features')
    
