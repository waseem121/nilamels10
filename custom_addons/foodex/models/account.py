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
import time

class account_move(models.Model):
    _inherit = "account.move"
    
    invoice_type = fields.Selection([('normal', 'Normal Invoice'), 
                        ('sample', 'Sample Invoice'),
                        ('transfer_invoice', 'Transfer Invoice'),
                        ('veg_invoice', 'Vegetable Invoice')], string='Invoice Type',
                                     default='')    
    
    

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    @api.model
    def _default_invoice_type(self):
        if self._context.get('invoice_type',False):
            return self._context.get('invoice_type',False)
        return 'normal'
    
    @api.model
    def _default_date_invoice(self):
        if self.env.user.transaction_date:
            return self.env.user.transaction_date
        else:
            return fields.Datetime.now()


    invoice_type = fields.Selection([('normal', 'Normal Invoice'), 
                        ('sample', 'Sample Invoice'),
                        ('transfer_invoice', 'Transfer Invoice'),
                        ('veg_invoice', 'Vegetable Invoice')], string='Invoice Type',
                                     default=_default_invoice_type)
                                     
    date_invoice = fields.Date(string='Invoice Date',
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="Keep empty to use the current date", copy=False, default=_default_date_invoice)
                         
                                     
    @api.multi
    def action_invoice_draft(self):
        res = super(AccountInvoice, self).action_invoice_draft()
        if self.invoice_type == 'transfer_invoice' and not self.refund_without_invoice:
            self.number = self.env['ir.sequence'].next_by_code('transfer.invoice.sequence')
        if self.is_direct_invoice or self.refund_without_invoice or self.type in ['in_invoice', 'in_refund'] and not self.invoice_type=='transfer_invoice':
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
    def write(self, vals):
#        print"foodex/write vals: ",vals
        if 'invoice_type' in vals.keys():
            if not vals.get('invoice_type',False):
                vals['invoice_type'] = 'normal'                
        return super(AccountInvoice, self).write(vals)    
                                     
    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if not res.invoice_type:
            res.invoice_type=='normal'
        if res.invoice_type == 'transfer_invoice' and not res.refund_without_invoice:
            res.number = self.env['ir.sequence'].next_by_code('transfer.invoice.sequence')
        else:
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

        if res.pricelist_id.update_transaction_value and res.pricelist_id.transaction_on == 'save':
            for lines in res.invoice_line_ids_two.filtered(lambda l: l.price_unit > 0.00):
                pricelist_item = res.pricelist_id.item_ids.filtered(lambda
                                                                          l: l.compute_price == 'fixed' and l.applied_on == '1_product' and l.uom_id.id == lines.uom_id.id)
                if pricelist_item:
                    each_price = res.pricelist_id.item_ids.search(
                        [('product_tmpl_id', '=', lines.product_id.product_tmpl_id.id),
                         ('compute_price', '=', 'fixed'), ('applied_on', '=', '1_product'),
                         ('pricelist_id', '=', res.pricelist_id.id), ('uom_id', '=', lines.uom_id.id)])
                    if not each_price:
                        res.pricelist_id.write({'item_ids': [(0, 0, {'applied_on': '1_product',
                                                                       'product_tmpl_id': lines.product_id.product_tmpl_id.id,
                                                                       'uom_id': lines.uom_id.id,
                                                                       'fixed_price': lines.price_unit})]})

                    # order_lines = order.order_line.filtered(lambda l:l.product_id.id in [x.product_id.id for x in each_price] and l.price_unit > 0.00).sorted(lambda l:l.price_unit)
                    # if order_lines:
                    # 	for each_pricelist in each_price:
                    else:
                        each_price.fixed_price = lines.price_unit
                else:
                    res.pricelist_id.write({'item_ids': [(0, 0, {'applied_on': '1_product',
                                                                   'product_tmpl_id': lines.product_id.product_tmpl_id.id,
                                                                   'uom_id': lines.uom_id.id,
                                                                   'fixed_price': lines.price_unit
                                                                   })]})

        if res.pricelist_id and res.pricelist_id.update_transaction_value:
            res.product_price_update()
        return res
    
    @api.multi
    def action_invoice_open(self):
        # invoice_ids
        start_time = time.time()
        if self.number:
            pickings = self.env['stock.picking'].search([('origin','=',self.number)])
            if len(pickings):
                for picking in pickings:
                    if picking.state not in ['done', 'cancel']:
                        raise Warning(_("The Delivery for this order is not validated yet, Please validate it first...!!!!"))
                    
        # make sure Partner has been assiged in the Account
        rec_account = self.partner_id.property_account_receivable_id or False
        if not rec_account:
            raise ValidationError(_("Please set Account Receivable for the customer."))
        if not rec_account.partner_id:
            raise UserError(_("Please set Partner for Account: %s.") % rec_account.name)
                
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
        print("after first part--- %s seconds ---" % (time.time() - start_time))

        if self.is_direct_invoice or self.refund_without_invoice or self.invoice_type=='transfer_invoice':
#            if not self.refund_without_invoice:
#                product_lst = self.invoice_line_ids.mapped('product_id')
#                for product_id in product_lst:
#                    product_sum_qty = sum(
#                        self.invoice_line_ids.filtered(lambda l: l.product_id.id == product_id.id).mapped('quantity'))
                        
#                    prod_qty_available = product_id.with_context(
#                        {'location': self.location_id.id, 'compute_child': False}).qty_available
#                        {'location': self.location_id.id, 'compute_child': False}).virtual_available_inv
#                    if prod_qty_available<=0.0:
#                        raise Warning(_('%s has not enough quantity into %s location.') % (
#                            product_id.name, self.location_id.name))
                        
                 
#                    prod_qty_available += product_sum_qty   # bcz this qty is already gets substracted from virtual available
#                    
#                    #TODO, commented temp
##                    if prod_qty_available < product_sum_qty:
##                        raise Warning(_('%s has not enough quantity into %s location.') % (
##                            product_id.name, self.location_id.name))
#                    
##                    foodex-account-checkme
#
#                for invoice_line in self.invoice_line_ids.filtered(
#                        lambda l: l.product_id.tracking != 'none' and not l.lot_ids):
#                    if self.env['stock.config.settings'].search([], order='id desc',
#                                                                limit=1).group_stock_production_lot:
#                        raise Warning(
#                            _('For product %s serial number must be required.') % invoice_line.product_id.name)
#                        zero_lot = invoice_line.lot_ids.filtered(lambda l: l.remaining_qty <= 0)
#                        if zero_lot:
#                            raise Warning(_('Define Lot/Serial number %s for product %s is now not available.' %
#                                            ([str(lot.name) for lot in zero_lot], invoice_line.product_id.name)))
#
#                for invoice_line in self.invoice_line_ids.filtered(
#                        lambda l: l.product_id.tracking == 'serial' and l.lot_ids):
#                    if len(invoice_line.lot_ids) != invoice_line.quantity:
#                        raise Warning(
#                            _('Please check serial number and quantity on product %s, those must be in same number.') %
#                            ("'" + invoice_line.product_id.name + "'"))
#
#                for invoice_line in self.invoice_line_ids.filtered(lambda l: l.product_id):
#                    available_qty = 0.00
#                    if invoice_line.product_id.tracking != 'none':
#                        for each_lot in invoice_line.lot_ids:
#                            available_qty += invoice_line.product_id.with_context(
#                                {'location': self.location_id.id, 'compute_child': False,
#                                 'lot_id': each_lot.id}).qty_available
#                    else:
#                        available_qty = invoice_line.product_id.with_context(
#                            {'location': self.location_id.id, 'compute_child': False}).qty_available
##                    if invoice_line.quantity > available_qty:
##                        raise Warning(_('Not enough quantity for %s .') % (invoice_line.product_id.name))
#            else:
#                for invoice_line in self.invoice_line_ids.filtered(
#                        lambda l: l.product_id.tracking != 'none' and not l.lot_ids):
#                    if self.env['stock.config.settings'].search([], order='id desc',
#                                                                limit=1).group_stock_production_lot:
#                        raise Warning(
#                            _('For product %s serial number must be required.') % invoice_line.product_id.name)
            if self.refund_invoice_id:
                self.do_return_picking()
            else:
                self.action_create_sales_order()    #creates only sales order no picking created here
#                start_time = time.time()
                self.action_stock_transfer()
#                print("after action_stock_transfer--- %s seconds ---" % (time.time() - start_time))
#                self.check_date()
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
        self.check_date()
        to_open_invoices.invoice_validate()
        # auto-reconcile start
        if self.type == 'out_refund':
            account = self.account_id
            if account.auto_reconcile:
                credit_aml = self.move_id.line_ids.filtered(lambda r: r.account_id.id == account.id)
                credit = credit_aml.credit
                print"credit: ",credit

                debit_aml_all = self.env['account.move.line'].search([('account_id','=',account.id),('debit','>',0.0),('reconciled','=',False)])
                print"debit_aml_all: ",debit_aml_all
                debit_aml_ids = []
                debit = 0.0
                skip = False
                for l in debit_aml_all:
                    debit += l.debit
                    if skip:
                        continue
                    debit_aml_ids.append(l.id)
    #                    if debit <=credit:
                    if credit <=debit:
                        skip=True
                print"debit: ",debit

                debit_aml = self.env['account.move.line'].browse(debit_aml_ids)
                print"debit_aml: ",debit_aml

                res = (credit_aml + debit_aml).reconcile()
                print"after reconcile res: ",res
        # auto-reconcile end
        
        return True
    
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
                if len(backorder_pickings):
                    for backorder_picking in backorder_pickings:
                        for move in backorder_picking.move_lines:
                            move.write({'date_expected':date_invoice,'date':date_invoice})
                        backorder_picking.write({'date':date_invoice, 'min_date':date_invoice,
                            'date_done':date_invoice,'max_date':date_invoice})
    
    
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
            name = inv.partner_shipping_id.street or inv.partner_shipping_id.name or False
            if not name:
                name = inv.name or '/'
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
#                ref = inv.origin or ''
                ref = inv.reference or inv.origin
            move_vals = {
#                'ref': inv.reference,
                'ref': ref,
                'invoice_type': inv.invoice_type,
                'salesman_id': inv.user_id and inv.user_id.id or False,
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
                    'discount_glob': invoice.discount_glob, 'discount_amount': invoice.discount_amount,
                    'invoice_type':invoice.invoice_type
                    })
        return res    
                
    # inherited to avoid looking for available stock validation
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
#            else:
#                stock_qty = lines.product_id.with_context(
#                    {'location': lines.invoice_id.location_id.id, 'compute_child': False})
#                if stock_qty.qty_available <= 0 or stock_qty.qty_available < lines.quantity:
#                    raise Warning(_('Please check quantity in source location \n Quantity available: %s \nProduct: %s' %
#                                    (stock_qty.qty_available, lines.product_id.name)))

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
    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        picking_ids = []
        if self.invoice_picking_id and self.invoice_picking_id.id:
            picking_ids = [self.invoice_picking_id.id]
            
        origin = self.number or False
        if origin:
            pickings = self.env['stock.picking'].search([('origin','=',origin)])
            for picking in pickings:
                picking_ids.append(picking.id)
                
        picking_ids = list(set(picking_ids))
        action['domain'] = [('id', 'in', tuple(picking_ids))]
        return action
    
class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    def _create_stock_moves_transfer(self, picking, zero_stock_product_ids):
        move_obj = self.env['stock.move']
        for each_line in self:
            if each_line.product_id.id in zero_stock_product_ids:
                continue
            location_id = picking.location_id.id
            location_dest_id = each_line.invoice_id.partner_id.property_stock_customer.id
            if each_line.invoice_id.refund_without_invoice:
                location_id = picking.location_id.id
                location_dest_id = picking.picking_type_id.default_location_dest_id.id
                
