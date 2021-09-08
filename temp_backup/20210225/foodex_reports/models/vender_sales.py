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

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    invoice_date = fields.Date(string="Date Invoice", related="invoice_id.date_invoice", store=True)

class VendorSales(models.TransientModel):
    _name = "vendor.sales"

    date_from = fields.Date(string="Date From", default=date.today(),required=True)
    date_to = fields.Date(string="Date To", default=date.today(),required=True)
    vendor_id = fields.Many2one('res.partner', string="Supplier")
    customer_ids = fields.Many2many('res.partner', string="Customer")
    location_id = fields.Many2one('stock.location', string="Location", domain=[('usage', '=', 'internal')])
    salesman_id = fields.Many2one('res.users', string="Salesman")
    category_id = fields.Many2one('product.category', string="Category")
    product_ids = fields.Many2many('product.product', string="Product")
    option = fields.Selection([('qty','Qty'),('qty_and_price','Qty and Price')], default="qty_and_price")
    view_by = fields.Selection([('detail', 'Detail'), ('summary', 'Summary')],
                    default='detail',
                    string="View By")
    group_by = fields.Selection(
        [('customer', 'Customer'), ('category', 'Category'), ('product', 'Product')],
        default='customer',
        string="Group By")

    @api.multi
    def action_vendor_sales_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'vendor_id':self.vendor_id.id if self.vendor_id else False,
            'date_from': self.date_from,
            'date_to':self.date_to,
            'option':self.option,
            'customer_ids':self.customer_ids.ids if self.customer_ids else False,
            'location_id':self.location_id.id if self.location_id else False,
            'salesman_id':self.salesman_id.id if self.salesman_id else False,
            'product_ids':self.product_ids.ids if self.product_ids else False,
            'category_id':self.category_id.id if self.category_id else False,
            'group_by':self.group_by
        }
        # self.vendor_ids = False
        return self.env['report'].get_action(self, 'foodex_reports.vendor_sale_report_template', data=datas)


class ReportVendorSales(models.AbstractModel):
    _name = 'report.foodex_reports.vendor_sale_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        domain = [('invoice_id.date_invoice', '>=', data.get('date_from')),
                  ('invoice_id.date_invoice', '<=', data.get('date_to')),
                  ('invoice_id.state', '!=', 'cancel'),
                  ('invoice_id.type','in',['out_invoice','out_refund'])
                  ]
        if data.get('customer_ids'):
            domain.append(('invoice_id.partner_id','in',data.get('customer_ids')))
        if data.get('location_id'):
            domain.append(('invoice_id.location_id','=',data.get('location_id')))
        if data.get('salesman_id'):
            domain.append(('invoice_id.user_id','=',data.get('salesman_id')))
        if data.get('product_ids'):
            domain.append(('product_id', 'in', data.get('product_ids')))
        if data.get('category_id'):
            domain.append(('product_id.categ_id', '=', data.get('category_id')))
        invoice_line_ids = self.env['account.invoice.line'].search(domain)
#        invoice_line_ids = self.env['account.invoice.line'].search([('invoice_id.id','=',675)])
        
        if data.get('vendor_id',False):
            invoice_line_lst = []
            if invoice_line_ids:
                for each in invoice_line_ids:
                    if each.product_id.seller_ids:
                        for each_seller in each.product_id.seller_ids:
                            if each_seller.name.id == data.get('vendor_id'):
                                invoice_line_lst.append(each.id)
            final_invoice_line_ids = self.env['account.invoice.line'].search([('id','in',invoice_line_lst)],order="invoice_date")
        else:
            final_invoice_line_ids = invoice_line_ids
        line_ids_to_check = final_invoice_line_ids.ids
            
        out_inv_ids = final_invoice_line_ids.filtered(lambda l:l.invoice_id.type == 'out_invoice')
        out_refund_ids = final_invoice_line_ids.filtered(lambda l:l.invoice_id.type == 'out_refund')
#        all_data = [out_inv_ids, out_refund_ids]
        out_inv_data = []
        out_refund_data = []
        out_invoices = out_inv_ids.mapped('invoice_id')
        refund_invoices = out_refund_ids.mapped('invoice_id')
        for inv in out_invoices:
#            this_invoice_line_ids = inv.invoice_line_ids
            this_invoice_line_ids = inv.invoice_line_ids.filtered(lambda l: l.id in line_ids_to_check)
            inv_product_ids = this_invoice_line_ids.mapped('product_id')
            for inv_product in inv_product_ids:
                qty, free_qty, price_unit, discount, amount = 0.0, 0.0, 0.0, 0.0, 0.0
                for l in this_invoice_line_ids:
                    if l.product_id.id == inv_product.id:
                        qty += l.quantity
                        free_qty += l.free_qty
                        price_unit += l.price_unit
                        discount += ((l.discount_amount or 0.0) + (l.discount_share or 0.0))
                        amount += (l.price_subtotal - (l.discount_share or 0))
                        
                v = {}
                v['product_id'] = inv_product.id
                v['invoice_id'] = inv.id
                v['date'] = inv.date_invoice
                v['number'] = inv.number
                v['partner_name'] = inv.partner_id.name
                v['product_name'] = inv_product.display_name
                v['price_unit'] = price_unit
                v['exchange_rate'] = inv.exchange_rate or 0.0
                v['discount'] = discount
                v['amount'] = amount
                v['qty'] = qty
                v['free_qty'] = free_qty
                
                out_inv_data.append(v)
            
        # get refund data
        for inv in refund_invoices:
            this_invoice_line_ids = inv.invoice_line_ids.filtered(lambda l: l.id in line_ids_to_check)
            inv_product_ids = this_invoice_line_ids.mapped('product_id')
            for inv_product in inv_product_ids:
                qty, free_qty, price_unit, discount, amount = 0.0, 0.0, 0.0, 0.0, 0.0
                for l in this_invoice_line_ids:
                    if l.product_id.id == inv_product.id:
                        qty += l.quantity
                        free_qty += l.free_qty
                        price_unit += l.price_unit
                        discount += ((l.discount_amount or 0.0) + (l.discount_share or 0.0))
                        amount += (l.price_subtotal - (l.discount_share or 0))

                v = {}
                v['product_id'] = inv_product.id
                v['invoice_id'] = inv.id
                v['date'] = inv.date_invoice
                v['number'] = inv.number
                v['partner_name'] = inv.partner_id.name
                v['product_name'] = inv_product.display_name
                v['price_unit'] = price_unit
                v['exchange_rate'] = inv.exchange_rate or 0.0
                v['discount'] = discount
                v['amount'] = amount
                v['qty'] = qty
                v['free_qty'] = free_qty
                
                out_refund_data.append(v)            
            
#        all_data = [out_inv_ids, out_refund_ids]
        out_inv_data = sorted(out_inv_data, key=lambda i: i['date'])
        out_refund_data = sorted(out_refund_data, key=lambda i: i['date'])
        
        all_data = [out_inv_data, out_refund_data]

        total_sold_qty, total_return_qty = 0, 0
        if len(out_inv_ids):
#            total_sold_qty = sum(l.quantity for l in out_inv_ids.filtered(lambda l:l.price_unit != 0))
            total_sold_qty = sum(l.quantity for l in out_inv_ids)
            total_sold_qty += sum(l.free_qty for l in out_inv_ids)
            
        if len(out_refund_ids):
#            total_return_qty = sum(l.quantity for l in out_refund_ids.filtered(lambda l:l.price_unit != 0))
            total_return_qty = sum(l.quantity for l in out_refund_ids)
            total_return_qty += sum(l.free_qty for l in out_refund_ids)
            total_return_qty *= -1
            
            
        total_sale = 0
        total_refund = 0
        if final_invoice_line_ids:
            if data.get('option') == 'qty_and_price':
                out_inv_ids = final_invoice_line_ids.filtered(lambda l:l.invoice_id.type == 'out_invoice')
                out_refund_ids = final_invoice_line_ids.filtered(lambda l:l.invoice_id.type == 'out_refund')
                if out_inv_ids:
                    for each in out_inv_ids:
                        if each.invoice_id.exchange_rate>0:
                            price_subtotal = each.price_subtotal / each.invoice_id.exchange_rate
                            discount_share = each.discount_share / each.invoice_id.exchange_rate
                        else:
                            price_subtotal = each.price_subtotal
                            discount_share = each.discount_share
