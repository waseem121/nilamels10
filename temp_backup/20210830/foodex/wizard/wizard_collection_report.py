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
from datetime import datetime, timedelta


class wizard_collection_report(models.TransientModel):
    _name = "wizard.collection.report"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
#    collector_id = fields.Many2one('res.partner', string='Collector',domain=[('is_collector', '=', True)])
    user_id = fields.Many2one('res.users', string='Salesman')
    print_date = fields.Date(string='Print Date', readonly=True, default=fields.Datetime.now)
    include_receipts = fields.Boolean(string='Include Accounting Receipts')
    show_details = fields.Boolean(string='Show Details')
    
    def _get_report_lines(self):
        report_lines = []
        res = self._get_all_totals()
        report_lines = res.get('report_lines')

        return report_lines
    
    def _get_stock_transfer_lines(self):
        report_lines = []
        res = self._get_all_totals()
        report_lines = res.get('stock_transfer_lines')

        return report_lines
    
    def _get_grand_total(self):
        
        res = self._get_all_totals()
        grand_total = res.get('grand_total')
        
        return grand_total
    
    def _get_all_totals(self):
        res = {}
        report_lines = []
        stock_transfer_lines = []
#        moves = self.env['account.move'].search([('date','>=',self.date_from),
#                            ('date','<=',self.date_to),
#                            ('collector_id','=',self.collector_id.id),
#                            ('state','=','posted')])
        moves = self.env['account.move'].search([('date','>=',self.date_from),
                            ('date','<=',self.date_to),
                            ('salesman_id','=',self.user_id.id),
                           ])
#        print"movess: ",moves
        
        total_receipts = 0.0
        regular_sale = 0.0
        stock_sale = 0.0
        grand_total = 0.0
        count = 1
        transfer_count = 1
        for move in moves:
            if move.journal_id.type not in ('bank','cash'):
                print"other than bank and cash type, continue"
                continue
            if not move.invoice_type:
                total_receipts += move.amount
                grand_total += move.amount

                line = {}
                line['count'] = count
                line['receipt_date'] = move.date
                line['receipt_no'] = move.name
                line['cust_code'] = move.partner_id.ref
                line['cust_name'] = move.partner_id.name
                line['amount'] = move.amount
                report_lines.append(line)
                count += 1
            
#            print"move name: ",move.name
            refund=False
            for l in move.line_ids:
                account_name = l.account_id and l.account_id.name or False
                if (account_name and account_name=='Cash On Hand') and l.credit>0.0:
                    refund=True
                    
            if move.invoice_type=='normal':
                if refund:
                    regular_sale -= move.amount
                else:
                    regular_sale += move.amount
            if move.invoice_type=='transfer_invoice':
                move_amount = 0.0
                if refund:
                    stock_sale -= move.amount
                    move_amount = -1.0 * (move.amount)
                else:
                    stock_sale += move.amount
                    move_amount = move.amount
                
                transfer_lines = {}
                transfer_lines['count'] = transfer_count
                transfer_lines['receipt_date'] = move.date
                transfer_lines['receipt_no'] = move.name
                transfer_lines['cust_code'] = move.partner_id.ref
                transfer_lines['cust_name'] = move.partner_id.name
                transfer_lines['amount'] = move_amount
                stock_transfer_lines.append(transfer_lines)
                transfer_count += 1
                
                
        res['regular_sale'] = regular_sale
        res['grand_total'] = grand_total
        res['total_receipts'] = total_receipts
        res['stock_sale'] = stock_sale
        res['gross_total'] = regular_sale + total_receipts + stock_sale
        res['report_lines'] = report_lines
        res['stock_transfer_lines'] = stock_transfer_lines
        return res

    @api.multi
    def generate_collection_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
        }
        return self.env['report'].get_action(self, 'foodex.collection_report_template', data=datas)


class report_foodex_collection_report_template(models.AbstractModel):
    _name = 'report.foodex.collection_report_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex.collection_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
        }
        return report_obj.render('foodex.collection_report_template', docargs)