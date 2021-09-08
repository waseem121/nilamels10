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


class SalesmanReport(models.TransientModel):
    _name = "salesman.report"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    salesman_id = fields.Many2one('res.users', string="Salesman", required=True)
    partner_ids= fields.Many2many('res.partner', string="Customer")
    location_ids = fields.Many2many('stock.location', string="Location",  domain=[('usage', '=', 'internal')])
    invoice_type = fields.Selection([
                                     ('all','All'),
                                     ('normal', 'Normal Invoice'),
                                     ('sample', 'Sample Invoice'),
                                     ('transfer_invoice', 'Transfer Invoice'),
                                     ('veg_invoice', 'Vegetable Invoice')], string='Invoice Type',
                                    default='all')

    @api.multi
    def action_get_salesman_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'date_from': self.date_from,
            'date_to':self.date_to,
            'partner_ids':self.partner_ids.ids if self.partner_ids else False,
            'location_ids':self.location_ids.ids if self.location_ids else False,
            'salesman_id':self.salesman_id.id if self.salesman_id else False,
            'invoice_type':self.invoice_type
        }
        return self.env['report'].get_action(self, 'foodex_reports.sale_man_report_template', data=datas)


class ReportsalesmanSales(models.AbstractModel):
    _name = 'report.foodex_reports.sale_man_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        domain = [('user_id','=',data.get('salesman_id')),('date_invoice', '>=', data.get('date_from')),('date_invoice', '<=', data.get('date_to')), ('type', '=', 'out_invoice')]
        if data.get('partner_ids'):
            domain.append(('partner_id','in',data.get('partner_ids')))
        if data.get('location_ids'):
            domain.append(('location_id', 'in', data.get('location_ids')))
        if not data.get('invoice_type') == 'all':
            domain.append(('invoice_type','=',data.get('invoice_type')))
        date_lst = []
        data_dict = {}
        total = 0
        invoice_ids = self.env['account.invoice'].sudo().search(domain,order="date_invoice")
        if invoice_ids:
            total  = sum(invoice_ids.mapped('amount_total'))
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.sale_man_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': invoice_ids,
            'total':total
        }
        return report_obj.render('foodex_reports.sale_man_report_template', docargs)