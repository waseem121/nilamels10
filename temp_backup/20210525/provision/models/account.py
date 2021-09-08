# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import Warning, ValidationError
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountAccount(models.Model):
    _inherit = "account.account"
    
    is_bank = fields.Boolean(string='Is Bank', default=False,
        help="if checked, this account can be used in the Bank and Cash journal as debit/credit account.")

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    
    
    product_id = fields.Many2one('product.product',string='Product Selection Existing')
    price_subtotal_editable = fields.Float(string='AmountEdit',
            digits=dp.get_precision('Product Price'))
            
            
#    @api.onchange('price_subtotal')
#    def set_price_subtotal_editable(self):
#        print"Subtotal called: ctxxx"
#        if self.price_subtotal:
#            self.price_subtotal_editable = round(self.price_subtotal, 6)
#        
#    @api.onchange('price_subtotal_editable')
#    def _onchange_price_subtotal_editable(self):
#        print"Editable  Called ctx: "
#        if self.price_subtotal_editable:
#            price_unit = round(((self.price_subtotal_editable+self.discount_amount) / self.quantity), 6)
#            print"Editable price_unit: ",price_unit
##            price_unit = round(((self.price_subtotal_editable+self.discount_amount) / self.quantity), 10)
#            if self._origin.id:
#                self._cr.execute("update account_invoice_line set price_unit=%s where id=%s",(price_unit,self._origin.id))
#                print"query executed"
#            self.price_unit = price_unit
#            
#            
#    @api.model
#    def create(self, vals):
#        if vals.get('price_subtotal_editable',0):
#            if float(vals.get('quantity')) > 0:
#                price_unit = float(vals.get('price_subtotal_editable')) / float(vals.get('quantity'))
#                if round(float(vals.get('price_unit')),6) != round(price_unit,6):
#                    vals['price_unit'] = round(price_unit,6)
#        res = super(AccountInvoiceLine, self).create(vals)
#        return res

    @api.onchange('price_subtotal_editable')
    def _onchange_price_subtotal_editable(self):
        print"Editable  Called ctx: "
        if self.price_subtotal_editable:
            print"self.price_subtotal_editable: ",self.price_subtotal_editable
            subtotal = self.price_subtotal
            print"subtotal: ",subtotal
            self.discount_amount = self.discount_amount + (subtotal - self.price_subtotal_editable)

            
            

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    x_picking_id = fields.Many2one('stock.picking', 'Picking')
    lpo_number = fields.Char(string='LPO Number')
    job_number = fields.Char(string='Job Number')
#    job_ids = fields.Many2many('job.order', string='Jobs', 
#                domain=[('state', 'not in', ('invoiced','cancel'))])
    job_ids = fields.Many2many('job.order', string='Jobs', 
                domain=[('state', 'not in', ('cancel',))])
    
    @api.onchange('x_picking_id')
    def _onchange_picking_id_auto_complete(self):
        
        if not self.x_picking_id:
            return
        
        if self.invoice_line_ids:
#            for l in self.invoice_line_ids:
#                l.unlink()
#            self.invoice_line_ids.unlink()
#            self.invoice_line_ids_two.unlink()
            self.amount_untaxed = 0.0
            self.amount_total = 0.0
            
#        self.partner_id = self.picking_id.partner_id
#        self.fiscal_position_id = False
#        self.invoice_payment_term_id = False
#        self.currency_id = self.picking_id.company_id and self.picking_id.company_id.currency_id

        moves = self.x_picking_id.move_lines
#        new_lines = self.env['account.invoice.line']
        Line = self.env['account.invoice.line']
        new_lines = []
        value = {}
        sequence = 1
        arr = []
        for move in moves:
            currency = self.currency_id
            line = {
                'sequence2':sequence,
                'name': move.name,
                'invoice_id': self.id,
                'currency_id': currency and currency.id or False,
                'date_maturity': move.date,
                'uom_id': move.product_uom.id,
                'product_id': move.product_id.id,
                'price_unit': move.price_unit or move.product_id.standard_price,
                'quantity': move.product_uom_qty,
                'partner_id': self.partner_id.id,
                'account_id':move.product_id.categ_id.property_account_income_categ_id.id
                }
#            Line.create(line)
            
            new_lines.append((0,0,line))
            arr.append(line)
            sequence+=1
        value.update(invoice_line_ids=new_lines)
#        self.invoice_line_ids = [x for x in new_lines]
        return {'value':value}
    
    @api.onchange('job_ids')
    def _onchange_job_ids(self):
        print"_onchange_job_ids called job_ids: ",self.job_ids
        print"_onchange_job_ids called job_ids: ",self._origin.job_ids
        
        
        print"_onchange_job_ids called invoice_line_ids: Len ",len(self.invoice_line_ids)
        sequence = len(self.invoice_line_ids) + 1
        
        if not self.job_ids:
            return
        
        if len(self.job_ids)>1:
            job_ids = self.job_ids.ids
            jobs = [self.env['job.order'].browse(job_ids[-1])]
        else:
            jobs = self.job_ids
        
        new_lines = []
        value = {}
        for job in jobs:
            currency = job.currency_id or self.currency_id
            for job_line in job.job_lines:
                line = {
                    'sequence2':sequence,
                    'name': job_line.name,
                    'invoice_id': self.id,
                    'currency_id': currency and currency.id or False,
                    'date_maturity': self.date,
                    'uom_id': job_line.uom_id.id,
                    'product_id': job_line.product_id.id,
                    'price_unit': job_line.price_unit or job_line.product_id.lst_price,
                    'price_subtotal_editable':job_line.qty * job_line.price_unit or job_line.product_id.lst_price or 0,
                    'quantity': job_line.qty,
                    'partner_id': self.partner_id.id,
                    'account_id':job_line.product_id.categ_id.property_account_income_categ_id.id
                    }

                new_lines.append((0,0,line))
                sequence+=1
#                job.write({'state': 'invoiced'})
        value.update(invoice_line_ids=new_lines)
        return {'value':value}    
    
    @api.multi
    def action_invoice_open(self):
        print"provision/account action_invoice_open called"

        # invoice_ids
        if self.number:
            pickings = self.env['stock.picking'].search([('origin','=',self.number)])
            if len(pickings):
                for picking in pickings:
                    if picking.state not in ['done', 'cancel']:
                        raise Warning(_("The Delivery for this order is not validated yet, Please validate it first...!!!!"))

        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))
        
        # make sure Partner has been assiged in the Account
        if self.type in ('out_invoice', 'out_refund'):
            rec_account = self.partner_id.property_account_receivable_id or False
        else:
            rec_account = self.partner_id.property_account_payable_id or False
        if not rec_account:
            raise ValidationError(_("Please set Account Receivable/Payable for the customer."))
        if not rec_account.partner_id:
            raise UserError(_("Please set Partner for Account: %s.") % rec_account.name)
        
        if self.x_picking_id:
            self.x_picking_id.write({'origin':self.number})
        if not self.x_picking_id:
            if self.is_direct_invoice or self.refund_without_invoice:
                if not self.refund_without_invoice:
                    location = self.location_id
                    if self.type == 'out_refund':
                        location = self.env['stock.location'].search([('usage','=','customer')])[0]
                    product_lst = self.invoice_line_ids.mapped('product_id')
                    for product_id in product_lst:
                        if product_id.type not in ('product', 'consu'):
                            continue
                            
                        product_sum_qty = sum(
                            self.invoice_line_ids.filtered(lambda l: l.product_id.id == product_id.id).mapped('quantity'))
                        product_sum_free_qty = sum(
                            self.invoice_line_ids.filtered(lambda l: l.product_id.id == product_id.id).mapped('free_qty'))
                        product_sum_qty = product_sum_qty + product_sum_free_qty

                        prod_qty_available = product_id.with_context(
                            {'location': location.id, 'compute_child': False}).qty_available
    #                        {'location': self.location_id.id, 'compute_child': False}).virtual_available_inv
                        if prod_qty_available < product_sum_qty:
                            raise Warning(_('%s has not enough quantity into %s location.') % (
                                product_id.name, location.name))
                                
                    for invoice_line in self.invoice_line_ids.filtered(
                            lambda l: l.product_id.tracking != 'none' and not l.lot_ids):
                                
                        if invoice_line.product_id.type not in ('product', 'consu'):
                            continue                                
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
                                
                        if invoice_line.product_id.type not in ('product', 'consu'):
                            continue
                        if len(invoice_line.lot_ids) != invoice_line.quantity:
                            raise Warning(
                                _('Please check serial number and quantity on product %s, those must be in same number.') %
                                ("'" + invoice_line.product_id.name + "'"))

                    for invoice_line in self.invoice_line_ids.filtered(lambda l: l.product_id):
                        
                        if invoice_line.product_id.type not in ('product', 'consu'):
                            continue
                        available_qty = 0.00
                        if invoice_line.product_id.tracking != 'none':
                            for each_lot in invoice_line.lot_ids:
                                available_qty += invoice_line.product_id.with_context(
                                    {'location': location.id, 'compute_child': False,
                                     'lot_id': each_lot.id}).qty_available
                        else:
                            available_qty = invoice_line.product_id.with_context(
                                {'location': location.id, 'compute_child': False}).qty_available
                        if (invoice_line.quantity + invoice_line.free_qty) > available_qty:
                            raise Warning(_('Not enough quantity for %s .') % (invoice_line.product_id.name))
                else:
                    for invoice_line in self.invoice_line_ids.filtered(
                            lambda l: l.product_id.tracking != 'none' and not l.lot_ids):
                                
                        if invoice_line.product_id.type not in ('product', 'consu'):
                            continue                                                                
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
    
    @api.model
    def create(self, vals):
        ## update job order state to invoiced
        res = super(AccountInvoice, self).create(vals)
        if 'job_ids' in vals:
            job_ids = vals.get('job_ids')
            if len(job_ids):
                job_ids = job_ids[0]
                job_ids = job_ids[2]
                if len(job_ids):
                    self.env['job.order'].browse(job_ids).action_invoiced()
#        if res.is_direct_invoice or res.refund_without_invoice or res.type in ['in_invoice', 'in_refund'] or self._context.get('sale_order_location',False):
        if res.is_direct_invoice or res.refund_without_invoice or self._context.get('sale_order_location',False):
            new_name = False
            journal = res.journal_id
            location = res.location_id
            if location.sequence_id:
                sequence = location.sequence_id
                if res.refund_without_invoice or res.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                    sequence = journal.refund_sequence_id
                new_name = sequence.with_context(ir_sequence_date=res.date_invoice).next_by_id()
            else:
                raise UserError(_('Please define a sequence on the Location.'))                
            if new_name:
                res.number = new_name

        if res.pricelist_id and res.pricelist_id.update_transaction_value:
            res.product_price_update()
        return res    
    
    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        ## update job order state to invoiced
        if 'job_ids' in vals:
            v_job_ids = vals.get('job_ids')
            if len(v_job_ids):
                v_job_ids = v_job_ids[0]
                v_job_ids = v_job_ids[2]
                if len(v_job_ids):
                    self.env['job.order'].browse(v_job_ids).action_invoiced()
                
        return res
    
    # add job number to the particulars field in move line
    @api.multi
    def action_move_create(self):
        result = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if inv.type not in ('out_invoice', 'out_refund'):
                continue
            move = inv.move_id or False
            if move:
                move.line_ids.write({'x_particulars':inv.lpo_number})
                move.line_ids.write({'x_job_no':inv.job_number})
        return result
    

    # remove KWD and zero fill strings from text
    @api.one
    def get_amount_word_custom(self):
        amount_text = self.get_amount_word()[0]
        amount_text = amount_text.replace("KWD","")
        
#        if not found -1        
        if amount_text.find("Zero fills") !=-1:
            split = amount_text.split("Zero fills")
            amount_text = split[0][:-4] + ' only.'
        return str(amount_text)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    x_job_no = fields.Char(string="Job No.")
    job_id = fields.Many2one('job.order', 'Job')
    
    @api.onchange('exchange_rate')
    def _onchange_exchange_rate(self):
        if self.exchange_rate and (self.debit or self.credit):
            amount_currency = 0.0
            if self.debit:
                amount_currency = self.debit * self.exchange_rate
            if self.credit:
                amount_currency = (self.credit * self.exchange_rate ) * -1
            print"self.exchange_rate: ",self.exchange_rate
            print"self.debit: ",self.debit
            print"amount_currency: ",amount_currency
            
            self.amount_currency = amount_currency
    
    def auto_reconcile_lines_custom(self, payment_info):
        if not self.ids:
            return self
        sm_debit_move, sm_credit_move = self._get_pair_to_reconcile()
        #there is no more pair to reconcile so return what move_line are left
        if not sm_credit_move or not sm_debit_move:
            return self

        field = self[0].account_id.currency_id and 'amount_residual_currency' or 'amount_residual'
        if not sm_debit_move.debit and not sm_debit_move.credit:
            #both debit and credit field are 0, consider the amount_residual_currency field because it's an exchange difference entry
            field = 'amount_residual_currency'
        if self[0].currency_id and all([x.currency_id == self[0].currency_id for x in self]):
            #all the lines have the same currency, so we consider the amount_residual_currency field
            field = 'amount_residual_currency'
        if self._context.get('skip_full_reconcile_check') == 'amount_currency_excluded':
            field = 'amount_residual'
        elif self._context.get('skip_full_reconcile_check') == 'amount_currency_only':
            field = 'amount_residual_currency'
        #Reconcile the pair together
#        amount_reconcile = min(sm_debit_move[field], -sm_credit_move[field])

        amount_reconcile = 0.0
        if payment_info['payment_type'] == 'inbound':
            amount_reconcile = payment_info.get(sm_debit_move.id)
        if payment_info['payment_type'] == 'outbound':
            amount_reconcile = payment_info.get(sm_credit_move.id)
        #Remove from recordset the one(s) that will be totally reconciled
        if amount_reconcile == sm_debit_move[field]:
            self -= sm_debit_move
        if amount_reconcile == -sm_credit_move[field]:
            self -= sm_credit_move

        #Check for the currency and amount_currency we can set
        currency = False
        amount_reconcile_currency = 0
        if sm_debit_move.currency_id == sm_credit_move.currency_id and sm_debit_move.currency_id.id:
            currency = sm_credit_move.currency_id.id
            amount_reconcile_currency = min(sm_debit_move.amount_residual_currency, -sm_credit_move.amount_residual_currency)

#        amount_reconcile = min(sm_debit_move.amount_residual, -sm_credit_move.amount_residual)

        if self._context.get('skip_full_reconcile_check') == 'amount_currency_excluded':
            amount_reconcile_currency = 0.0
            currency = self._context.get('manual_full_reconcile_currency')
        elif self._context.get('skip_full_reconcile_check') == 'amount_currency_only':
            currency = self._context.get('manual_full_reconcile_currency')

        self.env['account.partial.reconcile'].create({
            'debit_move_id': sm_debit_move.id,
            'credit_move_id': sm_credit_move.id,
            'amount': amount_reconcile,
            'amount_currency': amount_reconcile_currency,
            'currency_id': currency,
        })
        print"before reutrn auto_reconcile_lines_custom"

        #Iterate process again on self
#        return self.auto_reconcile_lines_custom(payment_info)
        return True
    
    
    # to reconcile invoice with user entered amount
    @api.multi
    def reconcile_custom(self, writeoff_acc_id=False, writeoff_journal_id=False, payment_info={}):
        # Empty self can happen if the user tries to reconcile entries which are already reconciled.
        # The calling method might have filtered out reconciled lines.
        if not self:
            return True

        #Perform all checks on lines
        company_ids = set()
        all_accounts = []
        partners = set()
        for line in self:
            company_ids.add(line.company_id.id)
            all_accounts.append(line.account_id)
            if (line.account_id.internal_type in ('receivable', 'payable')):
                partners.add(line.partner_id.id)
            if line.reconciled:
                raise UserError(_('You are trying to reconcile some entries that are already reconciled!'))
        if len(company_ids) > 1:
            raise UserError(_('To reconcile the entries company should be the same for all entries!'))
        if len(set(all_accounts)) > 1:
            raise UserError(_('Entries are not of the same account!'))
        if not (all_accounts[0].reconcile or all_accounts[0].internal_type == 'liquidity'):
            raise UserError(_('The account %s (%s) is not marked as reconciliable !') % (all_accounts[0].name, all_accounts[0].code))

        #reconcile everything that can be
        remaining_moves = self.auto_reconcile_lines_custom(payment_info)

        #if writeoff_acc_id specified, then create write-off move with value the remaining amount from move in self
        if writeoff_acc_id and writeoff_journal_id and remaining_moves:
            all_aml_share_same_currency = all([x.currency_id == self[0].currency_id for x in self])
            writeoff_vals = {
                'account_id': writeoff_acc_id.id,
                'journal_id': writeoff_journal_id.id
            }
            if not all_aml_share_same_currency:
                writeoff_vals['amount_currency'] = False
            writeoff_to_reconcile = remaining_moves._create_writeoff(writeoff_vals)
            #add writeoff line to reconcile algo and finish the reconciliation
            remaining_moves = (remaining_moves + writeoff_to_reconcile).auto_reconcile_lines_custom(payment_info)
            return writeoff_to_reconcile
        return True
    
    # Disable auto-populating the debit/credit and Lable in the move line, if first line is entered.
    @api.model
    def default_get(self, fieldlist):
        res = super(AccountMoveLine, self).default_get(fieldlist)
        if self._context.get('line_ids'):
            debit_val = credit_val = 0
            name = False
            for line in self._context.get('line_ids'):
                if line[2]:
                    if 'debit' in line[2].keys():
                        debit_val += line[2]['debit']
                    if 'credit' in line[2].keys():
                        credit_val += line[2]['credit']
                    if 'name' in line[2].keys():
                        name = line[2]['name']
            if debit_val != credit_val:
                if debit_val > credit_val:
                    debit_val -= credit_val
                    credit_val = 0
                elif credit_val > debit_val:
                    credit_val -= debit_val
                    debit_val = 0
#                if name:
#                    res.update({'debit':credit_val, 'credit':debit_val, 'name':name})
#                else:
#                    res.update({'debit':credit_val, 'credit':debit_val})
#                
                res.update({'debit':0.0, 'credit':0.0, 'name':''})
        return res
    
    
class AccountMove(models.Model):
    _inherit = 'account.move'    
    
    @api.multi
    def post(self):

        invoice = self._context.get('invoice', False)
        print "context---------in--post--------",self._context
        self._post_validate()
        for move in self:
            move.line_ids.create_analytic_lines()
            
            payment_name = self._context.get('payment_name', False)
            if payment_name:
                move.name = payment_name
                
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
            print"Move Name: ",move.name
        return self.write({'state': 'posted'})