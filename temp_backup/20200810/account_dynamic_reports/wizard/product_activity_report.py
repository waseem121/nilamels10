from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

FETCH_RANGE = 2000


class ProductActivityReport(models.TransientModel):
    _name = "product.activity.report"
    
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

#    product_ids = fields.Many2many('product.product', string='Product')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    location_id = fields.Many2one('stock.location', string='Store')
    salesman_id = fields.Many2one('res.users', string='Salesman')
    date_from = fields.Date(string='From date', default=_get_date_from)
    date_to = fields.Date(string='To date', default=_get_date_to)
    
    show_arabic_name = fields.Boolean(string='Show Arabic Name')

    
#    group_by = fields.Selection(
#        [('category', 'Category')],
#        string='Group by', default='category'
#    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=_get_default_company
    )
    sort_by = fields.Selection(
        [('date', 'Date'),
        ('customer', 'Customer')],
        string='Sort by', default='date'
    )
    based_on = fields.Selection(
        [('sales_and_returns', 'Sales and Returns'),
        ('sales', 'Sales'),
        ('sales_returns', 'SalesReturns'),
        ('purchase', 'Purchase'),
        ('purchase_returns', 'PurchaseReturns'),
        ('internal_transfer', 'Internal Transfer'),
        ],
        string='Report Source', default='sales_and_returns'
    )
    state = fields.Selection(
        [('all', 'All'),
        ('posted', 'Posted'),
        ('not_posted', 'Not Posted')],
        string='State', default='all'
    )
    
    
    @api.model
    def create(self, vals):
        ret = super(ProductActivityReport, self).create(vals)
        return ret

    @api.multi
    def write(self, vals):
        ret = super(ProductActivityReport, self).write(vals)
        return ret
    
    
    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('"Date from" must be less than or equal to "Date to"'))
        return True
    
    def get_filters(self, default_filters={}):
        
#        product = self.product_id
        filter_dict= {
            'product_id': self.product_id,
#            'product_ids': self.product_ids.ids,
#            'category_ids': self.category_ids.ids,
            'location_id': self.location_id or False,
            'salesman_id': self.salesman_id or False,
            'date_from': self.date_from or '2020-01-01',
            'date_to': self.date_to or '2030-01-01',
            'show_arabic_name': self.show_arabic_name or False,
            'based_on': self.based_on or False,
            'sort_by': self.sort_by or False,
            'state': self.state or 'all',
            
            # For Js widget only
#            'product_list': [(p.id, p.name) for p in products],
            'product_list': [],
        }
        filter_dict.update(default_filters)
        return filter_dict
    
    def process_filters(self):
        ''' To show on report headers'''
        
        data = self.get_filters(default_filters={})
        filters = {}
        
        if data.get('product_id', False):
            filters['product'] = self.product_id.name
        else:
            filters['product'] = ['All']

        # For Js framework
#        filters['journals_list'] = data.get('journals_list')
        filters['show_arabic_name'] = self.show_arabic_name or False
        
        filters['date_from'] = data.get('date_from')
        filters['date_to'] = data.get('date_to')
        filters['state'] = data.get('state')
        
        filters['product_list'] = data.get('product_list')

        return filters
    
    
    def build_detailed_move_lines(self, offset=0, categ_id=0, fetch_range=FETCH_RANGE):
        data = self.get_filters(default_filters={})
#        print"filter data: ",data
        offset_count = offset * fetch_range
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
#            filters['show_arabic_name'] = self.show_arabic_name or False
            
            account_lines = self.process_data()
            return filters, account_lines

    def action_pdf(self):
#        raise UserError(_('This feature is under development.'))
        filters, account_lines = self.get_report_datas()

        return self.env['report'].with_context({'landscape': 1}).get_action(
            self, 'account_dynamic_reports.product_activity', data={'Ledger_data': account_lines,
                        'Filters': filters
                        })

    def action_xlsx(self):
        raise UserError(_('This feature is under development.'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'PAR View',
            'tag': 'dynamic.par',
            'context': {'wizard_id': self.id}
        }
        return res
    
    
    
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
#        print"process_data data.get('category_ids'): ",data.get('category_ids')
#        
        date_from = data.get('date_from','2020-01-01')
        date_to = data.get('date_to','2030-01-01')
        product = data.get('product_id')
        
        final_res = []
        SQL = """
            SELECT 
                sum(sq.quantity) as qty
            FROM 
                stock_history sq
                FULL JOIN product_product pp on sq.product_id= pp.id
            WHERE 
                sq.date<='%s' AND
                sq.product_id = '%s'
            """ % (date_from, product.id)
        self._cr.execute(SQL)
        res = self._cr.dictfetchall()
        initial_qty = 0
        if res:
            initial_qty = res[0].get('qty',0)
        if not initial_qty: initial_qty = 0
        print"initial_qty: ",initial_qty
        
        opening = {}
        opening['invoice_id'] = ''
        opening['ref_no'] = 'Opening Balance'
        opening['date'] = date_from
        opening['desc'] = 'Opening Balance'
        opening['customer'] = ''
        opening['qty_in'] = initial_qty
        opening['qty_out'] = 0
        opening['price'] = '{:.3f}'.format(0.000)
        opening['discount'] = '{:.3f}'.format(0.000)
        opening['cost'] = '{:.3f}'.format(0.000)
        opening['balance'] = 0
        opening['is_line'] = True
        final_res.append(opening)
        
        

        
        based_on = data.get('based_on','sales_and_returns')
        if based_on == 'internal_transfer':
            move_domain = [('date', '>=', date_from),
                    ('date', '<=', date_to)]
                    
#            picking_type_ids = self.env['stock.picking.type'].search([('code','=','internal')])
#            print"picking_type_ids: ",picking_type_ids
#            print"picking_type_ids: ",picking_type_ids.ids
#            if picking_type_ids:
#                move_domain.append(('picking_id.picking_type_id', 'in', picking_type_ids.ids))

            move_domain.append(('location_id.usage', '=', 'internal'))
            move_domain.append(('location_dest_id.usage', '=', 'internal'))

            state = data.get('state','all')
            if state== 'all':
                move_domain.append(('state', '!=', 'cancel'))
            if state== 'posted':
                move_domain.append(('state', 'not in', ('cancel','draft')))
            if state== 'not_posted':
                move_domain.append(('state', '=', 'draft'))
            if data.get('location_id'):
                location_id = data.get('location_id')
                move_domain.append(('picking_id.location_id','=',location_id.id))
                
            move_domain.append(('product_id', '=', product.id))

            move_ids = self.env['stock.move'].search(move_domain)
            print"len(move_ids): ",len(move_ids)
            total_qty_in, total_qty_out, total_price, total_discount, total_cost, total_balance = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            for m in move_ids:
                qty_in, qty_out, price, discount, cost = 0.0, 0.0, 0.0, 0.0, 0.0
                picking = m.picking_id or False
                qty = m.product_uom_qty
                cost = qty * m.price_unit
                
                if m.location_id.usage == 'internal':
                    qty_out = qty
                if m.location_dest_id.usage == 'internal':
                    qty_in = qty
                    
                v = {}
                v['invoice_id'] = picking.id
                v['ref_no'] = picking and picking.name or ''
                v['date'] = picking and picking.min_date or ''
                v['desc'] = 'Internal Transfer'
                v['customer'] = picking and picking.partner_id and picking.partner_id.name or ''
                v['qty_in'] = qty_in
                v['qty_out'] = qty_out
                v['price'] = '{:.3f}'.format(price)
                v['discount'] = '{:.3f}'.format(discount)
                v['cost'] = '{:.3f}'.format(cost)
                v['balance'] = 0
                v['is_line'] = True
                final_res.append(v)

                total_qty_in += qty_in
                total_qty_out += qty_out
                total_price += price
                total_discount += discount
                total_cost += cost


        ## sales and sales returns
        if based_on in ('sales_and_returns', 'sales','sales_returns'):
            domain = [('invoice_id.date_invoice', '>=', date_from),
                    ('invoice_id.date_invoice', '<=', date_to)]
            if based_on == 'sales_and_returns':
                domain.append(('invoice_id.type', 'in', ('out_invoice','out_refund')))
            if based_on == 'sales':
                domain.append(('invoice_id.type', '=', 'out_invoice'))
            if based_on == 'sales_returns':
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
            domain.append(('product_id', '=',product.id))
            print"process_data domainnnn: ",domain
            
            invoice_line_ids = self.env['account.invoice.line'].search(domain)
            print"len product_invoice_line_ids: ",len(invoice_line_ids)
            total_qty_in, total_qty_out, total_price, total_discount, total_cost, total_balance = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            for l in invoice_line_ids:
                qty_in, qty_out, price, discount, cost = 0.0, 0.0, 0.0, 0.0, 0.0
                if l.invoice_id and l.invoice_id.type == 'out_refund':
                    cost = (l.cost_price * (l.quantity + l.free_qty))
                    price = l.price_subtotal
                    qty_in = l.quantity + l.free_qty
                    discount_share = l.discount_share
                else:
                    cost = (l.cost_price * l.quantity) * -1
                    price = l.price_subtotal * -1
                    qty_out = l.quantity + l.free_qty
                    discount_share = l.discount_share *-1
                
                # totals
                total_qty_in += qty_in
                total_qty_out += qty_out
                total_price += price
                total_cost += cost
                total_discount += discount_share

                invoice = l.invoice_id
                desc = 'Sales Invoice'
                if invoice.type == 'out_refund':
                    desc = 'Sales Return'
                if invoice.type == 'in_invoice':
                    desc = 'Purchase Invoice'
                if invoice.type == 'in_refund':
                    desc = 'Purchase Return'

                v = {}
                v['invoice_id'] = l.invoice_id.id
                v['ref_no'] = l.invoice_id.number
                v['date'] = l.invoice_id.date_invoice
                v['desc'] = desc
                v['customer'] = l.invoice_id.partner_id.name
                v['qty_in'] = qty_in
                v['qty_out'] = qty_out
                v['price'] = '{:.3f}'.format(price)
                v['discount'] = '{:.3f}'.format(discount_share)
                v['cost'] = '{:.3f}'.format(cost)
                v['balance'] = 0
                v['is_line'] = True
                final_res.append(v)
                

        # purchase and purchase returns
        if based_on in ('purchase', 'purchase_returns'):
            domain = [('order_id.date_order', '>=', date_from),
                    ('order_id.date_order', '<=', date_to)]
#            if based_on == 'purchase':
#                domain.append(('invoice_id.type', '=', 'in_invoice'))

            state = data.get('state','all')
            if state== 'all':
                domain.append(('order_id.state', '!=', 'cancel'))
            if state== 'posted':
                domain.append(('order_id.state', 'not in', ('cancel','draft')))
            if state== 'not_posted':
                domain.append(('order_id.state', '=', 'draft'))

            domain.append(('product_id', '=',product.id))
            print"process_data domainnnn: ",domain
            
            purchase_line_ids = self.env['purchase.order.line'].search(domain)
            print"len purchase_line_ids: ",len(purchase_line_ids)
            total_qty_in, total_qty_out, total_price, total_discount, total_cost, total_balance = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            for l in purchase_line_ids:
                qty_in, qty_out, price, discount, cost = 0.0, 0.0, 0.0, 0.0, 0.0
                
                cost = 0
                price = l.price_subtotal
                qty_in = l.product_qty + l.free_qty
                discount_share = l.discount_share
                
                # totals
                total_qty_in += qty_in
                total_qty_out += qty_out
                total_price += price
                total_cost += cost
                total_discount += discount_share

                purchase = l.order_id
                desc = 'Purchase'
                v = {}
                v['invoice_id'] = purchase.id
                v['ref_no'] = purchase.name
                v['date'] = purchase.date_order.split(' ')[0]
                v['desc'] = desc
                v['customer'] = purchase.partner_id.name
                v['qty_in'] = qty_in
                v['qty_out'] = qty_out
                v['price'] = '{:.3f}'.format(price)
                v['discount'] = '{:.3f}'.format(discount_share)
                v['cost'] = '{:.3f}'.format(cost)
                v['balance'] = 0
                v['is_line'] = True
                final_res.append(v)
                

        sort_by = self.sort_by or 'date'
        final_res = sorted(final_res, key=lambda i: i[sort_by])
        balance = 0
        for d in final_res:
            balance += d['qty_in'] - d['qty_out']
            d['balance'] += balance
        
        total_qty_in += initial_qty
        d1 = {'ref_no': 'Total',
            'name': 'Total',
            'total_qty_in': total_qty_in,
            'total_qty_out': total_qty_out,
            'total_price': '{:.3f}'.format(total_price),
            'total_discount': '{:.3f}'.format(total_discount),
            'total_cost': '{:.3f}'.format(total_cost),
            'total_balance': balance,
            'is_line':False
        }
        final_res.append(d1)
        
#        print"final_res \n\n\n",final_res
        return final_res