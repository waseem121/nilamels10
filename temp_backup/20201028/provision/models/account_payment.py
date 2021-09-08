# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ManualReconcilationLines(models.Model):
    _name = "manual.reconcilation.lines"
    
    name = fields.Date(string='Name')
    payment_id = fields.Many2one('account.payment', string="Payment")
    invoice_id = fields.Many2one('account.invoice', string="Invoice", readonly=True)
    date = fields.Date(string='Date', readonly=True)
    amount_total = fields.Float(string="Total", readonly=True)
    reconciled_amount = fields.Float(string="Reconciled Amount", readonly=True)
    balance = fields.Float(string="Balance")

class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    manual_reconcilation_lines = fields.One2many('manual.reconcilation.lines', 'payment_id', string='Reconcilation Lines')
    
    # inherited to add sequence based on Journal
    @api.multi
    def post(self):
        name = self.name
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

        return res
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
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
            invoices = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id),
                        ('state','=','open')])
            for inv in invoices:
                reconciled_amount = 0.0
                for payment in inv.payment_move_line_ids:
                    if inv.type in ('out_invoice', 'in_refund'):
                        reconciled_amount += sum([p.amount for p in payment.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids and p.reconciled!=True])
                
                lines.append((0,0,{'invoice_id':inv.id,
                        'date':inv.date_invoice,
                        'amount_total':inv.amount_total,
                        'reconciled_amount':reconciled_amount,
                        'balance':inv.amount_total - reconciled_amount
                        }))
            value.update(manual_reconcilation_lines=lines)
        
        return {'value':value}
    
    @api.multi
    def manual_reconcile(self):
        print"manual_reconcile called: ",self
        account_id = self.partner_id.property_account_receivable_id.id
        for line in self.manual_reconcilation_lines:
            credit_aml_all = []
            inv = line.invoice_id
            print"inv: ",inv
            credit = line.balance
            print"credit: ",credit
            credit_aml_all = inv.move_id.line_ids.filtered(lambda r: r.account_id.id == account_id)
#            for aml in inv.move_id.line_ids:
#                credit_aml_all.extend([r.debit_move_id for r in aml.matched_debit_ids] if aml.credit > 0 else [r.credit_move_id for r in aml.matched_credit_ids])
                
            debit_aml_all = self.env['account.move.line'].search([('account_id','=',inv.account_id.id),('debit','>',0.0),('reconciled','=',False)])
            debit_aml_ids = []
            debit = 0.0
            skip = False
            for l in debit_aml_all:
                debit += l.debit
                if skip:
                    continue
                debit_aml_ids.append(l.id)
                if credit <=debit:
                    skip=True
            print"debit: ",debit
            print"credit_aml_all: ",credit_aml_all

            debit_aml = self.env['account.move.line'].browse(debit_aml_ids)
            print"debit_aml: ",debit_aml
            ee
            res = (credit_aml_all + debit_aml).reconcile()
            print"after reconcile res: ",res
    