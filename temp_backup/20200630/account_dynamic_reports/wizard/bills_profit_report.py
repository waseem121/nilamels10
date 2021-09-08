from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

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
    location_id = fields.Many2one('stock.location', string='Store')
    salesman_id = fields.Many2one('res.users', string='Salesman')
#    brand_id = fields.Many2one('product.brand', string='Brand')
    date_from = fields.Date(string='From date', default=_get_date_from)
    date_to = fields.Date(string='To date', default=_get_date_to)

    show_profit_percent_sales = fields.Boolean(string='Show Profit percent/ Sales', default='True')
    show_profit_percent_cost = fields.Boolean(string='Show Profit percent/ Cost', default='True')
    show_profit_percent_net_profit = fields.Boolean(string='Show Profit percent/ Net Profit', default='True')

    group_by = fields.Selection(
        [('customer', 'Customer')],
        string='Group by', default='customer'
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=_get_default_company
    )
    sort_by = fields.Selection(
        [('customer', 'Customer'),
        ('bill_no', 'Bill Number'),
        ('profit', 'Profit')],
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
        
        filter_dict= {
            'category_ids': self.category_ids.ids,
            'location_id': self.location_id or False,
            'salesman_id': self.salesman_id or False,
            'date_from': self.date_from or '2020-01-01',
            'date_to': self.date_to or '2030-01-01',
            'show_profit_percent_sales': self.show_profit_percent_sales or False,
            'show_profit_percent_cost': self.show_profit_percent_cost or False,
            'show_profit_percent_net_profit': self.show_profit_percent_net_profit or False,
            
            'based_on': self.based_on or False,
            'sort_by': self.sort_by or False,
            'state': self.state or 'all',
            
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
        
        filters['date_from'] = data.get('date_from')
        filters['date_to'] = data.get('date_to')
        filters['based_on'] = data.get('based_on')
        filters['sort_by'] = data.get('sort_by')
        filters['state'] = data.get('state')
        
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
        domain = [('date_invoice', '>=', date_from),
                ('date_invoice', '<=', date_to)]
        
        based_on = data.get('based_on','sales_and_returns')
        if based_on == 'sales_and_returns':
            domain.append(('type', 'in', ('out_invoice','out_refund')))
        if based_on == 'sales':
            domain.append(('type', '=', 'out_invoice'))
        if based_on == 'returns':
            domain.append(('type', '=', 'out_refund'))
            
        state = data.get('state','all')
        if state== 'all':
            domain.append(('state', '!=', 'cancel'))
        if state== 'posted':
            domain.append(('state', 'not in', ('cancel','draft')))
        if state== 'not_posted':
            domain.append(('state', '=', 'draft'))

        if data.get('location_id'):
            location_id = data.get('location_id')
            domain.append(('location_id','=',location_id.id))
        if data.get('salesman_id'):
            salesman_id = data.get('salesman_id')
            domain.append(('user_id','=',salesman_id.id))
#        if data.get('product_ids'):
#            domain.append(('product_id', 'in', data.get('product_ids')))
#        if data.get('category_ids'):
#            domain.append(('product_id.categ_id', 'in', data.get('category_ids')))
        print"process_data domainnnn: ",domain

#        invoice_line_ids = self.env['account.invoice.line'].search(domain)
        invoice_ids = self.env['account.invoice'].search(domain)
        print"len(invoice_ids): ",len(invoice_ids)
        
        print"if data.get('category_ids'):: ",data.get('category_ids')
        category_ids = data.get('category_ids',[])
        category_ids = list(set(category_ids))
        print"category idsss: ",category_ids
#        all_categ = self.env['product.category'].browse(category_ids)
        
        product_ids = data.get('product_ids',[])
        product_ids = list(set(product_ids))
        print"product idsss: ",product_ids
        
#        all_products = self.env['product.product'].browse(product_ids)
#        print"len all products: ",len(all_products)
        
        final_res = []
        for invoice in invoice_ids:
            if (category_ids or product_ids):
                for l in invoice.invoice_line_ids_two:
                    product = l.product_id
                    if product_ids and (product.id not in product_ids):
                        continue
                    if category_ids and (product.categ_id.id not in category_ids):
                        continue
                
                
            d = {}
            number = invoice.number or ''
            if invoice.refund_without_invoice:
                number = 'Sales-Ret-'+str(number)
            else:
                number = 'Sales-'+str(number)
            total = invoice.amount_total
            extras = invoice.commission
            cost = invoice.total_cost
            discount = invoice.total_discount
            
            d['bill_no'] = number
            d['date'] = invoice.date_invoice
            d['customer'] = invoice.partner_id.name
            d['total'] = '{:.3f}'.format(total)
            d['discount'] = '{:.3f}'.format(discount)
            d['extras'] = '{:.3f}'.format(extras)
            d['net_sales'] = '{:.3f}'.format(total - discount - extras)
            d['cost'] = '{:.3f}'.format(cost)
            d['profit'] = '{:.3f}'.format(total - cost)
            
            final_res.append(d)
        
#        final_res = []
#        final_res.update({'bill_no': '123'})
#        final_res.append({'bill_no': '123'})
        print"final_res \n\n\n",len(final_res)
            
        return final_res
    
    def build_detailed_move_lines_old(self, offset=0, categ_id=0, fetch_range=FETCH_RANGE):
        data = self.get_filters(default_filters={})
#        print"filter data: ",data
        offset_count = offset * fetch_range
        
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
        if data.get('product_ids'):
            domain.append(('product_id', 'in', data.get('product_ids')))
        if data.get('category_ids'):
            domain.append(('product_id.categ_id', 'in', data.get('category_ids')))
        print"build_detailed_move_lines domainnnn: ",domain

        invoice_line_ids = self.env['account.invoice.line'].search(domain)
        print"build_detailed_move_lines len(invoice_line_ids): ",len(invoice_line_ids)
        
        product_ids = data.get('product_ids',[])
        if not len(product_ids):
            for l in invoice_line_ids:
                if not l.product_id:continue
                product_ids.append(l.product_id.id)
        product_ids = list(set(product_ids))
        print"build_detailed_move_lines product idsss: ",product_ids
        all_products = self.env['product.product'].browse(product_ids)

#        selected_product_ids = data.get('product_ids',False)
        show_arabic_name = data.get('show_arabic_name',False)
        show_profit_cost_ratio = data.get('show_profit_cost_ratio',False)
        show_profit_sales_ratio = data.get('show_profit_sales_ratio',False)
        show_balance = data.get('show_balance',False)
        show_balance_value = data.get('show_balance_value',False)
        show_last_price = data.get('show_last_price',False)
        show_last_cost = data.get('show_last_cost',False)
        show_bonus_and_bonus_cost = data.get('show_bonus_and_bonus_cost',False)
        show_price = data.get('show_price',False)
        show_barcode_field = data.get('show_barcode_field',False)
        show_categ = data.get('show_categ',False)
        show_brand = data.get('show_brand',False)
#        print"domainnnnnnnn: ",domain
        
#        invoice_ids = self.env['account.invoice'].sudo().search(domain,order='date_invoice')
        
#        all_products = []
        all_categ = [self.env['product.category'].browse(categ_id)]
        final_res = []
        for categ in all_categ:
            for each_product in all_products:
                if not each_product.categ_id:
                    continue
                if each_product.categ_id.id != categ.id:
                    continue
                
                v = {}
                cost, price, profit, qty,  = 0.0, 0.0, 0.0, 0.0
                free_qty, free_qty_cost = 0.0, 0.0
                unit = False
#                for l in invoice_lines:
                for l in invoice_line_ids:

                    if l.product_id.id != each_product.id:
                        continue
                    if l.invoice_id and l.invoice_id.type == 'out_refund':
                        profit -= (l.price_subtotal - (l.cost_price * (l.quantity + l.free_qty)))
                        cost -= (l.cost_price * l.quantity)
                        price -= (l.price_subtotal)
                        qty -= l.quantity
                        free_qty -= l.free_qty
                        free_qty_cost -= (l.cost_price * l.free_qty)
                        if not unit:
                            unit = l.uom_id.name or ''
                    else:
#                        cost += (l.cost_price * (l.quantity + l.free_qty))
                        profit += (l.price_subtotal - (l.cost_price * (l.quantity + l.free_qty)))
                        cost += (l.cost_price * l.quantity)
                        price += (l.price_subtotal)
#                        profit += (l.price_subtotal - (l.cost_price * l.quantity))
                        qty += l.quantity
                        
                        free_qty += l.free_qty
                        free_qty_cost += (l.cost_price * l.free_qty)
                        if not unit:
                            unit = l.uom_id.name or ''
                
                if not show_bonus_and_bonus_cost:
                    cost += free_qty_cost
                    qty += free_qty

                v['product_id'] = each_product.id
                v['product_code'] = each_product.default_code or ''
                v['product_name'] = each_product.name or ''
                v['arabic_name'] = each_product.name or ''
                v['barcode'] = each_product.barcode or ''
                v['category'] = each_product.categ_id.name
                v['brand'] = each_product.product_brand_id and each_product.product_brand_id.name or ''
                v['unit'] = unit
                v['qty'] = qty
                v['price'] = '{:.3f}'.format(price)
                v['cost'] = '{:.3f}'.format(cost)
                v['profit'] = '{:.3f}'.format(profit)
                v['profit_f'] = profit
                v['show_arabic_name'] = show_arabic_name
                v['show_profit_cost_ratio'] = show_profit_cost_ratio
                v['show_profit_sales_ratio'] = show_profit_sales_ratio
                v['show_balance'] = show_balance
                v['show_balance_value'] = show_balance_value
                v['show_last_price'] = show_last_price
                v['show_last_cost'] = show_last_cost
                v['show_bonus_and_bonus_cost'] = show_bonus_and_bonus_cost
                v['show_price'] = show_price
                v['show_barcode_field'] = show_barcode_field
                v['show_categ'] = show_categ
                v['show_brand'] = show_brand
                
                v['free_qty'] = free_qty
                v['free_qty_cost'] = '{:.3f}'.format(free_qty_cost)
                
                d_cost = cost
                if d_cost == 0.0:
                    d_cost = 1.0
                d_price = price
                if d_price == 0.0:
                    d_price = 1.0
                
                v['profit_cost_ratio'] = '{:.3f}'.format((profit / d_cost) * 100.0)
                v['profit_sales_ratio'] = '{:.3f}'.format((profit / d_price) * 100.0)
                
                balance = each_product.qty_available
                standard_price = each_product.standard_price
                
                v['balance'] = balance
                v['balance_value'] = '{:.3f}'.format(balance * standard_price)
                v['last_price'] = '{:.3f}'.format(each_product.lst_price)
                v['last_cost'] = '{:.3f}'.format(standard_price)
                v['profit_f'] = profit

                final_res.append(v)
                
        sort_by = self.sort_by or 'product'
        if sort_by == 'product':
            sort_by = 'product_name'
            final_res = sorted(final_res, key=lambda i: i[sort_by])
        else:
            if sort_by == 'sales': sort_by = 'price'
            final_res = sorted(final_res, key=lambda i: i[sort_by], reverse=True)
        
#        final_res = sorted(final_res, key=lambda i: i[sort_by])
        count = len(final_res)
#        print"count: ",count
#        print"offset_count: ",offset_count
#        print"final_res: ",final_res
        return count, offset_count, final_res
    
        
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
            filters['location_id'] = self.location_id or False
            filters['salesman_id'] = self.salesman_id or False
            filters['date_from'] = self.date_from or '2020-01-01'
            filters['date_to'] = self.date_from or '2030-01-01'
            filters['show_profit_percent_sales'] = self.show_profit_percent_sales or False
            filters['show_profit_percent_cost'] = self.show_profit_percent_cost or False
            filters['show_profit_percent_net_profit'] = self.show_profit_percent_net_profit or False
            filters['based_on'] = self.based_on or False
            filters['sort_by'] = self.sort_by or False
            filters['state'] = self.state or False
            
            account_lines = self.process_data()
            return filters, account_lines

    def action_pdf(self):
#        raise UserError(_('This feature is under development.'))
        filters, account_lines = self.get_report_datas()

        return self.env['report'].with_context({'landscape': 1}).get_action(
            self, 'account_dynamic_reports.product_profit', data={'Ledger_data': account_lines,
                        'Filters': filters
                        })

    def action_xlsx(self):
        raise UserError(_('This feature is under development.'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'BPR View',
            'tag': 'dynamic.bpr',
            'context': {'wizard_id': self.id}
        }
        return res