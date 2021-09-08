# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    discount_type = fields.Selection([
        ('perc', 'Percentage'), ('amount', 'Fixed Amount')],
        string='Discount Type', default='perc')
    discount_amount = fields.Float(
        string='Discount Amount', digits=dp.get_precision('Discount'))
    discount_glob = fields.Float(
        string='Discount(%)', digits=dp.get_precision('Discount'))
    total_share_discount = fields.Monetary(
        string='Total Share Discount', store=True,
        compute="_amount_all",
        readonly=True)
    total_item_discount = fields.Monetary(
        string='Total Item Discount', store=True, compute="_amount_all",
        readonly=True)
    total_discount = fields.Monetary(
        string='Total Discount', compute="_amount_all", store=True,
        readonly=True)
    gross_total = fields.Monetary(
        string='Gross Total', compute="_amount_all", store=True,
        readonly=True)

    @api.depends(
        'order_line.price_total', 'order_line.discount_item',
        'order_line.discount_amount_item', 'order_line.discount_share')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.00
            total_item_discount = 0.00
            total_share_discount = 0.00
            for line in order.order_line:
                total_item_discount += line.discount_amount_item
                total_share_discount += line.discount_share
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == \
                        'round_globally':
                    taxes = line.taxes_id.compute_all(
                        line.price_unit, line.order_id.currency_id,
                        line.product_qty, product=line.product_id,
                        partner=line.order_id.partner_id)
                    amount_tax += sum(
                        t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'gross_total': (amount_untaxed + amount_tax),
                'amount_total': (amount_untaxed + amount_tax) -
                                total_share_discount,
                'total_item_discount': total_item_discount,
                'total_share_discount': total_share_discount,
                'total_discount': total_item_discount + total_share_discount
            })


    @api.multi
    def action_view_invoice(self):
        res = super(PurchaseOrder, self).action_view_invoice()
        res['context']['default_discount_type'] = self.discount_type
        res['context']['default_discount_glob'] = self.discount_glob
        res['context']['default_discount_amount'] = self.discount_amount
        return res

    @api.onchange('discount_type', 'discount_amount', 'discount_glob',
                  'amount_untaxed')
    def _onchange_discount_type(self):
        prec_discount = self.env['decimal.precision'].precision_get(
            'Discount')
        amount_untaxed = self.amount_untaxed
        if float(amount_untaxed) == 0.0:
            amount_untaxed = 1.0
        if self.discount_type == 'amount':
            if len(self.order_line):
                line_data = []
                for line in self.order_line:
                    price_subtotal = self._context.get(
                        'price_subtotal') or line.price_subtotal
                    discount_percentage = \
                        self.discount_amount / amount_untaxed
                    discount_share = float_round(
                        discount_percentage * price_subtotal,
                        precision_digits=prec_discount)
                    line_data.append(
                        (1, line.id, {'discount_share': discount_share}))
                    line.write({
                        'discount_share': discount_share,
                    })
                    line.discount_share = discount_share
                self.order_line = line_data
        if self.discount_type == 'perc':
            discount_amount = amount_untaxed * (self.discount_glob / 100.0)
            if len(self.order_line):
                line_data = []
                for line in self.order_line:
                    price_subtotal = self._context.get(
                        'price_subtotal') or line.price_subtotal
                    discount_percentage = discount_amount / amount_untaxed
                    discount_share = float_round(
                        discount_percentage * price_subtotal,
                        precision_digits=prec_discount)
                    line_data.append(
                        (1, line.id, {'discount_share': discount_share}))
                    line.write({
                        'discount_share': discount_share,
                    })
                    line.discount_share = discount_share
                self.order_line = line_data


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    discount_item = fields.Float(string='Disc(%)', store=True)
    discount_amount_item = fields.Monetary(
        string='Disc Amount', store=True)
    discount_share = fields.Monetary(string='Share Discount', store=True)
    dis_share = fields.Monetary(string='share Discount per(%)', store=True)

    @api.onchange('discount_item', 'product_qty', 'price_unit')
    def onchange_discount_item(self):
        """
        Onchange Discount Items
        """
        if self._context.get('discount_item'):
            discount_amount_item = 0.00
            if self.discount_item:
                price_subtotal = self.product_qty * self.price_unit
                if price_subtotal:
                    discount_amount_item = \
                        (price_subtotal * self.discount_item) / 100
            self.discount_amount_item = discount_amount_item

    @api.onchange('discount_amount_item', 'product_qty', 'price_unit')
    def onchange_discount_amount_item(self):
        """
        Onchange Discount Amount
        """
        if self._context.get('discount_amount'):
            discount_item = 0.00
            if self.discount_amount_item:
                price_subtotal = self.product_qty * self.price_unit
                if price_subtotal:
                    discount_item = (self.discount_amount_item /
                                     price_subtotal) * 100
            self.discount_item = discount_item

    @api.depends('product_qty', 'price_unit', 'taxes_id',
                 'discount_amount_item', 'discount_item')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(
                line.price_unit, line.order_id.currency_id,
                line.product_qty, product=line.product_id,
                partner=line.order_id.partner_id)
            price_total = taxes['total_included'] - line.discount_amount_item
            price_subtotal = \
                taxes['total_excluded'] - line.discount_amount_item
            line.update({
                'price_tax': taxes['total_included'] - taxes[
                    'total_excluded'],
                'price_total': price_total,
                'price_subtotal': price_subtotal,
            })
            # call Onchange to update shared discount price
            # line.order_id.with_context({
            #     'price_subtotal': price_subtotal})._onchange_discount_type()

    @api.multi
    def _get_stock_move_price_unit(self):
        # res = super(PurchaseOrderLine, self)._get_stock_move_price_unit()
        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line.price_unit
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id,
                quantity=1.0, product=line.product_id,
                partner=line.order_id.partner_id
            )['total_excluded']
        if line.product_uom.id != line.product_id.uom_id.id:
            subtotal = line.price_subtotal - line.discount_share
            price_unit = subtotal / ((line.product_qty + line.free_qty) * (
                line.product_uom.factor_inv))
        if order.currency_id != order.company_id.currency_id:
            if order.exchange_rate:
                price_unit = order.currency_id.compute_custom(
                    price_unit, order.company_id.currency_id,
                    order.exchange_rate, round=False)
            else:
                price_unit = order.currency_id.compute(
                    price_unit, order.company_id.currency_id, round=False)
        return price_unit

    @api.model
    def create(self, vals):
        """
        """
        res = super(PurchaseOrderLine, self).create(vals)
        res.order_id._onchange_discount_type()
        return res