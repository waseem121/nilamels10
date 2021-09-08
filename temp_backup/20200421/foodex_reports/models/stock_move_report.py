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


class StockMoveReport(models.TransientModel):
    _name = "stock.move.report"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    product_id = fields.Many2one('product.product', string="Product", required=True)
    location_id = fields.Many2one('stock.location', string="Location", domain=[('usage', '=', 'internal')], required=True)

    @api.multi
    def action_stockmove_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'date_from': self.date_from,
            'date_to':self.date_to,
            'location_id':[self.location_id.id],
            'product_id':[self.product_id.id]
        }
        return self.env['report'].get_action(self, 'foodex_reports.stock_move_report_template', data=datas)


class ReportStockMove(models.AbstractModel):
    _name = 'report.foodex_reports.stock_move_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.stock_move_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        self.env.cr.execute(
            "SELECT id FROM stock_move WHERE create_date::date>=%s and create_date::date<=%s and product_id IN %s and location_id in %s ORDER BY create_date",
            (data.get('date_from'), data.get('date_to'), (tuple(data.get('product_id'))),(tuple(data.get('location_id')))))
        query_res = self.env.cr.dictfetchall()
        lst = []
        if query_res:
            lst = [each['id'] for each in query_res]
        domain = [('invoice_id.date_invoice', '>=', data.get('date_from')),
                  ('invoice_id.date_invoice', '<=', data.get('date_to')),
                  ('invoice_id.location_id', '=', data.get('location_id')),
                  ('invoice_id.state', '=', 'draft'),
                  ('product_id', '=', data.get('product_id'))]
        draft_line_ids = self.env['account.invoice.line'].sudo().search(domain)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': self.env['stock.move'].search([('id','in',lst)]) if lst else False,
            'draft_invoice': draft_line_ids
        }
        return report_obj.render('foodex_reports.stock_move_report_template', docargs)