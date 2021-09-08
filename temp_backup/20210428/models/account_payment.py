# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import openerp.addons.decimal_precision as dp

class ManualReconcilationLines(models.Model):
    _name = "manual.reconcilation.lines"
    
    name = fields.Date(string='Name')
    payment_id = fields.Many2one('account.payment', string="Payment")
    invoice_id = fields.Many2one('account.invoice', string="Invoice", readonly=True)
    date = fields.Date(string='Date', readonly=True)
    amount_total = fields.Float(string="Total", readonly=True ,digits=dp.get_precision('Discount'))
    draft_amount = fields.Float(string="Draft Amount", readonly=True ,digits=dp.get_precision('Discount'))
    reconciled_amount = fields.Float(string="Reconciled Amount", readonly=True, digits=dp.get_precision('Discount'))
    balance = fields.Float(string="Balance", readonly=True, digits=dp.get_precision('Discount'))
    amount_to_reconcile = fields.Float(string="Amount to Reconcile", digits=dp.get_precision('Discount'))
    debit_line_id = fields.Many2one('account.move.line', readonly=True, string='Voucher')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('sent', 'Sent'),
        ('reconciled', 'Reconciled')
    ], related='payment_id.state', string='State', readonly=True, copy=False, store=True, default='draft')
    
    @api.onchange('amount_to_reconcile')
    def _onchange_amount_to_reconcile(self):
        print"_onchange_amount_to_reconcile calledddddd"
        print"self.amount_to_reconcile: ",self.amount_to_reconcile
        print"self.balance: ",self.balance
        if self.amount_to_reconcile and self.balance:
            if self.amount_to_reconcile > self.balance:
                self.amount_to_reconcile = self.balance
                msg = 'Amount to reoncile should be less than Balance amount ie : '+str(self.balance)
                raise ValidationError(_(msg))
            

class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    manual_reconcilation_lines = fields.One2many('manual.reconcilation.lines', 'payment_id', string='Reconcilation Lines')
#    reconciled = fields.Boolean(string='Reconciled', help='Field to hide/show the Manual reconcilation button.')
    payment_mode = fields.Selection([
            ('abk', 'ABK Online'),
            ('knet', 'KNET'),
            ('cheque', 'Cheque'),
            ('bank_transfer', 'Bank Transfer'),
            ('internal_transfer', 'Internal Transfer'),
            ('payment', 'Payment'),
        ])
    cheque_no = fields.Char(string='Cheque No')
    cheque_date = fields.Date(string='Cheque Date')

    @api.one
    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id','manual_reconcilation_lines')
    def _compute_payment_difference(self):
        if 'active_model' in self._context.keys():
            if len(self.invoice_ids) == 0:
                return
            if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
                self.payment_difference = self.amount - self._compute_total_invoices_amount()
            else:
                self.payment_difference = self._compute_total_invoices_amount() - self.amount
        else:
            amount_to_reconcile = 0.0
            for l in self.manual_reconcilation_lines:
                amount_to_reconcile += l.amount_to_reconcile
            
            self.payment_difference = self.amount - amount_to_reconcile
    
    # to remove generating sequence
    # inherited to add invoice_type
    def _get_move_vals(self, journal=None):
        print"P get move called: "
        """ Return dict to create the payment move
        """
        journal = journal or self.journal_id
        if not journal.sequence_id:
            raise UserError(_('Configuration Error !'), _('The journal %s does not have a sequence, please specify one.') % journal.name)
        if not journal.sequence_id.active:
            raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
#        name = self.move_name or journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
        return {
#            'name': name,
            'date': self.payment_date,
            'ref': self.communication or '',
            'company_id': self.company_id.id,
            'journal_id': journal.id,
            'salesman_id': self.salesman_id and self.salesman_id.id or False,
            'collector_id': self.collector_id and self.collector_id.id or False,
#            'invoice_type':self.invoice_type,
#            'exchange_rate':self.exchange_rate,
        }
    
    @api.model
    def create(self, vals):
        journal_id = vals.get('journal_id',False)
        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
        
            if journal.sequence_id:
                sequence = journal.sequence_id
                name = sequence.with_context(ir_sequence_date=vals['payment_date']).next_by_id()
                vals['name'] = name
            else:
                raise UserError(_('Please define a sequence on the journal.'))
            
        res = super(AccountPayment, self).create(vals)
        return res
    
    # inherited to add sequence based on Journal
    @api.multi
    def post(self):
        name = self.name
        self = self.with_context(payment_name=self.name)
        res = super(AccountPayment, self).post()
        # get sequence from the voucher
        voucher_lines = self.env['account.move.line'].search([('payment_id','=',self.id)])
        if voucher_lines:
            name = voucher_lines[0].move_id.name
        
        for rec in self:
            if not name:
                journal = rec.journal_id
                if journal.sequence_id:
                    sequence = journal.sequence_id
                    name = sequence.with_context(ir_sequence_date=rec.payment_date).next_by_id()
                else:
                    raise UserError(_('Please define a sequence on the journal.'))
            rec.name = name
        self.manual_reconcile()    #TODO uncomment this
        return res
    

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        print"self: ",self
        print"self origin: ",self._origin
        old_lines = []
        if self._origin:
            if self._origin.manual_reconcilation_lines:
                old_lines = self._origin.manual_reconcilation_lines
            
        salesman_id = self.salesman_id and self.salesman_id.id or False
        if not self.invoice_type:   # to identify the Register payment or Direct Payment screen
            salesman_id = False
        if not salesman_id:
            if self.partner_id and self.partner_id.user_id:
                salesman_id = self.partner_id.user_id.id
        self.salesman_id = salesman_id
#        self.manual_reconcilation_lines = [(2, move.id) for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)]
        value = {}
        lines = []
        if self.partner_id:
            RecLines = self.env['manual.reconcilation.lines']
            if self.payment_type=='inbound':
                if self.partner_id.property_account_receivable_id:
                    debit_move_lines = self.env['account.move.line'].search([
                                ('account_id','=',self.partner_id.property_account_receivable_id.id),
                                ('debit','>',0)], order='date DESC')

                                
                    for debit_line in debit_move_lines:

                        if debit_line.reconciled:
                            continue
                        
                        domain = [('payment_id.state','=','draft'),
                                    ('payment_id.partner_id','=',self.partner_id.id),
                                    ('debit_line_id','=',debit_line.id)
                                ]
                        draft_lines = RecLines.search(domain)
                        
                        draft_amount = sum(draft_lines.mapped('amount_to_reconcile'))
                        reconciled_amount = debit_line.debit_cash_basis or 0.0
                        print"reconciled_amount: ",reconciled_amount
                        
                        if len(old_lines):
                            for l in old_lines:
                                if l.debit_line_id.id == debit_line.id:
                                    draft_amount -= l.amount_to_reconcile

                        # means fully reconciled
                        balance = (debit_line.debit - reconciled_amount) - draft_amount
                        if balance <= 0.0:
                            continue

                        lines.append((0,0,{
        #                        'invoice_id':False,
                                'debit_line_id': debit_line.id,
                                'date':debit_line.move_id.date,
                                'amount_total':debit_line.move_id.amount,
                                'draft_amount':draft_amount,
                                'reconciled_amount':reconciled_amount,
                                'balance': balance
                                }))

                    value.update(manual_reconcilation_lines=lines)
                    
            if self.payment_type=='outbound':
                if self.partner_id.property_account_payable_id:
                    credit_move_lines = self.env['account.move.line'].search([
                                ('account_id','=',self.partner_id.property_account_payable_id.id),
                                ('credit','>',0)], order='date DESC')
                    for credit_line in credit_move_lines:

                        if credit_line.reconciled:
                            continue
                        domain = [('payment_id.state','=','draft'),
                                ('payment_id.partner_id','=',self.partner_id.id),
                                ('debit_line_id','=',credit_line.id)
                                ]
                        draft_lines = RecLines.search(domain)
                        
                        draft_amount = sum(draft_lines.mapped('amount_to_reconcile'))
                        reconciled_amount = credit_line.credit_cash_basis or 0.0
                        
                        if len(old_lines):
                            for l in old_lines:
                                if l.debit_line_id.id == credit_line.id:
                                    draft_amount -= l.amount_to_reconcile

                        # means fully reconciled
                        balance = (credit_line.credit - reconciled_amount) - draft_amount
                        if balance <= 0.0:
                            continue

                        lines.append((0,0,{
        #                        'invoice_id':False,
                                'debit_line_id': credit_line.id,
                                'date':credit_line.move_id.date,
                                'amount_total':credit_line.move_id.amount,
                                'draft_amount':draft_amount,
                                'reconciled_amount':reconciled_amount,
                                'balance': balance
                                }))

                    value.update(manual_reconcilation_lines=lines)
                    
        return {'value':value}
    
    
    @api.multi
    def manual_reconcile(self):
        res = ''
        total_amount = self.amount
        amount_to_reconcile = sum(self.manual_reconcilation_lines.mapped('amount_to_reconcile'))
        if amount_to_reconcile > total_amount:
            msg = 'You can not enter Amount to Reconcile more than Payment Amount : '+str(self.amount)
            raise ValidationError(_(msg))
        
        account_id = False
        if self.payment_type=='inbound':
            account_id = self.partner_id.property_account_receivable_id.id
        if self.payment_type=='outbound':
            account_id = self.partner_id.property_account_payable_id.id
        if not account_id:
            return True
        
        total_diff = 0.0
        if self.payment_difference == 0 and self.payment_difference_handling == 'reconcile':
            total_diff = sum(self.manual_reconcilation_lines.mapped('balance')) - sum(self.manual_reconcilation_lines.mapped('amount_to_reconcile'))
        print"total_diff: in Rec ",total_diff
        
        domain = [('payment_id','in',self.ids),
                ('account_id','=',account_id)]
        if total_diff:
            domain.append(('name','!=','Rebate'))
        print"domain old: ",domain
        credit_lines = self.env['account.move.line'].search(domain)
#        print"credit_lines: ",credit_lines
        for line in self.manual_reconcilation_lines:
            if line.amount_to_reconcile == 0.0:
                print"continue"
                continue
            payment_info = {}
            debit_line_id = line.debit_line_id
            payment_info[debit_line_id.id] = line.amount_to_reconcile
            payment_info['payment_type'] = self.payment_type

            sum_credit = credit_lines.mapped('credit')
            print"sum_credit: ",sum_credit
            sum_debit = debit_line_id.mapped('debit')
            print"sum_debit: ",sum_debit

            print"credit_lines: ",credit_lines
            print"debit_line_id: ",debit_line_id
            print"before reconcile"
            res = (credit_lines + debit_line_id).reconcile_custom(False,False,payment_info)
            
        # New change
        print"newwwwwwwwwwwwwwwwwwwwwwwwwwwww reconcilation"
        if total_diff and self.payment_difference_handling == 'reconcile':
            print"inside ifffff rec"
            print"account_id Ref: ",account_id
            domain = [('payment_id','in',self.ids),
                    ('account_id','=',account_id)]
            if total_diff:
                domain.append(('name','=','Rebate'))
            print"domain: ",domain
            credit_lines = self.env['account.move.line'].search(domain)
#            print"credit_lines: inside Rec ",credit_lines
            
            for line in self.manual_reconcilation_lines:
                if line.amount_to_reconcile == 0.0:
                    print"continue Rec"
                    continue
                payment_info = {}
                debit_line_id = line.debit_line_id
                payment_info[debit_line_id.id] = line.balance - line.amount_to_reconcile
                payment_info['payment_type'] = self.payment_type

                sum_credit = credit_lines.mapped('credit')
                print"sum_credit: ",sum_credit
                sum_debit = debit_line_id.mapped('debit')
                print"sum_debit: ",sum_debit
                
                res = (credit_lines + debit_line_id).reconcile_custom(False,False,payment_info)
                print("afater reconciled: New")
            
            
        print("afater reconciled: ")
#        ee
        self.write({'state':'reconciled'})
        return res


    @api.multi
    def unreconcile_custom(self):
        account_id = False
        if self.payment_type=='inbound':
            account_id = self.partner_id.property_account_receivable_id.id
        if self.payment_type=='outbound':
            account_id = self.partner_id.property_account_payable_id.id
        if not account_id:
            return True
        
        credit_lines = self.env['account.move.line'].search([('payment_id','in',self.ids),
                ('account_id','=',account_id)])
        
        credit_aml_ids = credit_lines.ids
        debit_aml_ids = []
        for line in self.manual_reconcilation_lines:
            if line.amount_to_reconcile == 0.0:
                continue
            debit_aml_ids.append(line.debit_line_id.id)


        move_line_ids = credit_aml_ids + debit_aml_ids
        if len(move_line_ids):
            move_line_ids = list(set(move_line_ids))
            self.env['account.move.line'].browse(move_line_ids).remove_move_reconcile()
            self.write({'state':'posted'})
            
        return True    
    
    # before cancelling Un-Reconcile the entries
    @api.multi
    def cancel(self):
        self.unreconcile_custom()
        return super(AccountPayment, self).cancel()
        

    
    # inherited to use account selected in the Payment screen
    def _create_payment_entry(self, amount):
        print"provision _create_payment_entry called"
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            #if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)
        
        diff_amount = 0.0
        if self.partner_type == 'supplier':
            if self.company_id and self.company_id.currency_id.id:
                if self.currency_id.id != self.company_id.currency_id.id:
                    new_local_amount = self.local_amount * (self.payment_type in ('outbound', 'transfer') and 1 or -1)
                    debit = new_local_amount
                    
#                    invoice_amount = self.invoice_ids[0].amount_total / (self.invoice_ids[0].exchange_rate or 1.0)
                    invoice_amount = self.invoice_ids[0].residual / (self.invoice_ids[0].exchange_rate or 1.0)
                    diff_amount_local = invoice_amount - new_local_amount
                    diff_amount = diff_amount_local * self.exchange_rate

        if self.partner_type == 'customer':
            if self.company_id and self.company_id.currency_id.id:
                if self.currency_id.id != self.company_id.currency_id.id:
                    if self.invoice_ids[0].type=='out_invoice':
                        new_local_amount = self.local_amount * (self.payment_type in ('inbound') and 1 or -1)
                        credit = new_local_amount
                    elif self.invoice_ids[0].type=='out_refund':
                        new_local_amount = self.local_amount * (self.payment_type in ('outbound') and 1 or -1)
                        debit = new_local_amount
                        
                    invoice_amount = self.invoice_ids[0].residual / (self.invoice_ids[0].exchange_rate or 1.0)
                    
                    diff_amount_local = invoice_amount - new_local_amount
                    diff_amount = diff_amount_local * self.exchange_rate
#                    amount_currency = diff_amount + amount

        move = self.env['account.move'].create(self._get_move_vals())
        
        #Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml_dict.update({'exchange_rate': self.exchange_rate})
        print"counterpart_aml_dict: ",counterpart_aml_dict
        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        
        if self.payment_difference:
            print"yes payment  difference"

        total_diff = 0.0
        if self.payment_difference == 0 and self.payment_difference_handling == 'reconcile':
            total_diff = sum(self.manual_reconcilation_lines.mapped('balance')) - sum(self.manual_reconcilation_lines.mapped('amount_to_reconcile'))
            print"total_diff: ",total_diff
            
        #Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and (self.payment_difference or total_diff):
            if 'active_model' in self._context.keys():
                # called from invoice register payment
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id, invoice_currency)[2:]
                # the writeoff debit and credit must be computed from the invoice residual in company currency
                # minus the payment amount in company currency, and not from the payment difference in the payment currency
                # to avoid loss of precision during the currency rate computations. See revision 20935462a0cabeb45480ce70114ff2f4e91eaf79 for a detailed example.
                total_residual_company_signed = sum(invoice.residual_company_signed for invoice in self.invoice_ids)
                total_payment_company_signed = self.currency_id.with_context(date=self.payment_date).compute(self.amount, self.company_id.currency_id)
                if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
                    amount_wo = total_payment_company_signed - total_residual_company_signed
                else:
                    amount_wo = total_residual_company_signed - total_payment_company_signed
                # Align the sign of the secondary currency writeoff amount with the sign of the writeoff
                # amount in the company currency
                if amount_wo > 0:
                    debit_wo = amount_wo
                    credit_wo = 0.0
                    amount_currency_wo = abs(amount_currency_wo)
                else:
                    debit_wo = 0.0
                    credit_wo = -amount_wo
                    amount_currency_wo = -abs(amount_currency_wo)
                writeoff_line['name'] = _('Counterpart')
                writeoff_line['account_id'] = self.writeoff_account_id.id
                writeoff_line['debit'] = debit_wo
                writeoff_line['credit'] = credit_wo
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id
                writeoff_line = aml_obj.create(writeoff_line)
                if counterpart_aml['debit']:
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit']:
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo
            else:
                # called from Payment Screen
                if self.payment_type == 'inbound' and not total_diff:
                    writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                    writeoff_line['name'] = _('Counterpart')
                    writeoff_line['account_id'] = self.writeoff_account_id.id
                    writeoff_line['debit'] = 0.0
                    writeoff_line['credit'] = self.payment_difference or 0.0
                    writeoff_line['payment_id'] = counterpart_aml_dict['payment_id']
                    writeoff_line['amount_currency'] = 0.0
                    writeoff_line['currency_id'] = currency_id
                    writeoff_line = aml_obj.create(writeoff_line)
                    counterpart_aml['credit'] = counterpart_aml.credit - (self.payment_difference or 0.0)
                
                if self.payment_type == 'inbound' and total_diff:
                    print"yeeeeeeeeeeeeeeeeeeeeeeee"
                    writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                    writeoff_line['name'] = _('Rebate')
                    writeoff_line['account_id'] = counterpart_aml_dict['account_id']
                    writeoff_line['debit'] = 0.0
                    writeoff_line['credit'] = total_diff
                    writeoff_line['payment_id'] = counterpart_aml_dict['payment_id']
                    writeoff_line['amount_currency'] = 0.0
                    writeoff_line['currency_id'] = currency_id
                    
                    writeoff_line = aml_obj.create(writeoff_line)
#                    print"counterpart_aml Account: ",counterpart_aml.account_id
#                    print"counterpart_aml Debit: ",counterpart_aml.debit
#                    print"counterpart_aml Credit: ",counterpart_aml.credit
                
                    
        self.invoice_ids.register_payment(counterpart_aml)

        #Write counterpart lines
        if not self.currency_id != self.company_id.currency_id:
            amount_currency = 0
        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
        liquidity_aml_dict['exchange_rate'] = self.exchange_rate
#        print"liquidity_aml_dict before: ",liquidity_aml_dict
        if self.account_id:
            liquidity_aml_dict['account_id'] = self.account_id.id
            
        if self.payment_difference_handling == 'reconcile' and total_diff and self.payment_type == 'inbound' and not 'active_model' in self._context.keys():
            print"in last conditions"
            new_liq = liquidity_aml_dict.copy()
            new_liq['debit'] = total_diff
            new_liq['credit'] = 0.0
            new_liq['account_id'] = self.writeoff_account_id.id
#            print"last new_liq: ",new_liq
            aml_obj.create(new_liq)
            
        print"last liquidity_aml_dict: ",liquidity_aml_dict
        aml_obj.create(liquidity_aml_dict)
        move.post()
        return move    
    
class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"    
    
    account_id = fields.Many2one('account.account', string='Account',domain=[('is_bank', '=', True)],
        help='This account will be used when payment is posted')
    journal_type = fields.Selection('Journal Type', related='journal_id.type')
#    amount = fields.Monetary(string='Payment Amount', required=True)
#    amount = fields.Float(string="Payment Amount", required=True ,
#        digits=dp.get_precision('Discount'))

#
#    @api.multi
#    def manual_reconcile(self):
#        print"manual_reconcile called: ",self
#        
#        total_amount = self.amount
#        amount_to_reconcile = sum(self.manual_reconcilation_lines.mapped('amount_to_reconcile'))
#        if amount_to_reconcile > total_amount:
#            msg = 'You can not enter Amount to Reconcile more than Payment Amount : '+str(self.amount)
#            raise ValidationError(_(msg))
#        
#        
#        account_id = self.partner_id.property_account_receivable_id.id
#        debit_aml_ids = []
#        credit_aml_ids = []
#        
#        credit_lines = self.env['account.move.line'].search([('payment_id','in',self.ids),
#                ('account_id','=',account_id)])
#        print"credit_lines: ",credit_lines
#        print"credit_lines credit: ",credit_lines.credit
#        eee
#        
#        for line in self.manual_reconcilation_lines:
#            credit_aml_all = []
#            inv = line.invoice_id
#            print"inv: ",inv
#            debit = line.amount_to_reconcile
#            print"debit: ",debit
#            debit_aml_all = inv.move_id.line_ids.\
#                filtered(lambda r: r.account_id.id == account_id)
#            print"debit_aml_all: ",debit_aml_all
#            debit_aml_ids.append(debit_aml_all.id)
#            
##            for aml in inv.move_id.line_ids:
##                credit_aml_all.extend([r.debit_move_id for r in aml.matched_debit_ids] if aml.credit > 0 else [r.credit_move_id for r in aml.matched_credit_ids])
#                
#            credit_aml_all = self.env['account.move.line'].search([
#                                    ('account_id','=',inv.account_id.id),
#                                    ('credit','>',0.0),('reconciled','=',False)
#                                ],order="date ASC")
#                                
#            print"credit_aml_all: ",credit_aml_all
#            
#            for credit_aml in credit_aml_all:
#                print"credit_aml: Credit: ",credit_aml.credit
#                print"credit_aml: Credit move_id: ",credit_aml.move_id
#                total_amount -= credit_aml.credit
#                credit_aml_ids.append(credit_aml.id)
#                if total_amount <=0:
#                    break
#        
#        debit_aml_ids = list(set(debit_aml_ids))
#        credit_aml_ids = list(set(credit_aml_ids))
#        
#        debit_aml_all = self.env['account.move.line'].browse(debit_aml_ids)
#        credit_aml_all = self.env['account.move.line'].browse(credit_aml_ids)
#        print"debit_aml_all: ",debit_aml_all
#        print"credit_aml_all: ",credit_aml_all
#        ee
#        
##        res = (credit_aml_all + debit_aml_all).reconcile()
#        res = (credit_aml_all + debit_aml_all).reconcile_custom(payment_info)
#        print("afater reconciled: ")
#        return res
    
