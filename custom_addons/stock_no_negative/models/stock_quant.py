# -*- coding: utf-8 -*-
# © 2015-2017 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import config, float_compare
from odoo.exceptions import UserError

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.multi
    @api.constrains('product_id', 'qty')
    def check_negative_qty(self):
        p = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        check_negative_qty = (
            config['test_enable'] and self.env.context.get(
                'test_stock_no_negative')) or (
            'test_enable' not in config.options)
        if not check_negative_qty:
            return
        for quant in self:
            if (float_compare(quant.qty, 0, precision_digits=p) == -1 and
                    quant.product_id.type == 'product' and
                    not quant.product_id.allow_negative_stock and
                    not quant.product_id.categ_id.allow_negative_stock):
                msg_add = ''
                if quant.lot_id:
                    msg_add = _(" lot '%s'") % quant.lot_id.name_get()[0][1]
                raise ValidationError(_(
                    "You cannot validate this stock operation because the "
                    "stock level of the product '%s'%s would become negative "
                    "(%s) on the stock location '%s' and negative stock is "
                    "not allowed for this product.") % (
                        quant.product_id.name, msg_add, quant.qty,
                        quant.location_id.complete_name))

    @api.model
    def quants_move(self, quants, move, location_to, location_from=False, lot_id=False, owner_id=False,
                    src_package_id=False, dest_package_id=False, entire_pack=False):
        ### Custom code added start- Aasim
        if any([x for x in quants if x[0] is None]) and move.location_id.usage == 'internal' and move.product_id.type == 'product':
            raise UserError(_("You don't have enough stock for product %s.") % (move.product_id.name,))
        ### Custom code added stop- Aasim

        return super(StockQuant, self).quants_move(quants, move, location_to, location_from, lot_id, owner_id, src_package_id, dest_package_id, entire_pack)
