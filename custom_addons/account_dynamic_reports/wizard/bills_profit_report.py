from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import time

FETCH_RANGE = 2000


class BillsProfitReport(models.TransientModel):
    _name = "bills.profit.report"
    
    @api.model
    def _get_default_company(self):
        return self.env.user.company_id
    
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

    category_ids = fields.Many2many('product.category', string='Category')
    location_id = fields.Many2one('stock.location', string='Store', domain=[('usage', '=', 'internal')])
    salesman_id = fields.Many2one('res.users', string='Salesman')
    division_id = fields.Many2one('customer.division', string='Division')
    department_id = fields.Many2one('customer.department', string='Department')
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer', '=', True)])
#    account_id = fields.Many2one('account.account', string='Account', domain=['|',('type', 'in', ('receivable',)),('group_account','=',True)])
    account_id = fields.Many2one('account.account', string='Account', domain=['|',('type', 'in', ('receivable',)),('user_type_id.name','=','Asset View')])
#    brand_id = fields.Many2one('product.brand', string='Brand')
    date_from = fields.Date(string='From date', default=_get_date_from)
    date_to = fields.Date(string='To date', default=_get_date_to)

    show_profit_percent_sales = fields.Boolean(string='Show Profit (%) Sales')
    show_profit_percent_cost = fields.Boolean(string='Show Profit (%) Cost')
    show_profit_percent_net_profit = fields.Boolean(string='Show Profit (%) Net Profit')

    group_by = fields.Selection(
        [('none', 'None'),
        ('salesman', 'Salesman'),
        ('customer', 'Customer')
        ],
        string='Group by', default='none'
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=_get_default_company
    )
    sort_by = fields.Selection(
        [('customer', 'Customer'),
        ('bill_no', 'Bill Number'),
        ('profit', 'Profit'),
        ('date', 'Date')],
        string='Sort by', default='customer'
    )
    based_on = fields.Selection(
        [('sales_and_returns', 'Sales and Returns'),
        ('sales', 'Sales'),
        ('returns', 'Returns')],
        string='Based On', default='sales_and_returns'
    )
    state = fields.Selection(
        [('all', 'All'),
        ('posted', 'Posted'),
        ('not_posted', 'Not Posted')],
        string='State', default='all'
    )
    
    
    @api.model
    def create(self, vals):
        ret = super(BillsProfitReport, self).create(vals)
        return ret

    @api.multi
    def write(self, vals):
        ret = super(BillsProfitReport, self).write(vals)
        return ret
    
    
    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('"Date from" must be less than or equal to "Date to"'))
        return True
    
    def get_filters(self, default_filters={}):
        
#        products = self.product_ids if self.product_ids else self.env['product.product'].search([])

        all_sub_categ = []
        category_ids = self.category_ids.ids or []
        print"category_ids: ",category_ids
        if category_ids:
            categs = self.env['product.category'].browse(category_ids)
            for categ in categs:
                for sub_categ_id in categ.search([('id', 'child_of', categ.id)]).ids:
                    all_sub_categ.append(sub_categ_id)
        print"all_sub_categ: ",all_sub_categ
        category_ids = list(set(all_sub_categ))

        category_list = ['All Categories']
        if self.category_ids:
            category_list = [c.name for c in self.category_ids]
#        if len(category_ids):
#            category_list = [c.name for c in self.env['product.category'].browse(category_ids)]
            
        
        salesman = 'All'
        if self.salesman_id:
            salesman = self.salesman_id.name
        
        location = 'All'
        if self.location_id:
            location = self.location_id.name
            
        division = 'All'
        if self.division_id:
            division = self.division_id.name
            
        department = 'All'
        if self.department_id:
            department = self.department_id.name
            
        customer = 'All'
        if self.partner_id:
            customer = self.partner_id.name
            
        
        filter_dict= {
            'category_ids': category_ids,
            'location_id': self.location_id or False,
            'location': location,
            'salesman_id': self.salesman_id or False,
            'salesman': salesman,
            'division_id': self.division_id or False,
            'division':division,
            'department_id': self.department_id or False,
            'department': department,
            'partner_id': self.partner_id or False,
            'account_id': self.account_id or False,
            'account': self.account_id and self.account_id.name or '',
            'date_from': self.date_from or '2020-01-01',
            'date_to': self.date_to or '2030-01-01',
            'show_profit_percent_sales': self.show_profit_percent_sales or False,
            'show_profit_percent_cost': self.show_profit_percent_cost or False,
            'show_profit_percent_net_profit': self.show_profit_percent_net_profit or False,
            
            'based_on': self.based_on or False,
            'sort_by': self.sort_by or False,
            'state': self.state or 'all',
            'group_by': self.group_by or False,
            'customer': customer,
            
            'category_list': category_list,
            
            # For Js widget only
#            'product_list': [(p.id, p.name) for p in products],

        }
        filter_dict.update(default_filters)
        return filter_dict
    
    def process_filters(self):
        ''' To show on report headers'''
        
        data = self.get_filters(default_filters={})
        filters = {}
        
        if data.get('category_ids', []):
            filters['categories'] = self.env['product.category'].browse(data.get('category_ids', [])).mapped('name')
        else:
            filters['categories'] = ['All']

        # For Js framework
        filters['show_profit_percent_sales'] = data.get('show_profit_percent_sales')
        filters['show_profit_percent_cost'] = data.get('show_profit_percent_cost')
        filters['show_profit_percent_net_profit'] = data.get('show_profit_percent_net_profit')
        filters['group_by'] = data.get('group_by', False)
        
        filters['date_from'] = data.get('date_from')
        filters['date_to'] = data.get('date_to')
        filters['based_on'] = data.get('based_on')
        filters['sort_by'] = data.get('sort_by')
        filters['state'] = data.get('state')
        filters['category_list'] = data.get('category_list')
        filters['salesman'] = data.get('salesman')
        filters['division'] = data.get('division')
        filters['location'] = data.get('location')
        filters['department'] = data.get('department')
        filters['customer'] = data.get('customer')
        filters['account'] = data.get('account')
        
#        filters['product_list'] = data.get('product_list')

        return filters
    
    def process_data(self):
        '''
        It is the method for showing summary details of each accounts. Just basic details to show up
        Three sections,
        1. Initial Balance
        2. Current Balance
        3. Final Balance
        :return:
        '''
        data = self.get_filters(default_filters={})
#        print"filter data: ",data
         
        date_from = data.get('date_from','2020-01-01')
        date_to = data.get('date_to','2030-01-01')
        domain = [('invoice_id.date_invoice', '>=', date_from),
                ('invoice_id.date_invoice', '<=', date_to)]
         
        based_on = data.get('based_on','sales_and_returns')
        if based_on == 'sales_and_returns':
            domain.append(('invoice_id.type', 'in', ('out_invoice','out_refund')))
        if based_on == 'sales':
            domain.append(('invoice_id.type', '=', 'out_invoice'))
        if based_on == 'returns':
            domain.append(('invoice_id.type', '=', 'out_refund'))
             
        state = data.get('state','all')
#        domain.append(('invoice_id.id', '=', 220))
        if state== 'all':
            domain.append(('invoice_id.state', '!=', 'cancel'))
        if state== 'posted':
            domain.append(('invoice_id.state', 'not in', ('cancel','draft')))
        if state== 'not_posted':
            domain.append(('invoice_id.state', '=', 'draft'))
 
        if data.get('location_id'):
            location_id = data.get('location_id')
            domain.append(('invoice_id.location_id','=',location_id.id))
        if data.get('salesman_id'):
            salesman_id = data.get('salesman_id')
            domain.append(('invoice_id.user_id','=',salesman_id.id))
        if data.get('division_id'):
            division_id = data.get('division_id')
            domain.append(('invoice_id.division_id','=',division_id.id))
        if data.get('department_id'):
            department_id = data.get('department_id')
            domain.append(('invoice_id.department_id','=',department_id.id))
        if data.get('partner_id'):
            partner_id = data.get('partner_id')
            domain.append(('invoice_id.partner_id','=',partner_id.id))
        if data.get('category_ids',[]):
            category_ids = list(set(data.get('category_ids')))
            domain.append(('product_id.categ_id', 'in', category_ids))
        print"process_data domainnnn: ",domain
 
