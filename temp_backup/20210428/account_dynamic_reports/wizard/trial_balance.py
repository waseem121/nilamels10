from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from operator import itemgetter


class InsTrialBalance(models.TransientModel):
    _name = "ins.trial.balance"

    def _get_journals(self):
        return self.env['account.journal'].search([])

    @api.onchange('date_range', 'financial_year')
    def onchange_date_range(self):
        if self.date_range:
            date = datetime.today()
            if self.date_range == 'today':
                self.date_from = date.strftime("%Y-%m-%d")
                self.date_to = date.strftime("%Y-%m-%d")
            if self.date_range == 'this_week':
                day_today = date - timedelta(days=date.weekday())
                self.date_from = (day_today - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
                self.date_to = (day_today + timedelta(days=6)).strftime("%Y-%m-%d")
            if self.date_range == 'this_month':
                self.date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
                self.date_to = datetime(date.year, date.month, calendar.mdays[date.month]).strftime("%Y-%m-%d")
            if self.date_range == 'this_quarter':
                if int((date.month - 1) / 3) == 0:  # First quarter
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 3, calendar.mdays[3]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 1:  # Second quarter
                    self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 6, calendar.mdays[6]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 2:  # Third quarter
                    self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 9, calendar.mdays[9]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 3:  # Fourth quarter
                    self.date_from = datetime(date.year, 10, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, calendar.mdays[12]).strftime("%Y-%m-%d")
            if self.date_range == 'this_financial_year':
                if self.financial_year == 'january_december':
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'april_march':
                    if date.month < 4:
                        self.date_from = datetime(date.year - 1, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year, 3, 31).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 3, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'july_june':
                    if date.month < 7:
                        self.date_from = datetime(date.year - 1, 7, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year, 6, 30).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 6, 30).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(days=1))
            if self.date_range == 'yesterday':
                self.date_from = date.strftime("%Y-%m-%d")
                self.date_to = date.strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(days=7))
            if self.date_range == 'last_week':
                day_today = date - timedelta(days=date.weekday())
                self.date_from = (day_today - timedelta(days=date.weekday())).strftime("%Y-%m-%d")
                self.date_to = (day_today + timedelta(days=6)).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(months=1))
            if self.date_range == 'last_month':
                self.date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
                self.date_to = datetime(date.year, date.month, calendar.mdays[date.month]).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(months=3))
            if self.date_range == 'last_quarter':
                if int((date.month - 1) / 3) == 0:  # First quarter
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 3, calendar.mdays[3]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 1:  # Second quarter
                    self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 6, calendar.mdays[6]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 2:  # Third quarter
                    self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 9, calendar.mdays[9]).strftime("%Y-%m-%d")
                if int((date.month - 1) / 3) == 3:  # Fourth quarter
                    self.date_from = datetime(date.year, 10, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, calendar.mdays[12]).strftime("%Y-%m-%d")
            date = (datetime.now() - relativedelta(years=1))
            if self.date_range == 'last_financial_year':
                if self.financial_year == 'january_december':
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'april_march':
                    if date.month < 4:
                        self.date_from = datetime(date.year - 1, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year, 3, 31).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 3, 31).strftime("%Y-%m-%d")
                if self.financial_year == 'july_june':
                    if date.month < 7:
                        self.date_from = datetime(date.year - 1, 7, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year, 6, 30).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 6, 30).strftime("%Y-%m-%d")

    @api.model
    def _get_default_date_range(self):
        return self.env.user.company_id.date_range

    @api.model
    def _get_default_financial_year(self):
        return self.env.user.company_id.financial_year

    @api.model
    def _get_default_strict_range(self):
        return self.env.user.company_id.strict_range

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, 'Trial Balance'))
        return res

    financial_year = fields.Selection(
        [('april_march', '1 April to 31 March'),
         ('july_june', '1 july to 30 June'),
         ('january_december', '1 Jan to 31 Dec')],
        string='Financial Year', default=_get_default_financial_year)

    date_range = fields.Selection(
        [('today', 'Today'),
         ('this_week', 'This Week'),
         ('this_month', 'This Month'),
         ('this_quarter', 'This Quarter'),
         ('this_financial_year', 'This financial Year'),
         ('yesterday', 'Yesterday'),
         ('last_week', 'Last Week'),
         ('last_month', 'Last Month'),
         ('last_quarter', 'Last Quarter'),
         ('last_financial_year', 'Last Financial Year')],
        string='Date Range', default=_get_default_date_range
    )
    strict_range = fields.Boolean(
        string='Strict Range',
        default=_get_default_strict_range
    )
    show_hierarchy = fields.Boolean(
        string='Show hierarchy', default=True
    )
    target_moves = fields.Selection(
        [('all_entries', 'All entries'),
         ('posted_only', 'Posted Only')], string='Target Moves',
        default='all_entries', required=True
    )
    display_accounts = fields.Selection(
        [('all', 'All'),
         ('balance_not_zero', 'With balance not zero')], string='Display accounts',
        default='balance_not_zero', required=True
    )
    date_from = fields.Date(
        string='Start date',
    )
    date_to = fields.Date(
        string='End date',
    )
