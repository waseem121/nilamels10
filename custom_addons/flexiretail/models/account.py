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


class account_journal(models.Model):
    _inherit = "account.journal"

    pos_front_display = fields.Boolean('Display in POS Front', default=False)
    shortcut_key = fields.Char('Shortcut Key', size=1)
    debt = fields.Boolean(string='Debt Payment Method')
    apply_charges = fields.Boolean("Apply Charges");
    fees_amount = fields.Float("Fees Amount");
    fees_type = fields.Selection(selection=[('fixed','Fixed'),('percentage','Percentage')],string="Fees type", default="fixed")
    optional = fields.Boolean("Optional")
    is_cashdrawer = fields.Boolean("IS Cashdrawer")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('voucher'):
            if self._context.get('journal_ids') and self._context.get('journal_ids')[0][2]:
                args = [[u'id', u'in', self._context.get('journal_ids')[0][2]]]
                return super(account_journal, self).name_search(name, args=args, operator=operator, limit=limit)
            return False
        else:
            return super(account_journal, self).name_search(name, args=args, operator=operator, limit=limit)

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self._context.get('from_pos'):
            super(AccountBankStatementLine, self)._check_amount()

    @api.one
    @api.constrains('amount', 'amount_currency')
    def _check_amount_currency(self):
        if not self._context.get('from_pos'):
            super(AccountBankStatementLine, self)._check_amount_currency()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
