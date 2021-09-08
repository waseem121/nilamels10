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


class VendorSales(models.TransientModel):
    _name = "vendor.sales"

    date_from = fields.Date(string="Date From", default=date.today(),required=True)
    date_to = fields.Date(string="Date To", default=date.today(),required=True)
    vendor_id = fields.Many2one('res.partner', string="Supplier", required=True)
    customer_ids = fields.Many2many('res.partner', string="Customer")
    location_id = fields.Many2one('stock.location', string="Location", domain=[('usage', '=', 'internal')])
    salesman_id = fields.Many2one('res.users', string="Salesman")
    product_ids = fields.Many2many('product.product', string="Product", required=True)
    option = fields.Selection([('qty','Qty'),('qty_and_price','Qty and Price')], default="qty_and_price")

    @api.multi
    def action_vendor_sales_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'vendor_id':self.vendor_id.id if self.vendor_id else False,
            'date_from': self.date_from,
            'date_to':self.date_to,
            'customer_ids':self.customer_ids.ids if self.customer_ids else False,
            'location_id':self.location_id.id if self.location_id else False,
            'salesman_id':self.salesman_id.id if self.salesman_id else False,
            'product_ids':self.product_ids.ids if self.product_ids else False
        }
        # self.vendor_ids = False
        return self.env['report'].get_action(self, 'foodex_reports.vendor_sale_report_template', data=datas)


class ReportVendorSales(models.AbstractModel):
    _name = 'report.foodex_reports.vendor_sale_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        domain = [('invoice_id.date_invoice', '>=', data.get('date_from')),
                  ('invoice_id.date_invoice', '<=', data.get('date_to')),
                  ('product_id', 'in', data.get('product_ids')),
                  ('invoice_id.type','in',['out_invoice','out_refund'])
                  ]
        if data.get('customer_ids'):
            domain.append(('invoice_id.partner_id','in',data.get('customer_ids')))
        if data.get('location_id'):
            domain.append(('invoice_id.location_id','=',data.get('location_id')))
        if data.get('salesman_id'):
            domain.append(('invoice_id.user_id','=',data.get('salesman_id')))
        invoice_line_ids = self.env['account.invoice.line'].search(domain)
        invoice_line_lst = []
        if invoice_line_ids:
            for each in invoice_line_ids:
                if each.product_id.seller_ids:
                    for each_seller in each.product_id.seller_ids:
                        if each_seller.name.id == data.get('vendor_id'):
                            invoice_line_lst.append(each.id)
        final_invoice_line_ids = self.env['account.invoice.line'].search([('id','in',invoice_line_lst)])
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.vendor_sale_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': final_invoice_line_ids if final_invoice_line_ids else False,
            'date_from':data.get('date_from'),
            'date_to':data.get('date_to'),
        }
        return report_obj.render('foodex_reports.vendor_sale_report_template', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: