from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

class base_config_settings(models.TransientModel):
    _inherit = 'base.config.settings'
   
    signup_bg_image_id = fields.Many2one('ir.attachment')

    @api.model
    def get_default_signup_bg_image_id(self, fields):
        IrConfigParam = self.env['ir.config_parameter']
        return {
            'signup_bg_image_id': safe_eval(IrConfigParam.get_param('clarico_signup.signup_bg_image_id', 'False')),
        }

    @api.multi
    def set_signup_bg_image_id(self):
        self.ensure_one()
        IrConfigParam = self.env['ir.config_parameter']
        IrConfigParam.set_param('clarico_signup.signup_bg_image_id', repr(self.signup_bg_image_id.id))



