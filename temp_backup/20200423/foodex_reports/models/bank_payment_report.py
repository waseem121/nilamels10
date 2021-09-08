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

from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import date,datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta


# class account_move(models.Model):
#     _inherit = 'account.move'
#
#     @api.multi
#     @api.onchange('date')
#     def onchange_date(self):
#         print "\n\n onchange cal--------",self.date
#         self.date = datetime.strptime(self.date,DF) + relativedelta(months=2)


class BankPaymentReport(models.TransientModel):
    _name = "bank.payment.report"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    journal_id = fields.Many2one('account.journal', string="Journal")
    collector_id = fields.Many2one('res.partner',string="Collector")
    salesman_id = fields.Many2one('res.users', string="Salesman")

    @api.multi
    def action_report_bank_payment(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'date_from': self.date_from,
            'date_to':self.date_to,
            'journal_id':self.journal_id.id,
            'salesman_id':self.salesman_id.id if self.salesman_id else False,
            'collector_id':self.collector_id.id if self.collector_id else False
        }
        return self.env['report'].get_action(self, 'foodex_reports.bankpayment_report_template', data=datas)


class ReportBankPayment(models.AbstractModel):
    _name = 'report.foodex_reports.bankpayment_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        journal_ids = False
        if self._context.get('from_cashpayment'):
            journal_ids = self.env['account.journal'].search([('is_cpv','=',True)])
        if self._context.get('from_bankpayment'):
            journal_ids = self.env['account.journal'].search([('is_bpv', '=', True)])
        domain = [('date', '>=', data.get('date_from')),('date', '<=', data.get('date_to')), ('journal_id', 'in', journal_ids.ids)]
        if data.get('salesman_id'):
            domain.append(('salesman_id','=',data.get('salesman_id')))
        if data.get('collector_id'):
            domain.append(('collector_id','=',data.get('collector_id')))
        account_move_ids = self.env['account.move'].sudo().search(domain,order="date,journal_id")
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.bankpayment_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': account_move_ids if account_move_ids else False,
            'from_cashpayment':self._context.get('from_cashpayment'),
            'from_bankpayment':self._context.get('from_bankpayment'),
        }
        return report_obj.render('foodex_reports.bankpayment_report_template', docargs)