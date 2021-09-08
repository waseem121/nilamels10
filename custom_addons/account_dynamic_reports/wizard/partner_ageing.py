from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import collections
from collections import OrderedDict

FETCH_RANGE = 2500


class InsPartnerAgeing(models.TransientModel):
    _name = "ins.partner.ageing"

    @api.onchange('partner_type')
    def onchange_partner_type(self):
        self.partner_ids = [(5,)]
        if self.partner_type:
            company_id = self.env.user.company_id
            if self.partner_type == 'customer':
                partner_company_domain = [('parent_id', '=', False),
                                          ('customer', '=', True),
                                          '|',
                                          ('company_id', '=', company_id.id),
                                          ('company_id', '=', False)]

                self.partner_ids |= self.env['res.partner'].search(partner_company_domain)
            if self.partner_type == 'supplier':
                partner_company_domain = [('parent_id', '=', False),
                                          ('supplier', '=', True),
                                          '|',
                                          ('company_id', '=', company_id.id),
                                          ('company_id', '=', False)]

                self.partner_ids |= self.env['res.partner'].search(partner_company_domain)

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'Ageing'))
        return res

    @api.model
    def _get_default_bucket_1(self):
        return self.env.user.company_id.bucket_1

    @api.model
    def _get_default_bucket_2(self):
        return self.env.user.company_id.bucket_2

    @api.model
    def _get_default_bucket_3(self):
        return self.env.user.company_id.bucket_3

    @api.model
    def _get_default_bucket_4(self):
        return self.env.user.company_id.bucket_4

    @api.model
    def _get_default_bucket_5(self):
        return self.env.user.company_id.bucket_5

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    as_on_date = fields.Date(string='As on date', required=True, default=fields.Date.today())
    bucket_1 = fields.Integer(string='Bucket 1', required=True, default=_get_default_bucket_1)
    bucket_2 = fields.Integer(string='Bucket 2', required=True, default=_get_default_bucket_2)
    bucket_3 = fields.Integer(string='Bucket 3', required=True, default=_get_default_bucket_3)
    bucket_4 = fields.Integer(string='Bucket 4', required=True, default=_get_default_bucket_4)
    bucket_5 = fields.Integer(string='Bucket 5', required=True, default=_get_default_bucket_5)
    include_details = fields.Boolean(string='Include Details', default=True)
    type = fields.Selection([('receivable','Receivable Accounts Only'),
                              ('payable','Payable Accounts Only')], string='Type')
#    partner_type = fields.Selection([('customer', 'Customer Only'),
#                             ('supplier', 'Supplier Only')], string='Partner Type')
    partner_type = fields.Selection([('customer', 'Customer Only')
                             ], string='Partner Type')

    partner_ids = fields.Many2many(
        'res.partner', required=False
    )
    partner_category_ids = fields.Many2many(
        'res.partner.category', string='Partner Tag',
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=_get_default_company
    )
    draft_invoices_refunds = fields.Boolean(string='Draft Invoices and Refunds', default=True,
        help="includes unposted invoices and refunds in the report.")
    sales_man_id = fields.Many2one("res.users", string="Salesman")
    based_on_date = fields.Selection([
        ('due_date', 'Due Date'),
        ('invoice_date', 'Invoice Date')],
        string='Based on Date', default='invoice_date',
        help="Report based on Due date or the Invoice dates")
    show_zero_balance = fields.Boolean(string='Show Zero Balance', default=True)

    @api.multi
    def write(self, vals):
        if not vals.get('partner_ids'):
            vals.update({
                'partner_ids': [(5, 0, 0)]
            })

        if vals.get('partner_category_ids'):
            vals.update({'partner_category_ids': [(4, j) for j in vals.get('partner_category_ids')]})
        if vals.get('partner_category_ids') == []:
            vals.update({'partner_category_ids': [(5,)]})

        ret = super(InsPartnerAgeing, self).write(vals)
        return ret

    def validate_data(self):
        if not(self.bucket_1 < self.bucket_2 and self.bucket_2 < self.bucket_3 and self.bucket_3 < self.bucket_4 and \
            self.bucket_4 < self.bucket_5):
            raise ValidationError(_('"Bucket order must be ascending"'))
        return True
    
    def _get_invoice_totals(self, args_query, args_value, invoice_type):
#        print"invoice_type: ",invoice_type
#        print"args_query: ",args_query
#        print"args_value: ",args_value
        cr = self.env.cr
        if invoice_type=='invoice':
            new_query = '''SELECT sum(i.amount_total)
                FROM account_invoice i,res_partner p
                WHERE i.partner_id=p.id AND 
                i.type in ('out_invoice','out_refund') AND 
                i.refund_without_invoice!=True AND i.state='draft' AND 
                '''+args_query
            
        elif invoice_type == 'refund':
            new_query = '''SELECT sum(i.amount_total)
                FROM account_invoice i,res_partner p
                WHERE i.partner_id=p.id AND 
                i.type in ('out_invoice','out_refund') AND 
                i.refund_without_invoice=True AND i.state='draft' AND 
                '''+args_query
        cr.execute(new_query, args_value)
        invoice_totals =  cr.dictfetchall()
        amount = 0.0
        if invoice_totals:
            amount = invoice_totals[0]['sum'] or 0.0
#        print"amt: ",amount
        return amount

    def get_filters(self, default_filters={}):
        company_id = self.env.user.company_id
        partner_company_domain = [('parent_id','=', False),
                                  '|',
                                  ('customer', '=', True),
                                  ('supplier', '=', True),
                                  '|',
                                  ('company_id', '=', company_id.id),
                                  ('company_id', '=', False)]

        partners = self.partner_ids if self.partner_ids else self.env['res.partner'].search(partner_company_domain)
        categories = self.partner_category_ids if self.partner_category_ids else self.env['res.partner.category'].search([])

        filter_dict = {
            'partner_ids': self.partner_ids.ids,
            'partner_category_ids': self.partner_category_ids.ids,
            'company_id': self.company_id and self.company_id.id or False,
            'as_on_date': self.as_on_date,
            'type': self.type,
            'partner_type': self.partner_type,
            'bucket_1': self.bucket_1,
            'bucket_2': self.bucket_2,
            'bucket_3': self.bucket_3,
            'bucket_4': self.bucket_4,
            'bucket_5': self.bucket_5,
            'include_details': self.include_details,
            'sales_man_id': self.sales_man_id and self.sales_man_id.id or False,
            'based_on_date': self.based_on_date or 'invoice_date',
            'draft_invoices_refunds': self.draft_invoices_refunds or True,
            'show_zero_balance': self.show_zero_balance or True,

            # For Js widget only
            'partners_list': [(p.id, p.name) for p in partners],
            'category_list': [(c.id, c.name) for c in categories],
            'company_name': self.company_id and self.company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def process_filters(self):
        ''' To show on report headers'''

        data = self.get_filters(default_filters={})

        filters = {}

        filters['bucket_1'] = data.get('bucket_1')
        filters['bucket_2'] = data.get('bucket_2')
        filters['bucket_3'] = data.get('bucket_3')
        filters['bucket_4'] = data.get('bucket_4')
        filters['bucket_5'] = data.get('bucket_5')
        
        if data.get('sales_man_id', False):
            filters['sales_man'] = self.env['res.users'].browse(data.get('sales_man_id')).name
        else:
            filters['sales_man'] = 'All'

        if data.get('partner_ids', []):
            filters['partners'] = self.env['res.partner'].browse(data.get('partner_ids', [])).mapped('name')
        else:
            filters['partners'] = ['All']

        if data.get('as_on_date', False):
            filters['as_on_date'] = data.get('as_on_date')

        if data.get('company_id'):
            filters['company_id'] = data.get('company_id')
        else:
            filters['company_id'] = ''

        if data.get('type'):
            filters['type'] = data.get('type')

        if data.get('partner_type'):
            filters['partner_type'] = data.get('partner_type')

        if data.get('partner_category_ids', []):
            filters['categories'] = self.env['res.partner.category'].browse(data.get('partner_category_ids', [])).mapped('name')
        else:
            filters['categories'] = ['All']

        if data.get('include_details'):
            filters['include_details'] = True
        else:
            filters['include_details'] = False
            
        filters['based_on_date'] = data.get('based_on_date')
        filters['draft_invoices_refunds'] = data.get('draft_invoices_refunds')
        filters['partner_type'] = 'Customers'
        filters['show_zero_balance'] = data.get('show_zero_balance')

        # For Js framework
        filters['partners_list'] = data.get('partners_list')
        filters['category_list'] = data.get('category_list')
        filters['company_name'] = data.get('company_name')

        return filters
    
#    def prepare_bucket_list_old(self):
#        periods = {}
#        date_from = self.as_on_date
#        date_from = fields.Date.from_string(date_from)
#
#        lang = self.env.user.lang
#        language_id = self.env['res.lang'].search([('code', '=', lang)])[0]
#
#        bucket_list = [self.bucket_1,self.bucket_2,self.bucket_3,self.bucket_4,self.bucket_5]
#
#        # Bucket 0 (eg Upto As on) ====> Common and must line
#        start = False
#        stop = date_from
#        name = 'Not Due'
#        periods[0] = {
#            'bucket': 'As on',
#            'name': name,
#            'start': '',
#            'stop': stop.strftime('%Y-%m-%d'),
#        }
#
#        stop = date_from
#        final_date = False
#        for i in range(5):
#            start = stop - relativedelta(days=1)
#            stop = start - relativedelta(days=bucket_list[i])
#            name = '0 - ' + str(bucket_list[0]) if i==0 else  str(str(bucket_list[i-1] + 1)) + ' - ' + str(bucket_list[i])
#            final_date = stop
#            periods[i+1] = {
#                'bucket': bucket_list[i],
#                'name': name,
#                'start': start.strftime('%Y-%m-%d'),
#                'stop': stop.strftime('%Y-%m-%d'),
#            }
#
#        # Bucket Final (eg 180+) ====> Common and must line
#        start = final_date -relativedelta(days=1)
#        stop = ''
#        name = str(self.bucket_5) + ' +'
#
#        periods[6] = {
#            'bucket': 'Above',
#            'name': name,
#            'start': start.strftime('%Y-%m-%d'),
#            'stop': '',
#        }
#        return periods    

    def prepare_bucket_list(self):
        periods = {}
        date_from = self.as_on_date
        date_from = fields.Date.from_string(date_from)

        lang = self.env.user.lang
        language_id = self.env['res.lang'].search([('code', '=', lang)])[0]

#        bucket_list = [self.bucket_1,self.bucket_2,self.bucket_3,self.bucket_4,self.bucket_5]
        bucket_list = [self.bucket_1,self.bucket_2,self.bucket_3,self.bucket_4]

        # Bucket 0 (eg Upto As on) ====> Common and must line
        start = False
        stop = date_from
        name = 'Not Due'
        periods[0] = {
            'bucket': 'As on',
            'name': name,
            'start': '',
            'stop': stop.strftime('%Y-%m-%d'),
        }

        stop = date_from
        final_date = False
        for i in range(3):
            if self.based_on_date=='invoice_date':
                if i!=0:
                    start = stop - relativedelta(days=1)
                else:
                    start = stop
            else:
                start = stop - relativedelta(days=1)
            stop = start - relativedelta(days=bucket_list[i])
            name = '0 - ' + str(bucket_list[0]) if i==0 else  str(str(bucket_list[i-1] + 1)) + ' - ' + str(bucket_list[i])
            final_date = stop
            periods[i+1] = {
                'bucket': bucket_list[i],
                'name': name,
                'start': start.strftime('%Y-%m-%d'),
                'stop': stop.strftime('%Y-%m-%d'),
            }

        # Bucket Final (eg 180+) ====> Common and must line
        start = final_date -relativedelta(days=1)
        stop = ''
#        name = str(self.bucket_5) + ' +'
        name = str(self.bucket_4) + ' +'

        periods[4] = {
            'bucket': 'Above',
            'name': name,
            'start': start.strftime('%Y-%m-%d'),
            'stop': '',
        }
        return periods

    def process_detailed_data(self, offset=0, partner=0, fetch_range=FETCH_RANGE):
        '''

        It is used for showing detailed move lines as sub lines. It is defered loading compatable
        :param offset: It is nothing but page numbers. Multiply with fetch_range to get final range
        :param partner: Integer - Partner
        :param fetch_range: Global Variable. Can be altered from calling model
        :return: count(int-Total rows without offset), offset(integer), move_lines(list of dict)
        '''
        as_on_date = self.as_on_date
        period_dict = self.prepare_bucket_list()
        period_list = [period_dict[a]['name'] for a in period_dict]
        company_id = self.env.user.company_id

        type = ('receivable','payable')
        if self.type:
            type = tuple([str(self.type),'none'])

        offset = offset * fetch_range
        count = 0

        if partner:

            # Get the count of total lines for pagination

            sql = """
                    SELECT COUNT(*)
                    FROM
                        account_move_line AS l
                    LEFT JOIN
                        account_move AS m ON m.id = l.move_id
                    LEFT JOIN
                        account_account AS a ON a.id = l.account_id
                    LEFT JOIN
                        account_account_type AS ty ON a.user_type_id = ty.id
                    LEFT JOIN
                        account_journal AS j ON l.journal_id = j.id
                    WHERE
                        l.balance <> 0
                        AND m.state = 'posted'
                        AND ty.type IN %s
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                """ % (type, partner, as_on_date, company_id.id)
            self.env.cr.execute(sql)
            count = self.env.cr.fetchone()[0]

            SELECT = """SELECT m.name AS move_name,
                                m.id AS move_id,
                                l.date AS date,
                                l.date_maturity AS date_maturity, 
                                j.name AS journal_name,
                                cc.id AS company_currency_id,
                                a.name AS account_name, """

            for period in period_dict:
                if period_dict[period].get('start') and period_dict[period].get('stop'):
                    SELECT += """ CASE 
                                    WHEN 
                                        COALESCE(l.date_maturity,l.date) >= '%s' AND 
                                        COALESCE(l.date_maturity,l.date) <= '%s'
                                    THEN
                                        sum(l.balance) +
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND create_date <= '%s'), 0
                                                )
                                            ) -
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount) 
                                                FROM account_partial_reconcile 
                                                WHERE debit_move_id = l.id AND create_date <= '%s'), 0
                                                )
                                            )
                                    ELSE
                                        0
                                    END AS %s,"""%(period_dict[period].get('stop'),
                                                   period_dict[period].get('start'),
                                                   as_on_date,
                                                   as_on_date,
                                                   'range_'+str(period),
                                                   )
                elif not period_dict[period].get('start'):
                    SELECT += """ CASE 
                                    WHEN 
                                        COALESCE(l.date_maturity,l.date) >= '%s' 
                                    THEN
                                        sum(
                                            l.balance
                                            ) +
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND create_date <= '%s'), 0
                                                )
                                            ) -
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount) 
                                                FROM account_partial_reconcile 
                                                WHERE debit_move_id = l.id AND create_date <= '%s'), 0
                                                )
                                            )
                                    ELSE
                                        0
                                    END AS %s,"""%(period_dict[period].get('stop'), as_on_date, as_on_date, 'range_'+str(period))
                else:
                    SELECT += """ CASE
                                    WHEN
                                        COALESCE(l.date_maturity,l.date) <= '%s' 
                                    THEN
                                        sum(
                                            l.balance
                                            ) +
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND create_date <= '%s'), 0
                                                )
                                            ) -
                                        sum(
                                            COALESCE(
                                                (SELECT 
                                                    SUM(amount) 
                                                FROM account_partial_reconcile 
                                                WHERE debit_move_id = l.id AND create_date <= '%s'), 0
                                                )
                                            )
                                    ELSE
                                        0
                                    END AS %s """%(period_dict[period].get('start'), as_on_date, as_on_date ,'range_'+str(period))

            sql = """
                    FROM
                        account_move_line AS l
                    LEFT JOIN
                        account_move AS m ON m.id = l.move_id
                    LEFT JOIN
                        account_account AS a ON a.id = l.account_id
                    LEFT JOIN
                        account_account_type AS ty ON a.user_type_id = ty.id
                    LEFT JOIN
                        account_journal AS j ON l.journal_id = j.id
                    LEFT JOIN 
                        res_currency AS cc ON l.company_currency_id = cc.id
                    WHERE
                        l.balance <> 0
                        AND m.state = 'posted'
                        AND ty.type IN %s
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                    GROUP BY
                        l.date, l.date_maturity, m.id, m.name, j.name, a.name, cc.id
                    OFFSET %s ROWS
                    FETCH FIRST %s ROWS ONLY
                """%(type, partner, as_on_date, company_id.id, offset, fetch_range)
            self.env.cr.execute(SELECT + sql)
            final_list = self.env.cr.dictfetchall() or 0.0
            move_lines = []
            for m in final_list:
                if (m['range_0'] or m['range_1'] or m['range_2'] or m['range_3'] or m['range_4'] or m['range_5']):
                    m['balance_custom'] = 0
                    move_lines.append(m)

            if move_lines:
                return count, offset, move_lines, period_list
            else:
                return 0, 0, [], []

    def process_data(self):
        ''' Query Start Here
        ['partner_id':
            {'0-30':0.0,
            '30-60':0.0,
            '60-90':0.0,
            '90-120':0.0,
            '>120':0.0,
            'as_on_date_amount': 0.0,
            'total': 0.0}]
        1. Prepare bucket range list from bucket values
        2. Fetch partner_ids and loop through bucket range for values
        '''
        period_dict = self.prepare_bucket_list()
        company_id = self.env.user.company_id
        domain = ['|',('company_id','=',company_id.id),('company_id','=',False)]
        # TODO remove this custom domain
        domain.append(('customer','=', True))
        if self.partner_type == 'customer':
            domain.append(('customer','=', True))
        if self.partner_type == 'supplier':
            domain.append(('supplier','=', True))

        if self.partner_category_ids:
            domain.append(('category_id','in',self.partner_category_ids.ids))
            
        if self.sales_man_id:
            domain.append(('user_id','=', self.sales_man_id.id))

#        domain = [('id','=',1901)]   # 
#        domain = [('id','=',1285)]   # Hanil Wholesale
#        domain = [('id','=',1901)]   # Haba Store Fahaheel Bk10 St9 - Anwar
#        domain = [('id','=',1635)]   # Saf Al Kuwait Food Stuff Shuwaik
#        domain = [('id','=',469)]   # zam zam
#        domain = [('id','=',1554)]   # Abraj Al Kuwait Food Stuff Shuwaik
#        domain = [('id','=',1091)]   # Al Dallah Store II Riggai
#        domain = [('id','=',1113)]   # Evermart Riggai Bl-02 st-21
#        domain = [('id','=',664)]   # Lulu hyper
#        domain = [('id','=',1099)]   # Asia store
#        domain = [('id','=',378)]   # custom domain
#        domain = [('id','=',1898)]   # custom domain
#        domain = [('id','in',(378,375))]   # custom domain
        partner_ids = self.partner_ids or self.env['res.partner'].search(domain)
        as_on_date = self.as_on_date
        company_currency_id = company_id.currency_id.id

        type = ('receivable', 'payable')
        if self.type:
            type = tuple([str(self.type),'none'])
        
#        print"partner_ids Befor sorting: ",partner_ids
#        print"partner_ids Befor sorting len: ",len(partner_ids)
        partner_names = {}
        for partner in partner_ids:
            partner_names[partner.name] = partner.id
            
#        for key in sorted(partner_names):
#            print "%s: %s" % (key, partner_names[key])
            
#        print"partner_names: ",partner_names
#        dict1 = dict(OrderedDict(sorted(partner_names.items())) )
        dict1 = collections.OrderedDict(sorted(partner_names.items()))
#        print"dict11 len: ",len(dict1)
        new_partner_ids = []
        for d in dict1:
            partner_id = partner_names.get(d)
            new_partner_ids.append(partner_id)
#        print"new_partner_ids: ",new_partner_ids
        sorted_partner_ids = new_partner_ids
#        print"sorted_partner_ids:  Len",len(sorted_partner_ids)

        partner_ids = self.env['res.partner'].browse(new_partner_ids)
#        print"partner_ids after sorting: ",partner_ids
        
#        for p in partner_ids:
#            print"p.name: ",p.name
        # Build Dict
        partner_dict = {}
        for partner in partner_ids:
            partner_dict.update({partner.id:{}})

        # For total
        partner_dict.update({'Total': {}})
        for period in period_dict:
            partner_dict['Total'].update({period_dict[period]['name']: 0.0})
        partner_dict['Total'].update({'total': 0.0, 'partner_name': 'ZZZZZZZZZ',
                        'amount_due':0.0, 'uncleared_receipts':0.0,
                        'balance':0.0})
        partner_dict['Total'].update({'company_currency_id': company_currency_id})

        for partner in partner_ids:
            partner_dict[partner.id].update({'partner_name':partner.name})
            account = False
            if partner.supplier:
                code = partner.property_account_payable_id.code
                account = partner.property_account_payable_id
            else:
                code = partner.property_account_receivable_id.code
                account = partner.property_account_receivable_id
                
            credit_days = partner.property_payment_term_id and partner.property_payment_term_id.name or ''
            if credit_days:
                credit_days = credit_days.split(" ")[0]
            
            partner_dict[partner.id].update({'code': code})
            partner_dict[partner.id].update({'credit_days': credit_days})
            partner_dict[partner.id].update({'balance': 0.000})
            partner_dict[partner.id].update({'uncleared_receipts': 0.00})
            partner_dict[partner.id].update({'amount_due': 0.00})
            total_balance = 0.0

            # For getting count
            sql = """
                SELECT
                    COUNT(*) AS count
                FROM
                    account_move_line AS l
                LEFT JOIN
                    account_move AS m ON m.id = l.move_id
                LEFT JOIN
                    account_account AS a ON a.id = l.account_id
                LEFT JOIN
                    account_account_type AS ty ON a.user_type_id = ty.id
                WHERE
                    l.balance <> 0
                    AND m.state = 'posted'
                    AND ty.type IN %s
                    AND l.partner_id = %s
                    AND l.date <= '%s'
                    AND l.company_id = %s
            """%(type, partner.id, as_on_date, company_id.id)
            self.env.cr.execute(sql)
            fetch_dict = self.env.cr.dictfetchone() or 0.0
            count = fetch_dict.get('count') or 0.0

            if count:
                
                # get uncleared_receipts
#                SUM(l.debit) - sum(l.credit) AS uncleared_receipts
                if self.based_on_date == 'due_date':
                    sql = """
                        SELECT
                            SUM(l.credit) AS uncleared_receipts
                        FROM
                            account_move_line AS l
                        LEFT JOIN
                            account_move AS m ON m.id = l.move_id
                        LEFT JOIN
                            account_account AS a ON a.id = l.account_id
                        LEFT JOIN
                            account_account_type AS ty ON a.user_type_id = ty.id
                        WHERE
                            l.reconciled!=True
                            AND m.state = 'posted'
                            AND ty.type IN %s
                            AND l.partner_id = %s
                            AND l.date <= '%s'
                            AND l.company_id = %s
                    """%(type, partner.id, as_on_date, company_id.id)
                else:
                    sql_old = """
                        SELECT
                            SUM(l.credit) AS uncleared_receipts
                        FROM
                            account_move_line AS l
                        LEFT JOIN
                            account_move AS m ON m.id = l.move_id
                        LEFT JOIN
                            account_account AS a ON a.id = l.account_id
                        LEFT JOIN
                            account_account_type AS ty ON a.user_type_id = ty.id
                        WHERE
                            l.reconciled!=True
                            AND m.state = 'posted'
                            AND ty.type IN %s
                            AND l.partner_id = %s
                            AND (COALESCE(l.date,l.date_maturity) <= '%s')
                            AND l.date <= '%s'
                            AND l.company_id = %s
                    """%(type, partner.id, as_on_date, as_on_date, company_id.id)
                    sql = """
                        SELECT
                                SUM(l.credit) AS uncleared_receipts,
                                sum(COALESCE((SELECT SUM(amount)FROM account_partial_reconcile
                                    WHERE credit_move_id = l.id), 0)) AS sum_debit,
                                sum(COALESCE((SELECT SUM(amount) FROM account_partial_reconcile
                                    WHERE debit_move_id = l.id), 0)) AS sum_credit
                        FROM
                            account_move_line AS l
                        LEFT JOIN
                            account_move AS m ON m.id = l.move_id
                        LEFT JOIN
                            account_account AS a ON a.id = l.account_id
                        LEFT JOIN
                            account_account_type AS ty ON a.user_type_id = ty.id
                        WHERE
                            l.reconciled!=True
                            AND m.state = 'posted'
                            AND ty.type IN %s
                            AND l.partner_id = %s
                            AND (COALESCE(l.date,l.date_maturity) <= '%s')
                            AND l.date <= '%s'
                            AND l.company_id = %s
                    """%(type, partner.id, as_on_date, as_on_date, company_id.id)                    
                self.env.cr.execute(sql)
                query_res = self.env.cr.dictfetchall() or 0.0
                print"uncleared_receipts query_res: ",query_res
                uncleared_receipts = query_res[0].get('uncleared_receipts',0)
                print"uncleared_receipts: ",uncleared_receipts
                if uncleared_receipts is None:
                    uncleared_receipts = 0.0
                
#                sum_credit =query_res[0].get('sum_credit',0)
#                if sum_credit is None:
#                    sum_credit=0.0
                sum_debit =query_res[0].get('sum_debit',0)
                if sum_debit is None:
                    sum_debit=0.0
#                uncleared_receipts += (sum_credit - sum_debit)
                uncleared_receipts -= sum_debit
                print"uncleared_receipts11: ",uncleared_receipts
                
                sql = """
                    select sum(amount) as amount from account_partial_reconcile 
                    where credit_move_id in 
                        (select id from account_move_line where 
                        partner_id=%s and date<='%s') and 
                    debit_move_id in (select id from account_move_line 
                        where partner_id=%s and date>'%s')
                """%(partner.id,as_on_date,partner.id,as_on_date)
                self.env.cr.execute(sql)
                query_res = self.env.cr.dictfetchall() or 0.0
                print"uncleared_receipts New query_res: ",query_res
                uncleared_receipts_new = query_res[0].get('amount',0)
                print"uncleared_receipts_new: ",uncleared_receipts_new
                if uncleared_receipts_new is None:
                    uncleared_receipts_new = 0.0
                uncleared_receipts += uncleared_receipts_new
                
                
                refund_amount = 0.0
                inv_amount = 0.0
                if self.draft_invoices_refunds:
                    if self.based_on_date == 'due_date':
                        args_query = ('p.id=%s AND i.date_due<=%s')
                    else:
                        args_query = ('p.id=%s AND i.date_invoice<=%s')
                    args_value = (partner.id,as_on_date)

#                        period_dict[period].get('start')
                    inv_amount = self._get_invoice_totals(args_query,args_value,'invoice')
#                    print"inv_amount1: ",inv_amount
                    
                    refund_amount = self._get_invoice_totals(args_query,args_value,'refund')
#                    print"refund_amount1: ",refund_amount
#                    uncleared_receipts += refund_amount
                
                uncleared_receipts = float(round(uncleared_receipts, 3))
                print"uncleared_receipts22: ",uncleared_receipts
                partner_dict[partner.id].update({'uncleared_receipts': uncleared_receipts})
                
                
                # get Balance
#                SUM(l.debit) - sum(l.credit) AS uncleared_receipts
                if self.based_on_date == 'due_date':
                    sql = """
                        SELECT
                                sum(l.balance) AS balance,
                                sum(COALESCE((SELECT SUM(amount)FROM account_partial_reconcile
                                    WHERE credit_move_id = l.id), 0)) AS sum_debit,
                                sum(COALESCE((SELECT SUM(amount) FROM account_partial_reconcile
                                    WHERE debit_move_id = l.id), 0)) AS sum_credit
                        FROM
                            account_move_line AS l
                        LEFT JOIN
                            account_move AS m ON m.id = l.move_id
                        LEFT JOIN
                            account_account AS a ON a.id = l.account_id
                        LEFT JOIN
                            account_account_type AS ty ON a.user_type_id = ty.id
                        WHERE
                            l.reconciled!=True
                            AND m.state = 'posted'
                            AND ty.type IN %s
                            AND l.partner_id = %s
                            AND l.date <= '%s'
                            AND l.company_id = %s
                    """%(type, partner.id, as_on_date, company_id.id)
                else:
                    sql = """
                        SELECT
                                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance
                        FROM
                            account_move_line AS l
                        LEFT JOIN
                            account_move AS m ON m.id = l.move_id
                        LEFT JOIN
                            account_account AS a ON a.id = l.account_id
                        LEFT JOIN
                            account_account_type AS ty ON a.user_type_id = ty.id
                        WHERE
                            m.state = 'posted'
                            AND ty.type IN %s
                            AND l.partner_id = %s
                            AND (COALESCE(l.date,l.date_maturity) <= '%s')
                            AND l.company_id = %s
                    """%(type, partner.id, as_on_date, company_id.id)
                self.env.cr.execute(sql)
                query_res = self.env.cr.dictfetchall() or 0.0
                balance =query_res[0].get('balance',0)
                if balance is None:
                    balance=0.0
                print"balance: ",balance
#                sum_credit =query_res[0].get('sum_credit',0)
#                if sum_credit is None:
#                    sum_credit=0.0
#                print"sum_credit: ",sum_credit
#                sum_debit =query_res[0].get('sum_debit',0)
#                if sum_debit is None:
#                    sum_debit=0.0
#                print"sum_debit: ",sum_debit
                
#                balance += (sum_debit - sum_credit)
                print"balance after debit credit: ",balance
                
                balance += inv_amount
                balance -= refund_amount
                partner_dict[partner.id].update({'balance': float(round(balance,3))})
#                partner_dict[partner.id].update({'balance': float(balance)})
                #TODO uncommment this before updating
                if float(balance)==0.0:
                    if not self.show_zero_balance:
                        partner_dict.pop(partner.id)
                        sorted_partner_ids.remove(partner.id)
                        print"Zero balance skipped" #removing zero balance partner
                        continue
                
#                print"period_dict: ",period_dict
                account_id = partner.property_account_receivable_id.id
                for period in period_dict:
                    print"period_dict[period]: ",period_dict[period]
                    print"period_dict[period]['name']: ",period_dict[period]['name']
                    if self.based_on_date == 'due_date':
                        where = " AND l.date <= '%s' AND l.partner_id = %s AND COALESCE(l.date_maturity,l.date) "%(as_on_date, partner.id)
                    else:
                        where = " AND l.date <= '%s' AND l.partner_id = %s AND l.date "%(as_on_date, partner.id)
                    if period_dict[period].get('start') and period_dict[period].get('stop'):
                        where += " BETWEEN '%s' AND '%s'" % (period_dict[period].get('stop'), period_dict[period].get('start'))
                    elif not period_dict[period].get('start'): # ie just
                        where += " >= '%s'" % (period_dict[period].get('stop'))
                    else:
                        where += " <= '%s'" % (period_dict[period].get('start'))
                    print"where: ",where

                    if self.based_on_date == 'due_date':
                        sql = """
                            SELECT
                                sum(l.balance) AS balance,
                                sum(COALESCE((SELECT SUM(amount)FROM account_partial_reconcile
                                    WHERE credit_move_id = l.id AND create_date <= '%s'), 0)) AS sum_debit,
                                sum(COALESCE((SELECT SUM(amount) FROM account_partial_reconcile 
                                    WHERE debit_move_id = l.id AND create_date <= '%s'), 0)) AS sum_credit
                            FROM
                                account_move_line AS l
                            LEFT JOIN
                                account_move AS m ON m.id = l.move_id
                            LEFT JOIN
                                account_account AS a ON a.id = l.account_id
                            LEFT JOIN
                                account_account_type AS ty ON a.user_type_id = ty.id
                            WHERE
                                l.balance <> 0
                                AND l.debit > 0
                                AND m.state = 'posted'
                                AND ty.type IN %s
                                AND l.company_id = %s
                                AND l.reconciled!=True
                        """%(as_on_date, as_on_date, type, company_id.id)
                    else:
                        sql = """
                            SELECT
                                sum(l.balance) AS balance
                            FROM
                                account_move_line AS l
                            LEFT JOIN
                                account_move AS m ON m.id = l.move_id
                            LEFT JOIN
                                account_account AS a ON a.id = l.account_id
                            LEFT JOIN
                                account_account_type AS ty ON a.user_type_id = ty.id
                            WHERE
                                l.balance <> 0
                                AND l.debit > 0
                                AND m.state = 'posted'
                                AND ty.type IN %s
                                AND l.company_id = %s
                                AND (COALESCE(l.date,l.date_maturity) <= '%s')
                        """%(type, company_id.id, as_on_date)
                    amount = 0.0
                    self.env.cr.execute(sql + where)
                    fetch_dict = self.env.cr.dictfetchall() or 0.0
#                    print"fetch_dict: ",fetch_dict

                    if not fetch_dict[0].get('balance'):
                        amount = 0.0
                    else:
#                        amount = fetch_dict[0]['balance'] + fetch_dict[0]['sum_debit'] - fetch_dict[0]['sum_credit']
                        amount = fetch_dict[0]['balance']
                        total_balance += amount
                        
                    print"amount: ",amount
                    print"account_id: ",account_id
                    if period_dict[period].get('start') and period_dict[period].get('stop'):
                        where = account_id, as_on_date, account_id,period_dict[period].get('stop'), period_dict[period].get('start')
                        print"Where both: ",where
                        sql = """
                            select sum(amount) from account_partial_reconcile 
                            where credit_move_id in 
                                (select id from account_move_line where 
                                account_id=%s and date<='%s' and credit>0) and debit_move_id in 
                            (select id from account_move_line where 
                                account_id=%s and date>='%s' and 
                            date<='%s' and debit>0)"""%(where)
#                        print"sql: ",sql
                    elif not period_dict[period].get('start'): # ie just
                        where = account_id, as_on_date, account_id,period_dict[period].get('stop')
                        print"Where:start ",where
                        sql = """
                            select sum(amount) from account_partial_reconcile 
                            where credit_move_id in 
                                (select id from account_move_line where 
                                account_id=%s and date<='%s' and credit>0) and debit_move_id in 
                            (select id from account_move_line where 
                                account_id=%s and date>='%s' and debit>0)"""%(where)
                    else:
#                        print"period_dict[period]: ",period_dict[period]
                        where = account_id, as_on_date, account_id,period_dict[period].get('start')
                        print"Where: else",where
                        sql = """
                            select sum(amount) from account_partial_reconcile 
                            where credit_move_id in 
                                (select id from account_move_line where 
                                account_id=%s and date<='%s' and credit>0) and debit_move_id in 
                            (select id from account_move_line where 
                                account_id=%s and date<='%s' and debit>0)"""%(where)
                    self.env.cr.execute(sql)
                    query_res = self.env.cr.dictfetchall()
#                    print"amount Before: ",amount
                    print"query res982: ",query_res
                    new_reconciled_amount = 0.0
                    if not query_res[0].get('sum'):
                        new_reconciled_amount = 0.0
                    else:
                        new_reconciled_amount = query_res[0]['sum']
                    amount -= new_reconciled_amount
#                    if amount<0: amount = 0.0
                    print"amount after subs: ",amount
                    
                    #Get draft invoices and refunds based on checkbox
                    if self.draft_invoices_refunds:
                        if self.based_on_date == 'due_date':
                            args_query = ('p.id=%s AND COALESCE(i.date_due,i.date_invoice)<=%s')
                            args_value = (partner.id,as_on_date)

    #                        period_dict[period].get('start')
                            if period_dict[period].get('start') and period_dict[period].get('stop'):
                                args_query = ('p.id=%s AND COALESCE(i.date_due,i.date_invoice)>=%s AND COALESCE(i.date_due,i.date_invoice)<=%s')
#                                args_value = (partner.id, period_dict[period].get('start'), period_dict[period].get('stop'))
                                args_value = (partner.id, period_dict[period].get('stop'), period_dict[period].get('start'))
                            elif period_dict[period].get('start'):
                                args_query = ('p.id=%s AND COALESCE(i.date_due,i.date_invoice)>=%s')
                                args_value = (partner.id, period_dict[period].get('start'))
                            else:
                                args_query = ('p.id=%s AND COALESCE(i.date_due,i.date_invoice)<=%s')
                                args_value = (partner.id,period_dict[period].get('stop'))
                        else:
                            args_query = ('p.id=%s AND i.date_invoice<=%s')
                            args_value = (partner.id,as_on_date)

                            if period_dict[period].get('start') and period_dict[period].get('stop'):
                                args_query = ('p.id=%s AND i.date_invoice>=%s AND i.date_invoice<=%s')
#                                args_value = (partner.id, period_dict[period].get('start'), period_dict[period].get('stop'))
                                args_value = (partner.id, period_dict[period].get('stop'), period_dict[period].get('start'))
                            elif not period_dict[period].get('start'):
#                                args_query = ('p.id=%s AND i.date_invoice>=%s')
                                args_query = ('p.id=%s AND i.date_invoice<=%s')
#                                args_value = (partner.id, period_dict[period].get('start'))
                                args_value = (partner.id, period_dict[period].get('stop'))
                            else:
                                args_query = ('p.id=%s AND i.date_invoice<=%s')
#                                args_value = (partner.id,period_dict[period].get('stop'))
                                args_value = (partner.id,period_dict[period].get('start'))
                                
                            if period_dict[period]['name']== 'Not Due':
                                args_query = ('p.id=%s AND i.date_invoice>=%s AND i.date_invoice<=%s')
                                args_value = (partner.id,as_on_date,as_on_date)
                        
                        print"args_query: ",args_query
                        print"args_value: ",args_value
                        inv_amount = self._get_invoice_totals(args_query,args_value,'invoice')
                        print"inv amount: ",inv_amount

                        refund_amount = self._get_invoice_totals(args_query,args_value,'refund')
                        print"refund_amount: ",refund_amount

                        amount += (inv_amount-refund_amount)
                        print"amount after drafts: ",amount

                    
#                    print"period_dict[period]['name']11: ",period_dict[period]['name']
                    ## new change
                    if period_dict[period]['name']== 'Not Due':
                        if self.based_on_date=='invoice_date':
                            amount = 0

                    if period_dict[period]['name']!= 'Not Due':
                        partner_dict['Total']['amount_due'] += amount
                        partner_dict[partner.id]['amount_due'] += amount
                    partner_dict[partner.id].update({period_dict[period]['name']:amount})
                    partner_dict['Total'][period_dict[period]['name']] += amount
                
                this_amount_due = float(round((partner_dict[partner.id]['amount_due'] - uncleared_receipts), 3))
#                partner_dict[partner.id]['amount_due'] -= uncleared_receipts
                partner_dict[partner.id]['amount_due'] = this_amount_due
                partner_dict['Total']['amount_due'] -= uncleared_receipts
                
                partner_dict[partner.id].update({'count': count})
                partner_dict[partner.id].update({'pages': self.get_page_list(count)})
                partner_dict[partner.id].update({'single_page': True if count <= FETCH_RANGE else False})
                partner_dict[partner.id].update({'total': total_balance})
                partner_dict['Total']['total'] += total_balance
                
                partner_dict['Total']['balance'] += balance
                partner_dict['Total']['uncleared_receipts'] += uncleared_receipts
#                partner_dict['Total']['amount_due'] = 0
                
                partner_dict[partner.id].update({'company_currency_id': company_currency_id})
                partner_dict['Total'].update({'company_currency_id': company_currency_id})
            else:
                partner_dict.pop(partner.id, None)
                sorted_partner_ids.remove(partner.id)
                
#        print"period_dict: ",period_dict
        t_dict = partner_dict.pop('Total')
        t_dict['balance'] = '%.3f' % t_dict.get('balance')
        t_dict['uncleared_receipts'] = '%.3f' % t_dict.get('uncleared_receipts')
        t_dict['amount_due'] = '%.3f' % t_dict.get('amount_due')
#        print"partner_dict: ",partner_dict
        partner_dict['Total'] = t_dict
#        print"partner_dict after 888: ",partner_dict

#        final_partner_dict = {}
#        final_partner_dict = OrderedDict()
#        for partner_id in partner_ids:
#            print"partner_id: ",partner_id
#            print"partner_id name: ",partner_id.name
#            final_partner_dict[partner_id.id] = {}
#            final_partner_dict[partner_id.id] = partner_dict.get(partner_id.id)
#        final_partner_dict['Total'] = t_dict
#        print"before adding total"
#        
#        print"partner_dict: ",partner_dict

#        return period_dict, final_partner_dict
        return period_dict, partner_dict, sorted_partner_ids

    def get_page_list(self, total_count):
        '''
        Helper function to get list of pages from total_count
        :param total_count: integer
        :return: list(pages) eg. [1,2,3,4,5,6,7 ....]
        '''
        page_count = int(total_count / FETCH_RANGE)
        if total_count % FETCH_RANGE:
            page_count += 1
        return [i+1 for i in range(0, int(page_count))] or []

    def get_report_datas(self, default_filters={}):
        '''
        Main method for pdf, xlsx and js calls
        :param default_filters: Use this while calling from other methods. Just a dict
        :return: All the datas for GL
        '''
        if self.validate_data():
            filters = self.process_filters()
#            print"filters: ",filters
            period_dict, ageing_lines, sorted_partner = self.process_data()
            period_list = [period_dict[a]['name'] for a in period_dict]
            return filters, ageing_lines, period_dict, period_list, sorted_partner

    def action_pdf(self):
        filters, ageing_lines, period_dict, period_list, sorted_partner = self.get_report_datas()

        return self.env['report'].with_context({'landscape': 1}).get_action(
            self, 'account_dynamic_reports.partner_ageing', data={'Ageing_data': ageing_lines,
                        'Filters': filters,
                        'Period_Dict': period_dict,
                        'Period_List': period_list,
                        'sorted_partner': sorted_partner
                        })

    def action_xlsx(self):
        raise UserError(_('Please install a free module "dynamic_xlsx".'
                          'You can get it by contacting "pycustech@gmail.com". It is free'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'Ageing View',
            'tag': 'dynamic.pa',
            'context': {'wizard_id': self.id}
        }
        return res