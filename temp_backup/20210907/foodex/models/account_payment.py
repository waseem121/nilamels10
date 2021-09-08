# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"

    @api.model
    def _default_date(self):
        if self.env.user.transaction_date:
            return self.env.user.transaction_date
        else:
            return fields.Datetime.now()    
    
    payment_date = fields.Date(string='Payment Date', default=_default_date, required=True, copy=False)
    invoice_type = fields.Selection([('normal', 'Normal Invoice'), 
                        ('sample', 'Sample Invoice'),
                        ('transfer_invoice', 'Transfer Invoice'),
                        ('veg_invoice', 'Vegetable Invoice')], string='Invoice Type',
                                     default='')
                                     
#class ManualReconcilationLines(models.Model):
#    _name = "manual.reconcilation.lines"
#    
#    name = fields.Date(string='Name')
#    payment_id = fields.Many2one('account.payment', string="Payment")
#    invoice_id = fields.Many2one('account.invoice', string="Invoice", readonly=True)
#    date = fields.Date(string='Date', readonly=True)
#    amount_total = fields.Float(string="Total", readonly=True)
#    reconciled_amount = fields.Float(string="Reconciled Amount", readonly=True)
#    balance = fields.Float(string="Balance")
    
    
class account_payment(models.Model):
    _inherit = "account.payment"
    
#    manual_reconcilation_lines = fields.One2many('manual.reconcilation.lines', 'payment_id', string='Reconcilation Lines')

    # inhrited to add invoice type
    @api.model
    def default_get(self, fields):
        rec = super(account_payment, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            rec['invoice_type'] = invoice['invoice_type']
            rec['salesman_id'] = invoice['user_id']
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
        print"get move vals salesmand_id: ",self.salesman_id
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
            'invoice_type':self.invoice_type,
            'receipt_no': self.receipt_no or '',
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
#        self.manual_reconcilation_lines = [(2, move.id) for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)]
#        value = {}
#        lines = []
#        if self.partner_id:
#            invoices = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id),
#                        ('state','=','open')])
#            for inv in invoices:
#                reconciled_amount = 0.0
#                for payment in inv.payment_move_line_ids:
#                    if inv.type in ('out_invoice', 'in_refund'):
#                        reconciled_amount += sum([p.amount for p in payment.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids])
##                        new_lines = [p for p in payment.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids]
#                        
##                    elif self.type in ('in_invoice', 'out_refund'):
##                        amount += sum([p.amount for p in payment.matched_credit_ids if p.credit_move_id in inv.move_id.line_ids])
#
#                        
#                
#                lines.append((0,0,{'invoice_id':inv.id,
#                        'date':inv.date_invoice,
#                        'amount_total':inv.amount_total,
#                        'reconciled_amount':reconciled_amount,
#                        'balance':inv.amount_total - reconciled_amount
#                        }))
#            value.update(manual_reconcilation_lines=lines)
#        
#        return {'value':value}
#    
#    @api.multi
#    def manual_reconcile(self):
#        print"manual_reconcile called: ",self
#        for line in self.manual_reconcilation_lines:
#            credit_aml_all = []
#            inv = line.invoice_id
#            print"inv: ",inv
#            credit = line.balance
#            for aml in inv.move_id.line_ids:
#                credit_aml_all.extend([r.debit_move_id for r in aml.matched_debit_ids] if aml.credit > 0 else [r.credit_move_id for r in aml.matched_credit_ids])
#                
#            debit_aml_all = self.env['account.move.line'].search([('account_id','=',inv.account_id.id),('debit','>',0.0),('reconciled','=',False)])
#            debit_aml_ids = []
#            debit = 0.0
#            skip = False
#            for l in debit_aml_all:
#                debit += l.debit
#                if skip:
#                    continue
#                debit_aml_ids.append(l.id)
#                if credit <=debit:
#                    skip=True
#            print"debit: ",debit
#            print"credit_aml_all: ",credit_aml_all
#
#            debit_aml = self.env['account.move.line'].browse(debit_aml_ids)
#            print"debit_aml: ",debit_aml
#            ee
#            res = (credit_aml_all + debit_aml).reconcile()
#            print"after reconcile res: ",res
            
                
            
        
        
#        action = self.env.ref('foodex.action_invoice_reconcile_foodex').read()[0]
#        invoice_ids = []
#        invoice_ids = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id)])
#                
#        action['domain'] = [('id', 'in', tuple(invoice_ids.ids))]
#        return action
        


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: