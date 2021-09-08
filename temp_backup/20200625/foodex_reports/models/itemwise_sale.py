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


class ItemSale(models.TransientModel):
    _name = "item.sale"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    partner_ids = fields.Many2many('res.partner', string="Customer")
    invoice_type = fields.Selection([('normal', 'Normal Invoice'),
                                     ('sample', 'Sample Invoice'),
                                     ('transfer_invoice', 'Transfer Invoice'),
                                     ('veg_invoice', 'Vegetable Invoice')], string='Invoice Type',
                                    default='')
    product_ids= fields.Many2many('product.product', string="Item")
    salesperson_id = fields.Many2one('res.users', string="Salesperson")
    location_ids = fields.Many2many('stock.location', string="Location", domain=[('usage', '=', 'internal')])
    categ_ids= fields.Many2many('product.category', string="Category")
    brand_ids= fields.Many2many('product.brand', string="Brand")

    @api.multi
    def action_itemwise_sale_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'partner_ids':self.partner_ids.ids if self.partner_ids else False,
            'categ_ids':self.categ_ids.ids if self.categ_ids else False,
            'brand_ids':self.brand_ids.ids if self.brand_ids else False,
            'date_from': self.date_from,
            'date_to':self.date_to,
            'invoice_type':self.invoice_type,
            'location_ids':self.location_ids.ids if self.location_ids else False,
            'product_ids':self.product_ids.ids if self.product_ids else False,
            'salesperson_id': self.salesperson_id.id if self.salesperson_id else False
        }
        return self.env['report'].get_action(self, 'foodex_reports.itemwise_sale_report_template', data=datas)


class ReportItemwiseSale(models.AbstractModel):
    _name = 'report.foodex_reports.itemwise_sale_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        single_product = False
        domain = [('invoice_id.date_invoice','>=',data.get('date_from')),('invoice_id.date_invoice','<=',data.get('date_to')),('invoice_id.type','=','out_invoice')]
        if data.get('invoice_type'):
            domain.append(('invoice_id.invoice_type','=',data.get('invoice_type')))
        if data.get('partner_ids'):
            domain.append(('invoice_id.partner_id', 'in', data.get('partner_ids')))
        if data.get('salesperson_id'):
            domain.append(('invoice_id.user_id','=',data.get('salesperson_id')))
        if data.get('location_ids'):
            domain.append(('invoice_id.location_id', 'in', data.get('location_ids')))
        if data.get('categ_ids'):
            domain.append(('product_id.categ_id', 'in', data.get('categ_ids')))
        if data.get('brand_ids'):
            domain.append(('product_id.product_brand_id', 'in', data.get('brand_ids')))
            
#        domain.append(('invoice_id.number', '=', '2020/0133'))
            
        if data.get('product_ids'):
            if len(data.get('product_ids')) == 1:
                single_product = True
            domain.append(('product_id','in',data.get('product_ids')))
        invoice_line_ids = self.env['account.invoice.line'].sudo().search(domain,order="create_date")
#        print"len invoice_line_ids: ",invoice_line_ids

        total_sold_qty = sum(l.quantity for l in invoice_line_ids.filtered(lambda l:l.price_unit != 0))
        
        total_cost = 0.0
        total_amount = 0.0
        if invoice_line_ids:
#            out_inv_ids = invoice_line_ids.filtered(lambda l:l.invoice_id.type == 'out_invoice')
#            out_refund_ids = invoice_line_ids.filtered(lambda l:l.invoice_id.type == 'out_refund')
            for each in invoice_line_ids:
                total_cost += (each.quantity * each.cost_price)
                total_amount += (each.price_subtotal - each.discount_share)
        
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.itemwise_sale_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': invoice_line_ids if invoice_line_ids else False,
            'single_item':single_product,
            'get_lines': self._get_lines,
            'total_sold_qty':total_sold_qty,
            'total_cost':total_cost,
            'total_amount':total_amount,
        }
        return report_obj.render('foodex_reports.itemwise_sale_report_template', docargs)
    
    def _get_lines(self, obj):
        fdict = {}
        fdict['Tijan'] = {'srl':'01', 'invoice_date':'2020-04-27'}
#        fdict['Tijan2'] = {}
        
        
        single_product = False
        domain = [('invoice_id.date_invoice','>=',obj.date_from),('invoice_id.date_invoice','<=',obj.date_to),('invoice_id.type','=','out_invoice')]
        print"domain: ",domain
        if obj.invoice_type:
            domain.append(('invoice_id.invoice_type','=',obj.invoice_type))
        if obj.partner_ids:
            domain.append(('invoice_id.partner_id', 'in', obj.partner_ids.ids))
        if obj.salesperson_id:
            domain.append(('invoice_id.user_id','=',obj.salesperson_id))
        if obj.location_ids:
            domain.append(('invoice_id.location_id', 'in', obj.location_ids.ids))
        if obj.categ_ids:
            domain.append(('product_id.categ_id', 'in', obj.categ_ids.ids))
        if obj.brand_ids:
            domain.append(('product_id.product_brand_id', 'in', obj.brand_ids.ids))
            
#        domain.append(('invoice_id.number', '=', '2020/0133'))
        print"domain: ",domain
            
        if obj.product_ids:
            if len(obj.product_ids) == 1:
                single_product = True
            domain.append(('product_id','in',obj.product_ids.ids))
        invoice_line_ids = self.env['account.invoice.line'].sudo().search(domain,order="create_date")
        print"invoice_line_ids: ",invoice_line_ids
        if len(invoice_line_ids):
            products = invoice_line_ids.mapped('product_id')
            print"products: ",products
            vals = {}
            for product in products:
                vals[product.name] = []
                
                i = 1
                for l in invoice_line_ids:
                    t = {}
                    if product.id != l.product_id.id:
                        print"diff product continue"
                        continue
                        
                    t['srl'] = i
                    t['invoice_date'] = l.invoice_id.date_invoice
                    t['invoice_number'] = l.invoice_id.number
                    t['cust_name'] = l.invoice_id.partner_id.name
                    t['qty_sold'] = l.quantity
                    t['free_qty'] = l.free_qty
                    t['price_unit'] = l.price_unit
                    t['cost'] = l.quantity * l.cost_price
                    t['discount'] = l.discount_share + l.discount_amount
                    t['subtotal'] = l.price_subtotal - l.discount_share

                    vals[product.name].append(t)
                    i+=1
                
        
        print"vals: ",vals
        return vals