#        domain.append(['invoice_id','in',(310,)])
#         invoice_line_ids_temp = self.env['account.invoice.line'].search(domain).ids
#         invoice_line_ids = [210577, 210578, 210579, 210580, 210581, 210582, 210583, 210584, 210585, 210586, 210587, 210588, 210589, 210590, 210591, 210592, 210593, 210594, 210595, 210596, 210597, 210598, 210599, 210600, 210601, 210602, 210603, 210604, 210605, 210606, 210607, 210608, 210609, 210610, 210611, 210612, 210613, 210614, 210615, 210616, 210617, 210618, 210619, 210620, 210621, 210622, 210623, 210624, 210625, 210626, 210627, 210628, 210629, 210630, 210631, 210632, 210633, 210634, 210635, 210636, 210637, 210638, 210639, 210640, 210641, 210642, 210643, 210644, 210645, 210646, 210647, 210648, 210649, 210650, 210651, 210652, 210653, 210654, 210655, 210656, 210657, 210658, 210659, 210660, 210661]
#         print"len(invoice_line_ids) ",len(invoice_line_ids),invoice_line_ids
        qry = """
            SELECT ail.id as id,
            COALESCE(ail.free_qty,0) as free_qty,
            COALESCE(ail.commission_share,0) as commission_share,
            1/ COALESCE(uom.factor,1) * COALESCE(ail.cost_price,0) as cost_price,
            ail.price_subtotal as price_subtotal,
            ail.discount_share as discount_share,
            ail.quantity as quantity,
            COALESCE(ai.exchange_rate, 1.0) as exchange_rate,
            ai.refund_without_invoice as refund_without_invoice,
            ai.id as invoice_id,
            ai.number as number,
            ai.date_invoice as date_invoice,
            ai.partner_id as partner_id,
            rp.name as partner_name,
            ai.type as type
            FROM account_invoice_line ail
            JOIN account_invoice ai ON (ai.id = ail.invoice_id)
            JOIN res_partner rp ON(rp.id = ai.partner_id) 
            JOIN product_product pp ON (pp.id=ail.product_id)
            JOIN product_template pt ON (pt.id=pp.product_tmpl_id)
            JOIN product_uom uom ON (uom.id=ail.uom_id)
            WHERE ai.date_invoice BETWEEN '%s' AND '%s'
        """ %(date_from,date_to)
        based_on = data.get('based_on','sales_and_returns')
        if based_on == 'sales_and_returns':
            qry += " AND ai.type IN ('out_invoice','out_refund')"
        elif based_on == 'sales':
            qry += " AND ai.type = 'out_invoice'"
        elif based_on == 'returns':
            qry += " AND ai.type = 'out_refund'"
        state = data.get('state','all')
 
        if state== 'all':
            qry += " AND ai.state != 'cancel'"
        elif state== 'posted':
            qry += " AND ai.state NOT IN ('cancel','draft')"
        elif state== 'not_posted':
            qry += " AND ai.state = 'draft'"
 
        if data.get('location_id'):
            location_id = data.get('location_id')
            qry += " AND ai.location_id = '%s'"%location_id.id
        if data.get('salesman_id'):
            salesman_id = data.get('salesman_id')
            qry += " AND ai.user_id = '%s'"%salesman_id.id
        if data.get('division_id'):
            division_id = data.get('division_id')
            qry += " AND ai.division_id = '%s'"%division_id.id
        if data.get('department_id'):
            department_id = data.get('department_id')
            qry += " AND ai.department_id = '%s'"%department_id.id
        if data.get('partner_id'):
            partner_id = data.get('partner_id')
            qry += " AND ai.partner_id = '%s'"%partner_id.id
        if data.get('category_ids',[]):
            category_ids = list(set(data.get('category_ids')))
            qry += " AND pt.categ_id IN (%s)"%",".join(map(str,category_ids))
#             domain.append(('product_id.categ_id', 'in', category_ids))

        print"data.get Account: ",data.get('account_id')
        if data.get('account_id'):
            accounts = [data.get('account_id')]
            if accounts[0].type == 'view':
                child_account_ids = self.env['account.account'].search([('parent_id', 'child_of', accounts[0].ids)])
                if len(child_account_ids):
                    accounts = child_account_ids.ids
            else:
                accounts = [accounts[0].id]
            qry += " AND ai.account_id IN (%s)"%",".join(map(str,accounts))
 
        self.env.cr.execute(qry)
        invoice_line_ids = self.env.cr.dictfetchall()
#         invoice_line_ids = [r.get('id') for r in res]
#         print("\n\n our invoice>>",invoice_line_ids)
#         100/0
 
        product_ids = data.get('product_ids',[])
        product_ids = list(set(product_ids))
 
        final_res = []
        total_profit = 0.0
        total_sales, total_discount, total_extras, total_net_sales, total_cost, total_profit= 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        for l in invoice_line_ids:
            invoice = l.get('invoice_id')
            exchange_rate = l.get('exchange_rate',1.0)
            if exchange_rate == 0:
                exchange_rate = 1.0
            if len(final_res):
                skip = False
                for this_res in final_res:
                    if skip:
                        continue
  
                    invoice_id = this_res.get('invoice_id',False)
                    if (invoice_id) and (invoice_id == l.get('invoice_id')):
                        skip=True
                        this_total = l.get('price_subtotal') / exchange_rate
                        this_cost = l.get('cost_price') * (l.get('quantity') + l.get('free_qty'))
                        discount_share = l.get('discount_share') or 0.0
                        if discount_share:
                            discount_share = discount_share / exchange_rate
                        commission_share = l.get('commission_share') or 0.0
                        if commission_share:
                            commission_share = l.get('commission_share') / exchange_rate
  
#                        this_profit = this_total - this_cost
                        this_net_sales = this_total - discount_share - commission_share
                        this_profit = this_net_sales - this_cost
  
                        if l.get('type') == 'out_refund':
                            this_res['total'] -= this_total
                            this_res['discount'] -= discount_share
                            this_res['extras'] -= commission_share
                            this_res['net_sales'] -= this_net_sales
                            this_res['cost'] -= this_cost
                            this_res['profit'] -= this_profit
                            this_res['profit_f'] -= this_profit
                        else:
                            this_res['total'] += this_total
                            this_res['discount'] += discount_share
                            this_res['extras'] += commission_share
                            this_res['net_sales'] += this_net_sales
                            this_res['cost'] += this_cost
                            this_res['profit'] += this_profit
                            this_res['profit_f'] += this_profit
  
                        ##
                        if l.get('type') == 'out_refund':
                            total_sales -= this_total
                            total_discount -= discount_share or 0.0
                            total_extras -= commission_share
  
                            total_profit -= this_net_sales - this_cost
                            total_net_sales -= this_net_sales
                            total_cost -= this_cost
  
                        else:
                            total_sales += this_total
                            total_discount += discount_share or 0.0
                            total_extras += commission_share
                              
                            total_profit += (this_net_sales - this_cost)
                            total_net_sales += this_net_sales
                            total_cost += this_cost
  
#                    else:
                if not skip:
                    skip=True
                    d = {}
                    invoice = l.get('invoice_id')
                    number = l.get('number') or ''
                    if l.get('refund_without_invoice'):
                        number = 'Sales-Ret-'+str(number)
                    else:
                        number = 'Sales-'+str(number)
                    this_total = l.get('price_subtotal') / exchange_rate
                    this_cost = l.get('cost_price') * (l.get('quantity') + l.get('free_qty'))
                    this_discount = l.get('discount_share') or 0.0
                    if this_discount:
                        this_discount = this_discount / exchange_rate
                          
                    this_extras = l.get('commission_share')
                    if this_extras:
                        this_extras = this_extras / exchange_rate
                          
                    this_net_sales = this_total - this_discount - this_extras
                    this_profit = this_net_sales - this_cost
  
                    if l.get('type') == 'out_refund':
                        this_total *= -1
                        this_discount *= -1
                        this_extras *= -1
                        this_net_sales *= -1
                        this_cost *= -1
                        this_profit *= -1
  
                    d['invoice_id'] = invoice
                    d['type'] = l.get('type')
                    d['bill_no'] = number
                    d['date'] = l.get('date_invoice')
                    d['customer'] = l.get('partner_name')
                    d['total'] = this_total
                    d['discount'] = this_discount
                    d['extras'] = this_extras
                    d['net_sales'] = this_net_sales
                    d['cost'] = this_cost
                    d['profit'] = this_profit
                    d['profit_f'] = this_profit
                    d['is_line'] = True
  
                    d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
                    d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
                    d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False
                    ##
                    total_sales += this_total
                    total_discount += this_discount
                    total_profit += this_profit
                    total_extras += this_extras
                    total_net_sales += this_net_sales
                    total_cost += this_cost
  
#                    print"append"
                    final_res.append(d)
#                    print"time 1111",(str(end - start))
            else:
#                print"elsseee"
                d = {}
                invoice = l.get('invoice_id')
                number = l.get('number') or ''
                if l.get('refund_without_invoice'):
                    number = 'Sales-Ret-'+str(number)
                else:
                    number = 'Sales-'+str(number)

                if l.get('exchange_rate'):
                    this_total = l.get('price_subtotal') / l.get('exchange_rate', 1.0)
                else:
                    this_total = l.get('price_subtotal')
                this_cost = l.get('cost_price') * (l.get('quantity') + l.get('free_qty'))
                this_discount = l.get('discount_share') or 0.0
                if this_discount:
                    this_discount = this_discount / exchange_rate
                this_extras = l.get('commission_share')
                if this_extras:
                    this_extras = this_extras / exchange_rate
                this_net_sales = this_total - this_discount - this_extras
                this_profit = this_net_sales - this_cost
  
                if l.get('type') == 'out_refund':
                    this_total *= -1
                    this_discount *= -1
                    this_extras *= -1
                    this_net_sales *= -1
                    this_cost *= -1
                    this_profit *= -1
  
                d['invoice_id'] = invoice
                d['type'] = l.get('type')
                d['bill_no'] = number
                d['date'] = l.get('date_invoice')
#                 d['customer'] = invoice.partner_id.name
                d['customer'] = l.get('partner_name')
                d['total'] = this_total
                d['discount'] = this_discount
                d['extras'] = this_extras
                d['net_sales'] = this_net_sales
                d['cost'] = this_cost
                d['profit'] = this_profit
                d['profit_f'] = this_profit
                d['is_line'] = True
  
                d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
                d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
                d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False
  
                ##
                total_sales += this_total
                total_discount += this_discount
                total_profit += this_profit
                total_extras += this_extras
                total_net_sales += this_net_sales
                total_cost += this_cost
  
                final_res.append(d)
  
        # profit/total profit * 100
        print"total_profit: ",total_profit
        for d in final_res:
            d_cost = d['cost']
            d_net_sales = d['net_sales']
            if d_cost == 0: d_cost=1.0
            if d_net_sales == 0: d_net_sales=1.0
            d['profit_percent_cost'] = (d['profit_f'] / d_cost) * 100.0
            d['profit_percent_sales'] = (d['profit_f'] / d_net_sales) * 100.0
            if d['type']=='out_refund':
                d['profit_percent_cost'] = d['profit_percent_cost'] * -1
                d['profit_percent_sales'] = d['profit_percent_sales'] * -1
                
  
            total_profit_d = total_profit
            if total_profit_d == 0:
                total_profit_d = 1.0
            profit_percent_net_profit = (d['profit_f'] / total_profit_d) * 100.0
#            if d['type']=='out_refund':
#                profit_percent_net_profit *= -1
            d['profit_percent_net_profit'] = '{:.3f}'.format(profit_percent_net_profit)
            d['total'] = '{:.3f}'.format(d['total'])
            d['discount'] = '{:.3f}'.format(d['discount'])
            d['extras'] = '{:.3f}'.format(d['extras'])
            d['net_sales'] = '{:.3f}'.format(d['net_sales'])
            d['cost'] = '{:.3f}'.format(d['cost'])
            d['profit'] = '{:.3f}'.format(d['profit'])
            d['profit_percent_sales'] = '{:.3f}'.format(d['profit_percent_sales'])
            d['profit_percent_cost'] = '{:.3f}'.format(d['profit_percent_cost'])
  
        sort_by = self.sort_by or 'customer'
        if sort_by == 'profit':
            sort_by = 'profit_f'
        if sort_by == 'customer':
            final_res = sorted(final_res, key=lambda i: i[sort_by])
        else:
            final_res = sorted(final_res, key=lambda i: i[sort_by], reverse=True)
  
        d1 = {'total_sales': '{:.3f}'.format(total_sales),
            'total_discount': '{:.3f}'.format(total_discount),
            'total_extras': '{:.3f}'.format(total_extras),
            'total_net_sales': '{:.3f}'.format(total_net_sales),
            'total_cost': '{:.3f}'.format(total_cost),
            'total_profit': '{:.3f}'.format(total_profit),
            'bill_no': 'Total',
            'is_line': False,
            'show_profit_percent_sales':self.show_profit_percent_sales or False,
            'show_profit_percent_cost':self.show_profit_percent_cost or False,
            'show_profit_percent_net_profit':self.show_profit_percent_net_profit or False
        }
        final_res.append(d1)
  
#        print"final_res \n\n\n",len(final_res)
#        print"final_res \n\n\n",final_res
        return final_res
#     def process_data(self):
#         '''
#         It is the method for showing summary details of each accounts. Just basic details to show up
#         Three sections,
#         1. Initial Balance
#         2. Current Balance
#         3. Final Balance
#         :return:
#         '''
#         data = self.get_filters(default_filters={})
# #        print"filter data: ",data
#         
#         date_from = data.get('date_from','2020-01-01')
#         date_to = data.get('date_to','2030-01-01')
#         domain = [('invoice_id.date_invoice', '>=', date_from),
#                 ('invoice_id.date_invoice', '<=', date_to)]
#         
#         based_on = data.get('based_on','sales_and_returns')
#         if based_on == 'sales_and_returns':
#             domain.append(('invoice_id.type', 'in', ('out_invoice','out_refund')))
#         if based_on == 'sales':
#             domain.append(('invoice_id.type', '=', 'out_invoice'))
#         if based_on == 'returns':
#             domain.append(('invoice_id.type', '=', 'out_refund'))
#             
#         state = data.get('state','all')
# #        domain.append(('invoice_id.id', '=', 220))
#         if state== 'all':
#             domain.append(('invoice_id.state', '!=', 'cancel'))
#         if state== 'posted':
#             domain.append(('invoice_id.state', 'not in', ('cancel','draft')))
#         if state== 'not_posted':
#             domain.append(('invoice_id.state', '=', 'draft'))
# 
#         if data.get('location_id'):
#             location_id = data.get('location_id')
#             domain.append(('invoice_id.location_id','=',location_id.id))
#         if data.get('salesman_id'):
#             salesman_id = data.get('salesman_id')
#             domain.append(('invoice_id.user_id','=',salesman_id.id))
#         if data.get('division_id'):
#             division_id = data.get('division_id')
#             domain.append(('invoice_id.division_id','=',division_id.id))
#         if data.get('department_id'):
#             department_id = data.get('department_id')
#             domain.append(('invoice_id.department_id','=',department_id.id))
#         if data.get('partner_id'):
#             partner_id = data.get('partner_id')
#             domain.append(('invoice_id.partner_id','=',partner_id.id))
#         if data.get('category_ids',[]):
#             category_ids = list(set(data.get('category_ids')))
#             domain.append(('product_id.categ_id', 'in', category_ids))
#         print"process_data domainnnn: ",domain
#         
#         print"data.get Account: ",data.get('account_id')
#         if data.get('account_id'):
#             accounts = [data.get('account_id')]
#             if accounts[0].type == 'view':
#                 child_account_ids = self.env['account.account'].search([('parent_id', 'child_of', accounts[0].ids)])
#                 if len(child_account_ids):
#                     accounts = child_account_ids.ids
#                 domain.append(('invoice_id.account_id','in',accounts))
#             else:
#                 domain.append(('invoice_id.account_id','=',accounts[0].id))
#         
# #        domain.append(['invoice_id','in',(310,)])
#         invoice_line_ids = self.env['account.invoice.line'].search(domain)
#         print"len(invoice_line_ids) ",len(invoice_line_ids)
#         
#         product_ids = data.get('product_ids',[])
#         product_ids = list(set(product_ids))
# #        print"product idsss: ",product_ids
#         
#         final_res = []
#         total_profit = 0.0
#         total_sales, total_discount, total_extras, total_net_sales, total_cost, total_profit= 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
#         for l in invoice_line_ids:
# #            if l.id==1721:
# #                continue
#             invoice = l.invoice_id
#             currency = invoice.currency_id
#             exchange_rate = 1.0
#             if currency.name!='KWD':
#                 exchange_rate = invoice.exchange_rate
#                 
#             if len(final_res):
#                 skip = False
#                 for this_res in final_res:
#                     if skip:
#                         continue
#                     
#                     invoice_id = this_res.get('invoice_id',False)
#                     if (invoice_id) and (invoice_id == l.invoice_id.id):
#                         skip=True
#                         this_total = l.price_subtotal / exchange_rate
#                         
#                         this_cost = l.cost_price* (l.quantity + l.free_qty)
#                         
#                         discount_share = l.discount_share or 0.0
#                         if discount_share:
#                             discount_share = discount_share / exchange_rate
#                         commission_share = l.commission_share or 0.0
#                         if commission_share:
#                             commission_share = l.commission_share / exchange_rate
#                         
# #                        this_profit = this_total - this_cost
#                         this_net_sales = this_total - discount_share - commission_share
#                         this_profit = this_net_sales - this_cost
# 
#                         if invoice.type == 'out_refund':
#                             this_res['total'] -= this_total
#                             this_res['discount'] -= discount_share
#                             this_res['extras'] -= commission_share
#                             this_res['net_sales'] -= this_net_sales
#                             this_res['cost'] -= this_cost
#                             this_res['profit'] -= this_profit
#                             this_res['profit_f'] -= this_profit
#                         else:
#                             this_res['total'] += this_total
#                             this_res['discount'] += discount_share
#                             this_res['extras'] += commission_share
#                             this_res['net_sales'] += this_net_sales
#                             this_res['cost'] += this_cost
#                             this_res['profit'] += this_profit
#                             this_res['profit_f'] += this_profit
# 
#                         ##
#                         if invoice.type == 'out_refund':
#                             total_sales -= this_total
#                             total_discount -= discount_share or 0.0
#                             total_extras -= commission_share
#                             
#                             total_profit -= this_net_sales - this_cost
#                             total_net_sales -= this_net_sales
#                             total_cost -= this_cost
#                             
#                         else:
#                             total_sales += this_total
#                             total_discount += discount_share or 0.0
#                             total_extras += commission_share
#                             
#                             total_profit += (this_net_sales - this_cost)
#                             total_net_sales += this_net_sales
#                             total_cost += this_cost
#                         
# 
# #                    else:
#                 if not skip:
#                     skip=True
#                     d = {}
#                     invoice = l.invoice_id
#                     number = invoice.number or ''
#                     if invoice.refund_without_invoice:
#                         number = 'Sales-Ret-'+str(number)
#                     else:
#                         number = 'Sales-'+str(number)
# 
#                     this_total = l.price_subtotal / exchange_rate
#                     this_cost = l.cost_price* (l.quantity + l.free_qty)
#                     this_discount = l.discount_share or 0.0
#                     if this_discount:
#                         this_discount = this_discount / exchange_rate
#                         
#                     this_extras = l.commission_share
#                     if this_extras:
#                         this_extras = this_extras / exchange_rate
#                         
#                     this_net_sales = this_total - this_discount - this_extras
#                     this_profit = this_net_sales - this_cost
# 
#                     if invoice.type == 'out_refund':
#                         this_total *= -1
#                         this_discount *= -1
#                         this_extras *= -1
#                         this_net_sales *= -1
#                         this_cost *= -1
#                         this_profit *= -1
# 
#                     d['invoice_id'] = invoice.id
#                     d['type'] = invoice.type
#                     d['bill_no'] = number
#                     d['date'] = invoice.date_invoice
#                     d['customer'] = invoice.partner_id.name
#                     d['total'] = this_total
#                     d['discount'] = this_discount
#                     d['extras'] = this_extras
#                     d['net_sales'] = this_net_sales
#                     d['cost'] = this_cost
#                     d['profit'] = this_profit
#                     d['profit_f'] = this_profit
#                     d['is_line'] = True
# 
#                     d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
#                     d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
#                     d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False
# 
#                     ##
#                     total_sales += this_total
#                     total_discount += this_discount
#                     total_profit += this_profit
#                     total_extras += this_extras
#                     total_net_sales += this_net_sales
#                     total_cost += this_cost
# 
# #                    print"append"
#                     final_res.append(d)
# #                    print"time 1111",(str(end - start))
#             else:
# #                print"elsseee"
#                 d = {}
#                 invoice = l.invoice_id
#                 number = invoice.number or ''
#                 if invoice.refund_without_invoice:
#                     number = 'Sales-Ret-'+str(number)
#                 else:
#                     number = 'Sales-'+str(number)
# 
#                 this_total = l.price_subtotal / exchange_rate
#                 this_cost = l.cost_price* (l.quantity + l.free_qty)
#                 this_discount = l.discount_share or 0.0
#                 if this_discount:
#                     this_discount = this_discount / exchange_rate
#                 this_extras = l.commission_share
#                 if this_extras:
#                     this_extras = this_extras / exchange_rate
#                 this_net_sales = this_total - this_discount - this_extras
#                 this_profit = this_net_sales - this_cost
#                 
#                 if invoice.type == 'out_refund':
#                     this_total *= -1
#                     this_discount *= -1
#                     this_extras *= -1
#                     this_net_sales *= -1
#                     this_cost *= -1
#                     this_profit *= -1
#                     
# 
#                 d['invoice_id'] = invoice.id
#                 d['type'] = invoice.type
#                 d['bill_no'] = number
#                 d['date'] = invoice.date_invoice
#                 d['customer'] = invoice.partner_id.name
#                 d['total'] = this_total
#                 d['discount'] = this_discount
#                 d['extras'] = this_extras
#                 d['net_sales'] = this_net_sales
#                 d['cost'] = this_cost
#                 d['profit'] = this_profit
#                 d['profit_f'] = this_profit
#                 d['is_line'] = True
# 
#                 d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
#                 d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
#                 d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False
# 
#                 ##
#                 total_sales += this_total
#                 total_discount += this_discount
#                 total_profit += this_profit
#                 total_extras += this_extras
#                 total_net_sales += this_net_sales
#                 total_cost += this_cost
# 
#                 final_res.append(d)
#                 
#                 
#             
#         # profit/total profit * 100
#         print"total_profit: ",total_profit
#         for d in final_res:
#             d_cost = d['cost']
#             d_net_sales = d['net_sales']
#             if d_cost == 0: d_cost=1.0
#             if d_net_sales == 0: d_net_sales=1.0
#             d['profit_percent_cost'] = (d['profit_f'] / d_cost) * 100.0
#             d['profit_percent_sales'] = (d['profit_f'] / d_net_sales) * 100.0
#             if d['type']=='out_refund':
#                 d['profit_percent_cost'] = d['profit_percent_cost'] * -1
#                 d['profit_percent_sales'] = d['profit_percent_sales'] * -1
#             
#             
#             total_profit_d = total_profit
#             profit_percent_net_profit = (d['profit_f'] / total_profit_d) * 100.0
# #            if d['type']=='out_refund':
# #                profit_percent_net_profit *= -1
#             d['profit_percent_net_profit'] = '{:.3f}'.format(profit_percent_net_profit)
#             
#             d['total'] = '{:.3f}'.format(d['total'])
#             d['discount'] = '{:.3f}'.format(d['discount'])
#             d['extras'] = '{:.3f}'.format(d['extras'])
#             d['net_sales'] = '{:.3f}'.format(d['net_sales'])
#             d['cost'] = '{:.3f}'.format(d['cost'])
#             d['profit'] = '{:.3f}'.format(d['profit'])
#             d['profit_percent_sales'] = '{:.3f}'.format(d['profit_percent_sales'])
#             d['profit_percent_cost'] = '{:.3f}'.format(d['profit_percent_cost'])
#             
#         
#         sort_by = self.sort_by or 'customer'
#         if sort_by == 'profit':
#             sort_by = 'profit_f'
#         if sort_by == 'customer':
#             final_res = sorted(final_res, key=lambda i: i[sort_by])
#         else:
#             final_res = sorted(final_res, key=lambda i: i[sort_by], reverse=True)
#         
#         d1 = {'total_sales': '{:.3f}'.format(total_sales),
#             'total_discount': '{:.3f}'.format(total_discount),
#             'total_extras': '{:.3f}'.format(total_extras),
#             'total_net_sales': '{:.3f}'.format(total_net_sales),
#             'total_cost': '{:.3f}'.format(total_cost),
#             'total_profit': '{:.3f}'.format(total_profit),
#             'bill_no': 'Total',
#             'is_line': False,
#             'show_profit_percent_sales':self.show_profit_percent_sales or False,
#             'show_profit_percent_cost':self.show_profit_percent_cost or False,
#             'show_profit_percent_net_profit':self.show_profit_percent_net_profit or False
#         }
#         final_res.append(d1)
# 
#         print"final_res \n\n\n",len(final_res)
# #        print"final_res \n\n\n",final_res
#         return final_res
        
    def get_report_datas(self, default_filters={}):
        '''
        Main method for pdf, xlsx and js calls
        :param default_filters: Use this while calling from other methods. Just a dict
        :return: All the datas for GL
        '''
        if self.validate_data():
            filters = self.process_filters()
#            filters={}
#
            filters['category_ids'] = self.category_ids.ids
            filters['location_id'] = self.location_id.id or False
            filters['salesman_id'] = self.salesman_id.id or False
            filters['division_id'] = self.division_id.id or False
            filters['department_id'] = self.department_id.id or False
            filters['partner_id'] = self.partner_id.id or False
            filters['date_from'] = self.date_from or '2020-01-01'
            filters['date_to'] = self.date_to or '2030-01-01'
            
            filters['show_profit_percent_sales'] = self.show_profit_percent_sales or False
            filters['show_profit_percent_cost'] = self.show_profit_percent_cost or False
            filters['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False
            filters['based_on'] = self.based_on or False
            filters['sort_by'] = self.sort_by or False
            filters['group_by'] = self.group_by or False
            filters['state'] = self.state or False
            
            filters['sorted_partner_ids'] = []
            if self.group_by == 'salesman':
                account_lines = self.process_data_s()
            elif self.group_by == 'customer':
                account_lines, sorted_partner_ids = self.process_data_s()
                filters['sorted_partner_ids'] = sorted_partner_ids
            else:
                account_lines = self.process_data()
            return filters, account_lines

    def action_pdf(self):
        filters, account_lines = self.get_report_datas()
#        print"account_lines: \n\n\n\n\n\n",account_lines

#        if self.group_by == 'salesman':
#            account_lines = self.process_data_s()
##            print"account_lines: \n\n\n\n\n\n",account_lines
#        else:
#            account_lines = self.process_data()

        return self.env['report'].with_context({'landscape': 1}).get_action(
            self, 'account_dynamic_reports.bills_profit', data={'Ledger_data': account_lines,
                        'Filters': filters
#                        'Filters': []
                        })

    def action_xlsx(self):
        raise UserError(_('This feature is under development.'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'BPR View',
#            'tag': 'dynamic.bpr',
            'context': {'wizard_id': self.id}
        }
#        if self.group_by == 'salesman':
        if self.group_by in ('salesman', 'customer'):
            res['tag'] = 'dynamic.bprs'
        else:
            res['tag'] = 'dynamic.bpr'
        return res
        
    def process_data_s(self):
        print"process_data_s called: *******"
        final_res = {}
        
        data = self.get_filters(default_filters={})
        date_from = data.get('date_from','2020-01-01')
        date_to = data.get('date_to','2030-01-01')
        domain = [('invoice_id.date_invoice', '>=', date_from),
                ('invoice_id.date_invoice', '<=', date_to)]
        
        based_on = data.get('based_on','sales_and_returns')
        if based_on == 'sales_and_returns':
            domain.append(('invoice_id.type', 'in', ('out_invoice','out_refund')))
        if based_on == 'sales':
            domain.append(('invoice_id.type', '=', 'out_invoice'))
        if based_on == 'returns':
            domain.append(('invoice_id.type', '=', 'out_refund'))
            
        state = data.get('state','all')
#        domain.append(('invoice_id.id', '=', 220))
        if state== 'all':
            domain.append(('invoice_id.state', '!=', 'cancel'))
        if state== 'posted':
            domain.append(('invoice_id.state', 'not in', ('cancel','draft')))
        if state== 'not_posted':
            domain.append(('invoice_id.state', '=', 'draft'))

        if data.get('location_id'):
            location_id = data.get('location_id')
            domain.append(('invoice_id.location_id','=',location_id.id))
        if data.get('salesman_id'):
            salesman_id = data.get('salesman_id')
            domain.append(('invoice_id.user_id','=',salesman_id.id))
        if data.get('division_id'):
            division_id = data.get('division_id')
            domain.append(('invoice_id.division_id','=',division_id.id))
        if data.get('department_id'):
            department_id = data.get('department_id')
            domain.append(('invoice_id.department_id','=',department_id.id))
        if data.get('partner_id'):
            partner_id = data.get('partner_id')
            domain.append(('invoice_id.partner_id','=',partner_id.id))
        if data.get('category_ids',[]):
            category_ids = list(set(data.get('category_ids')))
            domain.append(('product_id.categ_id', 'in', category_ids))
            
        if data.get('account_id'):
            accounts = [data.get('account_id')]
            if accounts[0].type == 'view':
                child_account_ids = self.env['account.account'].search([('parent_id', 'child_of', accounts[0].ids)])
                if len(child_account_ids):
                    accounts = child_account_ids.ids
                domain.append(('invoice_id.account_id','in',accounts))
            else:
                domain.append(('invoice_id.account_id','=',accounts[0].id))
            
        print"process_data domainnnn: ",domain
        
#        domain.append(['invoice_id','in',(310,)])
        invoice_line_ids = self.env['account.invoice.line'].search(domain)
        print"len(invoice_line_ids) ",len(invoice_line_ids)
        
        product_ids = data.get('product_ids',[])
        product_ids = list(set(product_ids))
#        print"product idsss: ",product_ids        

        
        if self.group_by == 'salesman':
            salesman_ids = []
            salesman_id = data.get('salesman_id',False)
            if not salesman_id:
                for l in invoice_line_ids:
                    if not l.invoice_id.user_id:continue
                    salesman_ids.append(l.invoice_id.user_id.id)
            else:
                salesman_ids = [salesman_id.id]
            salesman_ids = list(set(salesman_ids))

            all_users = self.env['res.users'].browse(salesman_ids)
            print"all users: ",all_users

            all_sales, all_discount, all_extras, all_net_sales, all_cost, all_profit = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            for user in all_users:
                total_sales, total_discount, total_extras, total_net_sales, total_cost, total_profit= 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                header_d = {}
                lines = []
                for l in invoice_line_ids:
                    if l.invoice_id.user_id.id!=user.id:
                        continue
                    invoice = l.invoice_id

                    currency = invoice.currency_id
                    exchange_rate = 1.0
                    if currency.name!='KWD':
                        exchange_rate = invoice.exchange_rate                

                    if len(lines):
                        skip = False
                        for this_res in lines:
                            if skip:
                                continue

                            invoice_id = this_res.get('invoice_id',False)
                            if (invoice_id) and (invoice_id == l.invoice_id.id):
                                skip=True
                                this_total = l.price_subtotal / exchange_rate
                                this_cost = (l.cost_price* (1/l.uom_id.factor)) * (l.quantity + l.free_qty)

                                discount_share = l.discount_share or 0.0
                                if discount_share:
                                    discount_share = discount_share / exchange_rate
                                commission_share = l.commission_share
                                if commission_share:
                                    commission_share = commission_share / exchange_rate

        #                        this_profit = this_total - this_cost
                                this_net_sales = this_total - discount_share - commission_share
                                this_profit = this_net_sales - this_cost

                                if invoice.type == 'out_refund':
                                    this_res['total'] -= this_total
                                    this_res['discount'] -= discount_share
                                    this_res['extras'] -= commission_share
                                    this_res['net_sales'] -= this_net_sales
                                    this_res['cost'] -= this_cost
                                    this_res['profit'] -= this_profit
                                    this_res['profit_f'] -= this_profit
                                else:
                                    this_res['total'] += this_total
                                    this_res['discount'] += discount_share
                                    this_res['extras'] += commission_share
                                    this_res['net_sales'] += this_net_sales
                                    this_res['cost'] += this_cost
                                    this_res['profit'] += this_profit
                                    this_res['profit_f'] += this_profit

                                ##
                                if invoice.type == 'out_refund':
                                    total_sales -= this_total
                                    total_discount -= discount_share or 0.0
                                    total_extras -= commission_share

                                    total_profit -= this_net_sales - this_cost
                                    total_net_sales -= this_net_sales
                                    total_cost -= this_cost

                                else:
                                    total_sales += this_total
                                    total_discount += discount_share or 0.0
                                    total_extras += commission_share

                                    total_profit += (this_net_sales - this_cost)
                                    total_net_sales += this_net_sales
                                    total_cost += this_cost


                        if not skip:
                            skip=True
                            d = {}
                            invoice = l.invoice_id
                            number = invoice.number or ''
                            if invoice.refund_without_invoice:
                                number = 'Sales-Ret-'+str(number)
                            else:
                                number = 'Sales-'+str(number)

                            this_total = l.price_subtotal / exchange_rate
                            this_cost = (l.cost_price*(1/l.uom_id.factor)) * (l.quantity + l.free_qty)
                            this_discount = l.discount_share or 0.0
                            if this_discount:
                                this_discount = this_discount / exchange_rate
                            this_extras = l.commission_share or 0.0
                            if this_extras:
                                this_extras = this_extras / exchange_rate
                            this_net_sales = this_total - this_discount - this_extras
                            this_profit = this_net_sales - this_cost

                            if invoice.type == 'out_refund':
                                this_total *= -1
                                this_discount *= -1
                                this_extras *= -1
                                this_net_sales *= -1
                                this_cost *= -1
                                this_profit *= -1

                            d['invoice_id'] = invoice.id
                            d['type'] = invoice.type
                            d['bill_no'] = number
                            d['date'] = invoice.date_invoice
                            d['customer'] = invoice.partner_id.name
                            d['total'] = this_total
                            d['discount'] = this_discount
                            d['extras'] = this_extras
                            d['net_sales'] = this_net_sales
                            d['cost'] = this_cost
                            d['profit'] = this_profit
                            d['profit_f'] = this_profit
                            d['is_line'] = True

                            d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
                            d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
                            d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False

                            ##
                            total_sales += this_total
                            total_discount += this_discount
                            total_profit += this_profit
                            total_extras += this_extras
                            total_net_sales += this_net_sales
                            total_cost += this_cost

                            lines.append(d)
                    else:
                        d = {}
                        invoice = l.invoice_id
                        number = invoice.number or ''
                        if invoice.refund_without_invoice:
                            number = 'Sales-Ret-'+str(number)
                        else:
                            number = 'Sales-'+str(number)

                        this_total = l.price_subtotal / exchange_rate
                        this_cost = (l.cost_price*(1/l.uom_id.factor))* (l.quantity + l.free_qty)
                        this_discount = l.discount_share or 0.0
                        if this_discount:
                            this_discount = this_discount / exchange_rate
                        this_extras = l.commission_share or 0.0
                        if this_extras:
                            this_extras = this_extras / exchange_rate
                        this_net_sales = this_total - this_discount - this_extras
                        this_profit = this_net_sales - this_cost

                        if invoice.type == 'out_refund':
                            this_total *= -1
                            this_discount *= -1
                            this_extras *= -1
                            this_net_sales *= -1
                            this_cost *= -1
                            this_profit *= -1


                        d['invoice_id'] = invoice.id
                        d['type'] = invoice.type
                        d['bill_no'] = number
                        d['date'] = invoice.date_invoice
                        d['customer'] = invoice.partner_id.name
                        d['total'] = this_total
                        d['discount'] = this_discount
                        d['extras'] = this_extras
                        d['net_sales'] = this_net_sales
                        d['cost'] = this_cost
                        d['profit'] = this_profit
                        d['profit_f'] = this_profit
                        d['is_line'] = True

                        d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
                        d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
                        d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False

                        ##
                        total_sales += this_total
                        total_discount += this_discount
                        total_profit += this_profit
                        total_extras += this_extras
                        total_net_sales += this_net_sales
                        total_cost += this_cost

                        lines.append(d)

                # all totals
                all_sales += total_sales
                all_discount += total_discount
                all_extras += total_extras
                all_net_sales += total_net_sales
                all_cost += total_cost
                all_profit += total_profit

                header_d['id'] = user.id
                header_d['name'] = user.name
                header_d['total_sales'] = '{:.3f}'.format(total_sales)
                header_d['discount'] = '{:.3f}'.format(total_discount)
                header_d['extras'] = '{:.3f}'.format(total_extras)
                header_d['net_sales'] = '{:.3f}'.format(total_net_sales)
                header_d['cost'] = '{:.3f}'.format(total_cost)
                header_d['profit'] = '{:.3f}'.format(total_profit)

                sort_by = self.sort_by or 'customer'
                if sort_by == 'profit':
                    sort_by = 'profit_f'
                if sort_by == 'customer':
                    lines = sorted(lines, key=lambda i: i[sort_by])
                else:
                    lines = sorted(lines, key=lambda i: i[sort_by], reverse=True)

                header_d['lines'] = lines
                header_d['single_page'] = True
                header_d['count'] = len(lines)

                final_res[user.id] = header_d

            final_res.update({'Total': {}})
            final_res['Total']['sales'] = '{:.3f}'.format(all_sales)
            final_res['Total']['discount'] = '{:.3f}'.format(all_discount)
            final_res['Total']['extras'] = '{:.3f}'.format(all_extras)
            final_res['Total']['net_sales'] = '{:.3f}'.format(all_net_sales)
            final_res['Total']['cost'] = '{:.3f}'.format(all_cost)
            final_res['Total']['profit'] = '{:.3f}'.format(all_profit)
            final_res['Total']['is_line'] = False
            print"len filan_res: ",len(final_res)
            return final_res
        
        ### group by customer
        if self.group_by == 'customer':
            partner_total = []
            partner_ids = []
            for l in invoice_line_ids:
                if not l.invoice_id.partner_id:continue
                partner_ids.append(l.invoice_id.partner_id.id)

            partner_ids = list(set(partner_ids))
            all_partners = self.env['res.partner'].browse(partner_ids)
            
            all_sales, all_discount, all_extras, all_net_sales, all_cost, all_profit = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            for partner in all_partners:
                total_sales, total_discount, total_extras, total_net_sales, total_cost, total_profit= 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                header_d = {}
                lines = []
                for l in invoice_line_ids:
                    if l.invoice_id.partner_id.id!=partner.id:
                        continue
                    invoice = l.invoice_id

                    currency = invoice.currency_id
                    exchange_rate = 1.0
                    if currency.name!='KWD':
                        exchange_rate = invoice.exchange_rate                

                    if len(lines):
                        skip = False
                        for this_res in lines:
                            if skip:
                                continue

                            invoice_id = this_res.get('invoice_id',False)
                            if (invoice_id) and (invoice_id == l.invoice_id.id):
                                skip=True
                                this_total = l.price_subtotal / exchange_rate
                                this_cost = (l.cost_price*(1/l.uom_id.factor))* (l.quantity + l.free_qty)

                                discount_share = l.discount_share or 0.0
                                if discount_share:
                                    discount_share = discount_share / exchange_rate
                                commission_share = l.commission_share
                                if commission_share:
                                    commission_share = commission_share / exchange_rate

        #                        this_profit = this_total - this_cost
                                this_net_sales = this_total - discount_share - commission_share
                                this_profit = this_net_sales - this_cost

                                if invoice.type == 'out_refund':
                                    this_res['total'] -= this_total
                                    this_res['discount'] -= discount_share
                                    this_res['extras'] -= commission_share
                                    this_res['net_sales'] -= this_net_sales
                                    this_res['cost'] -= this_cost
                                    this_res['profit'] -= this_profit
                                    this_res['profit_f'] -= this_profit
                                else:
                                    this_res['total'] += this_total
                                    this_res['discount'] += discount_share
                                    this_res['extras'] += commission_share
                                    this_res['net_sales'] += this_net_sales
                                    this_res['cost'] += this_cost
                                    this_res['profit'] += this_profit
                                    this_res['profit_f'] += this_profit

                                ##
                                if invoice.type == 'out_refund':
                                    total_sales -= this_total
                                    total_discount -= discount_share or 0.0
                                    total_extras -= commission_share

                                    total_profit -= this_net_sales - this_cost
                                    total_net_sales -= this_net_sales
                                    total_cost -= this_cost

                                else:
                                    total_sales += this_total
                                    total_discount += discount_share or 0.0
                                    total_extras += commission_share

                                    total_profit += (this_net_sales - this_cost)
                                    total_net_sales += this_net_sales
                                    total_cost += this_cost


                        if not skip:
                            skip=True
                            d = {}
                            invoice = l.invoice_id
                            number = invoice.number or ''
                            if invoice.refund_without_invoice:
                                number = 'Sales-Ret-'+str(number)
                            else:
                                number = 'Sales-'+str(number)

                            this_total = l.price_subtotal / exchange_rate
                            this_cost = (l.cost_price*(1/l.uom_id.factor))* (l.quantity + l.free_qty)
                            this_discount = l.discount_share or 0.0
                            if this_discount:
                                this_discount = this_discount / exchange_rate
                            this_extras = l.commission_share or 0.0
                            if this_extras:
                                this_extras = this_extras / exchange_rate
                            this_net_sales = this_total - this_discount - this_extras
                            this_profit = this_net_sales - this_cost

                            if invoice.type == 'out_refund':
                                this_total *= -1
                                this_discount *= -1
                                this_extras *= -1
                                this_net_sales *= -1
                                this_cost *= -1
                                this_profit *= -1

                            d['invoice_id'] = invoice.id
                            d['type'] = invoice.type
                            d['bill_no'] = number
                            d['date'] = invoice.date_invoice
                            d['customer'] = invoice.partner_id.name
                            d['total'] = this_total
                            d['discount'] = this_discount
                            d['extras'] = this_extras
                            d['net_sales'] = this_net_sales
                            d['cost'] = this_cost
                            d['profit'] = this_profit
                            d['profit_f'] = this_profit
                            d['is_line'] = True

                            d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
                            d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
                            d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False

                            ##
                            total_sales += this_total
                            total_discount += this_discount
                            total_profit += this_profit
                            total_extras += this_extras
                            total_net_sales += this_net_sales
                            total_cost += this_cost

                            lines.append(d)
                    else:
                        d = {}
                        invoice = l.invoice_id
                        number = invoice.number or ''
                        if invoice.refund_without_invoice:
                            number = 'Sales-Ret-'+str(number)
                        else:
                            number = 'Sales-'+str(number)

                        this_total = l.price_subtotal / exchange_rate
                        this_cost = (l.cost_price*(1/l.uom_id.factor))* (l.quantity + l.free_qty)
                        this_discount = l.discount_share or 0.0
                        if this_discount:
                            this_discount = this_discount / exchange_rate
                        this_extras = l.commission_share or 0.0
                        if this_extras:
                            this_extras = this_extras / exchange_rate
                        this_net_sales = this_total - this_discount - this_extras
                        this_profit = this_net_sales - this_cost

                        if invoice.type == 'out_refund':
                            this_total *= -1
                            this_discount *= -1
                            this_extras *= -1
                            this_net_sales *= -1
                            this_cost *= -1
                            this_profit *= -1


                        d['invoice_id'] = invoice.id
                        d['type'] = invoice.type
                        d['bill_no'] = number
                        d['date'] = invoice.date_invoice
                        d['customer'] = invoice.partner_id.name
                        d['total'] = this_total
                        d['discount'] = this_discount
                        d['extras'] = this_extras
                        d['net_sales'] = this_net_sales
                        d['cost'] = this_cost
                        d['profit'] = this_profit
                        d['profit_f'] = this_profit
                        d['is_line'] = True

                        d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
                        d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
                        d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False

                        ##
                        total_sales += this_total
                        total_discount += this_discount
                        total_profit += this_profit
                        total_extras += this_extras
                        total_net_sales += this_net_sales
                        total_cost += this_cost

                        lines.append(d)

                # all totals
                all_sales += total_sales
                all_discount += total_discount
                all_extras += total_extras
                all_net_sales += total_net_sales
                all_cost += total_cost
                all_profit += total_profit

                header_d['id'] = partner.id
                header_d['name'] = partner.name
                header_d['total_sales'] = '{:.3f}'.format(total_sales)
                header_d['discount'] = '{:.3f}'.format(total_discount)
                header_d['extras'] = '{:.3f}'.format(total_extras)
                header_d['net_sales'] = '{:.3f}'.format(total_net_sales)
                header_d['cost'] = '{:.3f}'.format(total_cost)
                header_d['profit'] = '{:.3f}'.format(total_profit)

                sort_by = self.sort_by or 'customer'
                if sort_by == 'profit':
                    sort_by = 'profit_f'
                if sort_by == 'customer':
                    lines = sorted(lines, key=lambda i: i[sort_by])
                else:
                    lines = sorted(lines, key=lambda i: i[sort_by], reverse=True)

                header_d['lines'] = lines
                header_d['single_page'] = True
                header_d['count'] = len(lines)

                final_res[partner.id] = header_d
                partner_total.append({
                    'name':partner.name,
                    'total':total_sales,
                    'id':partner.id,
                })
            
#            print"partner_totalllllllllll :",partner_total
            partner_total = sorted(partner_total, key=lambda k: k['total'], reverse=True)
#            print"partner_totalllllllllll Sortedddd :",partner_total
            
            final_res.update({'Total': {}})
            final_res['Total']['sales'] = '{:.3f}'.format(all_sales)
            final_res['Total']['discount'] = '{:.3f}'.format(all_discount)
            final_res['Total']['extras'] = '{:.3f}'.format(all_extras)
            final_res['Total']['net_sales'] = '{:.3f}'.format(all_net_sales)
            final_res['Total']['cost'] = '{:.3f}'.format(all_cost)
            final_res['Total']['profit'] = '{:.3f}'.format(all_profit)
            final_res['Total']['is_line'] = False

            print"len filan_res: ",len(final_res)
            
            sorted_partner_ids = []
            for pdict in partner_total:
#                sorted_partner_ids.append(pdict.get('id'))
                sorted_partner_ids.append(str(pdict.get('id')))
            print"sorted_partner_idsssssssssss:",sorted_partner_ids
            
        return final_res, sorted_partner_ids
#        return final_res
    
    
    def build_detailed_move_lines(self, offset=0, categ_id=0, fetch_range=FETCH_RANGE):
        data = self.get_filters(default_filters={})
#        print"filter data: ",data
        offset_count = offset * fetch_range
        data = self.get_filters(default_filters={})
        date_from = data.get('date_from','2020-01-01')
        date_to = data.get('date_to','2030-01-01')
        domain = [('invoice_id.date_invoice', '>=', date_from),
                ('invoice_id.date_invoice', '<=', date_to)]
        
        based_on = data.get('based_on','sales_and_returns')
        if based_on == 'sales_and_returns':
            domain.append(('invoice_id.type', 'in', ('out_invoice','out_refund')))
        if based_on == 'sales':
            domain.append(('invoice_id.type', '=', 'out_invoice'))
        if based_on == 'returns':
            domain.append(('invoice_id.type', '=', 'out_refund'))
            
        state = data.get('state','all')
#        domain.append(('invoice_id.id', '=', 220))
        if state== 'all':
            domain.append(('invoice_id.state', '!=', 'cancel'))
        if state== 'posted':
            domain.append(('invoice_id.state', 'not in', ('cancel','draft')))
        if state== 'not_posted':
            domain.append(('invoice_id.state', '=', 'draft'))

        if data.get('location_id'):
            location_id = data.get('location_id')
            domain.append(('invoice_id.location_id','=',location_id.id))
        if data.get('salesman_id'):
            salesman_id = data.get('salesman_id')
            domain.append(('invoice_id.user_id','=',salesman_id.id))
        if data.get('division_id'):
            division_id = data.get('division_id')
            domain.append(('invoice_id.division_id','=',division_id.id))
        if data.get('department_id'):
            department_id = data.get('department_id')
            domain.append(('invoice_id.department_id','=',department_id.id))
        if data.get('partner_id'):
            partner_id = data.get('partner_id')
            domain.append(('invoice_id.partner_id','=',partner_id.id))
        if data.get('category_ids',[]):
            category_ids = list(set(data.get('category_ids')))
            domain.append(('product_id.categ_id', 'in', category_ids))
        print"process_data domainnnn: ",domain
        
#        domain.append(['invoice_id','in',(310,)])
        invoice_line_ids = self.env['account.invoice.line'].search(domain)
        print"len(invoice_line_ids) ",len(invoice_line_ids)
        product_ids = data.get('product_ids',[])
        product_ids = list(set(product_ids))
                        
        show_arabic_name = data.get('show_arabic_name',False)
        
        if data.get('group_by') == 'salesman':
            all_users = [self.env['res.users'].browse(categ_id)]
            final_res = []
            for user in all_users:
                for l in invoice_line_ids:
                    if l.invoice_id.user_id.id!=user.id:
                        continue
                    invoice = l.invoice_id

                    currency = invoice.currency_id
                    exchange_rate = 1.0
                    if currency.name!='KWD':
                        exchange_rate = invoice.exchange_rate                                

                    if len(final_res):
                        skip = False
                        for this_res in final_res:
                            if skip:
                                continue

                            invoice_id = this_res.get('invoice_id',False)
                            if (invoice_id) and (invoice_id == l.invoice_id.id):
                                skip=True
                                this_total = l.price_subtotal / exchange_rate
                                this_cost = (l.cost_price*(1/l.uom_id.factor))* (l.quantity + l.free_qty)

                                discount_share = l.discount_share or 0.0
                                if discount_share:
                                    discount_share = discount_share / exchange_rate
                                commission_share = l.commission_share or 0.0
                                if commission_share:
                                    commission_share = commission_share / exchange_rate

        #                        this_profit = this_total - this_cost
                                this_net_sales = this_total - discount_share - commission_share
                                this_profit = this_net_sales - this_cost

                                if invoice.type == 'out_refund':
                                    this_res['total'] -= this_total
                                    this_res['discount'] -= discount_share
                                    this_res['extras'] -= commission_share
                                    this_res['net_sales'] -= this_net_sales
                                    this_res['cost'] -= this_cost
                                    this_res['profit'] -= this_profit
                                    this_res['profit_f'] -= this_profit
                                else:
                                    this_res['total'] += this_total
                                    this_res['discount'] += discount_share
                                    this_res['extras'] += commission_share
                                    this_res['net_sales'] += this_net_sales
                                    this_res['cost'] += this_cost
                                    this_res['profit'] += this_profit
                                    this_res['profit_f'] += this_profit

        #                    else:
                        if not skip:
                            skip=True
                            d = {}
                            invoice = l.invoice_id
                            number = invoice.number or ''
                            if invoice.refund_without_invoice:
                                number = 'Sales-Ret-'+str(number)
                            else:
                                number = 'Sales-'+str(number)

                            this_total = l.price_subtotal / exchange_rate
                            this_cost = (l.cost_price*(1/l.uom_id.factor))* (l.quantity + l.free_qty)
                            this_discount = l.discount_share or 0.0
                            if this_discount:
                                this_discount = this_discount / exchange_rate
                            this_extras = l.commission_share or 0.0
                            if this_extras:
                                this_extras = this_extras / exchange_rate
                            this_net_sales = this_total - this_discount - this_extras
                            this_profit = this_net_sales - this_cost

                            if invoice.type == 'out_refund':
                                this_total *= -1
                                this_discount *= -1
                                this_extras *= -1
                                this_net_sales *= -1
                                this_cost *= -1
                                this_profit *= -1

                            d['invoice_id'] = invoice.id
                            d['type'] = invoice.type
                            d['bill_no'] = number
                            d['date'] = invoice.date_invoice
                            d['customer'] = invoice.partner_id.name
                            d['total'] = this_total
                            d['discount'] = this_discount
                            d['extras'] = this_extras
                            d['net_sales'] = this_net_sales
                            d['cost'] = this_cost
                            d['profit'] = this_profit
                            d['profit_f'] = this_profit
                            d['is_line'] = True

                            d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
                            d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
                            d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False

                            final_res.append(d)
        #                    print"time 1111",(str(end - start))
                    else:
        #                print"elsseee"
                        d = {}
                        invoice = l.invoice_id
                        number = invoice.number or ''
                        if invoice.refund_without_invoice:
                            number = 'Sales-Ret-'+str(number)
                        else:
                            number = 'Sales-'+str(number)

                        this_total = l.price_subtotal / exchange_rate
                        this_cost = (l.cost_price*(1/l.uom_id.factor))* (l.quantity + l.free_qty)
                        this_discount = l.discount_share or 0.0
                        if this_discount:
                            this_discount = this_discount / exchange_rate
                        this_extras = l.commission_share or 0.0
                        if this_extras:
                            this_extras = this_extras / exchange_rate
                        this_net_sales = this_total - this_discount - this_extras
                        this_profit = this_net_sales - this_cost

                        if invoice.type == 'out_refund':
                            this_total *= -1
                            this_discount *= -1
                            this_extras *= -1
                            this_net_sales *= -1
                            this_cost *= -1
                            this_profit *= -1


                        d['invoice_id'] = invoice.id
                        d['type'] = invoice.type
                        d['bill_no'] = number
                        d['date'] = invoice.date_invoice
                        d['customer'] = invoice.partner_id.name
                        d['total'] = this_total
                        d['discount'] = this_discount
                        d['extras'] = this_extras
                        d['net_sales'] = this_net_sales
                        d['cost'] = this_cost
                        d['profit'] = this_profit
                        d['profit_f'] = this_profit
                        d['is_line'] = True

                        d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
                        d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
                        d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False

                        final_res.append(d)        


                sort_by = self.sort_by or 'customer'
                if sort_by == 'profit':
                    sort_by = 'profit_f'
                if sort_by == 'customer':
                    final_res = sorted(final_res, key=lambda i: i[sort_by])
                else:
                    final_res = sorted(final_res, key=lambda i: i[sort_by], reverse=True)
            total_profit = 0.0
            for d in final_res:
                total_profit += d['profit']

            for d in final_res:
                d_cost = d['cost']
                if d_cost == 0: d_cost = 1.0
                d_net_sales = d['net_sales']
                if d_net_sales == 0: d_net_sales = 1.0
                profit_percent_sales = (d['profit'] / d_net_sales) *100.0
                profit_percent_cost = (d['profit'] / d_cost) *100.0
                if d['type'] == 'out_refund':
                    profit_percent_sales *= -1
                    profit_percent_cost *= -1

                d['profit_percent_sales'] = '{:.3f}'.format(profit_percent_sales)
                d['profit_percent_cost'] = '{:.3f}'.format(profit_percent_cost)
                d['profit_percent_net_profit'] = '{:.3f}'.format((d['profit'] / total_profit) *100.0)

                d['total'] = '{:.3f}'.format(d['total'])
                d['discount'] = '{:.3f}'.format(d['discount'])
                d['extras'] = '{:.3f}'.format(d['extras'])
                d['net_sales'] = '{:.3f}'.format(d['net_sales'])
                d['cost'] = '{:.3f}'.format(d['cost'])
                d['profit'] = '{:.3f}'.format(d['profit'])
                
        if data.get('group_by') == 'customer':
            all_partners = [self.env['res.partner'].browse(categ_id)]
            final_res = []
            for partner in all_partners:
                for l in invoice_line_ids:
                    if l.invoice_id.partner_id.id!=partner.id:
                        continue
                    invoice = l.invoice_id

                    currency = invoice.currency_id
                    exchange_rate = 1.0
                    if currency.name!='KWD':
                        exchange_rate = invoice.exchange_rate                                

                    if len(final_res):
                        skip = False
                        for this_res in final_res:
                            if skip:
                                continue

                            invoice_id = this_res.get('invoice_id',False)
                            if (invoice_id) and (invoice_id == l.invoice_id.id):
                                skip=True
                                this_total = l.price_subtotal / exchange_rate
                                this_cost = (l.cost_price*(1/l.uom_id.factor))* (l.quantity + l.free_qty)

                                discount_share = l.discount_share or 0.0
                                if discount_share:
                                    discount_share = discount_share / exchange_rate
                                commission_share = l.commission_share or 0.0
                                if commission_share:
                                    commission_share = commission_share / exchange_rate

        #                        this_profit = this_total - this_cost
                                this_net_sales = this_total - discount_share - commission_share
                                this_profit = this_net_sales - this_cost

                                if invoice.type == 'out_refund':
                                    this_res['total'] -= this_total
                                    this_res['discount'] -= discount_share
                                    this_res['extras'] -= commission_share
                                    this_res['net_sales'] -= this_net_sales
                                    this_res['cost'] -= this_cost
                                    this_res['profit'] -= this_profit
                                    this_res['profit_f'] -= this_profit
                                else:
                                    this_res['total'] += this_total
                                    this_res['discount'] += discount_share
                                    this_res['extras'] += commission_share
                                    this_res['net_sales'] += this_net_sales
                                    this_res['cost'] += this_cost
                                    this_res['profit'] += this_profit
                                    this_res['profit_f'] += this_profit

        #                    else:
                        if not skip:
                            skip=True
                            d = {}
                            invoice = l.invoice_id
                            number = invoice.number or ''
                            if invoice.refund_without_invoice:
                                number = 'Sales-Ret-'+str(number)
                            else:
                                number = 'Sales-'+str(number)

                            this_total = l.price_subtotal / exchange_rate
                            this_cost = (l.cost_price*(1/l.uom_id.factor))* (l.quantity + l.free_qty)
                            this_discount = l.discount_share or 0.0
                            if this_discount:
                                this_discount = this_discount / exchange_rate
                            this_extras = l.commission_share or 0.0
                            if this_extras:
                                this_extras = this_extras / exchange_rate
                            this_net_sales = this_total - this_discount - this_extras
                            this_profit = this_net_sales - this_cost

                            if invoice.type == 'out_refund':
                                this_total *= -1
                                this_discount *= -1
                                this_extras *= -1
                                this_net_sales *= -1
                                this_cost *= -1
                                this_profit *= -1

                            d['invoice_id'] = invoice.id
                            d['type'] = invoice.type
                            d['bill_no'] = number
                            d['date'] = invoice.date_invoice
                            d['customer'] = invoice.partner_id.name
                            d['total'] = this_total
                            d['discount'] = this_discount
                            d['extras'] = this_extras
                            d['net_sales'] = this_net_sales
                            d['cost'] = this_cost
                            d['profit'] = this_profit
                            d['profit_f'] = this_profit
                            d['is_line'] = True

                            d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
                            d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
                            d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False

                            final_res.append(d)
        #                    print"time 1111",(str(end - start))
                    else:
        #                print"elsseee"
                        d = {}
                        invoice = l.invoice_id
                        number = invoice.number or ''
                        if invoice.refund_without_invoice:
                            number = 'Sales-Ret-'+str(number)
                        else:
                            number = 'Sales-'+str(number)

                        this_total = l.price_subtotal / exchange_rate
                        this_cost = (l.cost_price*(1/l.uom_id.factor))* (l.quantity + l.free_qty)
                        this_discount = l.discount_share or 0.0
                        if this_discount:
                            this_discount = this_discount / exchange_rate
                        this_extras = l.commission_share or 0.0
                        if this_extras:
                            this_extras = this_extras / exchange_rate
                        this_net_sales = this_total - this_discount - this_extras
                        this_profit = this_net_sales - this_cost

                        if invoice.type == 'out_refund':
                            this_total *= -1
                            this_discount *= -1
                            this_extras *= -1
                            this_net_sales *= -1
                            this_cost *= -1
                            this_profit *= -1


                        d['invoice_id'] = invoice.id
                        d['type'] = invoice.type
                        d['bill_no'] = number
                        d['date'] = invoice.date_invoice
                        d['customer'] = invoice.partner_id.name
                        d['total'] = this_total
                        d['discount'] = this_discount
                        d['extras'] = this_extras
                        d['net_sales'] = this_net_sales
                        d['cost'] = this_cost
                        d['profit'] = this_profit
                        d['profit_f'] = this_profit
                        d['is_line'] = True

                        d['show_profit_percent_sales'] = self.show_profit_percent_sales or False
                        d['show_profit_percent_cost'] = self.show_profit_percent_cost or False
                        d['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False

                        final_res.append(d)        


#                sort_by = self.sort_by or 'customer'
#                if sort_by == 'profit':
#                    sort_by = 'profit_f'
#                if sort_by == 'customer':
#                    final_res = sorted(final_res, key=lambda i: i[sort_by])
#                else:
#                    final_res = sorted(final_res, key=lambda i: i[sort_by], reverse=True)
                final_res = sorted(final_res, key=lambda i: i['total'], reverse=True)
                
            total_profit = 0.0
            for d in final_res:
                total_profit += d['profit']

            for d in final_res:
                d_cost = d['cost']
                if d_cost == 0: d_cost = 1.0
                d_net_sales = d['net_sales']
                if d_net_sales == 0: d_net_sales = 1.0
                profit_percent_sales = (d['profit'] / d_net_sales) *100.0
                profit_percent_cost = (d['profit'] / d_cost) *100.0
                if d['type'] == 'out_refund':
                    profit_percent_sales *= -1
                    profit_percent_cost *= -1

                d['profit_percent_sales'] = '{:.3f}'.format(profit_percent_sales)
                d['profit_percent_cost'] = '{:.3f}'.format(profit_percent_cost)
                d['profit_percent_net_profit'] = '{:.3f}'.format((d['profit'] / total_profit) *100.0)

                d['total'] = '{:.3f}'.format(d['total'])
                d['discount'] = '{:.3f}'.format(d['discount'])
                d['extras'] = '{:.3f}'.format(d['extras'])
                d['net_sales'] = '{:.3f}'.format(d['net_sales'])
                d['cost'] = '{:.3f}'.format(d['cost'])
                d['profit'] = '{:.3f}'.format(d['profit'])        
            
        
#        final_res = sorted(final_res, key=lambda i: i[sort_by])
        count = len(final_res)
#        print"count: ",count
#        print"offset_count: ",offset_count
#        print"final_res: ",final_res
        return count, offset_count, final_res