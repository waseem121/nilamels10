# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields,api

class PosAccountAnalytic(models.Model):
    _name = 'pos.account.analytic'
    
    sequence = fields.Integer(string='Sequence', default=10)
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account', string='Analytic Account',
        domain=[('analytic_type_id.is_view', '!=', 'view')])
    pos_config_id = fields.Many2one(
        comodel_name='pos.config', string='POS Configuration')
        
#    _rec_name = account_analytic_id
        

class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    account_analytic_ids = fields.One2many('pos.account.analytic', 'pos_config_id', string='Analytic Accounts', copy=False)
#    default = fields.Boolean(default=True, copy=False, help="If checked then analytic configuration of this location will be used.")
    
    @api.multi
    def _get_account_analytic(self, location_id, pos_config_id):

        if not pos_config_id:
            return False

        self.env.cr.execute(
            'SELECT pacc.id '
            'FROM pos_account_analytic AS pacc '
            'WHERE pos_config_id = %s '
            'ORDER BY sequence',
            (pos_config_id,))
        
        res = self.env.cr.fetchall()
        if not res:
            return False
        
        pos_account_analytic_ids = [x[0] for x in res]
        pos_account_analytic_obj = self.env['pos.account.analytic']
        pos_account_analytic = pos_account_analytic_obj.browse(pos_account_analytic_ids[0])
        
        return pos_account_analytic.account_analytic_id.id
        
#    def _check_default(self):
#        for pos_config in self:
#            if pos_config.default:
#                pos_config_ids = self.search([
#                    ('default', '=', True), ('stock_location_id','=',pos_config.stock_location_id.id)
#                    ])
#                if len(pos_config_ids) > 1:
#                    return False
#        return True
    
#    _constraints = [
#        (_check_default,
#            'You cannot create more than one default configuration per stock location.',
#            ['default']),
#    ]

