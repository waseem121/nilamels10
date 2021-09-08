# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _
from odoo.addons.sale_stock.models.sale_order import SaleOrderLine
from odoo.exceptions import Warning, ValidationError, UserError


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.constrains('order_line')
    def check_order_line_lot(self):
        for line in self.order_line.filtered(lambda l:l.product_id.tracking == 'serial' and l.lot_ids):
            if len(line.lot_ids) != line.product_uom_qty:
                raise ValidationError(_('Please check serial number and quantity on product %s, those must be in same number.') % 
                                  ("'" + line.product_id.name + "'")) 

    @api.multi
    def action_confirm(self):
        for order in self:
            order.state = 'sale'
            order.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                self.force_quotation_send()

            if order.pricelist_id.update_transaction_value:
                for lines in order.order_line.filtered(lambda l:l.price_unit > 0.00):
                    pricelist_item = order.pricelist_id.item_ids.filtered(lambda l:l.compute_price == 'fixed' and l.applied_on == '0_product_variant')
                    if pricelist_item:
                        each_price = order.pricelist_id.item_ids.search([('product_id', '=', lines.product_id.id),
                                                             ('compute_price', '=', 'fixed'), ('applied_on', '=', '0_product_variant'),
                                                             ('pricelist_id', '=', order.pricelist_id.id)])
                        if not each_price:
                            order.pricelist_id.write({'item_ids':[(0, 0, {'applied_on':'0_product_variant',
                                                  'product_id':lines.product_id.id,
                                                  'fixed_price':lines.price_unit})]})

                        order_lines = order.order_line.filtered(lambda l:l.product_id.id in [x.product_id.id for x in each_price] and l.price_unit > 0.00).sorted(lambda l:l.price_unit)
                        if order_lines:
                            for each_pricelist in each_price:
                                each_pricelist.fixed_price = order_lines[0].price_unit
                    else:
                        order.pricelist_id.write({'item_ids':[(0, 0, {'applied_on':'0_product_variant',
                                                  'product_id':lines.product_id.id,
                                                  'fixed_price':lines.price_unit
                                                  })]})

            if order.is_this_direct_sale:
                order.invoice_status = 'invoiced'
                order.action_invoice_create()
                order.action_done()
            else:
                # do not create picking if sales order created from invoice
                no_picking = self._context.get('no_picking', False)
                if not no_picking:
                    order.order_line._action_procurement_create()
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting') and not self.is_this_direct_sale:
            self.action_done()
        return True

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id
        }
        if self.is_this_direct_sale:
            invoice_vals.update({
                'is_direct_invoice':True,
                'discount_amount': self.discount_amount,
                'discount_glob': self.discount_glob,
                'location_id':self.location_id.id,
                'date_invoice':self.date_order,
                'from_direct_sale':True,
                'pricelist_id':self.pricelist_id.id,
            })
        return invoice_vals

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            discount_amt = 0.0
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
#                 line.write({'discount_share':order.discount_glob})
                amount_untaxed += line.price_subtotal
                discount_amt += line.discount_amount
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                    product=line.product_id, partner=order.partner_shipping_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax

            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': (amount_untaxed + amount_tax - order.discount_amount),
                'total_discount':discount_amt + order.discount_amount
            })

#    location_id = fields.Many2one('stock.location', string="Source Location")
    location_id = fields.Many2one('stock.location', string="Source Location", default=lambda self: self.env.user.allowed_default_location.id)
    discount_amount = fields.Float(string='Discount Amount', digits=dp.get_precision('Discount'))
    discount_glob = fields.Float(string='Discount(%)', digits=dp.get_precision('Discount'))
    total_discount = fields.Monetary(string='Total Discount', compute='_amount_all', store=True)
    is_this_direct_sale = fields.Boolean(string='Default Sale')

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(sale_order, self).onchange_partner_id()
        self.user_id = self.env.user.id
        if self.partner_id.user_id:
            self.user_id = self.partner_id.user_id.id
        return res

    @api.onchange('location_id')
    def get_available_qty(self):
        for order_line in self.order_line:
            order_line.lot_ids = False
            product_id = order_line.product_id.with_context({'location' : self.location_id.id, 'compute_child': False})
            order_line.available_qty = product_id.qty_available

    @api.onchange('discount_amount', 'order_line')
    def get_total_per_discount(self):
        if self.discount_amount != 0.0 and self.discount_amount >= 0.0:
            self.discount_glob = (self.discount_amount / (self.amount_untaxed + self.amount_tax)) * 100
        else:
            self.discount_glob = 0.0
  
    @api.onchange('discount_glob', 'order_line')
    def get_total_amount_discount(self):
        if self.discount_glob != 0.0 and self.discount_glob >= 0.0:
            self.discount_amount = ((self.amount_untaxed + self.amount_tax) * self.discount_glob) / 100
        else:
            self.discount_amount = 0.0

    @api.multi
    def action_cancel(self):
        if self.is_this_direct_sale and self.invoice_ids:
            raise ValidationError(_('You can\'t cancel sale order because invoice reference.please delete invoice first.'))
        self.write({'state': 'cancel'})

    @api.multi
    def unlink(self):
        if self.filtered(lambda l:l.is_this_direct_sale and l.invoice_ids):
            raise ValidationError(_('You can\'t delete sale order because invoice reference.please delete invoice first.'))
        return super(sale_order, self).unlink()

#     @api.multi
#     def write(self,vals):
#         print "\n write method is called ==================="
#         res = super(sale_order,self).write(vals)
#         if self.is_this_direct_sale and not self._context.get('from _discount'):
#             print "\n this is direct sale @@@@@@@@@@@@@@@@@@"
#             disc_share_amount = discount_amt = discount_glob = total_share = 0.0
#             print "\n each line in sale_order_line"
#             for each in self.order_line:
#     #             price = each.price_unit * (1 - (each.discount or 0.0) / 100.0)
#     #             taxes = each.tax_id.compute_all(price, each.order_id.currency_id, each.product_uom_qty, product=each.product_id, partner=each.order_id.partner_shipping_id)
#     #             if each.discount_share > 0.00:
#     #                 discount_share_amount = taxes['total_excluded'] * (1 - (each.discount_share or 0.0) / 100.0)
#     #                 disc_share_amount = (taxes['total_included'] * line.discount_share)/100
#     #                 each.discount_share_amount = disc_share_amount 
#                 each._compute_amount()
#                 total_share += each.discount_share_amount
# #                 self.discount_amount = total_share
# #             self.get_total_amount_discount()
#             print "\n total_share >>>>>>>>>>>>> ",total_share
#             print "\n self.discount_amount >>>> ",self.discount_amount
# #             self.discount_amount = total_share
#             new_discount = total_share
#             if new_discount > 0.00:
#                 print "\n new discount amount >>>>>>> ",new_discount
#                 self.write({'discount_amount':new_discount})
# #             self.discount_amount = new_discount
#             if total_share > self.discount_amount:
#                 each.discount_share_amount -= total_share-self.discount_amount
#             elif total_share < self.discount_amount:
#                 each.discount_share_amount += self.discount_amount-total_share
#         return res


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    discount_amount = fields.Float(string='Discount Amount', digits=dp.get_precision('Discount'), default=0.0)
    lot_ids = fields.Many2many('stock.production.lot', 'sale_stock_production_lot_rel', string="Lots")
    available_qty = fields.Float(string='Available Qty', store=True)
    discount_share = fields.Float(string='Discount Share(%)', digits=dp.get_precision('Discount'))
#     line_discount_share_amount = fields.Float(string="Share Amount", digits=dp.get_precision('Discount'), default=0.0,compute='_compute_amount',store=True)
    line_discount_share_amount = fields.Float(string="Share Amount", digits=dp.get_precision('Discount'))

#     def disc_share_amount(self):
#         print "\n disc_share_amount !!!!!!!!!!!!!!!!!!!!!!!"
#         disc_share_amount=0.0
#         for ln in self:
#             if ln.order_id.is_this_direct_sale:
#                 for line in self:
#                     price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#                     taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
#                     if line.discount_share > 0.00:
#                         discount_share_amount = taxes['total_excluded'] * (1 - (line.discount_share or 0.0) / 100.0)
#                         disc_share_amount = (taxes['total_included'] * line.discount_share)/100
#                     line.update({'discount_share_amount':disc_share_amount})
    
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'discount_share')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        total_disc_amount = 0.0
        disc = 0.0
        disc_amount = 0.0
        for line in self:
            disc_share_amount = discount_share_amount = 0.00
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            disc += line.discount_share
#             print "\n\n- -disc---", disc
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
#             if line.discount_share > 0.00:
#                 discount_share_amount = taxes['total_excluded'] * (1 - (line.discount_share or 0.0) / 100.0)
#                 disc_share_amount = (taxes['total_included'] * line.discount_share) / 100
#             print "\n\n --261---", disc, disc_share_amount
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
#                 'line_discount_share_amount': disc_share_amount
            })
#             if line.order_id.is_this_direct_sale:
#                 total_disc = 0.0
#                 for line in line.order_id.order_line:
#                     total_disc += line.discount_share_amount
#                 line.order_id.discount_amount = total_disc

    @api.constrains('product_id', 'product_uom_qty', 'lot_ids')
    def create_lot_from_lines(self):
        if self.order_id.is_this_direct_sale:
            split_lot_obj = self.env['split.lot.qty'].search([('sale_order_id', '=', self.id)])
            split_lot_qty_list = []
            if self.product_id.tracking != 'none':
                if self.product_id.tracking == 'lot':
                    remaining_qty = self.product_uom_qty
                    for each_lot in self.lot_ids:
                        if each_lot.remaining_qty == remaining_qty:
                            split_lot_qty_list.append((0, 0, {'lot_id': each_lot.id, 'available_qty': each_lot.remaining_qty,
                                                            'split_qty': each_lot.remaining_qty}))
                            remaining_qty = 0
                        elif each_lot.remaining_qty <= remaining_qty:
                            split_lot_qty_list.append((0, 0, {'lot_id': each_lot.id, 'available_qty': each_lot.remaining_qty,
                                                              'split_qty': each_lot.remaining_qty}))
                            remaining_qty = remaining_qty - each_lot.remaining_qty
                        elif each_lot.remaining_qty > remaining_qty:
                            split_lot_qty_list.append((0, 0, {'lot_id': each_lot.id, 'available_qty': each_lot.remaining_qty,
                                                              'split_qty': remaining_qty}))
                            remaining_qty = 0
                elif self.product_id.tracking == 'serial':
                    remaining_qty = self.product_uom_qty
                    for each_lot in self.lot_ids:
                        split_lot_qty_list.append((0, 0, {'lot_id': each_lot.id,
                                                          'available_qty': each_lot.remaining_qty, 'split_qty': 1}))
                        remaining_qty -= 1
                split_lot_obj.unlink()
                split_lot_obj.create({'sale_order_id': self.id,
                                      'order_qty': self.product_uom_qty,
                                      'split_lot_qty_line_ids': split_lot_qty_list})

    @api.multi
    def split_qty(self):
        if self.order_id.state != 'done':
            split_lot_qty = self.env['split.lot.qty'].search([('sale_order_id', '=', self.id)], limit=1)
            if split_lot_qty and self.product_id.tracking != 'none':
                return {'name': _('Split Lot Form'),
                        'view_type': 'form',
                        "view_mode": 'form',
                        'res_model': 'split.lot.qty',
                        'type': 'ir.actions.act_window',
                        'view_id': self.env.ref('direct_sale.split_lot_qty_form_id').id,
                        'target': 'new',
                        'res_id': split_lot_qty.id,
                        'context':{'from_invoice':True}
                        }

    @api.onchange('product_id')
    def get_available_qty(self):
        product_id = self.product_id.with_context({'location' : self.order_id.location_id.id, 'compute_child': False})
        self.available_qty = product_id.qty_available or 0.00

    @api.onchange('discount_amount')
    def calculate_discount(self):
        self.discount = (self.discount_amount / (self.product_uom_qty * self.price_unit or 1)) * 100

    @api.onchange('discount')
    def calculte_amount_from_discount(self):
        self.discount_amount = ((self.price_unit * self.product_uom_qty) * self.discount) / 100

#         self.order_id.disconut_amount = self.discount_amount*len(self.order_id.order_line)
#         for line in self.order_id.order_line:
#             price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#             taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
#             if line.discount_share > 0.00:
#                 discount_share_amount = taxes['total_excluded'] * (1 - (line.discount_share or 0.0) / 100.0)
#             line.price_subtotal = discount_share_amount if discount_share_amount else taxes['total_excluded']

    @api.constrains('lot_ids')
    def check_lots_ids(self):
        if self.order_id.is_this_direct_sale:
            if self.product_id.tracking != 'none' and not self.lot_ids:
                    raise ValidationError(_('For product %s serial number must be required.') % self.product_id.name)

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % 
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
                'name': self.name,
                'sequence': self.sequence,
                'origin': self.order_id.name,
                'account_id': account.id,
                'price_unit': self.price_unit,
                'quantity': qty,
                'discount': self.discount,
                'uom_id': self.product_uom.id,
                'product_id': self.product_id.id or False,
                'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
                'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
                'account_analytic_id': self.order_id.project_id.id,
                'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            }

        if self.order_id.is_this_direct_sale:
            product_id = self.product_id.with_context({'location' : self.order_id.location_id.id, 'compute_child': False})
            res.update({
                        'lot_ids' : [(6, 0, self.lot_ids.ids)],
                        'is_direct_invoice_line':True,
                        'available_qty':product_id.qty_available,
                        'forecast_qty':product_id.virtual_available,
                        'discount_amount': self.discount_amount,
            })
        return res


class split_lot_qty(models.Model):
    _name = 'split.lot.qty'

    sale_order_id = fields.Many2one('sale.order.line', string='Order Line Id', readonly=True)
    account_invoice_line_id = fields.Many2one('account.invoice.line', string='Invoice Line')
    order_qty = fields.Float(string='Order Qty')
    split_lot_qty_line_ids = fields.One2many('split.lot.qty.line', 'split_lot_id', string='Split Lot Ids')

    @api.multi
    def write(self, vals):
        res = super(split_lot_qty, self).write(vals)
        if not self.account_invoice_line_id.invoice_id.refund_without_invoice:
            qty = 0
            for each_line in self.split_lot_qty_line_ids:
                qty += each_line.split_qty
                if each_line.split_qty > each_line.available_qty:
                    raise Warning(
                        _('Please Check Split Quantity in %s,It is more than available Quantity') % (each_line.lot_id.name))

            if self.order_qty != qty:
                raise Warning(_('Please Check Sum Of Split Qty,It Is Not Same To Order Qty'))


class split_lot_qty_line(models.Model):
    _name = 'split.lot.qty.line'

    split_lot_id = fields.Many2one('split.lot.qty', string='Split Lot')
    lot_id = fields.Many2one('stock.production.lot', string='Lots Id')
    available_qty = fields.Float(string='Available Qty')
    split_qty = fields.Float(string='Split Qty')


class product_pricelist(models.Model):
    _inherit = 'product.pricelist'

    update_transaction_value = fields.Boolean(string="Update Transaction Value")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
