# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import date


class weekly_report(models.TransientModel):
    _name = "weekly.report"

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())

    @api.multi
    def generate_weekly_report(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
            'date_from':self.date_from,
            'date_to':self.date_to,
        }
        return self.env['report'].get_action(self, 'weekly_account_report.weekly_report_template', data=datas)
    
    #This is temp script for updating the labels in voucher from invoice shipping address field
    @api.multi
    def temp_update_labels(self):
        invoices = self.env['account.invoice'].search([('type','in',('out_invoice','out_refund')),
                    ('state','in',('proforma','proforma2','open','paid'))])
        print"len(invoices): ",len(invoices)
        if len(invoices):
            for invoice in invoices:
#                if invoice.id != 230:
#                    print"skip for now!"
#                    continue
                move_id = invoice.move_id or False
                print"move_id",move_id
                if not move_id:
                    continue
                
                shipping_name = invoice.partner_shipping_id and invoice.partner_shipping_id.name or False
                if not shipping_name:
                    street = invoice.partner_shipping_id and invoice.partner_shipping_id.street or False
                    if street:
                        shipping_name = street
                if not shipping_name:
                    street = invoice.partner_id.name or invoice.partner_id.street or False
                    if street:
                        shipping_name = street
                name = shipping_name
                if not name:
                    print"no name, continue"
                    continue

                for l in move_id.line_ids:
                    l.write({'name':name})
                    print"move name updated..."
        
        print"done updating move names, Exit"
        return True
    
class report_weekly_account_report_weekly_report_template(models.AbstractModel):
    _name = 'report.weekly_account_report.weekly_report_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('weekly_account_report.weekly_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'get_division_lines':self.get_division_lines,
    
            'get_sales_res_staff':self.get_sales_res_staff,
            'get_delivered_invoices':self.get_delivered_invoices,
            'get_cash_collection':self.get_cash_collection,
            'get_account_receivalble_res':self.get_account_receivalble_res,
            'get_account_payable_res':self.get_account_payable_res,
            'get_quotatoin_received_from_moh_res':self.get_quotatoin_received_from_moh_res,
            'get_quotatoin_submitted_res':self.get_quotatoin_submitted_res,
            'get_purchase_res':self.get_purchase_res,

        }
        return report_obj.render('weekly_account_report.weekly_report_template', docargs)
    
    
    def get_quotatoin_received_from_moh_res(self,obj):
        res = []
        purchase_orders = self.env['purchase.order'].search([('state','=','draft'),
                    ('date_order','>=',obj.date_from),
                    ('date_order','<=',obj.date_to)])
                    
        for order in purchase_orders:
            for line in order.order_line:
                each_dict = {}
                each_dict['rfq_code'] = order.name
                each_dict['supplier'] = order.partner_id.name
                each_dict['item'] = line.product_id.name
                each_dict['closing'] = line.price_subtotal
                res.append(each_dict)
        return res
    
    def get_quotatoin_submitted_res(self,obj):
        res = []
        purchase_orders = self.env['purchase.order'].search([('state','=','purchase'),
                    ('date_order','>=',obj.date_from),
                    ('date_order','<=',obj.date_to)])
                    
        for order in purchase_orders:
            for line in order.order_line:
                each_dict = {}
                each_dict['rfq_code'] = order.name
                each_dict['supplier'] = order.partner_id.name
                each_dict['item'] = line.product_id.name
                each_dict['closing'] = line.price_subtotal
                res.append(each_dict)
        return res
    
    def get_purchase_res(self,obj):
        res = []
#        customer_groups = self.env['customer.department'].search([])
        purchase_obj = self.env['purchase.order']
        inv_obj = self.env['account.invoice']
#        for group in customer_groups:
        for division in self.env['customer.division'].search([]):
            self.env.cr.execute("select po.id from purchase_order po,res_partner p where po.partner_id=p.id and "\
                "p.customer_division_id=%s and po.state in ('purchase','done') and po.date_order>=%s and po.date_order<=%s", (division.id,obj.date_from,obj.date_to))
            query_results = self.env.cr.dictfetchall()            
            for each in query_results:
                order = purchase_obj.browse(each.get('id'))
                invoices = inv_obj.search([('origin','=',order.name)])
                for invoice in invoices:
                    each_dict = {}
                    each_dict['division'] = division.name
                    each_dict['supplier'] = order.partner_id.name
                    each_dict['date'] = order.date_order
                    each_dict['invoice_detail'] = invoice.number
                    each_dict['closing'] = invoice.amount_total
                    res.append(each_dict)
        return res
    
    def get_account_receivalble_res(self,obj):
        res = []
#        a = {}
#        a['name']='Test'
#        a['total']=12.345
#        res.append(a)
        
        
        account_type_ids = self.env['account.account.type'].search([('name','=','Receivable')])
        accounts = self.env['account.account'].search([('user_type_id','=',account_type_ids[0].id)])
#        accounts = self.env['account.account'].search([('type','=','receivable')])
        used_ids = []
        count = 1
        for account in accounts:
#            if count>=10:
#                continue    #TODO remove this
            each_dict = {}
            if float(account.balance ) == 0.0:
                continue
            if account.id in used_ids:
                continue
                
            each_dict['name'] = account.name
            each_dict['total'] = account.balance
            res.append(each_dict)
            used_ids.append(account.id)
            count+=1
        
        return res
    
    def get_account_payable_res(self,obj):
        res = []
        account_type_ids = self.env['account.account.type'].search([('name','=','Payable')])
        accounts = self.env['account.account'].search([('user_type_id','=',account_type_ids[0].id)])
#        accounts = self.env['account.account'].search([('type','=','payable')])
        used_ids = []
        count = 1
        for account in accounts:
#            if count>=10:
#                continue    #TODO remove this
            each_dict = {}
            if float(account.balance ) == 0.0:
                continue
            if account.id in used_ids:
                continue
                
            each_dict['name'] = account.name
            each_dict['total'] = account.balance
            res.append(each_dict)
            used_ids.append(account.id)
            count+=1
        
        return res    
    
#    def get_customer_divisions(self, obj):
#        res = []
#        for customer_division in obj.env['customer.division'].search([]):
#            res.append(customer_division.name)
#        return res    
    
    # new, get Division lines
    def get_division_lines(self, obj):
        res = []
        inv_obj = self.env['account.invoice']
        
        for division in self.env['customer.division'].search([]):
            self.env.cr.execute("select id from account_invoice where "\
                "state in ('open','paid') and division_id=%s and "\
                "date_invoice>=%s and date_invoice<=%s and type in ('out_invoice','out_refund')", (division.id, obj.date_from, obj.date_to))
#            self.env.cr.execute("select inv.id from account_invoice inv,res_partner p where inv.partner_id=p.id and "\
#                "p.customer_division_id=%s and inv.state in ('open','paid') and "\
#                "inv.date_invoice>=%s and inv.date_invoice<=%s and inv.type in ('out_invoice','out_refund')", (division.id, obj.date_from, obj.date_to))
            query_results = self.env.cr.dictfetchall()
#            print"query_results======: ",query_results

            invoice_ids, amount, each_dict = [], 0.0, {}
            for each in query_results:
                invoice = inv_obj.browse(each.get('id'))
                amount += invoice.amount_total
                invoice_ids.append(invoice.id)

            each_dict['division'] = division.name
            each_dict['amount'] = amount
            each_dict['qty'] = len(invoice_ids)
            res.append(each_dict)
#        print"res: ",res
        return res
#    
      
    def get_sales_res_staff(self, obj):
        res = []

        inv_obj = self.env['account.invoice']
        for user in self.env['res.users'].search([]):
#            self.env.cr.execute("select inv.id from account_invoice inv,res_users u where inv.user_id=u.id and "\
#                "u.id=%s and inv.state in ('open','paid') and inv.date_invoice>=%s and inv.date_invoice<=%s", (user.id,obj.date_from,obj.date_to))
            self.env.cr.execute("select inv.id from account_invoice inv,res_users u where inv.user_id=u.id and "\
                "u.id=%s and inv.state != 'cancel' and inv.type='out_invoice' and inv.date_invoice>=%s and inv.date_invoice<=%s", (user.id,obj.date_from,obj.date_to))
            query_results = self.env.cr.dictfetchall()
            
            invoice_ids, amount,each_dict = [], 0.0, {}
            for each in query_results:
                invoice = inv_obj.browse(each.get('id'))
                amount += invoice.amount_total
                invoice_ids.append(invoice.id)
            
            if amount == 0.0:
                continue
                
            each_dict['name'] = user.name
            each_dict['amount'] = amount
            each_dict['no_of_inv'] = len(invoice_ids)
            res.append(each_dict)
        
        return res
    
    def get_delivered_invoices(self, obj):
        res = []
#        a = {'name':'ASHAR', 'inv_number':'INV-001','amount':39}
#        b = {'name':'Majdi', 'inv_number':'INV-002','amount':46}
#        c = {'name':'Abdullah', 'inv_number':'INV-003','amount':16}
#
#        res.append(a)
#        res.append(b)
#        res.append(c)
#        return res
#        res = []
        
        inv_obj = self.env['account.invoice']
        for user in self.env['res.users'].search([]):
            self.env.cr.execute("select inv.id from account_invoice inv,res_users u where inv.user_id=u.id and "\
                "u.id=%s and inv.state in ('open','paid') and inv.date_invoice>=%s and inv.date_invoice<=%s", (user.id,obj.date_from,obj.date_to))
            query_results = self.env.cr.dictfetchall()
  
            for each in query_results:
                each_dict = {}
                invoice = inv_obj.browse(each.get('id'))
                picking = invoice.invoice_picking_id or False
#                if not picking:
#                    continue
#                if picking.state != 'done':
#                    continue
                if invoice.amount_total == 0.0:
                    continue

                each_dict['name'] = user.name
                each_dict['inv_number'] = invoice.number
                each_dict['amount'] = invoice.amount_total
                res.append(each_dict)        
        return res
    
    def get_cash_collection(self, obj):

        res = []
        payment_obj = self.env['account.payment']
        partners = self.env['res.partner'].search([('is_salesman','=',True)])
        
        settings = self.env['sale.config.settings'].search([])
        if len(settings):
            collector_based = settings.collector_based or False
            if collector_based:
                partners = self.env['res.partner'].search([('is_collector','=',True)])
        partners = self.env['res.partner'].search([('is_collector','=',True)])
        salesman_based = False
        for partner in partners:
#            self.env.cr.execute("select ap.id from account_payment ap,res_partner p where ap.collector_id=p.id and "\
#                "p.id=%s and ap.state in ('posted') and ap.payment_type='inbound' and ap.payment_date>=%s and ap.payment_date<=%s", (partner.id,obj.date_from,obj.date_to))
            self.env.cr.execute("select id from account_payment where collector_id=%s and "\
                "state in ('posted','sent','reconciled') and payment_type='inbound' and payment_date>=%s and payment_date<=%s", (partner.id,obj.date_from,obj.date_to))
            if salesman_based:
                self.env.cr.execute("select ap.id from account_payment ap,res_partner p where ap.salesman_id=p.id and "\
                    "p.id=%s and ap.state in ('posted') and ap.payment_type='inbound' and ap.payment_date>=%s and ap.payment_date<=%s", (partner.id,obj.date_from,obj.date_to))                
            query_results = self.env.cr.dictfetchall()
            
            for each in query_results:
                each_dict = {}
                payment = payment_obj.browse(each.get('id'))
       
                each_dict['name'] = partner.name
                each_dict['date_from'] = obj.date_from
                each_dict['date_to'] = obj.date_to
                each_dict['amount'] = payment.amount
                res.append(each_dict)        
        return res
