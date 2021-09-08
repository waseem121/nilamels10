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


class SupplierRegister(models.TransientModel):
    _name = "supplier.register"

    date_from = fields.Date(string="Date From", default=date.today(),required=True)
    date_to = fields.Date(string="Date To", default=date.today(),required=True)
    vendor_id = fields.Many2one('res.partner', string="Supplier", required=True)

    @api.multi
    def action_supplier_register_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'vendor_id':self.vendor_id.id if self.vendor_id else False,
            'date_from': self.date_from,
            'date_to':self.date_to
        }
        # self.vendor_ids = False
        return self.env['report'].get_action(self, 'foodex_reports.supplier_register_report_template', data=datas)


class ReportSupplierRegister(models.AbstractModel):
    _name = 'report.foodex_reports.supplier_register_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.supplier_register_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        self.env.cr.execute("SELECT id FROM purchase_order WHERE date_order::date>=%s and date_order::date<=%s and partner_id = %s ORDER BY date_order", (data.get('date_from'),data.get('date_to'),str(data.get('vendor_id'))))
        query_res = self.env.cr.dictfetchall()
        po_ids = False
        if query_res:
            po_ids = self.env['purchase.order'].sudo().search([('id','in',[each['id'] for each in query_res])], order='date_order')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': po_ids,
            'date_from':data.get('date_from'),
            'date_to':data.get('date_to'),
            'total': ''
        }
        return report_obj.render('foodex_reports.supplier_register_report_template', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: