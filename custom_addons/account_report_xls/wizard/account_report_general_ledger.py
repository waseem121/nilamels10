# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.report.general.ledger"
    _description = "General Ledger Report"
    
       
    def print_xls(self):
        report = self.check_report()
        print'report@@AccountReportGeneralLedger@@@@',report
        datas = report['data']
        print'datas@@AccountReportGeneralLedger@@@@',datas
        data = self.pre_print_report(datas)
        print'data@@AccountReportGeneralLedger@@@@',data
        users = self.env['res.users'].sudo().browse(self._uid)
        company = users.company_id
#        if not data['form']['date_from'] or not data['form']['date_to']:
#            raise UserError("Please Difine Start Date and End Date.")
        
        sortby = data['form']['sortby']
        if sortby == 'sort_date':
            sortby_name = 'Date'
        elif sortby == 'sort_journal_partner':
            sortby_name = 'Journal & Partner'
            
        target_moves = data['form']['target_move']
        if target_moves == 'posted':
            target_moves_name = 'All Posted Entries'
        elif target_moves == 'all':
            target_moves_name = 'All Entries'
            
        init_balance = data['form']['initial_balance']
        if init_balance:
            initial_balance_name = 'Yes'
        if not init_balance:
            initial_balance_name = 'No'
            
        display_account = data['form']['display_account']
        
        if display_account == 'all':
            display_account_name = 'all'
        elif display_account == 'movement':
            display_account_name = 'With movements'
        elif display_account == 'not_zero':
            display_account_name = 'With balance is not equal to 0'
        
        journal_code =[]
        for journal in self.env['account.journal'].sudo().browse(data['form']['journal_ids']):
            journal_code.append(journal.code)
        journal_name = ','.join(journal_code)
        
        data['form'].update({'report_name':'GENERAL LEDGER - '+company.name+'-'+company.currency_id.name})
        data['form'].update({'display_account_name':display_account_name})
        data['form'].update({'journal_name':journal_name})
        data['form'].update({'sortby_name':sortby_name})
        data['form'].update({'target_moves_name':target_moves_name})
        data['form'].update({'initial_balance_name':initial_balance_name})
        
        used_context = data['form']['used_context']
        obj_account = self.env['account.account']
        get_accounts = data['form']['account_ids'] if data['form'].has_key('account_ids') else 0
        print'get_accounts',get_accounts
        if get_accounts:
            accounts = obj_account.browse(get_accounts)
        else:
            accounts = self.env['account.account'].search([])
        print'accounts',accounts
        accounts_res =  self.env['report.account.report_generalledger'].with_context(used_context)._get_account_move_entry(accounts, init_balance, sortby, display_account)
        print'accounts_res',accounts_res
        data['form'].update({'accounts':accounts_res})
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account_report_xls.general_ledger_xls.xls',
            'datas': data['form'],
            'name': 'GeneralLedger'
        }