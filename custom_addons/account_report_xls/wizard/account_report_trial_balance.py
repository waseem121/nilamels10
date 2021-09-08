# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountBalanceReport(models.TransientModel):
    _inherit = "account.balance.report"
    _description = "Trial Balance Report"
    
    
    def print_xls(self):
        report = self.check_report()
        print'report@@AccountReportGeneralLedger@@@@',report
        datas = report['data']
        print'datas@@AccountReportGeneralLedger@@@@',datas
        data = self.pre_print_report(datas)
        print'data@@AccountReportGeneralLedger@@@@',data
        users = self.env['res.users'].sudo().browse(self._uid)
        company = users.company_id
        if not data['form']['date_from'] or not data['form']['date_to']:
            raise UserError("Please Difine Start Date and End Date.")  
        target_moves = data['form']['target_move']
        if target_moves == 'posted':
            target_moves_name = 'All Posted Entries'
        elif target_moves == 'all':
            target_moves_name = 'All Entries'
            
            
        display_account = data['form']['display_account']
        if display_account == 'all':
            display_account_name = 'all'
        elif display_account == 'movement':
            display_account_name = 'With movements'
        elif display_account == 'not_zero':
            display_account_name = 'With balance is not equal to 0'
            
        operating_units = ''
        
        data['form'].update({'report_name':'TRIAL BALANCE - '+company.name+'-'+company.currency_id.name})
        data['form'].update({'display_account_name':display_account_name})
        data['form'].update({'target_moves_name':target_moves_name})
        data['form'].update({'operating_units':operating_units})
        
        used_context = data['form']['used_context']
        obj_account = self.env['account.account']
        accounts = self.env['account.account'].search([])
        print'accounts',accounts
        accounts_res =  self.env['report.account.report_trialbalance'].with_context(used_context)._get_accounts(accounts, display_account)
        print'accounts_res',accounts_res
        data['form'].update({'accounts':accounts_res})
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account_report_xls.trial_balance_xls.xls',
            'datas': data['form'],
            'name': 'TrialBalance'
        }