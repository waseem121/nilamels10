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