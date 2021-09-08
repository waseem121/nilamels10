from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"
    
    promotion_account_id = fields.Many2one('account.account',
        string="POS Promotion Account",help="Account used for posting point of sale promotion entries")