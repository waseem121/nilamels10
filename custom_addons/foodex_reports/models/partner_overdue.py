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
import time
from datetime import date
import csv
import base64
import cStringIO
import StringIO
import xlwt


class PartnerOverdue(models.TransientModel):
    _name = "partner.overdue"

    date_from = fields.Date(string="Date From", default=date.today(),required=True)
    date_to = fields.Date(string="Date To", default=date.today(),required=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    
    name = fields.Char(string='File Name', readonly=True)
    data = fields.Binary(string="Data")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    
    @api.multi
    def action_export(self):
        
        stylePC = xlwt.XFStyle()
        styleBorder = xlwt.XFStyle()
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        font = xlwt.Font()
        fontP = xlwt.Font()
        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.THIN
        font.bold = True
#        font.height = 240
        font.height = 200
        fontP.bold = False
        stylePC.font = font
        stylePC.alignment = alignment
        styleBorder.font = fontP
        styleBorder.alignment = alignment
        styleBorder.borders = borders
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet("Partner Overdue")
#        worksheet = workbook.add_sheet("Stock Report", cell_overwrite_ok=True)

        row = 0
        worksheet.write_merge(row, row, 0, 0, 'Invoice Number', style=stylePC)
        worksheet.write_merge(row, row, 1, 1, 'Date', style=stylePC)
        worksheet.write_merge(row, row, 2, 2, 'Due Date', style=stylePC)
        worksheet.write_merge(row, row, 3, 3, 'Reference/Desc', style=stylePC)
        worksheet.write_merge(row, row, 4, 4, 'Delivery Address', style=stylePC)
        worksheet.write_merge(row, row, 5, 5, 'Invoice Amount', style=stylePC)
        worksheet.write_merge(row, row, 6, 6, 'Paid Amount', style=stylePC)
        worksheet.write_merge(row, row, 7, 7, 'Due Amount', style=stylePC)
        
        
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        partner = self.partner_id
        domain = [('partner_id','=',partner.id),
                ('state','not in',('draft','cancel')),
                ('residual','>', 0),
                ('date_invoice','>=',self.date_from),
                ('date_invoice','<=',self.date_to),
        ]
        invoice_ids = self.env['account.invoice'].search(domain)
        print"invoice_ids: ",invoice_ids
        if not len(invoice_ids):
            raise Warning(_('No ovedue invoices found in this date range.'))

        total_invoice_amount = 0.0
        total_paid_amount = 0.0
        total_due_amount = 0.0
        
        for invoice in invoice_ids:
            shipping_add = invoice.partner_shipping_id and invoice.partner_shipping_id.street or ''
            invoice_amount = invoice.amount_total
            due_amount = invoice.residual
            paid_amount = invoice_amount - due_amount
            
            total_invoice_amount += invoice_amount
            total_paid_amount += paid_amount
            total_due_amount += due_amount
            
            invoice_amount = str('%.3f'%(invoice_amount))
            print"invoice_amount: ",invoice_amount
            
#            invoice_amount = '{:.3f}'.format(invoice_amount)
            due_amount = '{:.3f}'.format(due_amount)
            paid_amount = '{:.3f}'.format(paid_amount)
            
#            worksheet.write(categ_row + 1, 3 + i, 'Total', style=stylePC)
            i=0
            row += 1
            worksheet.write(row, i+0, invoice.number, style=styleBorder)
            worksheet.write(row, i+1, invoice.date_invoice, style=styleBorder)
            worksheet.write(row, i+2, invoice.date_due, style=styleBorder)
            worksheet.write(row, i+3, invoice.name or '', style=styleBorder)
            worksheet.write(row, i+4, shipping_add, style=styleBorder)
            worksheet.write(row, i+5, invoice_amount, style=styleBorder)
            worksheet.write(row, i+6, paid_amount, style=styleBorder)
            worksheet.write(row, i+7, due_amount, style=styleBorder)
        row += 2
        
        total_invoice_amount = '{:.3f}'.format(total_invoice_amount)
        total_due_amount = '{:.3f}'.format(total_due_amount)
        total_paid_amount = '{:.3f}'.format(total_paid_amount)
        
        worksheet.write_merge(row, row, 4, 4, 'Total', style=stylePC)
        worksheet.write_merge(row, row, 5, 5, total_invoice_amount, style=stylePC)
        worksheet.write_merge(row, row, 6, 6, total_paid_amount, style=stylePC)
        worksheet.write_merge(row, row, 7, 7, total_due_amount, style=stylePC)

        
#        total_invoice_amount = '{:.3f}'.format(total_invoice_amount)
#        total_due_amount = '{:.3f}'.format(total_due_amount)
#        total_paid_amount = '{:.3f}'.format(total_paid_amount)
        
        
        file_data = cStringIO.StringIO()
        workbook.save(file_data)
        self.write({
            'state': 'get',
            'data': base64.encodestring(file_data.getvalue()),
            'name': 'Export_partner_overdue.xls'
        })
        
        return {
            'name': 'Partner Overdue',
            'type': 'ir.actions.act_window',
            'res_model': 'partner.overdue',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    @api.multi
    def action_export_old(self):
        stop
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        partner = self.partner_id
        domain = [('partner_id','=',partner.id),
                ('state','not in',('draft','cancel')),
                ('residual','>', 0),
                ('date_invoice','>=',self.date_from),
                ('date_invoice','<=',self.date_to),
        ]
        invoice_ids = self.env['account.invoice'].search(domain)
        print"invoice_ids: ",invoice_ids
        if not len(invoice_ids):
            raise Warning(_('No ovedue invoices found in this date range.'))

        output = StringIO.StringIO()
        output.write('"InvoiceNumber","Date","Due Date","Reference/Desc",\
            "Delivery Address","Invoice Amount","Paid Amount","Due Amount"')
        output.write("\n")
        
        total_invoice_amount = 0.0
        total_paid_amount = 0.0
        total_due_amount = 0.0
        
        for invoice in invoice_ids:
            shipping_add = invoice.partner_shipping_id and invoice.partner_shipping_id.street or ''
            invoice_amount = invoice.amount_total
            due_amount = invoice.residual
            paid_amount = invoice_amount - due_amount
            
            total_invoice_amount += invoice_amount
            total_paid_amount += paid_amount
            total_due_amount += due_amount
            
            invoice_amount = str('%.3f'%(invoice_amount))
            print"invoice_amount: ",invoice_amount
            
#            invoice_amount = '{:.3f}'.format(invoice_amount)
            due_amount = '{:.3f}'.format(due_amount)
            paid_amount = '{:.3f}'.format(paid_amount)
            
        
            output.write('"%s","%s","%s","%s","%s","%s","%s","%s"' % 
                (invoice.number,invoice.date_invoice,invoice.date_due,
                invoice.name,shipping_add,invoice_amount,paid_amount,due_amount))
            output.write("\n")
        
        total_invoice_amount = '{:.3f}'.format(total_invoice_amount)
        total_due_amount = '{:.3f}'.format(total_due_amount)
        total_paid_amount = '{:.3f}'.format(total_paid_amount)
        
        output.write("\n")
        output.write('"%s","%s","%s","%s","%s","%s","%s","%s"' % 
            ('','','','',
            'Total',total_invoice_amount,total_paid_amount,total_due_amount))
        output.write("\n")
        
        
        today = time.strftime('%Y-%m-%d %H:%M:%S')
        out=base64.encodestring(output.getvalue())
        self.write({'data':out,'state':'get','name':'Export_Partner_OverDue'+today+'.csv'})
        return {
            'name': 'Partner Overdue',
            'type': 'ir.actions.act_window',
            'res_model': 'partner.overdue',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }            

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: