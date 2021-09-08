# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from odoo.exceptions import UserError

class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"
    
    @api.model
    def _default_date(self):
        if self.env.user.transaction_date:
            return self.env.user.transaction_date
        else:
            return fields.Datetime.now()
    
#    salesman_id = fields.Many2one('res.partner', string='Salesman',domain=[('is_salesman', '=', True)])
    salesman_id = fields.Many2one('res.users', string='Salesman')
    collector_id = fields.Many2one('res.partner', string='Collector',domain=[('is_collector', '=', True)])
    payment_date = fields.Date(string='Payment Date', default=_default_date, required=True, copy=False)
    invoice_type = fields.Selection([('normal', 'Normal Invoice'), ('sample', 'Sample Invoice')], string='Invoice Type',
                                     default='normal')
    exchange_rate = fields.Float(string='Exchange Rate', digits=dp.get_precision('Discount'))                                     
    local_amount = fields.Float(string='Local Payment Amount', digits=dp.get_precision('Discount'), help='Amount in Local Currency.')
    local_currency_id = fields.Many2one('res.currency', string='Currency')
    
    @api.onchange('local_amount')
    def onchange_local_amount(self):
        if self.local_amount:
            self.exchange_rate = float(self.amount) / float(self.local_amount or 1.0)
            
    @api.onchange('exchange_rate')
    def onchange_exchange_rate(self):
        if self.exchange_rate:
            self.local_amount = float(self.amount) / float(self.exchange_rate or 1.0)
                                     
class account_payment(models.Model):
    _inherit = "account.payment"
    
    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            currency_id = self.journal_id.currency_id or self.company_id.currency_id
#            if self.partner_type == 'supplier':
            if self.currency_id:
                currency_id = self.currency_id.id
            self.currency_id = currency_id
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
            return {'domain': {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods.ids)]}}
        return {}    
    
    # inhrited to add invoice type
    @api.model
    def default_get(self, fields):
        rec = super(account_payment, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            rec['payment_date'] = invoice['date_invoice']
            
            if invoice.get('currency_id',False) and invoice.get('company_currency_id',False):
                currency_id = invoice['currency_id'][0]
                company_currency_id = invoice['company_currency_id'][0]
                if currency_id != company_currency_id:
                    rec['local_currency_id'] = company_currency_id
#                rec['exchange_rate'] = invoice['exchange_rate']
                
        return rec

    # inherited to add invoice_type
    def _get_move_vals(self, journal=None):
        print"get move called: "
        """ Return dict to create the payment move
        """
        journal = journal or self.journal_id
        if not journal.sequence_id:
            raise UserError(_('Configuration Error !'), _('The journal %s does not have a sequence, please specify one.') % journal.name)
        if not journal.sequence_id.active:
            raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
        name = self.move_name or journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
        return {
            'name': name,
            'date': self.payment_date,
            'ref': self.communication or '',
            'company_id': self.company_id.id,
            'journal_id': journal.id,
            'salesman_id': self.salesman_id and self.salesman_id.id or False,
            'collector_id': self.collector_id and self.collector_id.id or False,
#            'invoice_type':self.invoice_type,
#            'exchange_rate':self.exchange_rate,
        }    
        
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        salesman_id = self.salesman_id and self.salesman_id.id or False
        if not self.invoice_type:   # to identify the Register payment or Direct Payment screen
            salesman_id = False
        if not salesman_id:
            if self.partner_id and self.partner_id.user_id:
                salesman_id = self.partner_id.user_id.id
        self.salesman_id = salesman_id
        return {}                
    
    # inherited to add auto reconcilation
    @api.multi
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconciliable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # Use the right sequence to set the name
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
            if not rec.name and rec.payment_type != 'transfer':
                raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})
            
            # Auto-reconcilation changes
            if rec.payment_type == 'inbound':
                account = rec.partner_id.property_account_receivable_id
                if account.auto_reconcile:
                    credit_aml = move.line_ids.filtered(lambda r: r.account_id.id == account.id)
                    credit = credit_aml.credit
                    print"credit: ",credit
                    credit_aml_ids = []
                    credit = 0
                    credit_aml_all = self.env['account.move.line'].search([('account_id','=',account.id),('credit','>',0.0),('reconciled','=',False)])
                    for l in credit_aml_all:
                        credit+=l.credit
                        credit_aml_ids.append(l.id)
                    credit_aml = self.env['account.move.line'].browse(credit_aml_ids)
                    print"credit11: ",credit


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

                    debit_aml = self.env['account.move.line'].browse(debit_aml_ids)
                    print"debit_aml: ",debit_aml

                    res = (credit_aml + debit_aml).reconcile()
                    print"after reconcile res: ",res
            
            
    def _create_payment_entry(self, amount):
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
        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        
        if self.payment_difference:
            print"yes payment  difference"
#        if diff_amount and not self.payment_difference:
##            move.write({'amount':move.amount+diff_amount})
##
##            gain_loss_account_id = self.env['account.account'].search(
##                [('name','=','Foreign Exchange Gain')])[0].id
#            foreign_exchange_profit_loss_accound_id = self.env['ir.values'].get_default('account.config.settings',
#                                                                'foreign_exchange_profit_loss_accound_id',
#                                                                company_id=self.company_id.id)
#            if not foreign_exchange_profit_loss_accound_id:
#                raise UserError(_('Please define Foreign Exchange Profit Loss Account in settings.'))
#            
#            # for difference amount create entry to Loss or gain account
#            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
#            writeoff_line['name'] = _('Exchange difference')
#            writeoff_line['move_id'] = move.id
##            writeoff_line['exchange_rate'] = self.exchange_rate
#            writeoff_line['exchange_rate'] = 0.0
#            writeoff_line['currency_id'] = currency_id
#            
#            if diff_amount > 0:
#                debit_wo = 0.0
#                credit_wo = diff_amount_local
#                amount_currency_wo = abs(diff_amount)
#                credit_account_id = foreign_exchange_profit_loss_accound_id
#                debit_account_id = self.destination_account_id.id
#                
#            else:
#                print"diff_amount_local: ",diff_amount_local
#                debit_wo = 0.0
#                credit_wo = abs(diff_amount_local)
#                amount_currency_wo = abs(diff_amount)
#                credit_account_id = self.destination_account_id.id
#                debit_account_id = foreign_exchange_profit_loss_accound_id
#                
#            # debit entry
#            writeoff_line['account_id'] = credit_account_id
#            writeoff_line['debit'] = debit_wo
#            writeoff_line['credit'] = credit_wo    
##            writeoff_line['amount_currency'] = -abs(amount_currency_wo)
#            writeoff_line['amount_currency'] = 0
#            writeoff_line_rec = aml_obj.create(writeoff_line)
#            print"debit entrny created"
##                
#            # credit entry
#            debit_wo = abs(diff_amount_local)
#            credit_wo = 0.0
#            writeoff_line['account_id'] = debit_account_id
#            writeoff_line['debit'] = debit_wo
#            writeoff_line['credit'] = credit_wo
##            writeoff_line['amount_currency'] = abs(amount_currency_wo)
#            writeoff_line['amount_currency'] = 0
#            writeoff_line = aml_obj.create(writeoff_line)
#            print"credit entry created"
#         

        #Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference:
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
        self.invoice_ids.register_payment(counterpart_aml)

        #Write counterpart lines
        if not self.currency_id != self.company_id.currency_id:
            amount_currency = 0
        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
        liquidity_aml_dict['exchange_rate'] = self.exchange_rate
        aml_obj.create(liquidity_aml_dict)

        move.post()
        return move
   


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: