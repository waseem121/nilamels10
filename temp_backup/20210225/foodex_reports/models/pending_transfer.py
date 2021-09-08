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

class StockMove(models.Model):
    _inherit = 'stock.move'

    move_sch_date = fields.Datetime(string="Picking Schedule Date", related="picking_id.min_date", store=True)

class PendingTransfer(models.TransientModel):
    _name = "pending.transfer"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    product_ids = fields.Many2many('product.product', string="Product")
    state = fields.Selection([('all','All'),
                             ('pending','Pending'),
                             ('new','New')
                             ], string="Status", default='all')
    src_location_id = fields.Many2one('stock.location', string="Source Location")
    dest_location_id = fields.Many2one('stock.location', string="Destination Location")
    location_condition = fields.Selection([('or','OR'),('and','AND')],default="or",string="Location Condition")

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
            'product_ids':self.product_ids.ids if self.product_ids else False,
            'state':self.state,
            'src_location_id':self.src_location_id.id if self.src_location_id else False,
            'dest_location_id': self.dest_location_id.id if self.dest_location_id else False,
            'location_condition':self.location_condition
        }
        return self.env['report'].get_action(self, 'foodex_reports.pending_transfer_report_template', data=datas)


class ReportPendingTransfer(models.AbstractModel):
    _name = 'report.foodex_reports.pending_transfer_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        self.env.cr.execute(
            "SELECT id FROM stock_move WHERE move_sch_date::date>=%s and move_sch_date::date<=%s and state != 'cancel' and picking_id is not null ORDER BY move_sch_date",
            (data.get('date_from'), data.get('date_to')))
        query_res = self.env.cr.dictfetchall()
        move_lst = [each['id'] for each in query_res] if query_res else []
        domain = [('id','in',move_lst)]
        if data.get('product_ids'):
            domain.append(('product_id','in',data.get('product_ids')))
        if data.get('state') == 'pending':
            domain.append(('picking_id.state','not in',['cancel','done']))
        if data.get('state') == 'new':
            domain.append(('picking_id.state','=','draft'))
        if data.get('location_condition') == 'or' and data.get('src_location_id') and data.get('dest_location_id'):
            domain.append('|')
            domain.append(('location_id','=',data.get('src_location_id')))
            domain.append(('location_dest_id','=',data.get('dest_location_id')))
        if data.get('location_condition') == 'and' and data.get('src_location_id') and data.get('dest_location_id'):
            domain.append(('location_id','=',data.get('src_location_id')))
            domain.append(('location_dest_id','=',data.get('dest_location_id')))
        if data.get('src_location_id') and not data.get('dest_location_id'):
            domain.append(('picking_id.location_id','=',data.get('src_location_id')))
        if data.get('dest_location_id') and not data.get('src_location_id'):
            domain.append(('location_dest_id','=',data.get('dest_location_id')))
        move_line_ids = self.env['stock.move'].search(domain)
        picking_lst = []
        if move_line_ids:
            for each in move_line_ids:
                if each.picking_id.id not in picking_lst:
                    picking_lst.append(each.picking_id.id)
        picking_ids = self.env['stock.picking'].search([('id','in',picking_lst)],order="min_date")
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.pending_transfer_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': picking_ids if picking_ids else False,
            'product_lst': data.get('product_ids')
        }
        return report_obj.render('foodex_reports.pending_transfer_report_template', docargs)