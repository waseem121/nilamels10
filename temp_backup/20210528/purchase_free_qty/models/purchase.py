from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import Warning
from datetime import datetime
from odoo.tools.float_utils import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    free_qty = fields.Float(string="Free Qty")

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine,self)._prepare_stock_moves(picking)
        if res and self.free_qty > 0 and res[0].get('product_uom_qty'):
            res[0]['product_uom_qty'] = res[0].get('product_uom_qty') + self.free_qty
        return res

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        vals = []
        data = {}
        for line in self:
            data[line.product_id.id] = 0

        for line in self:
            val = line._prepare_stock_moves(picking)
            if len(val):
                vals.append(val[0])
            else:
                if line.free_qty>0 and line.product_qty==0:
                    data[line.product_id.id] += line.free_qty
            
        for val in vals:
            val['product_uom_qty'] += data.get(val['product_id'], 0.0)
            done += moves.create(val)
        return done

