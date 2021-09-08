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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.exceptions import UserError


class StockMoveReport(models.TransientModel):
    _name = "stock.move.report"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    product_id = fields.Many2one('product.product', string="Product", required=True)
    location_id = fields.Many2one('stock.location', string="Location", domain=[('usage', '=', 'internal')] , required=True)
    option = fields.Selection([('qty','Show Qty'),('qty_cost','Show Qty And Cost')], string="Option", default="qty")
    state = fields.Selection([('all', 'All'),
                              ('pending', 'Pending'),
                              ('new', 'New')
                              ], string="Status", default='all')

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
            'state':self.state,
            'location_id':self.location_id.id if self.location_id else False,
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
            "SELECT id FROM stock_move WHERE create_date::date>=%s and create_date::date<=%s and product_id IN %s and state != 'cancel' ORDER BY create_date",
            (data.get('date_from'), data.get('date_to'), (tuple(data.get('product_id')))))
        query_res = self.env.cr.dictfetchall()
        lst = []
        if query_res:
            lst = [each['id'] for each in query_res]
        domain = [('id','in',lst)]
        if data.get('state') == 'pending':
            domain.append(('state','not in',['cancel','done']))
        if data.get('state') == 'new':
            domain.append(('state','=','draft'))
        if data.get('location_id'):
            domain.append('|')
            domain.append(('location_id','=',data.get('location_id')))
            domain.append(('location_dest_id','=',data.get('location_id')))
        data_lst = []
        move_ids = self.env['stock.move'].search(domain)
        if move_ids:
            for each in move_ids:
                data_lst.append({'record_id':each,'model':'stock.move','date':str(datetime.strptime(each.create_date,DTF).date())})
        domain_inv = [('invoice_id.date_invoice', '>=', data.get('date_from')),
                  ('invoice_id.date_invoice', '<=', data.get('date_to')),
                  ('invoice_id.state', '=', 'draft'),
                  ('invoice_id.type','in',['out_invoice','out_refund']),
                  ('product_id', 'in', data.get('product_id'))]
        if data.get('location_id'):
            domain_inv.append(('invoice_id.location_id','=',data.get('location_id')))
        draft_line_ids = self.env['account.invoice.line'].sudo().search(domain_inv,order="invoice_date")
        if draft_line_ids:
            for each in draft_line_ids:
                data_lst.append({'record_id':each,'model':'account.invoice','date':each.invoice_date})
        sorted_dict = []
        if data_lst:
            sorted_dict = sorted(data_lst, key = lambda i: i['date'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': sorted_dict,
            'draft_invoice': False
        }
        return report_obj.render('foodex_reports.stock_move_report_template', docargs)