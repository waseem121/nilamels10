# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_stock_picking(self):
        pickings = self.order_ids.mapped('picking_id').filtered(lambda x: x.state != 'done')
        action_picking = self.env.ref('health_planet.action_picking_readonly_tree_ready')
        action = action_picking.read()[0]
        action['context'] = {}
        action['domain'] = [('id', 'in', pickings.ids)]
        return action

    '''@api.multi
    def action_pos_session_closing_control(self):
        for session in self:
            pickings = self.order_ids.mapped('picking_id').filtered(lambda x: x.state != 'done')
            if pickings:
                raise UserError(_("Please process all the delivery orders before closing this session "))
        return super(PosSession, self).action_pos_session_closing_control()'''

    @api.constrains('user_id', 'state')
    def _check_unicity(self):
        # open if there is no session in 'opening_control', 'opened', 'closing_control' for one user
        if self.search_count([
            ('state', 'not in', ('closed', 'closing_control')),
            ('user_id', '=', self.user_id.id),
            ('name', 'not like', 'RESCUE FOR'),
        ]) > 1:
            # Customer requirement
            # Bad Practices
            pass

    @api.multi
    def login(self):
        for session in self:
            session.write({
            'login_number': session.login_number + 1,
        })