#    date_from1 = fields.Date(
#        string='Start date',default='2020-01-01',
#    )
#    date_to1 = fields.Date(
#        string='End date', default='2020-12-31'
#    )    
    account_ids = fields.Many2many(
        'account.account', string='Accounts'
    )
    analytic_ids = fields.Many2many(
        'account.analytic.account', string='Analytic Accounts'
    )
    journal_ids = fields.Many2many(
        'account.journal', string='Journals',
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=_get_default_company
    )
    
    show_debit_credit_balances = fields.Boolean(string='Show Debit Credit and Balances', default=True)
    show_total_debit_credit = fields.Boolean(string='Show Total Debit Credit')
    show_balances = fields.Boolean(string='Show Balances')
    group_account = fields.Boolean(string='Group Accounts')

    @api.multi
    def write(self, vals):

        if vals.get('date_range'):
            vals.update({'date_from':False,'date_to':False})
        if vals.get('date_from') and vals.get('date_to'):
            vals.update({'date_range':False})

        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(4, j) for j in vals.get('journal_ids')]})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})

        if vals.get('analytic_ids'):
            vals.update({'analytic_ids': [(4, j) for j in vals.get('analytic_ids')]})
        if vals.get('analytic_ids') == []:
            vals.update({'analytic_ids': [(5,)]})

        ret = super(InsTrialBalance, self).write(vals)
        return ret

    def validate_data(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('"Date from" must be less than or equal to "Date to"'))
        if self.show_debit_credit_balances and self.show_total_debit_credit and self.show_balances:
            raise ValidationError(_('"Please choose any one from \n1.Show Debit Credit and Balances \n 2.Show Total Debit Credit\n 3.Show Balances."'))
        return True

    def process_filters(self, data):
        ''' To show on report headers'''
        filters = {}

        if data.get('date_from') > data.get('date_to'):
            raise ValidationError(_('From date must not be less than to date'))

        if not data.get('date_from') or not data.get('date_to'):
            raise ValidationError(_('From date and To dates are mandatory for this report'))

        if data.get('journal_ids',[]):
            filters['journals'] = self.env['account.journal'].browse(data.get('journal_ids',[])).mapped('code')
        else:
            filters['journals'] = ''

        if data.get('analytic_ids', []):
            filters['analytics'] = self.env['account.analytic.account'].browse(data.get('analytic_ids', [])).mapped(
                'name')
        else:
            filters['analytics'] = ['All']

        if data.get('display_accounts') == 'all':
            filters['display_accounts'] = 'All'
        else:
            filters['display_accounts'] = 'With balance not zero'

        if data.get('date_from',False):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to', False):
            filters['date_to'] = data.get('date_to')

        if data.get('show_hierarchy', False):
            filters['show_hierarchy'] = True
        else:
            filters['show_hierarchy'] = False

        if data.get('strict_range', False):
            filters['strict_range'] = True
        else:
            filters['strict_range'] = False
            
        filters['show_debit_credit_balances'] =False
        if data.get('show_debit_credit_balances', False):
            filters['show_debit_credit_balances'] =True
            
        filters['show_total_debit_credit'] =False
        if data.get('show_total_debit_credit', False):
            filters['show_total_debit_credit'] =True
            
        filters['show_balances'] =False
        if data.get('show_balances', False):
            filters['show_balances'] =True
            

        # For Js framework
        filters['journals_list'] = data.get('journals_list')
        filters['analytics_list'] = data.get('analytics_list')
        filters['company_name'] = data.get('company_name')

        return filters

    def prepare_hierarchy_old(self, move_lines):
        '''
        It will process the move lines as per the hierarchy.
        :param move_lines: list of dict
        :return: list of dict with hierarchy levels
        '''

        def prepare_tmp(id=False, code=False, indent_list=[], parent=[]):
            return {
                'id': id,
                'code': code,
                'initial_debit': 0,
                'initial_credit': 0,
                'initial_balance': 0,
                'debit': 0,
                'credit': 0,
                'balance': 0,
                'ending_debit': 0,
                'ending_credit': 0,
                'ending_balance': 0,
                'dummy': True,
                'indent_list': indent_list,
                'len': len(indent_list) or 1,
                'parent': ' a'.join(['0'] + parent)
            }

        if move_lines:
            hirarchy_list = []
            parent_1 = []
            parent_2 = []
            parent_3 = []
            for line in move_lines:

                q = move_lines[line]
                tmp = q.copy()
#                print"tmp: ",str(tmp['id'])
#                if str(tmp['id']) == '5670':
#                    print"tmp00: ",tmp
#                    abc
#                if str(tmp['code']) == '1':
#                    print"tmp: ",tmp
#                    ee
                tmp.update(prepare_tmp(id=str(tmp['id']) + 'z1',
                                  code=str(tmp['code'])[0],
                                  indent_list=[1],
                                  parent=[]))
                if tmp['code'] not in [k['code'] for k in hirarchy_list]:
                    hirarchy_list.append(tmp)
                    parent_1 = [tmp['id']]

                tmp = q.copy()
                tmp.update(prepare_tmp(id=str(tmp['id']) + 'z2',
                                  code=str(tmp['code'])[:2],
                                  indent_list=[1,2],
                                  parent=parent_1))
                if tmp['code'] not in [k['code'] for k in hirarchy_list]:
                    hirarchy_list.append(tmp)
                    parent_2 = [tmp['id']]

                tmp = q.copy()
                tmp.update(prepare_tmp(id=str(tmp['id']) + 'z3',
                                  code=str(tmp['code'])[:3],
                                  indent_list=[1, 2, 3],
                                  parent=parent_1 + parent_2))

                if tmp['code'] not in [k['code'] for k in hirarchy_list]:
                    hirarchy_list.append(tmp)
                    parent_3 = [tmp['id']]
                final_parent = ['0'] + parent_1 + parent_2 + parent_3
                tmp = q.copy()
                tmp.update({'code': str(tmp['code']), 'parent': ' a'.join(final_parent), 'dummy': False, 'indent_list': [1, 2, 3, 4],})
                hirarchy_list.append(tmp)

            for line in move_lines:
                q = move_lines[line]
                for l in hirarchy_list:
                    if str(q['code'])[0] == l['code'] or \
                            str(q['code'])[:2] == l['code'] or \
                            str(q['code'])[:3] == l['code']:
#                    if str(q['code'])[0] == l['code'] or \
#                            str(q['code'])[:3] == l['code']:
                        l['initial_debit'] += q['initial_debit']
                        l['initial_credit'] += q['initial_credit']
                        l['initial_balance'] += q['initial_balance']
                        l['debit'] += q['debit']
                        l['credit'] += q['credit']
                        l['balance'] += q['balance']
                        l['ending_debit'] += q['ending_debit']
                        l['ending_credit'] += q['ending_credit']
                        l['ending_balance'] += q['ending_balance']

            return sorted(hirarchy_list, key=itemgetter('code'))
        return []
    
    
    def prepare_hierarchy(self, move_lines):
        '''
        It will process the move lines as per the hierarchy.
        :param move_lines: list of dict
        :return: list of dict with hierarchy levels
        '''

        def prepare_tmp(id=False, code=False, indent_list=[], parent=[]):
            return {
                'id': id,
                'code': code,
                'initial_debit': 0,
                'initial_credit': 0,
                'initial_balance': 0,
                'debit': 0,
                'credit': 0,
                'balance': 0,
                'ending_debit': 0,
                'ending_credit': 0,
                'ending_balance': 0,
                'dummy': True,
                'indent_list': indent_list,
                'len': len(indent_list) or 1,
                'parent': ' a'.join(['0'] + parent)
            }

        if move_lines:
            hirarchy_list = []
            parent_1 = []
            parent_2 = []
            parent_3 = []
            for line in move_lines:

                q = move_lines[line]
                tmp = q.copy()
#                print"tmp: ",str(tmp['id'])
#                if str(tmp['id']) == '5670':
#                    print"tmp00: ",tmp
#                    abc
#                if str(tmp['code']) == '1':
#                    print"tmp: ",tmp
#                    ee
                tmp.update(prepare_tmp(id=str(tmp['id']) + 'z1',
                                  code=str(tmp['code'])[0],
                                  indent_list=[1],
                                  parent=[]))
                if tmp['code'] not in [k['code'] for k in hirarchy_list]:
                    hirarchy_list.append(tmp)
                    parent_1 = [tmp['id']]

                tmp = q.copy()
                tmp.update(prepare_tmp(id=str(tmp['id']) + 'z2',
                                  code=str(tmp['code'])[:2],
                                  indent_list=[1,2],
                                  parent=parent_1))
                if tmp['code'] not in [k['code'] for k in hirarchy_list]:
                    hirarchy_list.append(tmp)
                    parent_2 = [tmp['id']]

                tmp = q.copy()
                tmp.update(prepare_tmp(id=str(tmp['id']) + 'z3',
                                  code=str(tmp['code'])[:3],
                                  indent_list=[1, 2, 3],
                                  parent=parent_1 + parent_2))

                if tmp['code'] not in [k['code'] for k in hirarchy_list]:
                    hirarchy_list.append(tmp)
                    parent_3 = [tmp['id']]
                final_parent = ['0'] + parent_1 + parent_2 + parent_3
                tmp = q.copy()
                tmp.update({'code': str(tmp['code']), 'parent': ' a'.join(final_parent), 'dummy': False, 'indent_list': [1, 2, 3, 4],})
                hirarchy_list.append(tmp)

            for line in move_lines:
                q = move_lines[line]
                for l in hirarchy_list:
                    if str(q['code'])[0] == l['code'] or \
                            str(q['code'])[:3] == l['code'] and \
                            l['debit']==0.0 and l['dummy']:
                        l['initial_debit'] = q['initial_debit']
                        l['initial_credit'] = q['initial_credit']
                        l['initial_balance'] = q['initial_balance']
                        l['debit'] = q['debit']
                        l['credit'] = q['credit']
                        l['balance'] = q['balance']
                        l['ending_debit'] = q['ending_debit']
                        l['ending_credit'] = q['ending_credit']
                        l['ending_balance'] = q['ending_balance']
            result = sorted(hirarchy_list, key=itemgetter('code'))
            new_result = []
            for line in result:
#                if not line.get('balance') and len(line.get('code')) !=1:
#                    continue
                new_result.append(line)
                
#            for line in new_result:
#                print"line: ",line
                
            return new_result
        return []    

    def process_data(self, data):
        if data:
            cr = self.env.cr
            WHERE = '(1=1)'

            # Journals
            if data.get('journal_ids',[]):
                WHERE += ' AND j.id IN %s' % str(tuple(data.get('journal_ids'))+tuple([0]))

            # Analytic Accounts
            if data.get('analytic_ids', []):
                WHERE += ' AND anl.id IN %s' % str(tuple(data.get('analytic_ids')) + tuple([0]))

            # Operating Locations
            # if data.get('operating_location_ids', []):
            #     WHERE += ' AND l.operating_location_id IN %s' % str(
            #         tuple(data.get('operating_location_ids')) + tuple([0]))

            # Company
            if data.get('company_id', False):
                WHERE += ' AND l.company_id = %s' % data.get('company_id')

            if data.get('target_moves') == 'posted_only':
                WHERE += " AND m.state = 'posted'"

            account_ids = self.env['account.account'].search([])
            if self.account_ids:
                ids = [val.id for val in self.account_ids]
                account_ids = self.env['account.account'].search([('parent_id', 'child_of', ids)])
            
            company_id = self.env.user.company_id
            company_currency_id = company_id.currency_id

            move_lines = {x.code: {'name':x.name,'code':x.code,'id':x.id,
                                 'initial_debit':0.0, 'initial_credit':0.0,'initial_balance':0.0,
                                 'debit':0.0, 'credit':0.0, 'balance':0.0,
                                 'ending_credit':0.0, 'ending_debit':0.0, 'ending_balance':0.0,
                                 'company_currency_id': company_currency_id.id} for x in account_ids} # base for accounts to display
                
            retained = {}
            retained_earnings = 0.0
            retained_credit = 0.0
            retained_debit = 0.0
            total_deb = 0.0
            total_cre = 0.0
            total_bln = 0.0
            total_init_deb = 0.0
            total_init_cre = 0.0
            total_init_bal = 0.0
            total_end_deb = 0.0
            total_end_cre = 0.0
            total_end_bal = 0.0
            Account = self.env['account.account']
            group_accounts = Account.search([('group_account','=',True)])
            remove_lines = []
            added_codes = []
            for account in account_ids:
                company_id = self.env.user.company_id
                currency = account.company_id.currency_id or company_id.currency_id
                WHERE_INIT = WHERE + " AND l.date < '%s'" % data.get('date_from')
                WHERE_INIT += " AND l.account_id = %s" % account.id
                init_blns = 0.0
                deb = 0.0
                cre = 0.0
                end_blns = 0.0
                end_cr = 0.0
                end_dr = 0.0
                # Initial Balance
                sql = ('''
                    SELECT 
                        COALESCE(SUM(l.debit),0) AS initial_debit,
                        COALESCE(SUM(l.credit),0) AS initial_credit,
                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS initial_balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    WHERE %s
                ''')%WHERE_INIT
                cr.execute(sql)
                init_blns = cr.dictfetchone()

                move_lines[account.code]['initial_balance'] = init_blns['initial_balance']
                move_lines[account.code]['initial_debit'] = init_blns['initial_debit']
                move_lines[account.code]['initial_credit'] = init_blns['initial_credit']

                if account.user_type_id.include_initial_balance and self.strict_range:
                    # Initial balance must be zero in case of income and expense accounts, It is on account type menu
                    move_lines[account.code]['initial_balance'] = 0.0
                    move_lines[account.code]['initial_debit'] = 0.0
                    move_lines[account.code]['initial_credit'] = 0.0
                    if self.strict_range:
                        retained_earnings += init_blns['initial_balance']
                        retained_credit += init_blns['initial_credit']
                        retained_debit += init_blns['initial_debit']
                    #init_blns = 0.0
                total_init_deb += init_blns['initial_debit']
                total_init_cre += init_blns['initial_credit']
                total_init_bal += init_blns['initial_balance']
                # Current Balance
                WHERE_CURRENT = WHERE + " AND l.date >= '%s'" % data.get('date_from') + " AND l.date <= '%s'" % data.get('date_to')
                WHERE_CURRENT += " AND a.id = %s" % account.id
#                print"WHERE_CURRENT: ",WHERE_CURRENT
                sql = ('''
                    SELECT
                        COALESCE(SUM(l.debit),0) AS debit,
                        COALESCE(SUM(l.credit),0) AS credit,
                        COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) AS balance
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    JOIN account_account a ON (l.account_id=a.id)
                    WHERE %s
                ''') % WHERE_CURRENT
                cr.execute(sql)
                op = cr.dictfetchone()
                deb = op['debit']
                cre = op['credit']
                bln = op['balance']
                move_lines[account.code]['debit'] = deb
                move_lines[account.code]['credit'] = cre
                move_lines[account.code]['balance'] = bln

                end_blns = init_blns['initial_balance'] + bln
                end_cr = init_blns['initial_credit'] + cre
                end_dr = init_blns['initial_debit'] + deb

                #if account.user_type_id.include_initial_balance and self.strict_range:
                move_lines[account.code]['ending_balance'] = end_blns
                move_lines[account.code]['ending_credit'] = end_cr
                move_lines[account.code]['ending_debit'] = end_dr
                
                total_end_bal += end_blns
                total_end_cre += end_cr
                total_end_deb += end_dr
                
                if data.get('display_accounts') == 'balance_not_zero':
                    if end_blns: # debit or credit exist
                        total_deb += deb
                        total_cre += cre
                        total_bln += bln
                    elif bln:
                        continue
                    else:          
#                        move_lines.pop(account.code)
                        remove_lines.append(account.code)
                else:
                    total_deb += deb
                    total_cre += cre
                    total_bln += bln                        
                    
            ## show only group account
#            remove_lines = []
            for group_account in group_accounts:
                child_ids = Account.search([('parent_id','=',group_account.id)])
#                child_ids = group_account._get_children_and_consol()
#                child_ids = group_account._get_children_and_consol_only_leaf_account()
                child_ids = child_ids.ids

                gdebit = 0.0
                gcredit = 0.0
                gbalance = 0.0

                gtotal_init_bal = 0.0
                gtotal_init_cre = 0.0
                gtotal_init_deb = 0.0

                gtotal_end_bal = 0.0
                gtotal_end_cre = 0.0
                gtotal_end_deb = 0.0
                for line in move_lines:
                    account_id = move_lines[line].get('id')
                    if account_id in child_ids:
#                    account = Account.browse(account_id)
#                    if not account.parent_id:
#                        continue
#                    if account.parent_id.id == group_account.id:
                        
                        gdebit += move_lines[line].get('debit')
                        gcredit += move_lines[line].get('credit')
                        gbalance += move_lines[line].get('balance')
                        
                        gtotal_init_bal += move_lines[line].get('initial_balance')
                        gtotal_init_cre += move_lines[line].get('initial_credit')
                        gtotal_init_deb += move_lines[line].get('initial_debit')
                        
                        gtotal_end_bal += move_lines[line].get('ending_balance')
                        gtotal_end_cre += move_lines[line].get('ending_credit')
                        gtotal_end_deb += move_lines[line].get('ending_debit')
                        # remove the child accounts
#                        move_lines.pop(line)
                        remove_lines.append(line)
#                        print"remvoing: "
                        
                # append the group account
                code = group_account.code
                move_lines[code] = {}
                move_lines[code]['name'] = group_account.name
                move_lines[code]['code'] = code
                move_lines[code]['id'] = group_account.id
                move_lines[code]['company_currency_id'] = company_currency_id.id
                
                move_lines[code]['debit'] = gdebit
                move_lines[code]['credit'] = gcredit
                move_lines[code]['balance'] = gbalance

                move_lines[code]['initial_balance'] = gtotal_init_bal
                move_lines[code]['initial_credit'] = gtotal_init_cre
                move_lines[code]['initial_debit'] = gtotal_init_deb

                move_lines[code]['ending_balance'] = gtotal_end_bal
                move_lines[code]['ending_credit'] = gtotal_end_cre
                move_lines[code]['ending_debit'] = gtotal_end_deb
                added_codes.append(code)
                print"added group account"
                
            
            remove_lines = list(set(remove_lines))
            for line in remove_lines:
                if line in added_codes:
                    continue
                if move_lines.get(line,[]):
                    move_lines.pop(line)

#            if self.strict_range:
#                # Adding Retained earnings entry
#                retained = {'RETAINED': {'name':'Retained Earnings','code':'','id':'RET',
#                                        'initial_credit':company_currency_id.round(retained_credit),
#                                         'initial_debit':company_currency_id.round(retained_debit),
#                                         'initial_balance':company_currency_id.round(retained_earnings),
#                                         'credit':0.0, 'debit':0.0, 'balance': 0.0,
#                                         'ending_credit':company_currency_id.round(retained_credit),
#                                         'ending_debit':company_currency_id.round(retained_debit),
#                                         'ending_balance':company_currency_id.round(retained_earnings),
#                                         'company_currency_id': company_currency_id.id}}
#            print"total_init_bal: ",total_init_bal
#            print"total_bln: ",total_bln
            # Adding Sub Total
            subtotal = {'SUBTOTAL': {
                'name': 'Total',
                'code': '',
                'id': 'SUB',
                'initial_credit': company_currency_id.round(total_init_cre),
                'initial_debit':company_currency_id.round(total_init_deb),
                'initial_balance':company_currency_id.round(total_init_bal),
                'credit': company_currency_id.round(total_cre),
                'debit':company_currency_id.round(total_deb),
                'balance':company_currency_id.round(total_bln),
                'ending_credit': company_currency_id.round(total_init_cre + total_cre),
                'ending_debit': company_currency_id.round(total_init_deb + total_deb),
                'ending_balance': company_currency_id.round(total_init_bal + total_bln),
                'company_currency_id': company_currency_id.id}}
            
            sorted_accounts = []
#            account0 = Account.search([('code','=','0'),('type','=','view')])[0]
#            heads = Account.search([('parent_id','=',account0.id)],order='code')
#            print"heads: ",heads
            needed_codes = move_lines.keys()
            
            if self.show_hierarchy:
#                account0 = Account.search([('code','=','0'),('type','=','view')])[0]
                account0 = Account.search([('parent_id','=',False),('type','=','view')])[0]
                print"account0: ",account0
                heads = Account.search([('parent_id','=',account0.id)],order='code')
                print"heads: ",heads
                
                move_lines = self.prepare_hierarchy(move_lines)
                for line in move_lines:
                    if line.get('code',False):
                        account_ids = Account.search([('code','=',line.get('code'))])
                        if account_ids:
                            line['name'] = account_ids[0].name
                            
                sorted_accounts = []
                for head in heads:
    #                child_ids = head._get_children_and_consol_only_leaf_account()
                    child_ids = head._get_children_and_consol()
    #                child_ids = Account.search([('parent_id','=',head.id)])
                    for c in child_ids:
                        if c.type=='view':
                            child_ids1 = Account.search([('parent_id','=',c.id)])
                        else:
                            child_ids1 = c._get_children_and_consol()
                        for c1 in child_ids1:
                            if c1.code not in needed_codes:
                                continue
                            sorted_accounts.append(c1.code)                            
                            
                            
            else:
#                main_account_ids = self.env['account.account'].search([('type','=','view'),('parent_id','=',False)])
#                heir = {}
#                for a in main_account_ids:
#                    child_ids = self.env['account.account'].search([('parent_id','=',a.id)])
#                    heir[a.id] = {}
##                    heir[a.id]['child'] = child_ids.ids
#                    childs = []
#                    for c in child_ids:
#                        c_child_ids = self.env['account.account'].search([('parent_id','=',c.id)])
#                        if len(c_child_ids):
#                            childs.append(c_child_ids.ids)
#                    heir[a.id]['childs'] = childs
#                print"heirrrr: ",heir
                    
                
#                needed_codes = move_lines.keys()
                sorted_names = ['Asset','Asset View','Current Assets','Non-current Assets','Fixed Assets',
                    'Liability View',
                    'Current Liabilities',                
                    'Non-current Liabilities',                
                    'Equity',
                    'Income','Other Income','Income View',
                    'Expenses View','Expenses',
                    'Receivable',
                    'Payable',
                    'Bank and Cash',
                    'Credit Card',
                    'Prepayments',
                    'Current Year Earnings',
                    'Depreciation',
                    'Cost of Revenue',
                    'View']
                account_type_ids = []

                account_ids = []
                sorted_accounts = []            
                for name in sorted_names:
                    account_types = self.env['account.account.type'].search([('name','=',name)])
                    for type in account_types:
                        account_type_ids.append(type.id)

                        type_account_ids = self.env['account.account'].search([('user_type_id','=',type.id)])
                        if not type_account_ids:
                            continue
                        for a in type_account_ids:
                            if a.code not in needed_codes:
                                continue
                            sorted_accounts.append(a.code)
                        account_ids.extend(type_account_ids.ids)
    #                print"len account_ids: ",len(account_ids)

#            print"move_lines: ",move_lines
            return [move_lines, retained, subtotal, sorted_accounts]

    def get_filters(self, default_filters={}):
        # TODO
#        self.onchange_date_range()
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]

        journals = self.journal_ids if self.journal_ids else self.env['account.journal'].search(company_domain)
        analytics = self.analytic_ids if self.analytic_ids else self.env['account.analytic.account'].search(company_domain)

        filter_dict = {
            'journal_ids': self.journal_ids.ids,
            'analytic_ids': self.analytic_ids.ids,
            'company_id': self.company_id and self.company_id.id or False,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'display_accounts': self.display_accounts,
            'show_hierarchy': self.show_hierarchy,
            'strict_range': self.strict_range,
            'target_moves': self.target_moves,
            'show_debit_credit_balances': self.show_debit_credit_balances,
            'show_total_debit_credit': self.show_total_debit_credit,
            'show_balances': self.show_balances,

            # For Js widget only
            'journals_list': [(j.id, j.name) for j in journals],
            'analytics_list': [(anl.id, anl.name) for anl in analytics],
            'company_name': self.company_id and self.company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def get_report_datas(self, default_filters={}):
        '''
        Main method for pdf, xlsx and js calls
        :param default_filters: Use this while calling from other methods. Just a dict
        :return: All the datas for GL
        '''
        if self.validate_data():
            data = self.get_filters(default_filters)
            filters = self.process_filters(data)
            account_lines, retained, subtotal, sorted_accounts = self.process_data(data)
            return filters, account_lines, retained, subtotal, sorted_accounts

    def action_pdf(self):
        filters, account_lines, retained, subtotal, sorted_accounts = self.get_report_datas()

        return self.env['report'].with_context({'landscape': 1}).get_action(
            self, 'account_dynamic_reports.trial_balance', data={'Ledger_data':account_lines,
                        'Retained':retained,
                        'Subtotal':subtotal,
                        'Filters':filters,
                        'sorted_accounts':sorted_accounts
                        })

    def action_xlsx(self):
        raise UserError(_('Please install a free module "dynamic_xlsx".'
                          'You can get it by contacting "pycustech@gmail.com". It is free'))

    def action_view(self):
        true_count = 0
        if self.show_debit_credit_balances:
            true_count+=1
        if self.show_total_debit_credit:
            true_count+=1
        if self.show_balances:
            true_count+=1
        if true_count>1:
            raise ValidationError(_('"Please choose any one from \n1.Show Debit Credit and Balances \n 2.Show Total Debit Credit\n 3.Show Balances."'))
        
        res = {
            'type': 'ir.actions.client',
            'name': 'TB View',
            'tag': 'dynamic.tb',
            'context': {'wizard_id': self.id}
        }
        return res