#                        total_sale += (each.price_subtotal - each.discount_share)
                        total_sale += (price_subtotal - discount_share)
                if out_refund_ids:
                    for each in out_refund_ids:
                        if each.invoice_id.exchange_rate>0:
                            price_subtotal = each.price_subtotal / each.invoice_id.exchange_rate
                            discount_share = each.discount_share / each.invoice_id.exchange_rate
                        else:
                            price_subtotal = each.price_subtotal
                            discount_share = each.discount_share                        
#                        total_refund += (each.price_subtotal - each.discount_share)
                        total_refund += (price_subtotal - discount_share)
                        
        ## summary report lines start
        ## summary report lines end
            
                        
                        
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.vendor_sale_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
#            'data': final_invoice_line_ids if final_invoice_line_ids else False,
            'data': all_data,
            'summary_query': self._query_summary,
            'date_from':data.get('date_from'),
            'date_to':data.get('date_to'),
            'total_sold_qty':total_sold_qty,
            'total_return_qty':total_return_qty,
            'total_sale':total_sale,
            'total_refund':total_refund
        }
        return report_obj.render('foodex_reports.vendor_sale_report_template', docargs)
    
    def _query_summary(self, obj):
#        fdict = {}
#        fdict['Tijan'] = {}
#        fdict['Tijan2'] = {}

        domain = [('invoice_id.date_invoice', '>=', obj.date_from),
                  ('invoice_id.date_invoice', '<=', obj.date_to),
                  ('invoice_id.state', '!=', 'cancel'),
                  ('invoice_id.type','in',['out_invoice','out_refund'])
                  ]
        if obj.customer_ids:
            domain.append(('invoice_id.partner_id.id','in',obj.customer_ids.ids))
        if obj.location_id:
            domain.append(('invoice_id.location_id.id','=',obj.location_id.id))
        if obj.salesman_id:
            domain.append(('invoice_id.user_id.id','=',obj.salesman_id.id))
        if obj.product_ids:
            domain.append(('product_id', 'in', obj.product_ids.ids))
        if obj.category_id:
            domain.append(('product_id.categ_id.id', '=', obj.category_id.id))
        invoice_line_ids = self.env['account.invoice.line'].search(domain)
        
        if obj.vendor_id:
            invoice_line_lst = []
            if invoice_line_ids:
                for each in invoice_line_ids:
                    if each.product_id.seller_ids:
                        for each_seller in each.product_id.seller_ids:
                            if each_seller.name.id == obj.vendor_id.id:
                                invoice_line_lst.append(each.id)
            final_invoice_line_ids = self.env['account.invoice.line'].search([('id','in',invoice_line_lst)],order="invoice_date")
        else:
            final_invoice_line_ids = invoice_line_ids

        if not len(final_invoice_line_ids):
            fdict = {}
            fdict['No Lines to show in this criteria'] = {}
            return fdict
        
        # Customer Group
        if (obj.group_by == 'customer') or not obj.group_by:
            customers = []
            for l in final_invoice_line_ids:
                partner = l.invoice_id.partner_id
                if partner in customers:
                    print"partner already in dict"
                    continue
                customers.append(partner)
            vals = {}
            for customer in customers:
                vals[customer.name] = []
                i = 1
                for l in final_invoice_line_ids:
                    t = {}
                    partner = l.invoice_id.partner_id
                    if customer.id != partner.id:
                        continue
                        
                    currency = l.invoice_id.currency_id
                    exchange_rate = 1.0
                    if currency.name!='KWD':
                        exchange_rate = l.invoice_id.exchange_rate
                        
                    add=True
                    for d in vals[customer.name]:
                        if d['item'] == l.product_id.display_name:
                            qty = 0
                            if l.price_unit!=0:
                                qty = l.quantity
                            if l.invoice_id.type == 'out_refund':
                                d['return_qty'] = d['return_qty'] + qty
                            else:
                                d['qty'] = d['qty'] + qty
                                d['free_qty'] = d['free_qty'] + l.free_qty
                                
                                this_price_unit = l.price_unit or 0.0
                                if this_price_unit:
                                   this_price_unit = this_price_unit / exchange_rate 
                                this_discount = (l.discount_share + l.discount_amount) or 0.0
                                if this_discount:
                                   this_discount = this_discount / exchange_rate
                                   
#                                d['price_unit'] = d['price_unit'] + l.price_unit                                   
#                                d['discount'] = d['discount'] + (l.discount_share + l.discount_amount)
                                d['price_unit'] = d['price_unit'] + this_price_unit
                                d['discount'] = d['discount'] + this_discount
                                d['subtotal'] = d['subtotal'] + ((l.price_subtotal / exchange_rate) - this_discount)
                            add=False
                    if add:
                        t['srl'] = i
                        t['item'] = l.product_id.display_name
                        t['qty'] = 0
                        qty = 0
                        if l.price_unit!=0:
                            qty = l.quantity
                        t['qty'] = qty
                        t['free_qty'] = l.free_qty
                        if l.invoice_id.type == 'out_refund':
                            t['qty'] = 0
                            t['return_qty'] = qty
                            t['price_unit'] = 0
                            t['discount'] = 0
                            t['subtotal'] = 0
                        else:
                            this_price_unit = l.price_unit or 0.0
                            if this_price_unit:
                                this_price_unit = this_price_unit / exchange_rate
                            this_discount = (l.discount_share + l.discount_amount) or 0.0
                            if this_discount:
                               this_discount = this_discount / exchange_rate
                            
#                            t['price_unit'] = l.price_unit
#                            t['discount'] = l.discount_share + l.discount_amount
                            t['qty'] = qty
                            t['return_qty'] = 0
                            t['price_unit'] = this_price_unit
                            t['discount'] = this_discount
                            t['subtotal'] = (l.price_subtotal / exchange_rate) - this_discount

                        vals[customer.name].append(t)
                        i+=1
                        
        # Cateogy group
        if obj.group_by == 'category':
            categories = []
            for l in final_invoice_line_ids:
                category = l.product_id.categ_id
                if category in categories:
                    print"category already in dict"
                    continue
                categories.append(category)
                
            vals = {}
            for category in categories:
                vals[category.name] = []
                i = 1
                for l in final_invoice_line_ids:
                    t = {}
                    if category.id != l.product_id.categ_id.id:
                        print"diff categ continue"
                        continue
                        
                    currency = l.invoice_id.currency_id
                    exchange_rate = 1.0
                    if currency.name!='KWD':
                        exchange_rate = l.invoice_id.exchange_rate
                        
                    add=True
                    for d in vals[category.name]:
                        if d['item'] == l.product_id.display_name:
                            qty = 0
                            if l.price_unit!=0:
                                qty = l.quantity
                            if l.invoice_id.type == 'out_refund':
                                d['return_qty'] = d['return_qty'] + qty
                            else:
                                d['qty'] = d['qty'] + qty
                                d['free_qty'] = d['free_qty'] + l.free_qty
#                                d['price_unit'] = d['price_unit'] + l.price_unit
#                                d['discount'] = d['discount'] + (l.discount_share + l.discount_amount)
#                                d['subtotal'] = d['subtotal'] + (l.price_subtotal - l.discount_share)
                                
                                this_price_unit = l.price_unit or 0.0
                                if this_price_unit:
                                   this_price_unit = this_price_unit / exchange_rate 
                                this_discount = (l.discount_share + l.discount_amount) or 0.0
                                if this_discount:
                                   this_discount = this_discount / exchange_rate                                
                                   
                                d['price_unit'] = d['price_unit'] + this_price_unit
                                d['discount'] = d['discount'] + this_discount
                                d['subtotal'] = d['subtotal'] + ((l.price_subtotal / exchange_rate) - this_discount)
                                
                            add=False
                    if add:
                        t['srl'] = i
                        t['item'] = l.product_id.display_name
                        t['qty'] = 0
                        qty = 0
                        if l.price_unit!=0:
                            qty = l.quantity
                        t['qty'] = qty
                        t['free_qty'] = l.free_qty
                        if l.invoice_id.type == 'out_refund':
                            t['qty'] = 0
                            t['return_qty'] = qty
                            t['price_unit'] = 0
                            t['discount'] = 0
                            t['subtotal'] = 0
                        else:
                            this_price_unit = l.price_unit or 0.0
                            if this_price_unit:
                               this_price_unit = this_price_unit / exchange_rate 
                            this_discount = (l.discount_share + l.discount_amount) or 0.0
                            if this_discount:
                               this_discount = this_discount / exchange_rate
                            
                            t['qty'] = qty
                            t['return_qty'] = 0
                            t['price_unit'] = this_price_unit
                            t['discount'] = this_discount
                            t['subtotal'] = ((l.price_subtotal / exchange_rate) - this_discount)
#                            t['price_unit'] = l.price_unit
#                            t['discount'] = l.discount_share + l.discount_amount
#                            t['subtotal'] = l.price_subtotal - l.discount_share

                        vals[category.name].append(t)
                        i+=1
                        
        # Product group
        if obj.group_by == 'product':
            products = []
            for l in final_invoice_line_ids:
                product = l.product_id
                if product in products:
                    print"product already in dict"
                    continue
                products.append(product)
                
            vals = {}
            for product in products:
                vals[product.name] = []
                i = 1
                for l in final_invoice_line_ids:
                    t = {}
                    if product.id != l.product_id.id:
                        print"diff product continue"
                        continue
                        
                    currency = l.invoice_id.currency_id
                    exchange_rate = 1.0
                    if currency.name!='KWD':
                        exchange_rate = l.invoice_id.exchange_rate
                        
                    add=True
                    for d in vals[product.name]:
                        if d['item'] == l.product_id.display_name:
                            qty = 0
                            if l.price_unit!=0:
                                qty = l.quantity
                            if l.invoice_id.type == 'out_refund':
                                d['return_qty'] = d['return_qty'] + qty
                            else:
                                d['qty'] = d['qty'] + qty
                                d['free_qty'] = d['free_qty'] + l.free_qty
                                
                                this_price_unit = l.price_unit or 0.0
                                if this_price_unit:
                                   this_price_unit = this_price_unit / exchange_rate 
                                this_discount = (l.discount_share + l.discount_amount) or 0.0
                                if this_discount:
                                   this_discount = this_discount / exchange_rate                                
                                   
                                d['price_unit'] = d['price_unit'] + this_price_unit
                                d['discount'] = d['discount'] + this_discount
                                d['subtotal'] = d['subtotal'] + ((l.price_subtotal / exchange_rate) - this_discount)
#                                d['price_unit'] = d['price_unit'] + l.price_unit
#                                d['discount'] = d['discount'] + (l.discount_share + l.discount_amount)
#                                d['subtotal'] = d['subtotal'] + (l.price_subtotal - l.discount_share)
                            add=False
                    if add:
                        t['srl'] = i
                        t['item'] = l.product_id.display_name
                        t['qty'] = 0
                        qty = 0
                        if l.price_unit!=0:
                            qty = l.quantity
                        t['qty'] = qty
                        t['free_qty'] = l.free_qty
                        if l.invoice_id.type == 'out_refund':
                            t['qty'] = 0
                            t['return_qty'] = qty
                            t['price_unit'] = 0
                            t['discount'] = 0
                            t['subtotal'] = 0
                        else:
                            this_price_unit = l.price_unit or 0.0
                            if this_price_unit:
                               this_price_unit = this_price_unit / exchange_rate 
                            this_discount = (l.discount_share + l.discount_amount) or 0.0
                            if this_discount:
                               this_discount = this_discount / exchange_rate
                            
                            t['qty'] = qty
                            t['return_qty'] = 0
                            t['price_unit'] = this_price_unit
                            t['discount'] = this_discount
                            t['subtotal'] = (l.price_subtotal / exchange_rate) - this_discount
#                            t['price_unit'] = l.price_unit
#                            t['discount'] = l.discount_share + l.discount_amount
#                            t['subtotal'] = l.price_subtotal - l.discount_share

                        vals[product.name].append(t)
                        i+=1
        
        return vals
#        return fdict

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: