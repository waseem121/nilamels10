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
from datetime import datetime, timedelta, date

class SalesAnalysisGroup(models.TransientModel):
    _name = "sales.analysis.group"
    
    @api.model
    def _get_date_from(self):
        date = datetime.today()
        date = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
        return date
    
    @api.model
    def _get_date_to(self):
        date = datetime.today()
#        date = datetime(date.year, 12, 31).strftime("%Y-%m-%d")
        return date    
    
    category_id = fields.Many2one('product.category', string="Category")
    account_type_id = fields.Many2one('account.account.type', string="Account Group")
    date_from = fields.Date(string='From date', default=_get_date_from)
    date_to = fields.Date(string='To date', default=_get_date_to)
    state = fields.Selection(
        [('all', 'All'),
        ('posted', 'Posted'),
        ('not_posted', 'Not Posted')],
        string='State', default='all'
    )    
#    group_account = fields.selection([('')])
    

    @api.multi
    def do_print(self):
        self.clear_caches()
        print"do print calledddd"
#        return {}
        datas = {
            'model': self._name,
            'docids':self.id,
            'category_id': self.category_id and self.category_id.id or False,
            'account_type': self.account_type_id and self.account_type_id.id or False,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'state': self.state,
        }
        return self.env['report'].get_action(self, 'direct_sale.report_sales_analysis_group', data=datas)
    
class ReportSalesAnalysisGroup(models.AbstractModel):
    _name = 'report.direct_sale.report_sales_analysis_group'
    
    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        final_lines = []
        header_lines = []
        
        sub_header_values = []
        sub_header_values.append('Sales')
        sub_header_values.append('Cost')
        sub_header_values.append('Profit')

        sub_header_values.append('Sales')
        sub_header_values.append('Cost')
        sub_header_values.append('Profit')

        sub_header_values.append('Sales')
        sub_header_values.append('Cost')
        sub_header_values.append('Profit')
        
        sub_header_values.append('Total Sales')
        sub_header_values.append('Total Cost')
        sub_header_values.append('Total Profit')
        print"sub_header_values: ",sub_header_values

        sub_header = {}
        sub_header['account_group'] = ''
        sub_header['categ_lines'] = sub_header_values
        final_lines.append(sub_header)
        
        main_categ = self.env['product.category'].search([('parent_id','=',False)])
        categories = self.env['product.category'].search([('parent_id','=',main_categ[0].id)])
        categ_lines = []
        for categ in categories:
            categ_lines.append(categ.name)
        categ_lines.append('Total')
        
        header = {}
        header['account_group'] = 'Account Group'
        header['categ_lines'] = categ_lines
        header_lines.append(header)
        
        Account = self.env['account.account']
        Category = self.env['product.category']
        Invoice = self.env['account.invoice']        
        
        
#        if data.get('account_type',False):
#            account_types = [self.env['account.account.type'].browse(data.get('account_type'))]
#        else:
#            account_types = self.env['account.account.type'].search([('name','=','Receivable')])
            
        domain = [('code','in',(1211,1212,1213,1214,1215))]
        group_accounts = Account.search(domain)
        print"group accounts: ",group_accounts

        bottom_sales, bottom_cost, bottom_profit = 0,0,0
        
        for group_account in group_accounts:
            child_account_ids = Account.search([('parent_id', 'child_of', [group_account.id])])
            if not len(child_account_ids):
                continue
            
            categ_values = []
            r_sales, r_cost, r_profit = 0,0,0
            for category in categories:
                child_categories = Category.search([('id','child_of',category.id)])
                child_category_ids = []
                if len(child_categories):
                    child_category_ids = child_categories.ids
                child_category_ids.append(category.id)
                category_id = data.get('category_id',False)
                
                if category_id and (category_id in child_category_ids):
                    new_child_categories = Category.search([('id','child_of',category_id)])
                    new_child_category_ids = []
                    if len(new_child_categories):
                        new_child_category_ids = new_child_categories.ids
                    new_child_category_ids.append(category_id)
                    child_category_ids = new_child_category_ids
                domain = [('account_id','in',child_account_ids.ids),
                            ('state','not in',('draft','cancel')),
                            ('type','in',('out_invoice','out_refund'))
                        ]
                        
                state = data.get('state','posted')
                if state== 'all':
                    domain.append(('state', '!=', 'cancel'))
                if state== 'posted':
                    domain.append(('state', 'not in', ('cancel','draft')))
                if state== 'not_posted':
                    domain.append(('state', '=', 'draft'))
                    
                if data.get('date_from', False):
                    domain.append(('date_invoice', '>=', data.get('date_from')))
                if data.get('date_to', False):
                    domain.append(('date_invoice', '<=', data.get('date_to')))
                    
                invoice_ids = Invoice.search(domain)
                
                sales, cost, profit = 0.0, 0.0, 0.0
                for invoice in invoice_ids:
                    this_sales, this_cost, this_profit = 0, 0, 0
                    currency = invoice.currency_id
                    exchange_rate = 1.0
                    if currency.name!='KWD':
                        exchange_rate = invoice.exchange_rate
                    for l in invoice.invoice_line_ids:
                        if l.product_id.categ_id.id in child_category_ids:
                           this_sales += ((l.price_subtotal/exchange_rate) - (l.discount_share/exchange_rate) - (l.commission_share/exchange_rate))
                           this_cost += ((l.cost_price/exchange_rate) * (l.quantity + l.free_qty))
                           this_profit += (this_sales - this_cost)
                    if invoice.type == 'out_refund':
                        sales -=this_sales
                        cost -=this_cost
                        profit -=this_profit
                    else:
                        sales +=this_sales
                        cost +=this_cost
                        profit +=this_profit
                r_sales += sales
                r_cost += cost
                r_profit += profit
                

                
                categ_values.append(sales)
                categ_values.append(cost)
                categ_values.append(profit)
                
            categ_values.append(r_sales)
            categ_values.append(r_cost)
            categ_values.append(r_profit)
            
            bottom_sales += r_sales
            bottom_cost += r_cost
            bottom_profit += r_profit
            
            v = {}
            v['account_group'] = group_account.name
            v['categ_lines'] = categ_values
            final_lines.append(v)
#        print"bottom_sales: ",bottom_sales
        
        bottom_values = []
        ## row sales total
        

        ## adding Totals row
        i = 0
        for category in categories:
            bottom_cat_sales, bottom_cat_cost, bottom_cat_profit = 0,0,0
            for line in final_lines:
                if not line.get('account_group',False):
                    continue
                l = line.get('categ_lines')
                bottom_cat_sales += l[i]
                bottom_cat_cost += l[i+1]
                bottom_cat_profit += l[i+2]
            i += 3

            bottom_values.append('{:.3f}'.format(bottom_cat_sales))
            bottom_values.append('{:.3f}'.format(bottom_cat_cost))
            bottom_values.append('{:.3f}'.format(bottom_cat_profit))
        ## row sales total
        
#        bottom_values = []
#        bottom_values.append('')
#        bottom_values.append('')
#        bottom_values.append('')
#        
#        bottom_values.append('')
#        bottom_values.append('')
#        bottom_values.append('')
#
#        bottom_values.append('')
#        bottom_values.append('')
#        bottom_values.append('Total')
        
        bottom_values.append('{:.3f}'.format(bottom_sales))
        bottom_values.append('{:.3f}'.format(bottom_cost))
        bottom_values.append('{:.3f}'.format(bottom_profit))
#        print"bottom_values: ",bottom_values
       

        bottom_line = {}
        bottom_line['account_group'] = ''
        bottom_line['categ_lines'] = bottom_values
        final_lines.append(bottom_line)

        
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('direct_sale.report_sales_analysis_group')
        docids = self.env[data['model']].browse(data['docids'])
        
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data': final_lines,
            'header_lines': header_lines,
            'final_lines': final_lines,
        }
        return report_obj.render('direct_sale.report_sales_analysis_group', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: