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
from odoo.tools.float_utils import float_compare

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

#    customer_dept_id = fields.Many2one('customer.department', string="Customer Department")
#    customer_div_id = fields.Many2one('customer.division', string="Customer Division")
    
    @api.one
    @api.depends('invoice_line_ids.price_subtotal','discount_glob','item_discount','total_discount','tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice',
                 'type')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(round_curr(line.amount) for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        self.amount_total = self.amount_total - self.total_discount
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign    
        self.total_cost = sum(line.cost_price for line in self.invoice_line_ids)
            

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
        if self.env.user.allowed_default_location:
            result['location_id'] = self.env.user.allowed_default_location.id
        result['lot_setting'] = True if self.env['stock.config.settings'].search([], order='id desc',
                                                                                 limit=1).group_stock_production_lot else False
        return result
    # --------------------------------------------
    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
#        print "self._context.get('is_discount_posting_setting',False): ",self._context.get('is_discount_posting_setting',False)
#        if not self._context.get('is_discount_posting_setting', False):
#            return res

        ### If discount posting is enabled
        invoice_line = self.env['account.invoice.line']
        for each_res in res:
            if not each_res.get('invl_id', False):
                continue
            invoice_line = invoice_line.browse(each_res['invl_id'])
            
            shipping_name = self.partner_shipping_id and self.partner_shipping_id.name or False
            if not shipping_name:
                street = self.partner_shipping_id and self.partner_shipping_id.street or False
                if street:
                    shipping_name = street
            if not shipping_name:
                street = self.partner_id.name or self.partner_id.street or False
                if street:
                    shipping_name = street
            name = shipping_name
            if not name:
                name = '/'
            if self.type == 'in_invoice':
                name = self.origin or '/'
                if name and self.partner_id and self.partner_id.ref:
                    name = str(name)+' '+str(self.partner_id.ref)
            
                
            each_res['name'] = name
#            line_total_discount = invoice_line.discount_amount + invoice_line.discount_amount_global
            line_total_discount = invoice_line.discount_share
            each_res['line_total_discount'] = line_total_discount
            each_res['price_unit'] = each_res.get('price_unit')-line_total_discount
            each_res['price'] = each_res.get('price')-line_total_discount
            

        #        res.extend(self._discount_move_lines(res))
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
#        if line.get('invl_id', False):
#            res['debit'] = line['price'] > 0 and line['price'] + line.get('line_total_discount', 0.0)
#            res['credit'] = line['price'] < 0 and -(line['price'] - line.get('line_total_discount', 0.0))
#            if res.get('debit')>0:
#                res['debit'] = res['debit']-line.get('line_total_discount')
#            if res.get('credit')>0:
#                res['credit'] = res['credit']-line.get('line_total_discount')                
        #        res['line_total_discount'] = line.get('line_total_discount', 0.0)

        if line.get('invoice_id'):
            inv = self.browse(line['invoice_id'])
            jrl = inv.journal_id
            if jrl.group_invoice_lines and jrl.group_by_account:
                #             if jrl.group_invoice_lines and jrl.group_method == 'account':
#                res['name'] = '/'
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
    
    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        total = 0
        total_currency = 0
        for line in invoice_move_lines:
            if self.currency_id != company_currency:
                currency = self.currency_id.with_context(date=self._get_currency_rate_date() or fields.Date.context_today(self))
                if not (line.get('currency_id') and line.get('amount_currency')):
                    line['currency_id'] = currency.id
                    line['amount_currency'] = currency.round(line['price'])
                    if self.exchange_rate:
                        line['price'] = currency.compute_custom(line['price'], company_currency, self.exchange_rate)
                    else:
                        line['price'] = currency.compute(line['price'], company_currency)
            else:
                line['currency_id'] = False
                line['amount_currency'] = False
                line['price'] = self.currency_id.round(line['price'])
            if self.type in ('out_invoice', 'in_refund'):
                total += line['price']
                total_currency += line['amount_currency'] or line['price']
                line['price'] = - line['price']
            else:
                total -= line['price']
                total_currency -= line['amount_currency'] or line['price']
        return total, total_currency, invoice_move_lines    

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

#    @api.multi
#    def action_view_picking(self):
#        action = self.env.ref('stock.action_picking_tree_all').read()[0]
#        action['domain'] = [('id', '=', self.invoice_picking_id.id)]
#        return action
#    
    @api.multi
    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        origin = self.number
        pickings = self.env['stock.picking'].search([('origin','=',origin)])
        picking_ids = []
        if len(pickings):
            for picking in pickings:
                picking_ids.append(picking.id)
        else:
            picking_ids = [self.invoice_picking_id.id]
        
        action['domain'] = [('id', 'in', tuple(picking_ids))]
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
        if self.number:
            pickings = self.env['stock.picking'].search([('origin','=',self.number)])
            if len(pickings):
                for picking in pickings:
                    if picking.state not in ['done', 'cancel']:
                        raise Warning(_("The Delivery for this order is not validated yet, Please validate it first...!!!!"))
                    
#        sale_ids = self.env['sale.order'].search([])
#        for each in sale_ids:
#            if each.invoice_ids:
#                if self.id in (each.invoice_ids.ids):
#                    for picking in each.picking_ids:
#                        if picking.state not in ['done', 'cancel']:
#                            raise Warning(_("The Delivery for this order is not validated yet, Please validate it first...!!!!"))

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
                        {'location': self.location_id.id, 'compute_child': False}).qty_available
#                        {'location': self.location_id.id, 'compute_child': False}).virtual_available_inv
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
                self.check_date()
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
    
    # updates the date in picking
    def check_date(self):
        date_invoice = self.date_invoice
#        if self.env.user.transaction_date:
#            date_invoice = self.env.user.transaction_date
#           
        Picking = self.env['stock.picking']
        if self.invoice_picking_id:
            pickings = self.invoice_picking_id
            for picking in pickings:
                picking.write({'date':date_invoice, 'min_date':date_invoice,
                    'date_done':date_invoice,'max_date':date_invoice})
                for move in picking.move_lines:
                    move.write({'date_expected':date_invoice,'date':date_invoice})
                backorder_pickings = Picking.search([('backorder_id','=',picking.id)])
                print"backorder_pickings: ",backorder_pickings
                if len(backorder_pickings):
                    for backorder_picking in backorder_pickings:
                        for move in backorder_picking.move_lines:
                            move.write({'date_expected':date_invoice,'date':date_invoice})
                        backorder_picking.write({'date':date_invoice, 'min_date':date_invoice,
                            'date_done':date_invoice,'max_date':date_invoice})


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
            origin = self.number or False
            if not origin:
                origin = self.number            
            pick = {
                'picking_type_id': picking_type_id.id,
                'partner_id': self.partner_id.id,
                'origin': origin,
#                'min_date': self.invoice_line_ids[0].sale_line_ids[0].order_id.date_order if self.invoice_line_ids[
#                    0].sale_line_ids else self.date_invoice,
                'min_date': self.date_invoice,
                'location_dest_id': self.partner_id.property_stock_customer.id,
                'location_id': self.location_id.id,
                'invoice_type':self.invoice_type,
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

    
        
    @api.model
    def _default_date_invoice(self):
        if self.env.user.transaction_date:
            return self.env.user.transaction_date
        else:
            return fields.Datetime.now()
        
    def _compute_amount_untaxed_wo_global_disc(self):
        total = 0.0
        for line in self.invoice_line_ids:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            total += line.quantity * price
        self.amount_untaxed_wo_global_disc = total

    @api.one
    @api.depends('invoice_line_ids','invoice_line_ids_two')
    def _compute_max_invoice_line_id_w_price_subtotal(self):
        # print "inside _compute_max_invoice_line_id_w_price_subtotal"
        invoice_line_ids_w_price_subtotal = self.invoice_line_ids.filtered(lambda l: l.price_subtotal > 0.0)
        self.max_invoice_line_id_w_price_subtotal = invoice_line_ids_w_price_subtotal and max(
            invoice_line_ids_w_price_subtotal.ids) or 0
            
    @api.model
    @api.depends('currency_id')
    def _default_has_default_currency(self):
        has_default_currency=False
        if self.currency_id:
            if self.currency_id.id == self.company_id.currency_id.id:
                has_default_currency=True
        self.has_default_currency = has_default_currency
            
    invoice_type = fields.Selection([('normal', 'Normal Invoice'), ('sample', 'Sample Invoice')], string='Invoice Type',
                                     default='normal')
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', help="Delivery address for current invoice.")
    discount_type = fields.Selection([('perc', 'Percentage'), ('amount', 'Fixed Amount')], string='Discount Type',
                                     default='perc')
    item_discount = fields.Monetary(string='Item Discount', store=True, readonly=True, compute='_compute_discount')
    discount_amount = fields.Float(string='Discount Amount', digits=dp.get_precision('Discount'))
    discount_glob = fields.Float(string='Discount(%)', digits=dp.get_precision('Discount'))
#    total_discount_share = fields.Monetary(string='Total Discount Share', compute='_compute_discount', store=True)
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
    division_id = fields.Many2one('customer.division', string="Customer Division")
    department_id = fields.Many2one('customer.department', string="Customer Department")
    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange',
                              default=lambda self: self.env.user, readonly=False, required=True)
    exchange_rate = fields.Float(string='Exchange Rate', digits=dp.get_precision('Discount'), default=1.0)
    has_default_currency = fields.Boolean(string='Has Default Currency',compute='_default_has_default_currency')
    
