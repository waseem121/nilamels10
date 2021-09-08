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
import openerp.addons.decimal_precision as dp

class res_partner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def _get_debt(self):
        debt_account = self.env['account.account'].search([
            ('company_id', '=', self.env.user.company_id.id), ('code', '=', 'XDEBT')])
        debt_journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id), ('debt', '=', True)])
        if debt_account:
            self._cr.execute(
                """SELECT l.partner_id, SUM(l.debit - l.credit)
                FROM account_move_line l
                WHERE l.account_id = %s AND l.partner_id IN %s
                GROUP BY l.partner_id
                """,
                (debt_account.id, tuple(self.ids)))
    
            res = {}
            for partner in self:
                res[partner.id] = 0
            for partner_id, val in self._cr.fetchall():
                res[partner_id] += val

            if debt_journal:
                statements = self.env['account.bank.statement'].search(
                    [('journal_id', '=', debt_journal.id), ('state', '=', 'open')])
                if statements:
        
                    self._cr.execute(
                        """SELECT l.partner_id, SUM(l.amount)
                        FROM account_bank_statement_line l
                        WHERE l.statement_id IN %s AND l.partner_id IN %s
                        GROUP BY l.partner_id
                        """,
                        (tuple(statements.ids), tuple(self.ids)))
                    for partner_id, val in self._cr.fetchall():
                        res[partner_id] += val
                for partner in self:
                    partner.debt = res[partner.id]

    @api.one
    @api.depends('wallet_lines')
    def _calc_remaining(self):
        total = 0.00
        for s in self:
            for line in s.wallet_lines:
                total += line.credit - line.debit
        self.remaining_wallet_amount = total;

    @api.multi
    def _compute_remain_credit_limit(self):
        for partner in self:
            total_credited = 0
            orders = self.env['pos.order'].search([('partner_id', '=', partner.id),
                                                   ('state', '=', 'draft')])
            for order in orders:
                total_credited += order.amount_due
            partner.remaining_credit_limit = partner.credit_limit - total_credited

    debt = fields.Float(
        compute='_get_debt', string='Debt', readonly=True,
        digits=dp.get_precision('Account'), help='This debt value for only current company')
    wallet_lines = fields.One2many('wallet.management', 'customer_id', string="Wallet", readonly=True)
    remaining_wallet_amount = fields.Float(compute="_calc_remaining",string="Remaining Amount", readonly=True, store=True)
    prefer_ereceipt = fields.Boolean('Prefer E-Receipt')
    remaining_credit_limit = fields.Float("Remaining Credit Limit", compute="_compute_remain_credit_limit", default=0)

    @api.model
    def create_from_ui(self, partner):
        if partner.get('property_product_pricelist'):
            price_list_id = int(partner.get('property_product_pricelist'))
            partner.update({'property_product_pricelist': price_list_id})
        return super(res_partner, self).create_from_ui(partner)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: