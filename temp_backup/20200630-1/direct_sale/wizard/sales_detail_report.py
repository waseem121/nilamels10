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


class sales_detail_summary(models.TransientModel):
    _name = "sales.detail.summary"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    product_ids = fields.Many2many('product.product', string="Product")
    brand_ids = fields.Many2many('product.brand', string="Brand")
    category_ids = fields.Many2many('product.category', string="Category")
    location_ids = fields.Many2many('stock.location', 'sales_detail_location_rel', string="Location")
#    user_ids = fields.Many2many('res.users', string="Sales Person", default=lambda self:self.env.user.ids)
    user_ids = fields.Many2many('res.users', string="Sales Person")

    @api.multi
    def generate_sales_detail_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
        }
        return self.env['report'].get_action(self, 'direct_sale.sales_detail_report_template', data=datas)


class report_direct_sale_sales_detail_report_template(models.AbstractModel):
    _name = 'report.direct_sale.sales_detail_report_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('direct_sale.sales_detail_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'get_invoice':self.get_invoice
        }
        return report_obj.render('direct_sale.sales_detail_report_template', docargs)

    def get_invoice(self, obj):
        invoice_line_obj = self.env['account.invoice.line']
        user_ids = obj.user_ids.ids if obj.user_ids else self.env['res.users'].search([]).ids
        location_ids = obj.location_ids.ids if obj.location_ids else self.env['stock.location'].search([('usage', '=', 'internal')]).ids
        invoice = self.env['account.invoice'].search([('user_id', 'in', [x for x in user_ids]),
                                                      ('date_invoice', '>=', obj.date_from),
                                                      ('date_invoice', '<=', obj.date_to),
                                                      ('state', 'in', ('open', 'paid')),
                                                      ('location_id', 'in', [x for x in location_ids]),
                                                      ('type', 'in', ('out_invoice', 'out_refund'))
                                                      ], order='id')

        product_ids = obj.product_ids.ids if obj.product_ids else self.env['product.product'].search([]).ids
        brand_ids = obj.brand_ids.ids if obj.brand_ids else self.env['product.brand'].search([]).ids
        category_ids = obj.category_ids.ids if obj.category_ids else self.env['product.category'].search([]).ids
        for each_invoice in invoice:
            for order_line in each_invoice.invoice_line_ids.filtered(lambda l:l.product_id and l.product_id.id in [x for x in product_ids] 
                                                                     and l.product_id.product_brand_id.id in [x for x in brand_ids]
                                                                     and l.product_id.categ_id.id in [x for x in category_ids]):
                invoice_line_obj |= order_line
        return invoice_line_obj
