from odoo import api, fields, models

class website_config_settings(models.TransientModel):
    _inherit = 'website.config.settings'

    module_clarico_shop_left = fields.Selection([
        (0, 'Uninstall Module'),
        (1, 'Install Module')
        ], "Clarico Shop Left Layout")
    module_clarico_shop_right = fields.Selection([
        (0, 'Uninstall Module'),
        (1, 'Install Module')
        ], "Clarico Shop Right Layout")
    module_clarico_shop_list = fields.Selection([
        (0, 'Uninstall Module'),
        (1, 'Install Module')
        ], "Clarico Shop List Layout")
    module_clarico_blog = fields.Selection([
        (0, 'Uninstall Module'),
        (1, 'Install Module')
        ], "Clarico Blog")
    module_clarico_compare = fields.Selection([
        (0, 'Uninstall Module'),
        (1, 'Install Module')
        ], "Clarico Product Compare")
    module_clarico_account = fields.Selection([
        (0, 'Uninstall Module'),
        (1, 'Install Module')
        ], "Clarico Account")
    module_clarico_reset_password = fields.Selection([
         (0, 'Uninstall Module'),
         (1, 'Install Module')
         ], "Clarico Reset Password")
        
    
