# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare


class Picking(models.Model):
    _inherit = "stock.picking"

    def _create_lots_for_picking(self):
        Lot = self.env['stock.production.lot']
        for pack_op_lot in self.mapped('pack_operation_ids').mapped('pack_lot_ids'):
            if not pack_op_lot.lot_id:
                lot = Lot.create({'name': pack_op_lot.lot_name,
                                  'product_id': pack_op_lot.operation_id.product_id.id,
                                   'life_date': pack_op_lot.life_date,
                                    'use_date': pack_op_lot.use_date,
                                    'removal_date': pack_op_lot.removal_date,
                                    'alert_date': pack_op_lot.alert_date,
                                  })
                pack_op_lot.write({'lot_id': lot.id})
        # TDE FIXME: this should not be done here
        self.mapped('pack_operation_ids').mapped('pack_lot_ids').filtered(lambda op_lot: op_lot.qty == 0.0).unlink()
    create_lots_for_picking = _create_lots_for_picking