#    date_invoice = fields.Date(string='Invoice Date',
#        readonly=True, states={'draft': [('readonly', False)]}, index=True,
#        help="Keep empty to use the current date", copy=False, default=fields.Datetime.now)
    date_invoice = fields.Date(string='Invoice Date',
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="Keep empty to use the current date", copy=False, default=_default_date_invoice)
        
    total_cost = fields.Monetary(string='Total Cost',
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
        

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        self.pricelist_id = False
        self.user_id = self.env.user.id
        if self.partner_id.user_id:
            self.user_id = self.partner_id.user_id.id
        if self.partner_id:
            self.pricelist_id = self.partner_id.property_product_pricelist
        self.department_id = self.partner_id.customer_department_id.id
        self.division_id = self.partner_id.customer_division_id.id
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

    @api.onchange('discount_type', 'discount_amount', 'discount_glob','amount_untaxed')
    def _onchange_discount_type(self):
        prec_discount = self.env['decimal.precision'].precision_get('Discount')
        item_discount = 0.0
        if self.discount_type == 'amount':
            discount_amount = self.discount_amount
            invoice_lines = self.invoice_line_ids_two or self.invoice_line_ids
            if len(invoice_lines):
                for line in invoice_lines:
                    discount_percentage = self.discount_amount /self.amount_untaxed
                    discount_share = float_round(discount_percentage * line.price_subtotal, precision_digits=prec_discount)
                    line.write({'discount_share':discount_share})
                    line.discount_share = discount_share
                    item_discount += discount_share
        if self.discount_type == 'perc':
            discount_amount = self.amount_untaxed * (self.discount_glob/100.0)
            invoice_lines = self.invoice_line_ids_two or self.invoice_line_ids
            if len(invoice_lines):
                for line in invoice_lines:
                    discount_percentage = discount_amount /self.amount_untaxed
                    discount_share = float_round(discount_percentage * line.price_subtotal, precision_digits=prec_discount)
                    line.write({'discount_share':discount_share})
                    line.discount_share = discount_share
                    item_discount += discount_share
                    
        self.item_discount = item_discount
        item_discount = float_round(self.item_discount, precision_digits=prec_discount)
        total_discount = float_round(self.total_discount, precision_digits=prec_discount)
        
        ### if any fills diff, adding it to first line
        #get the latest item discount for comparing
        item_discount_prev = item_discount
        item_discount = 0.0
        invoice_lines = self.invoice_line_ids_two or self.invoice_line_ids
        if len(invoice_lines):
            for line in invoice_lines:
                item_discount += float_round(line.discount_share, precision_digits=prec_discount)
               
               
        if total_discount != item_discount:
            diff = total_discount - item_discount
            invoice_lines = self.invoice_line_ids_two or self.invoice_line_ids
            if len(invoice_lines):
                updated=False
                discount_share=0.0
                for line in invoice_lines:
                    if (line.price_subtotal<=0) or updated:
                        continue
                    discount_share = line.discount_share + diff
                    item_discount_prev = item_discount_prev + diff
#                    if diff<0:
#                        discount_share = line.discount_share - diff
#                        item_discount_prev = item_discount_prev - diff
#                    if diff>0:
#                        discount_share = line.discount_share + diff
#                        item_discount_prev = item_discount_prev + diff
                        
                    discount_share = float_round(discount_share, precision_digits=prec_discount)
                    line.write({'discount_share':discount_share})
                    line.discount_share=discount_share
                    updated=True
                self.item_discount = item_discount_prev
                
    @api.one
    @api.depends('discount_amount','discount_glob', 'invoice_line_ids.discount_amount')
    def _compute_discount(self):
        prec_discount = self.env['decimal.precision'].precision_get('Discount')
        if self.discount_type == 'amount':
            self.total_discount = float_round(self.discount_amount, precision_digits=prec_discount)
            item_discount = sum(self.invoice_line_ids.mapped('discount_share'))
            self.item_discount = float_round(item_discount, precision_digits=prec_discount)
        if self.discount_type == 'perc':
            total_discount = self.amount_untaxed * (self.discount_glob/100.0)
            self.total_discount = total_discount
            
            item_discount = sum(self.invoice_line_ids.mapped('discount_share'))
            self.item_discount = float_round(item_discount, precision_digits=prec_discount)

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
        self.residual = abs(residual)
#        if self.state!='draft': # Show the discounted value in Amount Due
#            total_discount = self.total_discount
#            self.residual_signed = (abs(residual) * sign) - total_discount
#            self.residual = abs(residual) - total_discount
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
    
    # inherited to add reference/ description  to ref field in account move
    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

#            name = inv.name or '/'
            shipping_name = inv.partner_shipping_id and inv.partner_shipping_id.name or False
#            name = inv.number
#            if name:
#                name = 'Credit Invoice '+str(name)
            if not shipping_name:
                street = inv.partner_shipping_id and inv.partner_shipping_id.street or False
                if street:
                    shipping_name = street
            if not shipping_name:
                street = inv.partner_id.name or inv.partner_id.street or False
                if street:
                    shipping_name = street
            name = shipping_name
            if not name:
                name = '/'
            if inv.type == 'in_invoice':
                name = inv.origin or '/'
                if name and inv.partner_id.ref:
                    name = str(name)+' '+str(inv.partner_id.ref)
            if inv.payment_term_id:
                totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
                res_amount_currency = total_currency
                ctx['date'] = inv._get_currency_rate_date()
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)

            journal = inv.journal_id.with_context(ctx)
            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or inv.date_invoice
            ref = inv.name or inv.reference
            if inv.type == 'in_invoice':
                ref = inv.origin or ''
            move_vals = {
#                'ref': inv.reference,
                'ref': ref,
#                'invoice_type': inv.invoice_type,
                'salesman_id': inv.user_id and inv.user_id.id or False,
                'division_id': inv.division_id and inv.division_id.id or False,
                'department_id': inv.department_id and inv.department_id.id or False,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
            }
            ctx['company_id'] = inv.company_id.id
            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
        return True

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(invoice, date_invoice, date, description, journal_id)
        res.update({'location_id': invoice.location_id.id, 'is_direct_invoice': invoice.is_direct_invoice,
                    'discount_glob': invoice.discount_glob, 'discount_amount': invoice.discount_amount
                    })
        return res
    
    # inherited to delete the moves and pickings related to this invoice
    @api.multi
    def action_cancel(self):
        origin = self.number
        state = self.state
        res = super(AccountInvoice, self).action_cancel()
        if state!='draft':
            Pack = self.env['stock.pack.operation'].sudo()
            picking_sudo = self.env['stock.picking'].sudo()
            all_pickings = []
            if origin:
                all_pickings = picking_sudo.search([('origin','=',origin)])
            if not all_pickings:
                if self.invoice_picking_id:
                    all_pickings = [picking_sudo.browse(self.invoice_picking_id.id)]
            stock_quant_sudo = self.env['stock.quant'].sudo()
            account_move_sudo = self.env['account.move'].sudo()
            if len(all_pickings):
                for picking in all_pickings:
                    #delete quants first
                    for move in picking.move_lines:
                        #1 find the quant in which these qty will be added
                        add_qty_quant_ids=[]
                        self._cr.execute("""SELECT id FROM stock_quant WHERE 
                            product_id = %s and location_id=%s and in_date<=%s ORDER BY id DESC""", 
                            (move.product_id.id,move.location_id.id,picking.min_date))
                        res = self._cr.fetchall()
                        if len(res):
                            add_qty_quant_ids = [x[0] for x in res]
                        if not len(add_qty_quant_ids):
                            self._cr.execute("""SELECT id FROM stock_quant WHERE 
                                product_id = %s and location_id=%s ORDER BY id DESC""", 
                                (move.product_id.id,move.location_id.id))
                            res = self._cr.fetchall()
                            if len(res):
                                add_qty_quant_ids = [x[0] for x in res]
                        print"add_qty_quant_ids: ",add_qty_quant_ids
                        if len(add_qty_quant_ids):
                            add_qty_quant = stock_quant_sudo.browse(add_qty_quant_ids[0])
                            add_qty_quant.write({'qty':float(add_qty_quant.qty+move.product_qty)})
                            print"qty added in old quant qty",add_qty_quant.qty
                            print"qty added in old quant"
                        else:
                            Move = self.env['stock.move'].sudo()
                            move_vals = {
                                'name': 'Return-'+str(picking.name),
                                'product_id': move.product_id.id,
                                'product_uom': move.product_uom.id,
                                'location_id': move.location_dest_id.id,
                                'location_dest_id': move.location_id.id,
#                                'picking_id': picking.id,
                                'company_id': picking.company_id.id,
                                'price_unit': move.price_unit,
#                                'picking_type_id': picking.picking_type_id.id,
#                                'lot_ids': [(6, 0, [x.id for x in each_line.lot_ids])],
#                                'warehouse_id': picking.picking_type_id.warehouse_id.id,
#                                'account_invoice_line_id': each_line.id,
                                'product_uom_qty': move.product_uom_qty,
                            }
                            Move = Move.create(move_vals)  
