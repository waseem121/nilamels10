from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

FETCH_RANGE = 2000


class ProductStockReport(models.TransientModel):
    _name = "product.stock.report"
    
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

    product_ids = fields.Many2many('product.product', string='Product')
    category_ids = fields.Many2many('product.category', string='Category')
    location_id = fields.Many2one('stock.location', string='Store', domain=[('usage', '=', 'internal')])
    partner_id = fields.Many2one('res.partner', string='Vendor')
    brand_id = fields.Many2one('product.brand', string='Brand')
    
    date_from = fields.Date(string='From date', default=_get_date_from)
    date_to = fields.Date(string='To date', default=_get_date_to)
    
    show_arabic_name = fields.Boolean(string='Show Arabic Name')
    show_product_code = fields.Boolean(string='Product Code', default='True')
    show_product_name = fields.Boolean(string='Product Name', default='True')
    show_barcode_field = fields.Boolean(string='Barcode Field')
    show_categ = fields.Boolean(string='Category')
    show_brand = fields.Boolean(string='Brand')    

    
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
    
    
    @api.model
    def create(self, vals):
        ret = super(ProductStockReport, self).create(vals)
        return ret

    @api.multi
    def write(self, vals):
        ret = super(ProductStockReport, self).write(vals)
        return ret
    
    
    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('"Date from" must be less than or equal to "Date to"'))
        return True
    
    def get_filters(self, default_filters={}):
        
        products = self.product_ids if self.product_ids else self.env['product.product'].search([])
        
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
        
        product_list_new = ['All Products']
        if self.product_ids or []:
            product_list_new = [p.name for p in self.product_ids]
            
        partner = 'All'
        if self.partner_id:
            partner = self.partner_id.name
        
        location = 'All'
        if self.location_id:
            location = self.location_id.name
            
        brand = 'All'
        if self.brand_id:
            brand = self.brand_id.name
        
        filter_dict= {
            'product_ids': self.product_ids.ids,
            'category_ids': category_ids,
            'date_from': self.date_from or '2020-01-01',
            'date_to': self.date_to or '2030-01-01',
            'show_arabic_name': self.show_arabic_name or False,
            'sort_by': self.sort_by or False,
            
            # For Js widget only
            'product_list': [(p.id, p.name) for p in products],
            'product_list_new': product_list_new,
            'category_list': category_list,
            'location': location,
            'partner': partner,
            'brand': brand,
        }
        filter_dict.update(default_filters)
        return filter_dict
    
    def process_filters(self):
        ''' To show on report headers'''
        
        data = self.get_filters(default_filters={})
        filters = {}
        
        if data.get('product_ids', []):
            filters['products'] = self.env['product.product'].browse(data.get('product_ids', [])).mapped('name')
        else:
            filters['products'] = ['All']
            
        if data.get('category_ids', []):
            filters['categories'] = self.env['product.category'].browse(data.get('category_ids', [])).mapped('name')
        else:
            filters['categories'] = ['All']

        # For Js framework
#        filters['journals_list'] = data.get('journals_list')
        filters['show_arabic_name'] = self.show_arabic_name or False
        
        filters['date_from'] = data.get('date_from')
        filters['date_to'] = data.get('date_to')
        filters['state'] = data.get('state')
        
        filters['product_list'] = data.get('product_list')
        filters['product_list_new'] = data.get('product_list_new')
        filters['category_list'] = data.get('category_list')
        filters['location'] = data.get('location')
        filters['partner'] = data.get('partner')
        filters['brand'] = data.get('brand')

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
            self, 'account_dynamic_reports.product_stock', data={'Ledger_data': account_lines,
                        'Filters': filters
                        })

    def action_xlsx(self):
        raise UserError(_('This feature is under development.'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'PSR View',
            'tag': 'dynamic.psr',
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
        
        
#        domain = [('invoice_id.date_invoice', '>=', date_from),
#                ('invoice_id.date_invoice', '<=', date_to)]
#        domain.append(('invoice_id.type', 'in', ('out_invoice','out_refund')))
#        if based_on == 'sales_and_returns':
#            domain.append(('invoice_id.type', 'in', ('out_invoice','out_refund')))
#        if based_on == 'sales':
#            domain.append(('invoice_id.type', '=', 'out_invoice'))
#        if based_on == 'sales_returns':
#            domain.append(('invoice_id.type', '=', 'out_refund'))
#        if based_on == 'purchase':
#            domain.append(('invoice_id.type', '=', 'in_invoice'))
#        if based_on == 'purchase_returns':
#            domain.append(('invoice_id.type', '=', 'in_refund'))


        domain = []
        if data.get('category_ids'):
            domain.append(('categ_id', 'in', data.get('category_ids')))
#        if data.get('product_ids'):
#            domain.append(('product_id', 'in', data.get('product_ids')))

        print"process_data domainnnn: ",domain

        product_ids = data.get('product_ids')
        if not len(product_ids):
            product_ids = []
            products = self.env['product.product'].search(domain)
            for p in products:
                product_ids.append(p.id)
            
        product_ids = list(set(product_ids))

        final_res = []
        total_qty, total_price, total_subtotal = 0.0, 0.0, 0.0
#        product_ids = [4341]
        product_ids = ','.join(map(str, product_ids))
        SQL = """
            SELECT 
                sq.product_id as product_id,
                sum(sq.quantity) as qty,
                sum(sq.price_unit_on_quant) as price
            FROM 
                stock_history sq

                FULL JOIN product_product pp on sq.product_id= pp.id
            WHERE 
                sq.date >= '%s' AND sq.date<='%s' AND
                sq.product_id in (%s) 
                GROUP BY sq.product_id
            """ % (date_from, date_to, product_ids)
        self._cr.execute(SQL)
        res = self._cr.dictfetchall()
        for each in res:
            product_id = each.get('product_id')
            price = each.get('price')
            qty = each.get('qty')
            
            product = self.env['product.product'].browse(product_id)
            price = product.lst_price
            v = {}
            v['product_id'] = product.id
            v['product_code'] = product.default_code
            v['product_name'] = product.name
            v['qty'] = qty
            v['price'] = '{:.3f}'.format(price)
            v['subtotal'] = '{:.3f}'.format(qty*price)
            v['is_line'] = True

            final_res.append(v)

            total_qty += qty
            total_price += price
            total_subtotal += (qty*price)


#        sort_by = self.sort_by or 'date'
#        final_res = sorted(final_res, key=lambda i: i[sort_by])

        d1 = {'product_name': 'Total',
            'name': 'Total',
            'total_qty': total_qty,
            'total_price': '{:.3f}'.format(total_price),
            'total_subtotal': '{:.3f}'.format(total_subtotal),
            'is_line':False
        }
        final_res.append(d1)
        
#        print"final_res \n\n\n",final_res
        return final_res
