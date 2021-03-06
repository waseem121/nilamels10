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

from openerp import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT
from itertools import groupby
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')

to_19 = ('Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six',
         'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen',
         'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen')
tens = ('Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety')
denom = ('',
         'Thousand', 'Million', 'Billion', 'Trillion', 'Quadrillion',
         'Quintillion', 'Sextillion', 'Septillion', 'Octillion', 'Nonillion',
         'Decillion', 'Undecillion', 'Duodecillion', 'Tredecillion', 'Quattuordecillion',
         'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Novemdecillion', 'Vigintillion')


def _convert_nn(val):
    """convert a value < 100 to English.
    """
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return dcap + '-' + to_19[val % 10]
            return dcap


def _convert_nnn(val):
    """
        convert a value < 1000 to english, special cased because it is the level that kicks 
        off the < 100 special case.  The rest are more general.  This also allows you to
        get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = to_19[rem] + ' Hundred'
        if mod > 0:
            word += ' '
    if mod > 0:
        word += _convert_nn(mod)
    return word


def english_number(val):
    if val < 100:
        return _convert_nn(val)
    if val < 1000:
        return _convert_nnn(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn(l) + ' ' + denom[didx]
            if r > 0:
                ret = ret + ', ' + english_number(r)
            return ret


def amount_to_text(number, currency, currency_record=None):
    if currency_record:
        decimal_places = '%' + '.%sf' % currency_record.decimal_places
        number = decimal_places % number
    else:
        number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = english_number(int(list[0]))
    end_word = english_number(int(list[1]))
    cents_number = int(list[1])
    if units_name == 'KWD':
        cents_name = (cents_number > 1) and 'fills' or 'fills'
    else:
        cents_name = (cents_number > 1) and 'Cents' or 'Cent'

    return ' '.join(filter(None,
                           [start_word, units_name, (start_word or units_name) and (end_word or cents_name) and 'and',
                            end_word, cents_name]))


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    #  for remove lot ids by setting
    def get_lot_status(self):
        if len(self)==1:
            self.lot_setting = False
            if self.env['stock.config.settings'].search([], order='id desc', limit=1).group_stock_production_lot:
                self.lot_setting = True
        else:
            for invoice in self:
                invoice.lot_setting = False
                if self.env['stock.config.settings'].search([], order='id desc', limit=1).group_stock_production_lot:
                    invoice.lot_setting = True

    lot_setting = fields.Boolean(string="Lot Setting", compute="get_lot_status")
    invoice_line_ids_two = fields.One2many(comodel_name='account.invoice.line', inverse_name='invoice_id')

    @api.model
    def default_get(self, fields):
        result = super(AccountInvoice, self).default_get(fields)
        result['lot_setting'] = True if self.env['stock.config.settings'].search([], order='id desc',
                                                                                 limit=1).group_stock_production_lot else False
        return result
    # --------------------------------------------
    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        # print "self._context.get('is_discount_posting_setting',False): ",self._context.get('is_discount_posting_setting',False)
        if not self._context.get('is_discount_posting_setting', False):
            return res

        ### If discount posting is enabled
        invoice_line = self.env['account.invoice.line']
        for each_res in res:
            if not each_res.get('invl_id', False):
                continue
            invoice_line = invoice_line.browse(each_res['invl_id'])
            line_total_discount = invoice_line.discount_amount + invoice_line.discount_amount_global
            each_res['line_total_discount'] = line_total_discount

        #        res.extend(self._discount_move_lines(res))
        #         print "invoice_line_move_line_get res: ",res
        return res

    @api.model
    def _discount_move_lines(self):
        company_id = self.env.user.company_id.id
        ir_values = self.env['ir.values']
        discount_posting_account_id = ir_values.get_default('account.config.settings',
                                                            'discount_posting_account_id_setting',
                                                            company_id=company_id)
        if not discount_posting_account_id:
            raise UserError(_('Discount account not configured.'))

        company_currency = self.company_id.currency_id
        ctx = dict(self._context, lang=self.partner_id.lang)
        ctx['date'] = self._get_currency_rate_date()

        amount_currency = False
        if self.currency_id != company_currency:
            amount_currency = company_currency.with_context(ctx).compute(self.total_discount, self.currency_id)

        part = self.env['res.partner']._find_accounting_partner(self.partner_id)
        return {
            'date_maturity': self.date_invoice,
            'partner_id': part.id,
            'name': 'Discount',
            'debit': self.total_discount > 0 and self.total_discount,
            'credit': self.total_discount < 0 and -self.total_discount,
            'account_id': discount_posting_account_id,
            'amount_currency': self.total_discount > 0 and abs(amount_currency) or -abs(amount_currency),
            'currency_id': self.currency_id != company_currency and self.currency_id.id or False,
            'quantity': 1,
            'product_id': False,
            'product_uom_id': False,
            'invoice_id': self.id,
        }

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        if line.get('invl_id', False):
            res['debit'] = line['price'] > 0 and line['price'] + line.get('line_total_discount', 0.0)
            res['credit'] = line['price'] < 0 and -(line['price'] - line.get('line_total_discount', 0.0))
        #        res['line_total_discount'] = line.get('line_total_discount', 0.0)

        if line.get('invoice_id'):
            inv = self.browse(line['invoice_id'])
            jrl = inv.journal_id
            if jrl.group_invoice_lines and jrl.group_by_account:
                #             if jrl.group_invoice_lines and jrl.group_method == 'account':
                res['name'] = '/'
                res['product_id'] = False
        return res

    def group_lines(self, iml, line):
        """Merge account move lines (and hence analytic lines) if invoice line hashcodes are equals"""
        if self.journal_id.group_invoice_lines:
            line2 = {}
            for x, y, l in line:
                tmp = self.inv_line_characteristic_hashcode(l)
                if tmp in line2:
                    am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                    line2[tmp]['debit'] = (am > 0) and am or 0.0
                    line2[tmp]['credit'] = (am < 0) and -am or 0.0
                    line2[tmp]['amount_currency'] += l['amount_currency']
                    line2[tmp]['analytic_line_ids'] += l['analytic_line_ids']
                    qty = l.get('quantity')
                    if qty:
                        line2[tmp]['quantity'] = line2[tmp].get('quantity', 0.0) + qty
                else:
                    line2[tmp] = l
            line = []
            for key, val in line2.items():
                if val.get('credit') == 0.00 and val.get('debit') == 0.00:
                    continue
                line.append((0, 0, val))
        return line

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        if not self._context.get('is_discount_posting_setting', False) or self.total_discount == 0:
            return move_lines

        vals = self._discount_move_lines()
        move_lines.append((0, 0, vals))
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        return move_lines

    # @api.multi
    # def compute_invoice_totals(self, company_currency, invoice_move_lines):
    #     total = 0
    #     total_currency = 0
    #     for line in invoice_move_lines:
    #         total_price = line['price'] - line['line_total_discount']
    #         if self.currency_id != company_currency:
    #             currency = self.currency_id.with_context(date=self._get_currency_rate_date() or fields.Date.context_today(self))
    #             if not (line.get('currency_id') and line.get('amount_currency')):
    #                 line['currency_id'] = currency.id
    #                 line['amount_currency'] = currency.round(total_price)
    #                 line['price'] = currency.compute(line['price'], company_currency)
    #         else:
    #             line['currency_id'] = False
    #             line['amount_currency'] = False
    #             line['price'] = self.currency_id.round(line['price'])
    #         if self.type in ('out_invoice', 'in_refund'):
    #             total += total_price
    #             total_currency += line['amount_currency'] or total_price
    #             line['price'] = - line['price']
    #         else:
    #             total -= total_price
    #             total_currency -= line['amount_currency'] or total_price
    #     return total, total_currency, invoice_move_lines

    @api.one
    def get_amount_word(self):
        amount_text = amount_to_text(self.amount_total, currency=self.currency_id.name,
                                     currency_record=self.currency_id)
        return str(amount_text)

    @api.multi
    def action_invoice_draft(self):
        res = super(AccountInvoice, self).action_invoice_draft()
        if self.is_direct_invoice or self.refund_without_invoice or self.type in ['in_invoice', 'in_refund']:
            if self.move_name:
                self.number = self.move_name
            else:
                new_name = False
                journal = self.journal_id
                if journal.sequence_id:
                    sequence = journal.sequence_id
                    if self.refund_without_invoice or self.type in ['out_refund',
                                                                    'in_refund'] and journal.refund_sequence:
                        sequence = journal.refund_sequence_id
                    new_name = sequence.with_context(ir_sequence_date=self.date_invoice).next_by_id()
                else:
                    raise UserError(_('Please define a sequence on the journal.'))
                if new_name:
                    self.number = new_name
        return res

    @api.multi
    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', '=', self.invoice_picking_id.id)]
        return action

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if res.is_direct_invoice or res.refund_without_invoice or res.type in ['in_invoice', 'in_refund'] or self._context.get('sale_order_location',False):
            new_name = False
            journal = res.journal_id
            if journal.sequence_id:
                sequence = journal.sequence_id
                if res.refund_without_invoice or res.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                    sequence = journal.refund_sequence_id
                new_name = sequence.with_context(ir_sequence_date=res.date_invoice).next_by_id()
            else:
                raise UserError(_('Please define a sequence on the journal.'))
            if new_name:
                res.number = new_name
        # else:
        #     print "\n else ::::::::::::::::"
        #     sequence_number = self.env['ir.sequence'].next_by_code('account.invoice')
        #     res.name, res.number = sequence_number, sequence_number
        # res.number = sequence_number
        # TODO uncomment this
        if res.pricelist_id and res.pricelist_id.update_transaction_value:
            res.product_price_update()
        return res

    @api.multi
    def write(self, vals):
        print"account/write/self: ",self
        #  for remove lot ids by setting
        if self.lot_setting:
            if vals.get('invoice_line_ids'):
                # vals['invoice_line_ids_two'] = vals.get('invoice_line_ids')
                vals['invoice_line_ids_two'] = None
        else:
            if vals.get('invoice_line_ids_two'):
                # vals['invoice_line_ids'] = vals.get('invoice_line_ids_two')
                vals['invoice_line_ids'] = None
        # ------------------------------
        res = super(AccountInvoice, self).write(vals)
        if self.pricelist_id and self.pricelist_id.update_transaction_value and vals.get('invoice_line_ids'):
            self.product_price_update()
        return res

    @api.multi
    def action_invoice_open(self):
        # invoice_ids
        sale_ids = self.env['sale.order'].search([])
        for each in sale_ids:
            if each.invoice_ids:
                if self.id in (each.invoice_ids.ids):
                    for picking in each.picking_ids:
                        if picking.state not in ['done', 'cancel']:
                            raise Warning(_("The Delivery for this order is not validated yet, Please validate it first...!!!!"))

        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))

        if self.is_direct_invoice or self.refund_without_invoice:
            if not self.refund_without_invoice:
                product_lst = self.invoice_line_ids.mapped('product_id')
                for product_id in product_lst:
                    product_sum_qty = sum(
                        self.invoice_line_ids.filtered(lambda l: l.product_id.id == product_id.id).mapped('quantity'))
                    prod_qty_available = product_id.with_context(
#                        {'location': self.location_id.id, 'compute_child': False}).qty_available
                        {'location': self.location_id.id, 'compute_child': False}).virtual_available_inv
                    if prod_qty_available < product_sum_qty:
                        raise Warning(_('%s has not enough quantity into %s location.') % (
                            product_id.name, self.location_id.name))

                for invoice_line in self.invoice_line_ids.filtered(
                        lambda l: l.product_id.tracking != 'none' and not l.lot_ids):
                    if self.env['stock.config.settings'].search([], order='id desc',
                                                                limit=1).group_stock_production_lot:
                        raise Warning(
                            _('For product %s serial number must be required.') % invoice_line.product_id.name)
                        zero_lot = invoice_line.lot_ids.filtered(lambda l: l.remaining_qty <= 0)
                        if zero_lot:
                            raise Warning(_('Define Lot/Serial number %s for product %s is now not available.' %
                                            ([str(lot.name) for lot in zero_lot], invoice_line.product_id.name)))

                for invoice_line in self.invoice_line_ids.filtered(
                        lambda l: l.product_id.tracking == 'serial' and l.lot_ids):
                    if len(invoice_line.lot_ids) != invoice_line.quantity:
                        raise Warning(
                            _('Please check serial number and quantity on product %s, those must be in same number.') %
                            ("'" + invoice_line.product_id.name + "'"))

                for invoice_line in self.invoice_line_ids.filtered(lambda l: l.product_id):
                    available_qty = 0.00
                    if invoice_line.product_id.tracking != 'none':
                        for each_lot in invoice_line.lot_ids:
                            available_qty += invoice_line.product_id.with_context(
                                {'location': self.location_id.id, 'compute_child': False,
                                 'lot_id': each_lot.id}).qty_available
                    else:
                        available_qty = invoice_line.product_id.with_context(
                            {'location': self.location_id.id, 'compute_child': False}).qty_available
                    if invoice_line.quantity > available_qty:
                        raise Warning(_('Not enough quantity for %s .') % (invoice_line.product_id.name))
            else:
                for invoice_line in self.invoice_line_ids.filtered(
                        lambda l: l.product_id.tracking != 'none' and not l.lot_ids):
                    if self.env['stock.config.settings'].search([], order='id desc',
                                                                limit=1).group_stock_production_lot:
                        raise Warning(
                            _('For product %s serial number must be required.') % invoice_line.product_id.name)
                            
            if self.refund_invoice_id:
                self.do_return_picking()
            else:
                self.action_create_sales_order()    #creates only sales order no picking created here
                self.action_stock_transfer()
        to_open_invoices.action_date_assign()
        company_id = self.env.user.company_id.id
        ir_values = self.env['ir.values']
        is_discount_posting_setting = ir_values.get_default('account.config.settings', 'is_discount_posting_setting',
                                                            company_id=company_id) or False
        ctx = dict(self._context or {})
        ctx['is_discount_posting_setting'] = is_discount_posting_setting
        # sequence_code = self.env['ir.sequence'].next_by_code('account.invoice')
        # self.number = sequence_code
        # ctx['sequence_number'] = sequence_code
        # ctx['name'] = sequence_code
        # ctx['number'] = sequence_code
        to_open_invoices.with_context(ctx).action_move_create()
        # sequence number
        # self.number = sequence_code
        # self.name = sequence_code
        return to_open_invoices.invoice_validate()

    @api.one
    def product_price_update(self):
        for lines in self.invoice_line_ids.filtered(lambda l: l.product_id and l.price_unit > 0.00):
            pricelist_item = self.pricelist_id.item_ids.filtered(
                lambda l: l.compute_price == 'fixed' and l.applied_on == '0_product_variant')
            if pricelist_item:
                each_price = self.pricelist_id.item_ids.search([('product_id', '=', lines.product_id.id),
                                                                ('compute_price', '=', 'fixed'),
                                                                ('applied_on', '=', '0_product_variant'),
                                                                ('pricelist_id', '=', self.pricelist_id.id)])
                if not each_price:
                    self.pricelist_id.write({'item_ids': [(0, 0, {'applied_on': '0_product_variant',
                                                                  'product_id': lines.product_id.id,
                                                                  'fixed_price': lines.price_unit})]})

                order_lines = self.invoice_line_ids.filtered(
                    lambda l: l.product_id.id in [x.product_id.id for x in each_price] and l.price_unit > 0.00).sorted(
                    lambda l: l.price_unit)
                if order_lines:
                    for each_pricelist in each_price:
                        each_pricelist.fixed_price = order_lines[0].price_unit
            else:
                self.pricelist_id.write({'item_ids': [(0, 0, {'applied_on': '0_product_variant',
                                                              'product_id': lines.product_id.id,
                                                              'fixed_price': lines.price_unit
                                                              })]})

    @api.multi
    @api.returns('stock.warehouse', lambda value: value.id)
    def get_warehouse(self):
        """ Returns warehouse id of warehouse that contains location """
        return self.env['stock.warehouse'].search([
            ('view_location_id.parent_left', '<=', self.parent_left),
        ('view_location_id.parent_right', '>=', self.parent_left)], limit=1)

    @api.multi
    def action_create_sales_order(self):
        warehouse = self.location_id.get_warehouse()
        so_vals = {'partner_id':self.partner_id.id,
                'date_order':self.date_invoice,
                'user_id':self.user_id.id,
                'location_id':self.location_id.id,
                'pricelist_id':self.pricelist_id.id,
                'team_id':self.team_id and self.team_id.id or False,
                'warehouse_id':warehouse.id,
                'picking_policy':'direct',
                'invoice_status':'no',
                'state':'draft',
                
        }
        saleorder = self.env['sale.order'].create(so_vals)
        for line in self.invoice_line_ids:
            line_vals = {
                'product_id':line.product_id.id,
                'product_uom_qty':line.quantity,
                'product_uom':line.uom_id.id,
                'price_unit':line.price_unit,
                'name':line.name,
                'order_id':saleorder.id
            }
            so_line = self.env['sale.order.line'].create(line_vals)
            line.write({'sale_line_ids':[(6, 0, [so_line.id])]})
        
        context = self.env.context.copy()
        context.update({'no_picking':True})
        saleorder.with_context(context).action_confirm()    # this gets called of multi_uom_pricelist
        return True

    @api.multi
    def action_stock_transfer(self):
        if not self.invoice_picking_id:
            domain = [('warehouse_id.company_id', '=', self.env.user.company_id.id)]
            if self.refund_without_invoice:
                domain += ('code', '=', 'incoming'), ('default_location_dest_id', '=', self.location_id.id)
            else:
                domain += ('code', '=', 'outgoing'), ('default_location_src_id', '=', self.location_id.id)
            picking_type_id = self.env['stock.picking.type'].search(domain, limit=1)
            if not picking_type_id:
                raise Warning(_('No picking type available for %s location.') % self.location_id.name)
            pick = {
                'picking_type_id': picking_type_id.id,
                'partner_id': self.partner_id.id,
                'origin': self.number,
                'min_date': self.invoice_line_ids[0].sale_line_ids[0].order_id.date_order if self.invoice_line_ids[
                    0].sale_line_ids else self.date_invoice,
                'location_dest_id': self.partner_id.property_stock_customer.id,
                'location_id': self.location_id.id,
            }
            if self.refund_without_invoice:
                pick.update({'location_id': self.partner_id.property_stock_customer.id,
                             'location_dest_id': self.location_id.id
                             })
            picking = self.env['stock.picking'].create(pick)
            self.invoice_picking_id = picking.id
            self.picking_count = len(picking)
            moves = self.invoice_line_ids.filtered(
                lambda r: r.product_id and r.product_id.type in ['product', 'consu'])._create_stock_moves_transfer(
                picking)
            picking.action_assign()
            picking.force_assign()

            if self.refund_without_invoice:
                self.refund_without_invoice_lot_pack_op()
            else:
                self.assign_lot_pack_op()
            picking.action_confirm()

            wiz = self.env['stock.immediate.transfer'].create({'pick_id': picking.id})
            wiz.process()
            for each_moves in moves:
                total = sum(each_moves.quant_ids.mapped('inventory_value'))
                each_moves.account_invoice_line_id.cost_price = (total / each_moves.product_uom_qty or 1)

    @api.multi
    def refund_without_invoice_lot_pack_op(self):
        split_lot_obj = self.env['split.lot.qty']
        product_group_by = {}
        for lines in self.invoice_line_ids.filtered(lambda l: l.product_id):
            if lines.product_id.tracking != 'none':
                split_lot_obj = split_lot_obj.search([('account_invoice_line_id', '=', lines.id)])
                total_qty = 0
                for each_split_line in split_lot_obj.split_lot_qty_line_ids:
                    total_qty += each_split_line.split_qty
                    split_qty = sum(split_lot_obj.split_lot_qty_line_ids.mapped('split_qty'))
                    final_qty = lines.quantity if split_qty != lines.quantity else each_split_line.split_qty
                    if not lines.product_id.id in product_group_by:
                        product_group_by.update({lines.product_id.id: []})
                    product_group_by[lines.product_id.id].append({'lot_id': each_split_line.lot_id.id,
                                                                  'qty_todo': final_qty,
                                                                  'qty': final_qty})

        for pack_opt in self.invoice_picking_id.pack_operation_product_ids:
            if pack_opt.product_id.tracking != 'none':
                pack_opt.pack_lot_ids = False
                for product, lotvals in product_group_by.items():
                    if pack_opt.product_id.id == product:
                        lot_total_qty = []
                        key = lambda x: x['lot_id']
                        for k, v in groupby(sorted(lotvals, key=key), key=key):
                            qty = 0
                            qty_todo = 0
                            for each in v:
                                qty += float(each['qty'])
                                qty_todo += float(each['qty_todo'])
                            lot_total_qty.append((0, 0, {'lot_id': k, 'qty': qty, 'qty_todo': qty_todo}))
                        pack_opt.write({'pack_lot_ids': lot_total_qty})

    @api.multi
    def assign_lot_pack_op(self):
        split_lot_obj = self.env['split.lot.qty']
        product_group_by = {}
        for lines in self.invoice_line_ids.filtered(lambda l: l.product_id):
            zero_lot = lines.lot_ids.filtered(lambda l: l.remaining_qty <= 0)
            if zero_lot:
                raise Warning(_('Define Lot/Serial number %s for product %s is now not available.' %
                                ([str(lot.name) for lot in zero_lot], lines.product_id.name)))
            if lines.product_id.tracking != 'none':
                split_lot_obj = split_lot_obj.search([('account_invoice_line_id', '=', lines.id)])
                total_qty = 0
                for each_split_line in split_lot_obj.split_lot_qty_line_ids:
                    total_qty += each_split_line.split_qty
                    if not lines.product_id.id in product_group_by:
                        product_group_by.update({lines.product_id.id: []})
                    product_group_by[lines.product_id.id].append({'lot_id': each_split_line.lot_id.id,
                                                                  'qty_todo': each_split_line.split_qty,
                                                                  'qty': each_split_line.split_qty})
                if total_qty < lines.quantity:
                    raise Warning(_('Need more lot quantity in product %s. ') % (lines.product_id.name))
            else:
                stock_qty = lines.product_id.with_context(
                    {'location': lines.invoice_id.location_id.id, 'compute_child': False})
                if stock_qty.qty_available <= 0 or stock_qty.qty_available < lines.quantity:
                    raise Warning(_('Please check quantity in source location \n Quantity available: %s \nProduct: %s' %
                                    (stock_qty.qty_available, lines.product_id.name)))

        for pack_opt in self.invoice_picking_id.pack_operation_product_ids:
            if pack_opt.product_id.tracking != 'none':
                pack_opt.pack_lot_ids = False
                for product, lotvals in product_group_by.items():
                    if pack_opt.product_id.id == product:
                        lot_total_qty = []
                        key = lambda x: x['lot_id']
                        for k, v in groupby(sorted(lotvals, key=key), key=key):
                            qty = 0
                            qty_todo = 0
                            for each in v:
                                qty += float(each['qty'])
                                qty_todo += float(each['qty_todo'])
                            lot_total_qty.append((0, 0, {'lot_id': k, 'qty': qty, 'qty_todo': qty_todo}))
                        pack_opt.write({'pack_lot_ids': lot_total_qty})

    @api.multi
    def assign_refund_lot_pack_op(self):
        stock_pack_operation_id = self.env['stock.pack.operation'].search(
            [('picking_id', '=', self.invoice_picking_id.id)])
        for operation in stock_pack_operation_id:
            for each_lot in operation.pack_lot_ids:
                each_lot.action_add_quantity(each_lot.qty_todo)

    @api.multi
    def do_return_picking(self):
        picking_type_id = self.refund_invoice_id.invoice_picking_id.picking_type_id.return_picking_type_id
        if not picking_type_id:
            raise Warning(_('No return picking type available for %s location.') % self.location_id.name)
        if picking_type_id:
            if not picking_type_id.default_location_dest_id:
                raise Warning(_('Picking has not default Destination Location.'))
            if picking_type_id.default_location_dest_id.id != self.location_id.id:
                raise Warning(_('Picking default destination location should same with invoice location.'))

        picking_id = self.refund_invoice_id.invoice_picking_id
        if not picking_id:
            raise Warning(_('No picking available for invoice %s') % self.refund_invoice_id.number)

        stock_return_picking = self.env['stock.return.picking']
        lst = ['product_return_moves', 'original_location_id', 'parent_location_id', 'location_id']

        stock_return_default_value = stock_return_picking.with_context({'active_id': picking_id.id}).default_get(lst)
        stock_return_picking_id = stock_return_picking.with_context({'active_id': picking_id.id}).create(
            stock_return_default_value)
        return_picking_id = stock_return_picking_id.with_context({'active_id': picking_id.id})._create_returns()
        if return_picking_id:
            return_picking_id = self.env['stock.picking'].browse(return_picking_id[0])
            self.write({'invoice_picking_id': return_picking_id.id, 'picking_count': len(return_picking_id)})
            self.assign_refund_lot_pack_op()
            return_picking_id.action_done()

    #    @api.multi
    #    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice',
    #                 'type', 'total_discount')
    #    def _compute_amount(self):
    #        for invoice in self:
    #            amount_untaxed = amount_tax = total_discount = discount_amt = 0.0
    #            for line in invoice.invoice_line_ids:
    #                amount_untaxed += line.price_subtotal
    #                discount_amt += ((line.price_unit * line.quantity) * line.discount) / 100
    #            invoice.amount_untaxed = sum(line.price_subtotal for line in invoice.invoice_line_ids)
    #            invoice.amount_tax = sum(line.amount for line in invoice.tax_line_ids)
    #            invoice.update(
    #                {'item_discount': discount_amt,
    #                 'amount_total': (invoice.amount_untaxed + invoice.amount_tax + discount_amt)})
    #            invoice.update({'amount_total': invoice.amount_total - invoice.total_discount})
    #
    #            invoice.amount_total = invoice.amount_total
    #
    #            amount_total_company_signed = invoice.amount_total
    #            amount_untaxed_signed = invoice.amount_untaxed
    #            if invoice.currency_id and invoice.company_id and invoice.currency_id != invoice.company_id.currency_id:
    #                currency_id = invoice.currency_id.with_context(date=invoice.date_invoice)
    #                amount_total_company_signed = currency_id.compute(invoice.amount_total, invoice.company_id.currency_id)
    #                amount_untaxed_signed = currency_id.compute(invoice.amount_untaxed, invoice.company_id.currency_id)
    #            sign = invoice.type in ['in_refund', 'out_refund'] and -1 or 1
    #            invoice.item_discount = discount_amt
    #            invoice.amount_total_company_signed = amount_total_company_signed * sign
    #            invoice.amount_total_signed = invoice.amount_total * sign
    #            invoice.amount_untaxed_signed = amount_untaxed_signed * sign

    def _compute_amount_untaxed_wo_global_disc(self):
        total = 0.0
        for line in self.invoice_line_ids:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            total += line.quantity * price
        self.amount_untaxed_wo_global_disc = total

    @api.one
    @api.depends('invoice_line_ids')
    def _compute_max_invoice_line_id_w_price_subtotal(self):
        # print "inside _compute_max_invoice_line_id_w_price_subtotal"
        invoice_line_ids_w_price_subtotal = self.invoice_line_ids.filtered(lambda l: l.price_subtotal > 0.0)
        self.max_invoice_line_id_w_price_subtotal = invoice_line_ids_w_price_subtotal and max(
            invoice_line_ids_w_price_subtotal.ids) or 0

    discount_type = fields.Selection([('perc', 'Percentage'), ('amount', 'Fixed Amount')], string='Discount Type',
                                     default='perc')
    item_discount = fields.Monetary(string='Item Discount', store=True, readonly=True, compute='_compute_discount')
    discount_amount = fields.Float(string='Discount Amount', digits=dp.get_precision('Discount'))
    discount_glob = fields.Float(string='Discount(%)', digits=dp.get_precision('Discount'))
    total_discount_share = fields.Monetary(string='Total Discount Share', compute='_compute_discount', store=True)
    total_discount = fields.Monetary(string='Total Discount', compute='_compute_discount')
    amount_untaxed_wo_global_disc = fields.Monetary(string='Untaxed Amount (w/o Global Discount)', readonly=True,
                                                    compute='_compute_amount_untaxed_wo_global_disc')
    max_invoice_line_id_w_price_subtotal = fields.Integer('Max Line ID',
                                                          compute='_compute_max_invoice_line_id_w_price_subtotal',
                                                          store=True, help='Technical Field')
    is_direct_invoice = fields.Boolean(string='IS Direct Invoice')
    location_id = fields.Many2one('stock.location', string="Location", copy=False)
    picking_count = fields.Integer(string="Picking Count", copy=False)
    invoice_picking_id = fields.Many2one('stock.picking', string="Picking", copy=False)
    from_direct_sale = fields.Boolean(string='Direct Sale')
    number = fields.Char(store=True, readonly=True, copy=False)
    refund_without_invoice = fields.Boolean(string='Refund Without Invoice')
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange',
                              default=lambda self: self.env.user, readonly=False)
    date_invoice = fields.Date(string='Invoice Date',
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="Keep empty to use the current date", copy=False, default=fields.Datetime.now)

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        self.pricelist_id = False
        self.user_id = self.env.user.id
        if self.partner_id.user_id:
            self.user_id = self.partner_id.user_id.id
        if self.partner_id:
            self.pricelist_id = self.partner_id.property_product_pricelist
        return res

    @api.onchange('location_id')
    def get_available_qty(self):
        location_id = self.location_id.id
        if self.refund_without_invoice:
            location_id = self.partner_id.property_stock_customer.id
        for invoice_line in self.invoice_line_ids:
            invoice_line.lot_ids = False
            product_available_qty = invoice_line.product_id.with_context(
                {'location': location_id, 'compute_child': False})
            if product_available_qty:
                invoice_line.available_qty = product_available_qty.qty_available
                invoice_line.forecast_qty = product_available_qty.virtual_available_inv
            analytic_default_id = self.env['account.analytic.default'].account_get(
                product_id=invoice_line.product_id.id, account_id=invoice_line.account_id.id,
                location_id=self.location_id.id, journal_id=self.journal_id.id, company_id=self.env.user.id)
            if analytic_default_id:
                invoice_line.account_analytic_id = analytic_default_id.analytic_id.id

    @api.onchange('discount_type', 'discount_amount', 'discount_glob')
    def _onchange_discount_type(self):
        prec_discount = self.env['decimal.precision'].precision_get('Discount')
        if self.discount_type == 'perc':
            self.discount_amount = float_round(self.amount_untaxed_wo_global_disc * self.discount_glob / 100.0,
                                               precision_digits=prec_discount)
        else:
            self.discount_glob = self.amount_untaxed_wo_global_disc and float_round(
                (self.discount_amount / self.amount_untaxed_wo_global_disc) * 100.0,
                precision_digits=prec_discount) or 0.0

    @api.one
    @api.depends('discount_amount', 'invoice_line_ids.discount_amount')
    def _compute_discount(self):
        #        self.total_discount_share = ((self.amount_untaxed + self.amount_tax) * self.discount_glob) / 100
        self.item_discount = sum(self.invoice_line_ids.mapped('discount_amount'))
        self.total_discount = self.discount_amount + self.item_discount

    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        residual = 0.0
        residual_company_signed = 0.0
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self.sudo().move_id.line_ids:
            if line.account_id.internal_type in ('receivable', 'payable'):
                residual_company_signed += line.amount_residual
                if line.currency_id == self.currency_id:
                    residual += line.amount_residual_currency if line.currency_id else line.amount_residual
                else:
                    from_currency = (line.currency_id and line.currency_id.with_context(
                        date=line.date)) or line.company_id.currency_id.with_context(date=line.date)
                    residual += from_currency.compute(line.amount_residual, self.currency_id)
        self.residual_company_signed = abs(residual_company_signed) * sign
        self.residual_signed = abs(residual) * sign
        self.residual = abs(residual) - self.total_discount_share
        digits_rounding_precision = self.currency_id.rounding
        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False

    @api.model
    def _refund_cleanup_lines(self, lines):
        """ Convert records to dict of values suitable for one2many line creation

            :param recordset lines: records to convert
            :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
        """
        result = []
        for line in lines:
            values = {}
            for name, field in line._fields.iteritems():
                if name in MAGIC_COLUMNS:
                    continue
                elif field.type == 'many2one':
                    values[name] = line[name].id
                elif field.type not in ['many2many', 'one2many']:
                    values[name] = line[name]
                elif name == 'invoice_line_tax_ids':
                    values[name] = [(6, 0, line[name].ids)]
                elif name == 'lot_ids':
                    values[name] = [(6, 0, line[name].ids)]
            values.update({'refund_invoice_line_id': line.id})
            result.append((0, 0, values))
        return result

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(invoice, date_invoice, date, description, journal_id)
        res.update({'location_id': invoice.location_id.id, 'is_direct_invoice': invoice.is_direct_invoice,
                    'discount_glob': invoice.discount_glob, 'discount_amount': invoice.discount_amount
                    })
        return res


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    def _calc_line_adjustment(self):
        global_discount_perc = self.invoice_id.discount_glob
        prec_discount = self.env['decimal.precision'].precision_get('Discount')
        total_line_discount = 0.0
        for line in self.invoice_id.invoice_line_ids:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            each_discount_amount = price * (global_discount_perc or 0.0) / 100.0
            each_discount_amount = float_round(each_discount_amount * line.quantity, precision_digits=prec_discount)
            total_line_discount += each_discount_amount

        return self.invoice_id.discount_amount - total_line_discount

    @api.one
    @api.depends('invoice_id.discount_amount', 'invoice_id.discount_glob')
    def _compute_discount_amount_global(self):
        if not len(self.invoice_id.invoice_line_ids):
            return

        if not (self.invoice_id.discount_amount and self.invoice_id.discount_glob):
            return
        if not self.id:
            return

        #        if sum(self.invoice_id.invoice_line_ids.mapped('price_subtotal')) == 0.0:
        #            return

        prec_discount = self.env['decimal.precision'].precision_get('Discount')
        each_discount_perc = self.invoice_id.discount_glob
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        each_discount_amount = price * ((each_discount_perc or 0.0) / 100.0)
        each_discount_amount = float_round(each_discount_amount * self.quantity, precision_digits=prec_discount)

        if self.price_subtotal > 0.0:
            max_invoice_line_id_w_price_subtotal = self.invoice_id.max_invoice_line_id_w_price_subtotal
        else:
            self.env.cr.execute(
                "SELECT max_invoice_line_id_w_price_subtotal FROM account_invoice i, account_invoice_line l WHERE l.invoice_id=i.id AND l.id=%s",
                (self.id,))
            res = self.env.cr.fetchone()
            max_invoice_line_id_w_price_subtotal = res and res[0] or 0
#        print "max_invoice_line_id_w_price_subtotal: ",max_invoice_line_id_w_price_subtotal
        adjustment = 0.0
        if self.id == max_invoice_line_id_w_price_subtotal:
            adjustment = self._calc_line_adjustment()
            # print "_compute_discount_amount_global adjustment: ",adjustment
            if adjustment:
                each_discount_amount += adjustment
                each_discount_perc = (price * self.quantity) > 0 and float_round(
                    (each_discount_amount / (price * self.quantity)) * 100, precision_digits=prec_discount) or 0.0

        self.discount_amount_global = each_discount_amount
        self.discount_global = each_discount_perc

    discount_amount = fields.Float(string='Disc.', digits=dp.get_precision('Discount'))
    discount = fields.Float(string='Disc.(%)', digits=dp.get_precision('Discount'))
    discount_amount_global = fields.Float(string='Global Disc.', compute=_compute_discount_amount_global,
                                          digits=dp.get_precision('Discount'))
    discount_global = fields.Float(string='Global Disc.(%)', compute=_compute_discount_amount_global,
                                   digits=dp.get_precision('Discount'))
    is_direct_invoice_line = fields.Boolean(string='IS Direct Invoice Line')
    lot_ids = fields.Many2many('stock.production.lot', 'invoice_stock_production_lot_rel', string="Lots")
    available_qty = fields.Float(string="Available Qty")
    forecast_qty = fields.Float(string="Forecast Qty")
    cost_price = fields.Float(string="Cost Price", digits=dp.get_precision('Discount'))
    refund_invoice_line_id = fields.Many2one('account.invoice.line', string="Refund Invoice line")
    #     cost_price_copy = fields.Float(string="Copy Cost Price", compute='_check_cost_amount', store=True, digits=dp.get_precision('Discount'))

    #     @api.multi
    #     @api.depends('product_id')
    #     def _check_cost_amount(self):
    #         for line in self.filtered(lambda l: l.product_id.id):
    #             picking_id = line.invoice_id.invoice_picking_id
    #             if picking_id:
    #                 move_line = picking_id.move_lines.filtered(lambda l: l.product_id.id == line.product_id.id and l.product_uom_qty == line.quantity)
    #                 for each_moves in move_line:
    #                     total = sum(each_moves.quant_ids.mapped('inventory_value'))
    #                     line.cost_price_copy = (total / each_moves.product_uom_qty or 1)
    #                     if line.cost_price_copy != line.cost_price:
    #                         line.write({'cost_price':line.cost_price_copy})
    #                     if not each_moves.account_invoice_line_id:
    #                         each_moves.write({'account_invoice_line_id':line.id})

    def _create_stock_moves_transfer(self, picking):
        move_obj = self.env['stock.move']
        for each_line in self:
            template = {
                'name': each_line.name or '',
                'product_id': each_line.product_id.id,
                'product_uom': each_line.uom_id.id,
                'location_id': picking.location_id.id,
                'location_dest_id': each_line.invoice_id.partner_id.property_stock_customer.id,
                'picking_id': picking.id,
                'product_udef _compute_discount_amount_global(self):uom_qty': each_line.quantity,
                'company_id': each_line.invoice_id.company_id.id,
                'price_unit': each_line.price_unit,
                'picking_type_id': picking.picking_type_id.id,
                'lot_ids': [(6, 0, [x.id for x in each_line.lot_ids])],
                'warehouse_id': picking.picking_type_id.warehouse_id.id,
                'account_invoice_line_id': each_line.id,
		'product_uom_qty': each_line.quantity,
            }
            move_obj |= move_obj.create(template)
        return move_obj

    @api.constrains('product_id', 'quantity', 'lot_ids')
    def create_lot_from_lines(self):
        if self.invoice_id.from_direct_sale or self.invoice_id.is_direct_invoice or self.invoice_id.refund_without_invoice:
            split_lot_obj = self.env['split.lot.qty']
            split_lot_obj_invoice = self.env['split.lot.qty']
            split_lot_qty_list = []
            if self.invoice_id.from_direct_sale and self.sale_line_ids:
                split_lot_obj = split_lot_obj.search([('sale_order_id', '=', self.sale_line_ids[0].id)]).unlink()
            split_lot_obj = split_lot_obj_invoice.search([('account_invoice_line_id', '=', self.id)])
            if self.invoice_id.refund_invoice_id:
                split_lot_obj = split_lot_obj_invoice.search([('account_invoice_line_id', 'in', [x.id for x in
                                                                                                 self.invoice_id.refund_invoice_id.invoice_line_ids])])

            if self.product_id and self.product_id.tracking != 'none':
                if self.product_id.tracking == 'lot':
                    remaining_qty = self.quantity
                    location_id = self.invoice_id.location_id.id
                    if self.invoice_id.refund_without_invoice:
                        location_id = self.invoice_id.partner_id.property_stock_customer.id
                    for each_lot in self.lot_ids:
                        available_qty = sum(
                            each_lot.quant_ids.filtered(lambda l: l.location_id.id == location_id).mapped('qty'))
                        if available_qty == remaining_qty:
                            split_lot_qty_list.append((0, 0, {'lot_id': each_lot.id, 'available_qty': available_qty,
                                                              'split_qty': available_qty}))
                            remaining_qty = 0
                        elif available_qty <= remaining_qty:
                            split_lot_qty_list.append((0, 0, {'lot_id': each_lot.id, 'available_qty': available_qty,
                                                              'split_qty': available_qty}))
                            remaining_qty = remaining_qty - available_qty
                        elif available_qty > remaining_qty:
                            split_lot_qty_list.append((0, 0, {'lot_id': each_lot.id, 'available_qty': available_qty,
                                                              'split_qty': remaining_qty}))
                            remaining_qty = 0
                elif self.product_id.tracking == 'serial':
                    remaining_qty = self.quantity
                    for each_lot in self.lot_ids:
                        split_lot_qty_list.append((0, 0, {'lot_id': each_lot.id,
                                                          'available_qty': each_lot.remaining_qty, 'split_qty': 1}))
                        remaining_qty -= 1
                if not self.invoice_id.refund_invoice_id:
                    split_lot_obj.unlink()
                    split_lot_obj.create({'account_invoice_line_id': self.id,
                                          'order_qty': self.quantity,
                                          'split_lot_qty_line_ids': split_lot_qty_list})

    @api.constrains('forecast_qty', 'quantity')
    def check_forecast_qty(self):
        print"self.is_direct_invoice_line: ",self.is_direct_invoice_line
        if not self.invoice_id.refund_without_invoice:
#            if self.quantity > self.forecast_qty:
#                raise ValidationError(_('"%s" Quantity greater than forecast quantity.') % self.product_id.name)
            if self.is_direct_invoice_line and self.quantity > self.forecast_qty:
                raise ValidationError(_('Quantity greater than forecast quantity.'))

    @api.multi
    def split_qty(self):
        split_qty_obj = self.env['split.lot.qty']
        if self.invoice_id.state == 'draft' and self.product_id.tracking != 'none':
            invoice_line_id = self.refund_invoice_line_id.id if self.invoice_id.refund_invoice_id else self.id
            split_qty_obj = split_qty_obj.search([('account_invoice_line_id', '=', invoice_line_id)], order='id desc',
                                                 limit=1)
            if split_qty_obj:
                return {'name': _('Split Lot Form'),
                        'view_type': 'form',
                        "view_mode": 'form',
                        'res_model': 'split.lot.qty',
                        'type': 'ir.actions.act_window',
                        'view_id': self.env.ref('direct_sale.split_lot_qty_form_id').id,
                        'target': 'new',
                        'res_id': split_qty_obj.id,
                        'context': {'from_invoice': True}
                        }

    @api.onchange('discount_amount')
    def get_item_discount(self):
        self.discount = (self.discount_amount / (self.quantity * self.price_unit or 1)) * 100

    @api.onchange('discount')
    def get_amount_from_per_discount(self):
        self.discount_amount = ((self.price_unit * self.quantity) * self.discount) / 100

    @api.one
    @api.depends('price_unit', 'discount_amount', 'discount_amount_global', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        """
        Compute the amounts of the Direct Sale line.
        """
        # if self.invoice_id.discount_amount and self.discount_amount_global == 0.0
        prec_discount = self.env['decimal.precision'].precision_get('Discount')
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = float_round(self.price_unit - ((self.discount_amount + self.discount_amount_global) / self.quantity),
                            precision_digits=prec_discount)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else (
                                                                                                    self.quantity * self.price_unit) - (
                                                                                                    self.discount_amount + self.discount_amount_global)
        if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(
                date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed,
                                                                        self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign

    #    @api.depends('price_unit', 'discount_amount', 'discount_amount_global', 'invoice_line_tax_ids', 'quantity',
    #                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
    #                 'invoice_id.date_invoice','invoice_id.date')
    #    def _compute_price(self):
    #        """
    #        Compute the amounts of the Direct Sale line.
    # """
    #        prec_discount = self.env['decimal.precision'].precision_get('Discount')
    #        for line in self:
    #            currency = line.invoice_id and line.invoice_id.currency_id or None
    #            price = float_round(line.price_unit - ((line.discount_amount + line.discount_amount_global) / line.quantity), precision_digits=prec_discount)
    #            taxes = False
    #            if line.invoice_line_tax_ids:
    #                taxes = line.invoice_line_tax_ids.compute_all(price, currency, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
    #            line.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else (line.quantity * line.price_unit) - (line.discount_amount + line.discount_amount_global)
    #            if line.invoice_id.currency_id and line.invoice_id.company_id and line.invoice_id.currency_id != line.invoice_id.company_id.currency_id:
    #                price_subtotal_signed = line.invoice_id.currency_id.with_context(date=line.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed, line.invoice_id.company_id.currency_id)
    #            sign = line.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
    #            line.price_subtotal_signed = price_subtotal_signed * sign

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(account_invoice_line, self)._onchange_product_id()
        location_id = self.invoice_id.location_id.id
        if self.invoice_id.refund_without_invoice:
            location_id = self.invoice_id.partner_id.property_stock_customer.id
        product_qty_available = self.product_id.with_context({'location': location_id, 'compute_child': False})
        if product_qty_available:
            self.update({'available_qty': product_qty_available.qty_available,
#                         'forecast_qty': product_qty_available.virtual_available})
                         'forecast_qty': product_qty_available.virtual_available_inv})  # forecasted qty to shows based on invoice lines

        if self.product_id and self.invoice_id.pricelist_id:
            inv_date = self.invoice_id.date_invoice or date.today().strftime(DT)
            product_id = self.product_id.with_context(
                lang=self.invoice_id.partner_id.lang,
                partner=self.invoice_id.partner_id.id,
                quantity=self.quantity,
                date=inv_date,
                pricelist=self.invoice_id.pricelist_id.id,
                uom=self.uom_id.id
            )

            self.price_unit = self.env['account.tax']._fix_tax_included_price(
                product_id.price, product_id.taxes_id, self.invoice_line_tax_ids)

        analytic_default_id = self.env['account.analytic.default'].account_get(product_id=self.product_id.id,
                                                                               account_id=self.account_id.id,
                                                                               location_id=self.invoice_id.location_id.id,
                                                                               journal_id=self.invoice_id.journal_id.id,
                                                                               company_id=self.env.user.id)
        if analytic_default_id:
            self.update({'account_analytic_id': analytic_default_id.analytic_id.id})
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    salesman_id = fields.Many2one('res.partner', string='Salesman',domain=[('is_salesman', '=', True)])
    collector_id = fields.Many2one('res.partner', string='Collector',domain=[('is_collector', '=', True)])
    ref_required = fields.Boolean(related='journal_id.ref_required', string="Ref required", store=True, help='its hidden field to make Ref mandatory/no mandatory based on journal selection')
    
    # inherited to, add Ref unique validations
    @api.model
    def create(self, vals):
        ref = vals.get('ref', False)
        journal_id = vals.get('journal_id', False)
        if journal_id and ref:
            ref_unique = self.env['account.journal'].browse(journal_id).ref_unique or False
            if ref_unique:
                ref=str(ref).lower()
                self.env.cr.execute("SELECT id FROM account_move WHERE LOWER(ref)=%s",(ref,))
                query_res = self.env.cr.dictfetchall()
                if len(query_res):
                    raise UserError(_("Ref should be unique, its already used."))

        return super(AccountMove, self).create(vals)

    @api.multi
    def post(self):

        invoice = self._context.get('invoice', False)
        print "context---------in--post--------",self._context
        self._post_validate()
        for move in self:
            move.line_ids.create_analytic_lines()
            if move.name == '/':
                new_name = False
                journal = move.journal_id
                if invoice:
                    if invoice.is_direct_invoice or invoice.refund_without_invoice or invoice.type in ['in_invoice',
                                                                                                       'in_refund']:
                        new_name = invoice.number
                    if not invoice.is_direct_invoice and invoice.refund_without_invoice and invoice.move_name and invoice.move_name != '/':
                        new_name = invoice.move_name
                else:
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                        sequence = journal.sequence_id
                        if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                            if not journal.refund_sequence_id:
                                raise UserError(_('Please define a sequence for the refunds'))
                            sequence = journal.refund_sequence_id
                        print "\n post called for sequence :::::::::::::::::::"
                        new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(_('Please define a sequence on the journal.'))
                if invoice:
                    if invoice.number:
                        move.name = invoice.number
                if new_name:
                    move.name = new_name
        return self.write({'state': 'posted'})


class account_journal(models.Model):
    _inherit = 'account.journal'

    group_by_account = fields.Boolean(string="Account Group", default=True)
    salesman_required = fields.Boolean(string="Salesman Required")
    collector_required = fields.Boolean(string="Collector Required",help='Cash collector required')
    ref_required = fields.Boolean(string="Ref Required",help='wether Ref is mandatory in Voucher.')
    ref_unique = fields.Boolean(string="Ref Unique",help='wether Ref should be unique in Voucher.')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
