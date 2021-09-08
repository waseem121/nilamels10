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
from datetime import date


class sales_cashier_summary(models.TransientModel):
    _name = "sales.cashier.summary"

    user_id = fields.Many2one('res.users', string="Sales Person", default=lambda self:self.env.user.id)
    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    invoice_state_by = fields.Selection([('draft', 'Draft'), ('open', 'Open'),
                                         ('paid', 'Paid')], string="State")

    @api.multi
    def generate_sales_cashier_report(self):
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
        }
        return self.env['report'].get_action([], 'direct_sale.sales_summary_report_template', data=datas)


class report_direct_sale_sales_summary_report_template(models.AbstractModel):
    _name = 'report.direct_sale.sales_summary_report_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('direct_sale.sales_summary_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'get_invoice':self.get_invoice,
            'get_invoice_payment':self.get_invoice_payment,
        }
        return report_obj.render('direct_sale.sales_summary_report_template', docargs)

    def get_invoice(self, obj):
        invoice = self.env['account.invoice'].search([('user_id', '=', obj.user_id.id),
                                                      ('date_invoice', '>=', obj.date_from),
                                                      ('date_invoice', '<=', obj.date_to),
                                                      ('state', 'in', ('open', 'paid')),
                                                      ('type', 'in', ('out_invoice', 'out_refund'))
                                                      ], order='id')
        return invoice

    def get_invoice_payment(self, invoice, cash):
        if cash:
            type = 'credit' if invoice.type == 'out_invoice' else 'debit'
            cash_amount = sum(invoice.payment_move_line_ids.filtered(lambda l:l.journal_id.type == 'cash').mapped(type))
            return cash_amount
        else:
            type = 'credit' if invoice.type == 'out_invoice' else 'debit'
            credit_amount = sum(invoice.payment_move_line_ids.filtered(lambda l:l.journal_id.type != 'cash').mapped(type))
            return credit_amount

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: