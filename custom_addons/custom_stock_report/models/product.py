from odoo import fields, models, api, _

class product_product(models.Model):
    _inherit = "product.product"
    
    @api.model
    def default_get(self, fields_list):
        res = super(product_product, self).default_get(fields_list)
        res.update({'type': 'product'})
        return res

    @api.constrains('default_code')
    def _check_default_code_constrain(self):
        count_default_code = self.search_count([('default_code','=',self.default_code)])
        if count_default_code > 1:
            raise Warning(_('Internal Reference must be unique.'))
