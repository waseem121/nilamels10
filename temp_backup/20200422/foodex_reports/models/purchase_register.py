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


class PurchaseRegister(models.TransientModel):
    _name = "purchase.register"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    vendor_ids = fields.Many2many('res.partner', string="Vendor")

    @api.multi
    def action_purchase_register_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'vendor_ids':self.vendor_ids.ids if self.vendor_ids else False,
            'date_from': self.date_from,
            'date_to':self.date_to
        }
        # self.vendor_ids = False
        return self.env['report'].get_action(self, 'foodex_reports.purchase_register_report_template', data=datas)


class ReportPurchaseRegister(models.AbstractModel):
    _name = 'report.foodex_reports.purchase_register_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.purchase_register_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        if data.get('vendor_ids'):
            self.env.cr.execute("SELECT id FROM purchase_order WHERE date_order::date>=%s and date_order::date<=%s and partner_id IN %s ORDER BY date_order", (data.get('date_from'),data.get('date_to'),(tuple(data.get('vendor_ids')))))
            query_res = self.env.cr.dictfetchall()
        else:
            self.env.cr.execute(
                "SELECT id FROM purchase_order WHERE date_order::date>=%s and date_order::date<=%s ORDER BY date_order",
                (data.get('date_from'), data.get('date_to')))
            query_res = self.env.cr.dictfetchall()
        po_ids = False
        if query_res:
            lst = [each['id'] for each in query_res]
            po_ids = self.env['purchase.order'].search([('id','in',lst)], order="date_order asc")
        po_lst = []
        total = 0
        if po_ids:
            for each in po_ids:
                if each.invoice_ids:
                    for each_inv in each.invoice_ids:
                        total += each_inv.currency_id.compute(each_inv.amount_total,  self.env['res.currency'].search([('name', '=', 'KWD')]))
                    po_lst.append(each)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': po_lst,
            'date_from':data.get('date_from'),
            'date_to':data.get('date_to'),
            'total': total if po_lst else False
        }
        return report_obj.render('foodex_reports.purchase_register_report_template', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: