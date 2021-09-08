# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _prepare_analytic_account(self, line):
        pos_config_obj = self.env['pos.config']

        location_id = line.order_id.location_id.id
        pos_config_id = line.order_id.session_id.config_id.id
        analytic_account_id = pos_config_obj._get_account_analytic(location_id, pos_config_id)
        print "analytic_account_id: ",analytic_account_id
        
        return analytic_account_id
