import time
from odoo import api, models, _
from odoo.exceptions import UserError

class ReportFinancial(models.AbstractModel):
    _inherit = 'report.account.report_financial'

    def _compute_account_balance(self, accounts):
        """ compute the balance, debit and credit for the provided accounts
        """
        # filter the accounts for selected level
        level = self._context.get('level',5)
        if not level: level=5
#        if level:
#            accounts = accounts.filtered(lambda a: a.level < int(level))
        
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
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
#            print "res: ",res

            account_account = self.env['account.account']
            account_ids = res.keys()
            for account in account_account.browse(account_ids):
                res[account.id].update({'level': account.level})
                if account.type != 'view':
                    continue

                all_child_ids = list(set(account._get_children_and_consol_only_leaf_account().ids).intersection(account_ids))
                print "all_child_ids: ",all_child_ids
                if not all_child_ids:
                    continue

                total_debit = total_credit = total_balance = 0.0
                for each_child_id in all_child_ids:
                    total_debit += res.get(each_child_id)['debit']
                    total_credit += res.get(each_child_id)['credit']
                    total_balance += res.get(each_child_id)['balance']

                res[account.id]['debit'] = total_debit
                res[account.id]['credit'] = total_credit
                res[account.id]['balance'] = total_balance
        print"level: ",level
        res = {k:v for k,v in res.iteritems() if int(v['level'] < int(level))}
        print"res after: ",res
        return res
    
    def get_account_lines(self, data):
        ### Customize: 1. Added account_level in account dict
        lines = []
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter']:
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
#            vals = {
#                'name': report.name,
#                'balance': res[report.id]['balance'] * report.sign,
#                'type': 'report',
#                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
#                'account_type': report.type or False, #used to underline the financial report balances
#            }
#            if data['debit_credit']:
#                vals['debit'] = res[report.id]['debit']
#                vals['credit'] = res[report.id]['credit']
#
#            if data['enable_filter']:
#                vals['balance_cmp'] = res[report.id]['comp_bal'] * report.sign
#
#            lines.append(vals)
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
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * report.sign or 0.0,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.type,
                        'account_level': account.level
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * report.sign
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        print "inherited get_account_lines lines: ",lines
        return lines

