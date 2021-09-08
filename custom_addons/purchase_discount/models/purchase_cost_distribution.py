# -*- coding: utf-8 -*-
from openerp import models, fields, exceptions, api, _


class PurchaseCostDistributionLine(models.Model):
    _inherit = "purchase.cost.distribution.line"

    @api.one
    @api.depends('move_id')
    def _get_standard_price_old(self):
        """
        update standard price based on shared discount
        """
        qty_default_uom = 0.0
        if self.purchase_line_id.product_qty > 0.0:
#            qty_default_uom = self.purchase_line_id.product_uom.\
#                _compute_quantity(
#                self.purchase_line_id.product_qty,
#                self.purchase_line_id.product_id.uom_id)
            qty_default_uom = self.move_id.product_qty
        subtotal = self.purchase_line_id.price_subtotal - \
                   self.purchase_line_id.discount_share
        if qty_default_uom > 0:
            self.standard_price_old = subtotal / qty_default_uom
        #            self.standard_price_old =  self.move_id.price_unit
        else:
            self.standard_price_old = subtotal
        # ## check currency difference
        if self.purchase_id.currency_id != self.distribution.currency_id:
            exchange_rate = self.purchase_line_id and self.purchase_line_id.order_id.exchange_rate or 0.0
            if exchange_rate:
                self.standard_price_old = self.purchase_id.currency_id.compute_custom(
                    self.standard_price_old, self.distribution.currency_id,
                    exchange_rate, round=False)
            else:
                self.standard_price_old = self.purchase_id.currency_id.compute(
                    self.standard_price_old, self.distribution.currency_id,
                    round=False)
                    
    
    # Substracting the Discount share from the subtotal
    @api.one
    @api.depends('product_price_unit', 'product_qty')
    def _compute_total_amount(self):
        # ## check currency difference not required as standard_price_old already in right currency
#        self.total_amount = self.standard_price_old * self.product_qty
        if self.purchase_id.currency_id.id != self.distribution.currency_id.id:
            exchange_rate = self.purchase_line_id and self.purchase_line_id.order_id.exchange_rate or 0.0
            if exchange_rate:
                local_subtotal = (self.purchase_line_id.price_subtotal - self.purchase_line_id.discount_share) / exchange_rate
            else:
                local_subtotal = (self.purchase_line_id.price_subtotal - self.purchase_line_id.discount_share) / 1
        else:
            local_subtotal = (self.purchase_line_id.price_subtotal - self.purchase_line_id.discount_share) / 1
        self.total_amount = local_subtotal
        
    total_amount = fields.Float(
        compute=_compute_total_amount, string='Amount line',
        digits=(12, 4))
