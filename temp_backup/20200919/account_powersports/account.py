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

from odoo import fields, models, api
from odoo.tools.amount_to_text_en import amount_to_text
import odoo.addons.decimal_precision as dp


class account_move(models.Model):
    _inherit = "account.move"
    
    @api.one
    def get_total_debit(self):
        debit = 0.0
        for m in self.line_ids:
            if m.debit:
                debit += m.debit
        return debit
    
    @api.one
    def get_total_credit(self):
        credit = 0.0
        for m in self.line_ids:
            if m.credit:
                credit += m.credit
        return credit

    @api.one
    def get_amount_word(self):
        debit_amount = 0.0
        credit_amount = 0.0
        amount = 0.0
        for line in self.line_ids:
            debit_amount += line.debit
            credit_amount += line.credit
        if debit_amount == credit_amount:
            amount = debit_amount
        amount_text = amount_to_text(amount, currency=self.company_id.currency_id.name)
        if self.company_id.currency_id.name == 'KWD':
            amount_text = amount_text.replace('Cent', 'Fills')
            amount_text = amount_text.replace('Cents', 'Fills')
            amount_text = amount_text.replace('Filss', 'Fills')
        if amount_text:
            return str(amount_text)

    @api.multi
    @api.depends('line_ids.debit', 'line_ids.credit')
    def _amount_compute(self):
        for move in self:
            total = 0.0
            for line in move.line_ids:
                total += line.debit
            move.amount = total

    amount = fields.Float(compute='_amount_compute', store=True, digits=dp.get_precision('Credit Debit Value'))


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def default_get(self, fieldlist):
        res = super(account_move_line, self).default_get(fieldlist)
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
                if name:
                    res.update({'debit':credit_val, 'credit':debit_val, 'name':name})
                else:
                    res.update({'debit':credit_val, 'credit':debit_val})
        return res

    @api.onchange('account_id')
    def onchange_account_id(self):
        if self.account_id.currency_id and self.account_id.currency_id.id != self.env.user.company_id.currency_id.id:
            self.currency_id = self.account_id.currency_id.id
            

    debit = fields.Float(default=0.0, currency_field='company_currency_id', digits=dp.get_precision('Credit Debit Value'))
    credit = fields.Float(default=0.0, currency_field='company_currency_id', digits=dp.get_precision('Credit Debit Value'))
    exchange_rate = fields.Float(default=0.0, digits=dp.get_precision('Credit Debit Value'))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
