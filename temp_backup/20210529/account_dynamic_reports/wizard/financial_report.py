# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import re

from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from operator import itemgetter


class InsFinancialReport(models.TransientModel):
    _name = "ins.financial.report"
    _description = "Financial Reports"

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.journal_ids = self.env['account.journal'].search(
                [('company_id', '=', self.company_id.id)])
        else:
            self.journal_ids = self.env['account.journal'].search([])

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


    def _compute_account_balance(self, accounts):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict.fromkeys(mapping, 0.0)
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                       " FROM " + tables + \
                       " WHERE account_id IN %s " \
                            + filters + \
                       " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                if self.account_report_id != \
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
                    res[report.id]['account'] = self._compute_account_balance(report.account_ids)
                    for value in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
                else:
                    res2 = self._compute_report_balance(report.parent_id)
                    for key, value in res2.items():
                        if report in [self.env.ref('account_dynamic_reports.ins_cash_in_operation_1'),
                                      self.env.ref('account_dynamic_reports.ins_cash_in_investing_1'),
                                      self.env.ref('account_dynamic_reports.ins_cash_in_financial_1')]:
                            res[report.id]['debit'] += value['debit']
                            res[report.id]['balance'] += value['debit']
                        else:
                            res[report.id]['credit'] += value['credit']
                            res[report.id]['balance'] += -(value['credit'])
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                if self.account_report_id != \
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
                    accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                    res[report.id]['account'] = self._compute_account_balance(accounts)
                    for value in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
                else:
                    accounts = self.env['account.account'].search(
                        [('user_type_id', 'in', report.account_type_ids.ids)])
                    res[report.id]['account'] = self._compute_account_balance(
                        accounts)
                    for value in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                if self.account_report_id != \
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
                    res2 = self._compute_report_balance(report.account_report_id)
                    for key, value in res2.items():
                        for field in fields:
                            res[report.id][field] += value[field]
                else:
                    res[report.id]['account'] = self._compute_account_balance(
                        report.account_ids)
                    for value in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                if self.account_report_id != \
                        self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
                    res2 = self._compute_report_balance(report.children_ids)
                    for key, value in res2.items():
                        for field in fields:
                            res[report.id][field] += value[field]
                else:
                    accounts = report.account_ids
                    if report == self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
                        accounts = self.env['account.account'].search([('company_id', '=', self.env.user.company_id.id),
                                                                       ('cash_flow_category', 'not in', [0])])
                    res[report.id]['account'] = self._compute_account_balance(accounts)
                    for values in res[report.id]['account'].values():
                        for field in fields:
                            res[report.id][field] += values.get(field)
        return res
    
    
    def prepare_hierarchy(self, move_lines):
        
        def prepare_tmp(id=False, code=False, indent_list=[], parent=[]):
            return {
                'id': id,
                'code': code,
                'debit': 0,
                'credit': 0,
                'balance': 0,
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
#                print"lineeeeeeeeeeee: ",line
                q = move_lines[line]
#                print"qqqqqqqqqqq: ",q
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
#                    if str(q['code'])[0] == l['code'] or \
#                            str(q['code'])[:3] == l['code'] and \
#                            l['debit']==0.0 and l['dummy']:
                    if str(q['code'])[0] == l['code'] or \
                            str(q['code'])[:3] == l['code'] and \
                            l['dummy']:
                        l['debit'] = q['debit']
                        l['credit'] = q['credit']
                        l['balance'] = q['balance']
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
    
#    def _get_indent_list(self, account):
#        indent_list = []
#        if not self.show_hierarchy:
#            return indent_list
#        if account.level:
#            for i in range(1,account.level):
#                indent_list.append(i)
#        else:
#            indent_list = [1]
#        return indent_list
    def _get_indent_list(self, account):
        indent_list = []
        if not self.show_hierarchy:
            return indent_list
        if account.level:
            for i in range(1,account.level+2):
                indent_list.append(i+1)
        else:
            indent_list = [0]
        return indent_list

    def get_account_lines(self, data):
        lines = []
        initial_balance = 0.0
        current_balance = 0.0
        ending_balance = 0.0
        show_hierarchy = data.get('show_hierarchy',False)
        Account = self.env['account.account']
        #account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        account_report = self.account_report_id
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        if self.account_report_id == \
                self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0'):
            cashflow_context = data.get('used_context')
            initial_to = fields.Date.from_string(data.get('used_context').get('date_from')) - timedelta(days=1)
            cashflow_context.update({'date_from': False, 'date_to': fields.Date.to_string(initial_to)})
            initial_balance = self.with_context(cashflow_context)._compute_report_balance(child_reports).\
                get(self.account_report_id.id)['balance']
            current_balance = res.get(self.account_report_id.id)['balance']
            ending_balance = initial_balance + current_balance
        if data['enable_filter']:
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        print"Self:account_report:Name:: ",account_report.name
        new_result_dict = {}
        last_debit, last_credit, last_balance = 0,0,0
        parent = False
        if account_report.name == 'Balance Sheet':
            for report in child_reports:
                print"report Name: ",report.name
                company_id = self.env.user.company_id
                currency_id = company_id.currency_id
                vals = {
                    'name': report.name,
                    'id': report.id,
                    'code':'01',
                    'balance': res[report.id]['balance'] * int(report.sign),
                    'parent': report.parent_id.id if report.parent_id.type in ['accounts','account_type'] else 0,
                    'self_id': report.id,
                    'type': 'report',
                    'style_type': 'main',
                    'precision': currency_id.decimal_places,
                    'symbol': currency_id.symbol,
                    'position': currency_id.position,
                    'list_len': [a for a in range(0,report.level)],
                    'level': report.level,
                    'indent_list':[1],
                    'company_currency_id': company_id.currency_id.id,
                    'account_type': report.type or False, #used to underline the financial report balances
                    'group_account': False,
                }
                if data['debit_credit']:
                    vals['debit'] = res[report.id]['debit']
                    vals['credit'] = res[report.id]['credit']

                if data['enable_filter']:
                    vals['balance_cmp'] = res[report.id]['comp_bal'] * int(report.sign)

                domain = [('group_account','=',True)]
                if report.name=='Assets':
                    user_type_ids = self.env['account.account.type'].search([('name','=','Asset View')])
                    if user_type_ids:
                        domain.append(('user_type_id','in',user_type_ids.ids))
                if report.name=='Liability':
                    user_type_ids = self.env['account.account.type'].search([('name','=','Liability View')])
                    if user_type_ids:
                        domain.append(('user_type_id','in',user_type_ids.ids))
                group_accounts = Account.search(domain)

    #            lines.append(vals) # TODO
                if report.name=='Balance Sheet':
                    vals['serial_no'] = 0
                    lines.append(vals)
                if report.name=='Profit (Loss) to report':
                    vals['serial_no'] = 5000000000000
                    lines.append(vals)
                    last_debit = vals.get('debit',0)
                    last_credit = vals.get('credit',0)
                    last_balance = vals.get('balance',0)

                if report.display_detail == 'no_detail':
                    #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                    continue

                if res[report.id].get('account'):
                    sub_lines = []
    #                all_account_ids = []
    #                for account_id, value in res[report.id]['account'].items():
    #                    all_account_ids.append(account_id)

                    for account_id, value in res[report.id]['account'].items():
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        flag = False
                        account = self.env['account.account'].browse(account_id)
    #                    print"user_type_id name: ",account.user_type_id.name
                        vals = {
                            'account': account.id,
                            'id': account.id,
    #                        'name': account.code + ' ' + account.name,
                            'name': account.name,
                            'code': account.code,
                            'serial_no': account.serial_no,
                            'balance': value['balance'] * int(report.sign) or 0.0,
                            'type': 'account',
                            'parent': report.id if report.type in ['accounts','account_type'] else 0,
                            'self_id': 50,
                            'style_type': 'sub',
                            'precision': currency_id.decimal_places,
                            'symbol': currency_id.symbol,
                            'position': currency_id.position,
                            'list_len':[a for a in range(0,report.display_detail == 'detail_with_hierarchy' and 4)],
                            'level': 4,
                            'indent_list':self._get_indent_list(account),
                            'company_currency_id': company_id.currency_id.id,
                            'account_type': account.internal_type,
                            'group_account': False,
                        }
                        new_result_dict[account.id] = vals
                        if data['debit_credit']:
                            vals['debit'] = value['debit']
                            vals['credit'] = value['credit']
                            if not currency_id.is_zero(vals['debit']) or not currency_id.is_zero(vals['credit']):
                                flag = True
                        if not currency_id.is_zero(vals['balance']):
                            flag = True
                        if data['enable_filter']:
                            vals['balance_cmp'] = value['comp_bal'] * int(report.sign)
                            if not currency_id.is_zero(vals['balance_cmp']):
                                flag = True
                        if flag:
                            sub_lines.append(vals)

                    ## group account changes start
    #                group_accounts = Account.search([('group_account','=',True),
    #                    ('id','in',all_account_ids)])
                    for group_account in group_accounts:
                        child_ids = Account.search([('parent_id','=',group_account.id)])
                        child_ids = child_ids.ids

                        remove_lines = []
                        total_credit,total_debit,total_balance = 0.0,0.0,0.0
                        self_id, parent = False, ''
                        for sub_line in sub_lines:
                            account_id = sub_line.get('account', False)
                            if account_id in child_ids:
                                if data['debit_credit']:
                                    total_credit += sub_line.get('credit')
                                    total_debit += sub_line.get('debit')
                                total_balance += sub_line.get('balance')

                                if not self_id:
                                    self_id = sub_line.get('self_id')
                                if not parent:
                                    parent = sub_line.get('parent')
                                remove_lines.append(account_id)

                        ## add group dict
                        group_dict = {}
                        group_dict['account_type'] = group_account.internal_type
                        group_dict['parent'] = parent
                        group_dict['symbol'] = currency_id.symbol
                        group_dict['precision'] = currency_id.decimal_places
                        group_dict['company_currency_id'] = company_id.currency_id.id
                        group_dict['style_type'] ='main'
                        group_dict['self_id'] = 50
                        group_dict['account'] = group_account.id
    #                    group_dict['name'] = group_account.code +' '+ group_account.name
                        group_dict['name'] = group_account.name
                        group_dict['id'] = group_account.id
                        group_dict['code'] = group_account.code
                        group_dict['serial_no'] = group_account.serial_no
    #                    group_dict['level'] = 4
                        group_dict['list_len'] = [0, 1, 2, 3]
                        group_dict['level'] = report.level
    #                    group_dict['list_len'] = [a for a in range(0,report.level)],
                        group_dict['indent_list'] = self._get_indent_list(group_account)
                        group_dict['credit'] = total_credit
                        group_dict['debit'] = total_debit
#                        group_dict['balance'] =  total_debit - total_credit
                        group_dict['balance'] =  total_balance
                        group_dict['position'] = currency_id.position
                        group_dict['type'] = 'account'
                        group_dict['group_account'] = True
                        sub_lines.append(group_dict)

                        remove_lines = list(set(remove_lines))
                        sub_lines = [i for i in sub_lines if not (i['account'] in remove_lines)]
                    ## group account changes end


    #                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
    #                lines += sorted(sub_lines, key=lambda sub_line: sub_line['code'])
                    lines += sorted(sub_lines, key=lambda sub_line: sub_line['serial_no'])

            ## new change
            user_type_ids = self.env['account.account.type'].search([('name','not in',('Income View','Expense View'))])
            view_accounts = Account.search([('type','=','view'),
                            ('serial_no','!=',False),
                            ('user_type_id','in',user_type_ids.ids),
                            ('group_account','!=',True)
                            ], order='serial_no asc')
            for view_account in view_accounts:
                if not view_account.serial_no:
                    continue
                debit, credit, balance = 0,0,0
                if view_account.name== 'Liability':
                    debit = last_debit
                    credit = last_credit
                    balance = last_balance
                view_dict = {}
                view_dict['account_type'] = view_account.internal_type
                view_dict['parent'] = report.id if report.type in ['accounts','account_type'] else 0
                view_dict['symbol'] = currency_id.symbol
                view_dict['precision'] = currency_id.decimal_places
                view_dict['company_currency_id'] = company_id.currency_id.id
                view_dict['style_type'] ='main'
                view_dict['self_id'] = 50
                view_dict['account'] = view_account.id
    #                    group_dict['name'] = view_account.code +' '+ view_account.name
                view_dict['name'] = view_account.name
                view_dict['id'] = view_account.id
                view_dict['code'] = view_account.code
                view_dict['serial_no'] = view_account.serial_no
    #                    group_dict['level'] = 4
                view_dict['list_len'] = [0, 1, 2, 3]
                view_dict['level'] = report.level
                view_dict['indent_list'] = self._get_indent_list(view_account)
    #                    group_dict['list_len'] = [a for a in range(0,report.level)],
                view_dict['credit'] = credit
                view_dict['debit'] = debit
                view_dict['balance'] =  balance
                view_dict['position'] = currency_id.position
                view_dict['type'] = 'account'
                view_dict['group_account'] = True

                lines.append(view_dict)
                new_result_dict[view_account.id] = view_dict
            lines = sorted(lines, key=lambda line: line['serial_no'])

            normal_accounts = Account.search(['|',('type','!=','view'),
                        ('group_account','=',True)
                    ])

    #        print"new_result_dict: ",new_result_dict
            for account in normal_accounts:
                line = new_result_dict.get(account.id,False)
                if line:
                    parent = account.parent_id or False
                    while parent:
                        line1 = new_result_dict.get(parent.id,False)
                        if line1:
                            line1 = self._update_line(line, line1, data)
                            new_result_dict[parent.id]=line1
                        parent = parent.parent_id or False
                        if not parent:
                            break
            for l in lines:
                d = new_result_dict.get(l.get(id),{})
                if d:
                    lines.append(d)
            # New change end



            ## show heirarchy change
#            if show_hierarchy:
#                heads = Account.search([('name','in',('Assets','Liability'))],order='code')
#                new_lines={}
#                for l in lines:
#                    if l.get('code'):
#                        new_lines[l.get('code')] = l
#                lines = self.prepare_hierarchy(new_lines)
#                for line in lines:
#                    if line.get('code',False):
#                        account_ids = Account.search([('code','=',line.get('code'))])
#                        if account_ids:
#                            line['name'] = account_ids[0].name


            return lines, initial_balance, current_balance, ending_balance
        elif account_report.name == 'Profit and Loss':
            for report in child_reports:
                print"report Name: ",report.name
                company_id = self.env.user.company_id
                currency_id = company_id.currency_id
                vals = {
                    'name': report.name,
                    'balance': res[report.id]['balance'] * int(report.sign),
                    'parent': report.parent_id.id if report.parent_id.type in ['accounts','account_type'] else 0,
                    'self_id': report.id,
                    'type': 'report',
                    'style_type': 'main',
                    'precision': currency_id.decimal_places,
                    'symbol': currency_id.symbol,
                    'position': currency_id.position,
                    'list_len': [a for a in range(0,report.level)],
                    'level': report.level,
                    'indent_list':[1],
                    'company_currency_id': company_id.currency_id.id,
                    'account_type': report.type or False, #used to underline the financial report balances
                }
                if data['debit_credit']:
                    vals['debit'] = res[report.id]['debit']
                    vals['credit'] = res[report.id]['credit']

                if data['enable_filter']:
                    vals['balance_cmp'] = res[report.id]['comp_bal'] * int(report.sign)
                    
                domain = [('group_account','=',True)]
                if report.name=='Income':
                    user_type_ids = self.env['account.account.type'].search([('name','in',('Income View','Income','Other Income'))])
                    if user_type_ids:
                        domain.append(('user_type_id','in',user_type_ids.ids))
                if report.name=='Expense':
                    user_type_ids = self.env['account.account.type'].search([('name','in',('Expenses','Expense View'))])
                    if user_type_ids:
                        domain.append(('user_type_id','in',user_type_ids.ids))
                group_accounts = Account.search(domain)

#                lines.append(vals) # TODO
                if report.name=='Profit and Loss':
                    vals['serial_no'] = 0
                    lines.append(vals)
                if report.display_detail == 'no_detail':
                    #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                    continue

                if res[report.id].get('account'):
                    sub_lines = []
                    for account_id, value in res[report.id]['account'].items():
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        flag = False
                        account = self.env['account.account'].browse(account_id)
                        vals = {
                            'account': account.id,
                            'name': account.code + ' ' + account.name,
                            'code': account.code,
                            'serial_no': account.serial_no,
                            'balance': value['balance'] * int(report.sign) or 0.0,
                            'type': 'account',
#                            'parent': report.id if report.type in ['accounts','account_type'] else 0,
                            'parent': report.parent_id.id if report.parent_id.type in ['accounts','account_type'] else 0,
                            'self_id': 50,
                            'style_type': 'sub',
                            'precision': currency_id.decimal_places,
                            'symbol': currency_id.symbol,
                            'position': currency_id.position,
                            'list_len':[a for a in range(0,report.display_detail == 'detail_with_hierarchy' and 4)],
                            'level': 4,
                            'indent_list': self._get_indent_list(account),
                            'company_currency_id': company_id.currency_id.id,
                            'account_type': account.internal_type,
                        }
                        new_result_dict[account.id] = vals
                        if data['debit_credit']:
                            vals['debit'] = value['debit']
                            vals['credit'] = value['credit']
                            if not currency_id.is_zero(vals['debit']) or not currency_id.is_zero(vals['credit']):
                                flag = True
                        if not currency_id.is_zero(vals['balance']):
                            flag = True
                        if data['enable_filter']:
                            vals['balance_cmp'] = value['comp_bal'] * int(report.sign)
                            if not currency_id.is_zero(vals['balance_cmp']):
                                flag = True
                        if flag:
                            sub_lines.append(vals)
                            
                    # group account start
                    for group_account in group_accounts:
                        child_ids = Account.search([('parent_id','=',group_account.id)])
                        child_ids = child_ids.ids

                        remove_lines = []
                        total_credit,total_debit,total_balance = 0.0,0.0,0.0
                        self_id, parent = False, ''
                        for sub_line in sub_lines:
                            account_id = sub_line.get('account', False)
                            if account_id in child_ids:
                                total_credit += sub_line.get('credit')
                                total_debit += sub_line.get('debit')

                                if not self_id:
                                    self_id = sub_line.get('self_id')
                                if not parent:
                                    parent = sub_line.get('parent')
                                remove_lines.append(account_id)

                        ## add group dict
                        group_dict = {}
                        group_dict['account_type'] = group_account.internal_type
                        group_dict['parent'] = parent
                        group_dict['symbol'] = currency_id.symbol
                        group_dict['precision'] = currency_id.decimal_places
                        group_dict['company_currency_id'] = company_id.currency_id.id
                        group_dict['style_type'] ='main'
                        group_dict['self_id'] = 50
                        group_dict['account'] = group_account.id
    #                    group_dict['name'] = group_account.code +' '+ group_account.name
                        group_dict['name'] = group_account.name
                        group_dict['id'] = group_account.id
                        group_dict['code'] = group_account.code
                        group_dict['serial_no'] = group_account.serial_no
    #                    group_dict['level'] = 4
                        group_dict['list_len'] = [0, 1, 2, 3]
                        group_dict['level'] = report.level
                        group_dict['indent_list'] = self._get_indent_list(group_account)
    #                    group_dict['list_len'] = [a for a in range(0,report.level)],
                        group_dict['credit'] = total_credit
                        group_dict['debit'] = total_debit
                        group_dict['balance'] =  total_debit - total_credit
                        group_dict['position'] = currency_id.position
                        group_dict['type'] = 'account'
                        group_dict['group_account'] = True
                        sub_lines.append(group_dict)

                        remove_lines = list(set(remove_lines))
                        sub_lines = [i for i in sub_lines if not (i['account'] in remove_lines)]
                    # group account end
                    
#                    lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
                    lines += sorted(sub_lines, key=lambda sub_line: sub_line['serial_no'])
                    
            ## new change
#            user_type_ids = self.env['account.account.type'].search([('name','not in',('Asset View','Liability View'))])
            user_type_ids = self.env['account.account.type'].search([('name','not in',('Asset View','Liability View','Equity'))])
            
            ## these are skip account types
            equity_user_type_ids = self.env['account.account.type'].search([('name','in',('Equity','Current Liabilities','Payable','Asset View','Non-current Liabilities'))])
            equity_account_ids = Account.search([('user_type_id','in',equity_user_type_ids.ids)])
            view_accounts = Account.search([('type','=','view'),
                            ('serial_no','!=',False),
                            ('user_type_id','in',user_type_ids.ids),
                            ('group_account','!=',True)
                            ], order='serial_no asc')
            for view_account in view_accounts:
                if not view_account.serial_no:
                    continue
                if view_account.user_type_id.id in equity_user_type_ids.ids:
                    continue
                if view_account.parent_id.id in equity_account_ids.ids:
                    continue
                debit, credit, balance = 0,0,0
                if view_account.name== 'Liability':
                    debit = last_debit
                    credit = last_credit
                    balance = last_balance
                view_dict = {}
                view_dict['account_type'] = view_account.internal_type
#                view_dict['parent'] = parent
                view_dict['parent'] = report.parent_id.id if report.parent_id.type in ['accounts','account_type'] else 0,
                view_dict['symbol'] = currency_id.symbol
                view_dict['precision'] = currency_id.decimal_places
                view_dict['company_currency_id'] = company_id.currency_id.id
                view_dict['style_type'] ='main'
                view_dict['self_id'] = 50
                view_dict['account'] = view_account.id
    #                    group_dict['name'] = view_account.code +' '+ view_account.name
                view_dict['name'] = view_account.name
                view_dict['id'] = view_account.id
                view_dict['code'] = view_account.code
                view_dict['serial_no'] = view_account.serial_no
    #                    group_dict['level'] = 4
                view_dict['list_len'] = [0, 1, 2, 3]
                view_dict['level'] = report.level
                view_dict['indent_list'] = self._get_indent_list(view_account)
    #                    group_dict['list_len'] = [a for a in range(0,report.level)],
                view_dict['credit'] = credit
                view_dict['debit'] = debit
                view_dict['balance'] =  balance
                view_dict['position'] = currency_id.position
                view_dict['type'] = 'account'
                view_dict['group_account'] = True

                lines.append(view_dict)
                new_result_dict[view_account.id] = view_dict
            lines = sorted(lines, key=lambda line: line['serial_no'])

            normal_accounts = Account.search(['|',('type','!=','view'),
                        ('group_account','=',True)
                    ])

    #        print"new_result_dict: ",new_result_dict
            for account in normal_accounts:
                line = new_result_dict.get(account.id,False)
                if line:
                    parent = account.parent_id or False
                    while parent:
                        line1 = new_result_dict.get(parent.id,False)
                        if line1:
                            line1 = self._update_line(line, line1, data)
                            new_result_dict[parent.id]=line1
                        parent = parent.parent_id or False
                        if not parent:
                            break
            for l in lines:
                d = new_result_dict.get(l.get(id),{})
                if d:
                    lines.append(d)
            # New change end
                    
            return lines, initial_balance, current_balance, ending_balance
        else:
            for report in child_reports:
                company_id = self.env.user.company_id
                currency_id = company_id.currency_id
                vals = {
                    'name': report.name,
                    'balance': res[report.id]['balance'] * int(report.sign),
                    'parent': report.parent_id.id if report.parent_id.type in ['accounts','account_type'] else 0,
                    'self_id': report.id,
                    'type': 'report',
                    'style_type': 'main',
                    'precision': currency_id.decimal_places,
                    'symbol': currency_id.symbol,
                    'position': currency_id.position,
                    'list_len': [a for a in range(0,report.level)],
                    'level': report.level,
                    'indent_list':[1],
                    'company_currency_id': company_id.currency_id.id,
                    'account_type': report.type or False, #used to underline the financial report balances
                }
                if data['debit_credit']:
                    vals['debit'] = res[report.id]['debit']
                    vals['credit'] = res[report.id]['credit']

                if data['enable_filter']:
                    vals['balance_cmp'] = res[report.id]['comp_bal'] * int(report.sign)

                lines.append(vals)
                if report.display_detail == 'no_detail':
                    #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                    continue

                if res[report.id].get('account'):
                    sub_lines = []
                    for account_id, value in res[report.id]['account'].items():
                        #if there are accounts to display, we add them to the lines with a level equals to their level in
                        #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                        #financial reports for Assets, liabilities...)
                        flag = False
                        account = self.env['account.account'].browse(account_id)
                        vals = {
                            'account': account.id,
                            'name': account.code + ' ' + account.name,
                            'balance': value['balance'] * int(report.sign) or 0.0,
                            'type': 'account',
                            'parent': report.id if report.type in ['accounts','account_type'] else 0,
                            'self_id': 50,
                            'style_type': 'sub',
                            'precision': currency_id.decimal_places,
                            'symbol': currency_id.symbol,
                            'position': currency_id.position,
                            'list_len':[a for a in range(0,report.display_detail == 'detail_with_hierarchy' and 4)],
                            'level': 4,
                            'indent_list':self._get_indent_list(account),
                            'company_currency_id': company_id.currency_id.id,
                            'account_type': account.internal_type,
                        }
                        if data['debit_credit']:
                            vals['debit'] = value['debit']
                            vals['credit'] = value['credit']
                            if not currency_id.is_zero(vals['debit']) or not currency_id.is_zero(vals['credit']):
                                flag = True
                        if not currency_id.is_zero(vals['balance']):
                            flag = True
                        if data['enable_filter']:
                            vals['balance_cmp'] = value['comp_bal'] * int(report.sign)
                            if not currency_id.is_zero(vals['balance_cmp']):
                                flag = True
                        if flag:
                            sub_lines.append(vals)
                    lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
            return lines, initial_balance, current_balance, ending_balance
    
    def _update_line(self, line, line1, data):
        debit = line.get('debit')
        credit = line.get('credit')
        balance = line.get('balance')
        
        if data['debit_credit']:
            line1['debit'] += debit
            line1['credit'] += credit
        line1['balance'] += balance
        
#        print"line1 AFter: ",line1
        return line1

    def get_report_values(self):
        self.ensure_one()

        self.onchange_date_range()

        company_domain = [('company_id', '=', self.env.user.company_id.id)]
        journal_ids = self.env['account.journal'].search(company_domain)
        analytics = self.env['account.analytic.account'].search(company_domain)
        analytic_tags = self.env['account.analytic.tag'].sudo().search([])

        data = dict()
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['date_from', 'enable_filter', 'debit_credit', 'date_to', 'date_range',
             'account_report_id', 'target_move', 'view_format', 'journal_ids',
             'analytic_ids', 'analytic_tag_ids',
             'company_id','enable_filter','date_from_cmp','date_to_cmp','label_filter','filter_cmp',
             'show_hierarchy'])[0]
        data['form'].update({'journals_list': [(j.id, j.name) for j in journal_ids]})
        data['form'].update({'analytics_list': [(j.id, j.name) for j in analytics]})
        data['form'].update({'analytic_tag_list': [(j.id, j.name) for j in analytic_tags]})

        if self.enable_filter:
            data['form']['debit_credit'] = False

        date_from, date_to = False, False
        used_context = {}
        used_context['date_from'] = self.date_from or False
        used_context['date_to'] = self.date_to or False

        used_context['strict_range'] = True
        used_context['company_id'] = self.env.user.company_id.id

        used_context['journal_ids'] = self.journal_ids.ids
        used_context['analytic_account_ids'] = self.analytic_ids
        used_context['analytic_tag_ids'] = self.analytic_tag_ids
        used_context['state'] = data['form'].get('target_move', '')
        data['form']['used_context'] = used_context

        comparison_context = {}
        comparison_context['strict_range'] = True
        comparison_context['company_id'] = self.env.user.company_id.id

        comparison_context['journal_ids'] = self.journal_ids.ids
        comparison_context['analytic_account_ids'] = self.analytic_ids
        comparison_context['analytic_tag_ids'] = self.analytic_tag_ids
        if self.filter_cmp == 'filter_date':
            comparison_context['date_to'] = self.date_to_cmp or ''
            comparison_context['date_from'] = self.date_from_cmp or ''
        else:
            comparison_context['date_to'] = False
            comparison_context['date_from'] = False
        comparison_context['state'] = self.target_move or ''
        data['form']['comparison_context'] = comparison_context
        report_lines, initial_balance, current_balance, ending_balance = self.get_account_lines(data.get('form'))

        data['form']['comparison_context']['analytic_tag_ids'] = []
        data['form']['used_context']['analytic_tag_ids'] = []
        data['form']['comparison_context']['analytic_account_ids'] = []
        data['form']['used_context']['analytic_account_ids'] = []

        company_id = self.env.user.company_id
        data['currency'] = company_id.currency_id.id
        data['report_lines'] = report_lines
        data['initial_balance'] = initial_balance or 0.0
        data['current_balance'] = current_balance or 0.0
        data['ending_balance'] = ending_balance or 0.0
        return data

    @api.model
    def _get_default_report_id(self):
        if self.env.context.get('report_name', False):
            return self.env.context.get('report_name', False)
        return self.env.ref('account.account_financial_report_profitandloss0').id

    @api.model
    def _get_default_date_range(self):
        return self.env.user.company_id.date_range

    @api.model
    def _get_default_financial_year(self):
        return self.env.user.company_id.financial_year

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    @api.depends('account_report_id')
    def name_get(self):
        res = []
        for record in self:
            name = record.account_report_id.name or 'Financial Report'
            res.append((record.id, name))
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
    view_format = fields.Selection([
        ('vertical', 'Vertical'),
        ('horizontal', 'Horizontal')],
        default='vertical',
        string="Format")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_default_company)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
                                   default=lambda self: self.env['account.journal'].search(
                                       [('company_id', '=', self.company_id.id)]))
    analytic_ids = fields.Many2many(
        'account.analytic.account', string='Analytic Accounts'
    )
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string='Analytic Tags'
    )
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')

    enable_filter = fields.Boolean(
        string='Enable Comparison',
        default=False)
    account_report_id = fields.Many2one(
        'account.financial.report',
        string='Account Reports',
        required=True, default=_get_default_report_id)

    debit_credit = fields.Boolean(
        string='Display Debit/Credit Columns',
        default=False,
        help="Help to identify debit and credit with balance line for better understanding.")

    date_from_cmp = fields.Date(string='Start Date')
    date_to_cmp = fields.Date(string='End Date')
    filter_cmp = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], string='Filter by',
                                  required=True, default='filter_date')
    label_filter = fields.Char(string='Column Label', default='Comparison Period',
                               help="This label will be displayed on report to show the balance computed for the given comparison filter.")
    show_hierarchy = fields.Boolean(
        string='Show Hierarchy',
        default=False)

    @api.model
    def create(self, vals):
        ret = super(InsFinancialReport, self).create(vals)
        return ret

    @api.multi
    def write(self, vals):

        if vals.get('date_range'):
            vals.update({'date_from': False, 'date_to': False})
        if vals.get('date_from') and vals.get('date_to'):
            vals.update({'date_range': False})

        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(4, j) for j in vals.get('journal_ids')]})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})

        if vals.get('analytic_ids'):
            vals.update({'analytic_ids': [(4, j) for j in vals.get('analytic_ids')]})
        if vals.get('analytic_ids') == []:
            vals.update({'analytic_ids': [(5,)]})
        if vals.get('analytic_tag_ids'):
            vals.update({'analytic_tag_ids': [(4, j) for j in vals.get('analytic_tag_ids')]})
        if vals.get('analytic_tag_ids') == []:
            vals.update({'analytic_tag_ids': [(5,)]})

        ret = super(InsFinancialReport, self).write(vals)
        return ret

    def action_pdf(self):
        ''' Button function for Pdf '''
        data = self.get_report_values()

        return self.env['report'].with_context({'landscape': 1}).get_action(
            self, 'account_dynamic_reports.ins_report_financial', data=data)

    def action_xlsx(self):
        ''' Button function for Xlsx '''
        raise UserError(_('Please install a free module "dynamic_xlsx".'
                          'You can get it by contacting "pycustech@gmail.com". It is free'))

    def action_view(self):
        res = {
            'type': 'ir.actions.client',
            'name': 'FR View',
            'tag': 'dynamic.fr',
            'context': {'wizard_id': self.id,
                        'account_report_id': self.account_report_id.id}
        }
        return res
