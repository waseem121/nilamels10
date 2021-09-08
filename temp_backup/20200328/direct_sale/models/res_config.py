from odoo import api, fields, models, _

class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'
    
    is_discount_posting_setting = fields.Boolean('Discount Posting')
    discount_posting_account_id_setting = fields.Many2one('account.account',string='Discount Account')
    foreign_exchange_profit_loss_accound_id = fields.Many2one('account.account',string='Foreign Exchange Profit Loss Account')
    
    
    @api.multi
    def set_is_discount_posting_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'account.config.settings','is_discount_posting_setting',self.is_discount_posting_setting, company_id=self.env.user.company_id.id)
            
    @api.multi
    def set_discount_posting_account_id_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'account.config.settings','discount_posting_account_id_setting',self.discount_posting_account_id_setting.id, company_id=self.env.user.company_id.id)
            
    @api.multi
    def set_foreign_exchange_profit_loss_accound_id(self):
        return self.env['ir.values'].sudo().set_default(
            'account.config.settings','foreign_exchange_profit_loss_accound_id',self.foreign_exchange_profit_loss_accound_id.id, company_id=self.env.user.company_id.id)            
        
