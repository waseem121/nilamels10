# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    instructor_id = fields.Many2one('res.partner', string='Doctor', readonly="1")

    def _force_picking_done(self, picking):
        """Force picking in order to be set as done."""
	try:
            self.ensure_one()
            super(PosOrder, self)._force_picking_done(picking)
            picking.action_assign()
            picking.action_done()
        except Exception as e:
            pass

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['instructor_id'] = ui_order.get('instructor_id', False)
        return order_fields
