from odoo import api, fields, models
    
    
class res_partner(models.Model):
    _inherit = ["res.partner"]
    
    is_brand=fields.Boolean("Is Brand?")
