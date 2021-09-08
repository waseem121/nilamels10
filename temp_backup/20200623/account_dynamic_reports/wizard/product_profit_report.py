from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ProductProfitReport(models.TransientModel):
    _name = "product.profit.report"

    product_id = fields.Many2one('product.product', string='Product')
    location_id = fields.Many2one('stock.location', string='Store')
    salesman_id = fields.Many2one('res.users', string='Salesman')
    date_from = fields.Date(string='From date')
    date_to = fields.Date(string='To date')
    
    show_groups = fields.Boolean(string='Show Groups')
    show_products = fields.Boolean(string='Show Arabic Name')
    show_profit_cost_ratio = fields.Boolean(string='show Profit/Cost Ratio')
    show_profit_sales_ratio = fields.Boolean(string='show Profit/Sales Ratio')
    show_sell_avg = fields.Boolean(string='show Sale Avg')
    show_cost_avg = fields.Boolean(string='show Cost Avg')
    show_profit_margin = fields.Boolean(string='show Profit Margin')
    show_balance = fields.Boolean(string='show Balance')
    show_balance_value = fields.Boolean(string='show Balance Value')
    show_last_price = fields.Boolean(string='show Last Price')
    show_last_cost = fields.Boolean(string='show Last Cost')
    show_product_activity_rate = fields.Boolean(string='Show Product Activity Rate')
    show_with_unrelated_units = fields.Boolean(string='Show With Unrelated Units')
    show_discounts_and_extras = fields.Boolean(string='Show Discounts and Extras')
    show_net_sales = fields.Boolean(string='Show Net Sales')
    show_bonus_and_bonus_cost = fields.Boolean(string='Show Bonus and Bonus Cost')

    product_code = fields.Boolean(string='Product Code')
    product_name = fields.Boolean(string='Product Name')
    barcode_field = fields.Boolean(string='Barcode Field')
    quantity = fields.Boolean(string='Quantity')
    unit = fields.Boolean(string='Unit')
    price = fields.Boolean(string='Price')
    
    @api.model
    def create(self, vals):
        ret = super(ProductProfitReport, self).create(vals)
        return ret

    @api.multi
    def write(self, vals):

#        if vals.get('partner_ids'):
#            vals.update({'partner_ids': [(4, j) for j in vals.get('partner_ids')]})

        if vals.get('date_from') and vals.get('date_to'):
            vals.update({'date_range': False})
        ret = super(ProductProfitReport, self).write(vals)
        return ret
    
    
    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('"Date from" must be less than or equal to "Date to"'))
        return True
    
    def get_filters(self, default_filters={}):
        
        filter_dict= {
            'product_id': self.product_id or False,
            'location_id': self.location_id or False,
            'salesman_id': self.salesman_id or False,
            'date_from': self.date_from or '2020-01-01',
            'date_to': self.date_to or '2030-01-01',
            'show_products': self.show_products or False,
        }
        filter_dict.update(default_filters)
        return filter_dict
    
    def process_filters(self):
        ''' To show on report headers'''
        
        data = self.get_filters(default_filters={})

        filters = {}

        # For Js framework
#        filters['journals_list'] = data.get('journals_list')
        filters['show_products'] = self.show_products or False

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
        print"data: ",data
        
        date_from = data.get('date_from','2020-01-01')
        date_to = data.get('date_to','2030-01-01')
        
        domain = [('date_invoice', '>=', date_from),
                ('date_invoice', '<=', date_to),
                ('type', '=', 'out_invoice'),
                ('state', '!=', 'cancel')]
        if data.get('location_id'):
            location_id = data.get('location_id')
            domain.append(('location_id','=',location_id.id))
        if data.get('salesman_id'):
            salesman_id = data.get('salesman_id')
            domain.append(('user_id','=',salesman_id.id))
        product_id = data.get('product_id',False)
        show_products = data.get('show_products',False)
        print"domainnnnnnnn: ",domain
        
        invoice_ids = self.env['account.invoice'].sudo().search(domain,order='date_invoice')
#        invoice_ids = self.env['account.invoice'].search([('date_invoice','>=','2020-06-01')])
        print"invoice idssssss: ",invoice_ids
        
        res = []
        for invoice in invoice_ids:
            v = {}
            for l in invoice.invoice_line_ids_two:
                if product_id and (l.product_id.id!=product_id.id):
                    continue
                    
                v['product_code'] = l.product_id.default_code or ''
                v['product_name'] = l.product_id.name or ''
                v['arabic_name'] = ''
                v['barcode'] = l.product_id.barcode or ''
                v['category'] = l.product_id.categ_id.name
                v['brand'] = l.product_id.product_brand_id and l.product_id.product_brand_id.name or ''
                v['unit'] = l.uom_id.name or ''
                v['qty'] = l.quantity or 0.0
                v['price'] = '{:.3f}'.format(l.price_subtotal)
#                v['cost'] = l.cost_price * (l.quantity + l.free_qty) or 0.0
#                v['profit'] = l.price_subtotal - (l.cost_price * (l.quantity + l.free_qty))
                v['cost'] = '{:.3f}'.format(l.cost_price * (l.quantity + l.free_qty))
                v['profit'] = '{:.3f}'.format(l.price_subtotal - (l.cost_price * (l.quantity + l.free_qty)))
                v['show_products'] = show_products
                    
                res.append(v)
#        res = {}
        return res
        
    def get_report_datas(self, default_filters={}):
        '''
        Main method for pdf, xlsx and js calls
        :param default_filters: Use this while calling from other methods. Just a dict
        :return: All the datas for GL
        '''
        if self.validate_data():
            filters = self.process_filters()
            filters={}
            filters['show_products'] = self.show_products or False
            account_lines = self.process_data()
            return filters, account_lines

    def action_pdf(self):
        filters, account_lines = self.get_report_datas()

        return self.env['report'].with_context({'landscape': 1}).get_action(
            self, 'account_dynamic_reports.partner_ledger', data={'Ledger_data': account_lines,
                        'Filters': filters
                        })

    def action_xlsx(self):
        raise UserError(_('Please install a free module "dynamic_xlsx".'
                          'You can get it by contacting "pycustech@gmail.com". It is free'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'PL View',
            'tag': 'dynamic.ppr',
            'context': {'wizard_id': self.id}
        }
        return res