#                            Move=Move.browse(3577)
                            print"move: ",Move
                            Move.action_confirm()
                            Move.action_done()
                            print"move done,"
                            new_quant = stock_quant_sudo._quant_create_from_move(move.product_qty,Move)
                            print"new_quant: ",new_quant
                            
                            
                        
                        #2 find quant to delete
                        self._cr.execute("""SELECT quant_id FROM stock_quant_move_rel WHERE move_id = %s""", (move.id,))
                        res = self._cr.fetchall()
                        quant_ids = [x[0] for x in res]
                        print"quant_ids: ",quant_ids
                        self._cr.execute("""DELETE FROM stock_quant_move_rel WHERE quant_id IN %s""", (tuple(quant_ids),))
                        self._cr.execute("""DELETE FROM stock_quant WHERE id IN %s""", (tuple(quant_ids),))
                        print"delete executed"
#                        stopp
                    
                    picking.write({'state':'cancel'})
                    Packs = Pack.search([('picking_id','=',picking.id)])
                    for pack in Packs:
                        pack.write({'state':'draft'})
    #                    pack.unlink()
                    pack_ids = self.env['stock.pack.operation'].search([('picking_id','=',picking.id)])
                    if len(pack_ids):
                        self.env.cr.execute("delete from stock_pack_operation where picking_id=%s",(picking.id,))
                    account_moves = account_move_sudo.search([('ref','=',picking.name)])
                    if len(account_moves):
                        for account_move in account_moves:
                            account_move.write({'state':'draft'})
#                            for line in account_move.line_ids:
#                                line.unlink()
                            account_move.unlink()

                    for move in picking.move_lines:
                        move.write({'state':'cancel'})
                        move.unlink()
                    picking.unlink()

        return res
    
    
    ## inherited to add exchange rate changes
    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id
        
        self.exchange_rate = self.purchase_id.exchange_rate or 0.0

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line - self.invoice_line_ids.mapped('purchase_line_id'):
            data = self._prepare_invoice_line_from_po_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line
            
        self.invoice_line_ids += new_lines
        self.purchase_id = False
        return {}
    
    def _prepare_invoice_line_from_po_line(self, line):
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
        else:
            qty = line.qty_received - line.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = line.taxes_id
        invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.invoice.line']
        if self.currency_id.id != line.order_id.currency_id.id:
            price = line.order_id.currency_id.with_context(date=self.date_invoice).compute_custom(line.price_unit, self.currency_id, line.order_id.exchange_rate, round=False)
        else:
            price = line.order_id.currency_id.with_context(date=self.date_invoice).compute(line.price_unit, self.currency_id, round=False)
        data = {
            'purchase_line_id': line.id,
            'name': line.order_id.name+': '+line.name,
            'origin': line.order_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
#            'price_unit': line.order_id.currency_id.with_context(date=self.date_invoice).compute(line.price_unit, self.currency_id, round=False),
            'price_unit': price,
            'quantity': qty,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': line.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, line.order_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data
    
    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        if self.currency_id:
            for line in self.invoice_line_ids.filtered(lambda r: r.purchase_line_id):
                line.price_unit = line.purchase_id.currency_id.with_context(date=self.date_invoice).compute_custom(line.purchase_line_id.price_unit, self.currency_id, line.purchase_line_id.order_id.exchange_rate, round=False)


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'
    
    # to store cost price
    @api.model
    def create(self, vals):
        if vals.get('product_id', False):
            vals['cost_price'] = self.env['product.product'].browse(vals['product_id']).standard_price or 0.0
        line = super(account_invoice_line, self).create(vals)
        line.invoice_id._onchange_discount_type()
        return line
    
    # to call the discount onchange
    @api.multi
    def unlink(self):
        invoice = self.invoice_id
        res = super(account_invoice_line, self).unlink()
        invoice._onchange_discount_type()
        return res
    
    # to store cost price
    @api.multi
    def write(self, vals):
        if vals.get('product_id', False):
            vals['cost_price'] = self.env['product.product'].browse(vals['product_id']).standard_price or 0.0
        return super(account_invoice_line, self).write(vals)    

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



    discount_amount = fields.Float(string='Disc Amt.', digits=dp.get_precision('Discount'), store=True)
    discount = fields.Float(string='Disc.(%)', digits=dp.get_precision('Discount'))
    discount_share = fields.Float(string='Disc Share', digits=dp.get_precision('Discount'))
    total_discount_amount = fields.Float(string='Total Disc Amt', digits=dp.get_precision('Discount'),
            help='dicount amount + discount share')
#    discount_amount_global = fields.Float(string='Global Disc.', compute=_compute_discount_amount_global,
#                                          digits=dp.get_precision('Discount'))
#    discount_global = fields.Float(string='Global Disc.(%)', compute=_compute_discount_amount_global,
#                                   digits=dp.get_precision('Discount'))
    is_direct_invoice_line = fields.Boolean(string='IS Direct Invoice Line')
    lot_ids = fields.Many2many('stock.production.lot', 'invoice_stock_production_lot_rel', string="Lots")
    available_qty = fields.Float(string="Available Qty")
    forecast_qty = fields.Float(string="Forecast Qty")
    cost_price = fields.Float(string="Cost Price", digits=dp.get_precision('Discount'))
    refund_invoice_line_id = fields.Many2one('account.invoice.line', string="Refund Invoice line")
    price_subtotal = fields.Float(string='Amount',
        store=True, readonly=True, compute='_compute_price', digits=dp.get_precision('Product Price'))
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
            location_id = picking.location_id.id
            location_dest_id = each_line.invoice_id.partner_id.property_stock_customer.id
            if each_line.invoice_id.refund_without_invoice:
                location_id = picking.location_id.id
                location_dest_id = picking.picking_type_id.default_location_dest_id.id
            template = {
                'name': each_line.name or '',
                'product_id': each_line.product_id.id,
                'product_uom': each_line.uom_id.id,
#                'location_id': picking.location_id.id,
#                'location_dest_id': each_line.invoice_id.partner_id.property_stock_customer.id,
                'location_id':location_id,
                'location_dest_id':location_dest_id,
                'picking_id': picking.id,
                'product_uom_qty': each_line.quantity,
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
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        """
        Compute the amounts of the Direct Sale line.
        """
        # if self.invoice_id.discount_amount and self.discount_amount_global == 0.0
        prec_discount = self.env['decimal.precision'].precision_get('Discount')
        currency = self.invoice_id and self.invoice_id.currency_id or None
        self.discount_amount = ((self.price_unit * self.quantity) * self.discount) / 100
        if self.quantity > 0:
#            price = float_round(self.price_unit - ((self.discount_amount + self.discount_amount_global) / self.quantity),
#                                precision_digits=prec_discount)
            price = float_round(self.price_unit - ((self.discount_amount) / self.quantity),
                                precision_digits=prec_discount)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else (
                                                                                                    self.quantity * self.price_unit) - (
                                                                                                    self.discount_amount)
        if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
#            price_subtotal_signed = self.invoice_id.currency_id.with_context(
#                date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed,
#                                                                        self.invoice_id.company_id.currency_id)
            price_subtotal_signed = self.invoice_id.currency_id.with_context(
                date=self.invoice_id._get_currency_rate_date()).compute_custom(price_subtotal_signed,
                                                                        self.invoice_id.company_id.currency_id, self.invoice_id.exchange_rate)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign


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
    _order = 'id ASC'
    
#    salesman_id = fields.Many2one('res.partner', string='Salesman',domain=[('is_salesman', '=', True)])
    salesman_id = fields.Many2one('res.users', string='Salesman')
    collector_id = fields.Many2one('res.partner', string='Collector',domain=[('is_collector', '=', True)])
    ref_required = fields.Boolean(related='journal_id.ref_required', string="Ref required", store=True, help='its hidden field to make Ref mandatory/no mandatory based on journal selection')
    division_id = fields.Many2one('customer.division', string="Customer Division")
    department_id = fields.Many2one('customer.department', string="Customer Department")
    
    # inherited to, add Ref unique validations
    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        rec = super(AccountMove, self).copy(default)
        rec._check_ref_unique(rec.journal_id.id, rec.ref)
        return rec
    
    # inherited to, add Ref unique validations
    @api.multi
    def write(self, vals):
        if vals.get('ref',False):
            journal_id = vals.get('journal_id',False)
            if not journal_id:
                journal_id = self.journal_id and self.journal_id.id
            self._check_ref_unique(journal_id, vals['ref'])
        return super(AccountMove, self).write(vals)
    
    def _check_ref_unique(self, journal_id, ref):
        if journal_id:
            ref_unique = self.env['account.journal'].browse(journal_id).ref_unique or False
            if ref_unique and ref:
                ref=str(ref).lower()
                self.env.cr.execute("SELECT id FROM account_move WHERE LOWER(ref)=%s",(ref,))
                query_res = self.env.cr.dictfetchall()
                if len(query_res):
                    raise UserError(_("Ref should be unique, its already used."))
        return True
            
    
    # inherited to, add Ref unique validations
    @api.model
    def create(self, vals):
        ref = vals.get('ref', False)
        journal_id = vals.get('journal_id', False)
        if journal_id and ref:
            self._check_ref_unique(journal_id, ref)
#        if not 'name' in vals.keys():
#            vals['name']='/'

        moves = super(AccountMove, self).create(vals)
        
        ## generate the sequence on create itself
        invoice = self._context.get('invoice', False)
        for move in moves:
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
                        print "\n create called for sequence :::::::::::::::::::"
                        new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(_('Please define a sequence on the journal.'))
                if invoice:
                    if invoice.number:
                        move.name = invoice.number
                if new_name:
                    move.name = new_name
        return moves

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

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _order = "id ASC"
    
    customer_division_id = fields.Many2one('customer.division', string=_("Customer Division"))
    customer_department_id = fields.Many2one('customer.department', string=_("Customer Department"))

    @api.onchange('partner_id')
    def onchange_partner(self):
        self.customer_department_id = self.partner_id.customer_department_id.id
        self.customer_division_id = self.partner_id.customer_division_id.id
        
    @api.onchange('account_id')
    def _onchange_account_id(self):
        currency_id = False
        if self.company_id:
            currency_id = self.company_id.currency_id and self.company_id.currency_id.id
        if not currency_id:
            currency = self.env['res.currency'].search([('name','=','KWD')])
            if len(currency):
                currency_id = currency[0].id
        self.currency_id = currency_id
        return {}

    @api.model
    def create(self, vals):
        res = super(AccountMoveLine, self).create(vals)
        dept_id = False
        div_id = False
        if res.invoice_id:
            dept_id = res.invoice_id.department_id.id
            div_id = res.invoice_id.division_id.id
            for each in res.move_id.line_ids:
                each.customer_division_id = div_id
                each.customer_department_id = dept_id
        if not dept_id and not div_id:
            if res.partner_id:
                res.customer_division_id = res.partner_id.customer_division_id.id
                res.customer_department_id = res.partner_id.customer_department_id.id
        return res

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    customer_division_id = fields.Many2one('customer.division', string=_("Customer Division"))
    customer_department_id = fields.Many2one('customer.department', string=_("Customer Department"))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountPayment, self)._onchange_partner_id()
        self.customer_division_id = self.partner_id.customer_division_id.id
        self.customer_department_id = self.partner_id.customer_department_id.id
        return res
    
    
class AccountAccount(models.Model):
    _inherit = "account.account"
    
    # inherited to show the entries for this particular account only
    @api.multi
    def action_open_reconcile(self):
        self.ensure_one()
        # Open reconciliation view for this account
        if self.internal_type == 'payable':
#            action_context = {'show_mode_selector': False, 'mode': 'suppliers'}
            action_context = {'show_mode_selector': False, 'mode': 'suppliers'}
            if self.partner_id:
                action_context = {'show_mode_selector': False, 'mode': 'suppliers', 'partner_ids': [self.partner_id.id], 'company_ids': [self.company_id.id]}
        elif self.internal_type == 'receivable':
            action_context = {'show_mode_selector': False, 'mode': 'customers'}
            if self.partner_id:
                action_context = {'show_mode_selector': False, 'mode': 'customers', 'partner_ids': [self.partner_id.id], 'company_ids': [self.company_id.id]}
        else:
            action_context = {'show_mode_selector': False, 'account_ids': [self.id,]}
        return {
            'type': 'ir.actions.client',
            'tag': 'manual_reconciliation_view',
            'context': action_context,
        }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
