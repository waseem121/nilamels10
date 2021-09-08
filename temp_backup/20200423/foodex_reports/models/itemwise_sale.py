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


class ItemSale(models.TransientModel):
    _name = "item.sale"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    partner_ids = fields.Many2many('res.partner', string="Customer")
    invoice_type = fields.Selection([('normal', 'Normal Invoice'),
                                     ('sample', 'Sample Invoice'),
                                     ('transfer_invoice', 'Transfer Invoice'),
                                     ('veg_invoice', 'Vegetable Invoice')], string='Invoice Type',
                                    default='')
    product_ids= fields.Many2many('product.product', string="Item")
    salesperson_id = fields.Many2one('res.users', string="Salesperson")
    location_ids = fields.Many2many('stock.location', string="Location", domain=[('usage', '=', 'internal')])

    @api.multi
    def action_itemwise_sale_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'partner_ids':self.partner_ids.ids if self.partner_ids else False,
            'date_from': self.date_from,
            'date_to':self.date_to,
            'invoice_type':self.invoice_type,
            'location_ids':self.location_ids.ids if self.location_ids else False,
            'product_ids':self.product_ids.ids if self.product_ids else False,
            'salesperson_id': self.salesperson_id.id if self.salesperson_id else False
        }
        return self.env['report'].get_action(self, 'foodex_reports.itemwise_sale_report_template', data=datas)


class ReportItemwiseSale(models.AbstractModel):
    _name = 'report.foodex_reports.itemwise_sale_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        single_product = False
        domain = [('invoice_id.date_invoice','>=',data.get('date_from')),('invoice_id.date_invoice','<=',data.get('date_to')),('invoice_id.type','=','out_invoice')]
        if data.get('invoice_type'):
            domain.append(('invoice_id.invoice_type','=',data.get('invoice_type')))
        if data.get('partner_ids'):
            domain.append(('invoice_id.partner_id', 'in', data.get('partner_ids')))
        if data.get('salesperson_id'):
            domain.append(('invoice_id.user_id','=',data.get('salesperson_id')))
        if data.get('location_ids'):
            domain.append(('invoice_id.location_id', 'in', data.get('location_ids')))
        if data.get('product_ids'):
            if len(data.get('product_ids')) == 1:
                single_product = True
            domain.append(('product_id','in',data.get('product_ids')))
        invoice_line_ids = self.env['account.invoice.line'].sudo().search(domain,order="create_date")
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.itemwise_sale_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': invoice_line_ids if invoice_line_ids else False,
            'single_item':single_product
        }
        return report_obj.render('foodex_reports.itemwise_sale_report_template', docargs)