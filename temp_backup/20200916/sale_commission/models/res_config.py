from odoo import api, fields, models, _

class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'
    
    group_enable_separate_discount_entry = fields.Boolean(
        "Enable Separate Discount Entry", group='base.group_user',
        implied_group='sale_commission.group_enable_separate_discount_entry',
        help="""Creates the separate journal entry for discount amount.""")
    group_enable_commission = fields.Boolean(
        "Enable Commission", group='base.group_user',
        implied_group='sale_commission.group_enable_commission',
        help="""Enables the commission.""")
    discount_account_id = fields.Many2one('account.account', string="Discount Account")
    
    
    @api.multi
    def set_discount_account_id(self):
        return self.env['ir.values'].sudo().set_default(
            'account.config.settings','discount_account_id',self.discount_account_id.id, company_id=self.env.user.company_id.id)