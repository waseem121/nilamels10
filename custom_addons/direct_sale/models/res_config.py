from odoo import api, fields, models, _

class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'
    
    is_discount_posting_setting = fields.Boolean('Discount Posting')
    discount_posting_account_id_setting = fields.Many2one('account.account',string='Discount Account')
    group_enable_currency_in_invoice = fields.Boolean(
        "Enable Currency in Invoice", group='base.group_user',
        implied_group='direct_sale.group_enable_currency_in_invoice',
        help="""Enables the multi currency and exchange rates features.""")
        
    group_allow_negative_qty = fields.Boolean(
        "Allow Negative Quantity in Invoice,Transfers,Damages", group='base.group_user',
        implied_group='direct_sale.group_allow_negative_qty',
        help="""Allow Negative Quantity in Invoice,Transfers,Damages.""")

    days_draft_invoice_from = fields.Integer(
        "Days from which draft invoice has tobe considered for Draft invoice qty.", group='base.group_user',
        help="""Days from which draft invoice has tobe considered for Draft invoice qty.""")
    
    @api.multi
    def set_is_discount_posting_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'account.config.settings','is_discount_posting_setting',self.is_discount_posting_setting, company_id=self.env.user.company_id.id)
            
    @api.multi
    def set_discount_posting_account_id_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'account.config.settings','discount_posting_account_id_setting',self.discount_posting_account_id_setting.id, company_id=self.env.user.company_id.id)

    @api.multi
    def set_days_draft_invoice_from_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'account.config.settings','days_draft_invoice_from',self.days_draft_invoice_from, company_id=self.env.user.company_id.id)
        
