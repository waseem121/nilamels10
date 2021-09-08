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
from datetime import datetime, date
from openerp.exceptions import Warning


class cash_points(models.Model):
    _name = 'cash.points'

    @api.multi
    def get_total_cash_amount(self):
        '''compute total amount'''
        loyalty_group_obj = self.env['loyalty.group']
        for each in self:
            if each.customer_id:
                group_id = loyalty_group_obj.search([('type', '=', 'customer_group'),
                                                     ('customer_ids', 'in', each.customer_id.id)])
                if group_id:
                    if group_id.to_amount > 0.0 and group_id.points > 0.0:
                        rate = group_id.to_amount / group_id.points
                        each.cash_point_amt = each.cash_point * rate

    date = fields.Date(string="Date")
    customer_id = fields.Many2one('res.partner', string="Customer", required=True)
    points = fields.Float(compute="get_customer_remaining_points", string="Points")
    cash_point = fields.Float(string="Cash Point")
    approved_by = fields.Many2one('res.users', string="Approved by")
    approved_date = fields.Date(string="Approved Date")
    state = fields.Selection([('draft', 'Draft'),
                              ('approved', 'Approved'),
                              ('paid', 'Paid'),
                              ('cancel', 'Cancel')], default='draft', string="Status")
    cash_point_amt = fields.Float(compute='get_total_cash_amount', string="Total Cash Amount")
    account_move_id = fields.Many2one('account.move', string="Journal Entry")
#     account_move_line_ids = fields.One2many(related='account_move_id.line_id', string="Payments", readonly=True)

    @api.constrains('points', 'cash_point')
    def check_points_use_to(self):
        if self.cash_point > self.points:
            raise Warning(_('Value Error!'),
                          _("You can not enter cash points greater then Points."))

    @api.multi
    @api.depends('customer_id')
    def get_customer_remaining_points(self):
        for each in self:
            if each.customer_id and each.customer_id.remaining_points:
                each.points = each.customer_id.remaining_points

    @api.one
    def approve_cash_point(self):
        self.approved_by = self._uid
        self.approved_date = date.today()
        return self.write({"state": "approved"})

    @api.one
    def cancel_cash_point(self):
        return self.write({"state": "cancel"})

    @api.one
    def pay_cash_point(self):
        '''create journal entry for the cash out '''
        if not self.cash_point_amt:
            raise Warning("Total Cash Amount Should Be greater then Zero")

        act_move_obj = self.env['account.move']
        act_move_line_obj = self.env['account.move.line']
        journal_data = act_move_obj.default_get(['period_id', 'date'])
        journal_id = self.env['account.journal'].search([('type', '=', 'cash'), ('name', '=', 'Cash')], limit=1)
        journal_id = journal_id[0]
        account_id = self.env['res.users'].search([('id', '=', self._uid)]).company_id.cash_out_account_id.id
        if not account_id:
            raise Warning(_('Please, configure account for cash out into company configuration.'))
        journal_record = {
            'date': journal_data.get('date'),
            'journal_id': journal_id.id,
            'narration': False,
            'partner_id': self.customer_id.id,
            'period_id': journal_data.get('period_id'),
            'ref': False,
            'to_check': False
        }
        jour_entry_id = act_move_obj.create(journal_record)
        if jour_entry_id:
            jour_move_line = {
                'account_id': account_id,
                'amount_currency': 0,
                'analytic_account_id': False,
                'credit': 0,
                'currency_id': False,
                'date_maturity': datetime.strftime(date.today(), '%m/%d/%Y'),
                'debit': self.cash_point_amt,
                'move_id': jour_entry_id.id,
                'name': 'Cash Out',
                'partner_id': self.customer_id.id,
                'tax_amount': 0,
                'tax_code_id': False
            }
            act_move_line_obj.create(jour_move_line)
            jour_move_line = {
                'account_id': self.customer_id.property_account_payable.id,
                'amount_currency': 0,
                'analytic_account_id': False,
                'credit': self.cash_point_amt,
                'currency_id': False,
                'date_maturity': datetime.strftime(date.today(), '%m/%d/%Y'),
                'debit': 0,
                'move_id': jour_entry_id.id,
                'name': 'Cash Out',
                'partner_id': self.customer_id.id,
                'tax_amount': 0,
                'tax_code_id': False
            }
            act_move_line_obj.create(jour_move_line)

        '''cash out enrty into the customer'''
        red_points_data = {
                    'partner_id': self.customer_id.id,
                    'order_name':'Cash Out',
                    'pos_order_id': False,
                    'sale_id': False,
                    'amount_total': self.cash_point_amt,
                    'point': self.cash_point,
                }
        self.env['res.partner.point.redeem'].create(red_points_data)
        return self.write({"state": "paid", "account_move_id" : jour_entry_id.id})
