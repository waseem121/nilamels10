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


class PendingTransfer(models.TransientModel):
    _name = "pending.transfer"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())

    @api.multi
    def action_pending_transfer_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'date_from': self.date_from,
            'date_to':self.date_to,
        }
        return self.env['report'].get_action(self, 'foodex_reports.pending_transfer_report_template', data=datas)


class ReportPendingTransfer(models.AbstractModel):
    _name = 'report.foodex_reports.pending_transfer_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        self.env.cr.execute(
            "SELECT id FROM stock_picking WHERE min_date::date>=%s and min_date::date<=%s and state not in ('cancel','done') ORDER BY min_date",
            (data.get('date_from'), data.get('date_to')))
        query_res = self.env.cr.dictfetchall()
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.pending_transfer_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': self.env['stock.picking'].search([('id','in',[each['id'] for each in query_res])]) if query_res else False,
        }
        return report_obj.render('foodex_reports.pending_transfer_report_template', docargs)