#            if not picking.location_id.usage=='customer':
#                available_qty = each_line.product_id.with_context(
#                    {'location': picking.location_id.id, 'compute_child': False}).qty_available
#                if available_qty < (each_line.quantity + each_line.free_qty):
#                    print"less qty continue"
#                    continue
            
            template = {
                'name': each_line.name or '',
                'product_id': each_line.product_id.id,
                'product_uom': each_line.uom_id.id,
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
            }
            move_obj |= move_obj.create(template)
        return move_obj

    
    ## not used anywhere
    forecast_qty_tranfer_inv = fields.Float(string="Forecast Qty Tr")
    invoice_type = fields.Selection(related='invoice_id.invoice_type', string='Invoice Type',
                                     store=True)    
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
#        print"foodex onchange product qty: ",self.quantity
        res = super(account_invoice_line, self)._onchange_product_id()
        location_id = self.invoice_id.location_id.id
        if self.invoice_id.refund_without_invoice:
            location_id = self.invoice_id.partner_id.property_stock_customer.id
        product_qty_available = self.product_id.with_context({'location': location_id, 'compute_child': False})
        if product_qty_available:
            forecast_qty = product_qty_available.virtual_available_inv
            if self.invoice_id:
                if self.invoice_id.invoice_type == 'transfer_invoice':
                    forecast_qty = product_qty_available.virtual_available_tranfer_inv
                    
            forecast_qty -= self.quantity
                    
            self.update({'available_qty': product_qty_available.qty_available,
#                         'forecast_qty': product_qty_available.virtual_available})
#                         'forecast_qty': product_qty_available.virtual_available_inv,  # forecasted qty to shows based on invoice lines
                         'forecast_qty': forecast_qty})
                         
        return res    
    
    @api.onchange('uom_id','quantity')
    def _onchange_uom_id(self):
        warning = {}
        result = {}
        date = uom_id = False
        if not self.uom_id:
            self.price_unit = 0.0
        if self.product_id and self.uom_id:
            if self.product_id.uom_so_id.category_id.id != self.uom_id.category_id.id:
                warning = {
                    'title': _('Warning!'),
                    'message': _('The selected unit of measure is not compatible with the unit of measure of the product.'),
                }

                self.uom_id = self.product_id.uom_so_id.id
            if self.uom_id:
                price = dict((product_id, res_tuple[0]) for product_id, res_tuple in self.invoice_id.pricelist_id._compute_price_rule([(self.product_id, self.quantity, self.partner_id)], date=False, uom_id=self.uom_id.id).iteritems())
                self.price_unit = price.get(self.product_id.id, 0.0)
                if warning:
                    result['warning'] = warning
                                        
                # changes for showing available stock based on UoM selected
                location_id = self.invoice_id.location_id.id
                if self.invoice_id.refund_without_invoice:
                    location_id = self.invoice_id.partner_id.property_stock_customer.id
                product_qty_available = self.product_id.with_context({'location': location_id, 'compute_child': False})
                if product_qty_available:
                    qty_available = product_qty_available.qty_available
                    if self.invoice_id.invoice_type=='transfer_invoice':
                        virtual_available = product_qty_available.virtual_available_tranfer_inv
                    else:
                        virtual_available = product_qty_available.virtual_available_inv
                    print"uom onchange virtual_available_inv: ",virtual_available
                    if self.uom_id.uom_type == 'bigger':
                        qty_available = (qty_available) / (self.uom_id.factor_inv)
                    if self.uom_id.uom_type == 'smaller':
                        qty_available = (qty_available) * (self.uom_id.factor_inv)
                        
                    if self.uom_id.uom_type == 'bigger':
                        virtual_available = (virtual_available) / (self.uom_id.factor_inv)
                    if self.uom_id.uom_type == 'smaller':
                        virtual_available = (virtual_available) * (self.uom_id.factor_inv)
                        
                    forecast_qty = virtual_available
                 
                    forecast_qty -= self.quantity
                    self.update({'available_qty': qty_available,
                            'forecast_qty': forecast_qty})
                                
        return result    

                                     
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
