
from odoo import models, fields, api
import time

class AccountAgedTrialBalance(models.TransientModel):
    _inherit = "account.aged.trial.balance"
    
    def print_xls(self):
        report = self.check_report()
        print'report@@AccountReportGeneralLedger@@@@',report
        datas = report['data']
        print'datas@@AccountReportGeneralLedger@@@@',datas
        data = self.pre_print_report(datas)
        print'data@@AccountReportGeneralLedger@@@@',data
        
        users = self.env['res.users'].sudo().browse(self._uid)
        company = users.company_id
        if not data['form']['date_from'] :
            raise UserError("You must set a start date.")
        
        target_moves = data['form']['target_move']
        if target_moves == 'posted':
            target_moves_name = 'All Posted Entries'
        elif target_moves == 'all':
            target_moves_name = 'All Entries'
            
        result_selection = data['form']['result_selection']
        if result_selection == 'customer':
            result_selection_name = 'Receivable Accounts'
        elif result_selection == 'supplier':
            result_selection_name = 'Payable Accounts'
        else:
            result_selection_name = 'Receivable and Payable Accounts'
            
            
        data['form'].update({'report_name':'AGED PARTNER BALANCE - '+company.name+'-'+company.currency_id.name})
        data['form'].update({'target_moves_name':target_moves_name})
        data['form'].update({'result_selection_name':result_selection_name})
        
        target_move = data['form'].get('target_move', 'all')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        
        if data['form']['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']    
        movelines, total, dummy = self.env['report.account.report_agedpartnerbalance']._get_partner_move_lines(account_type, date_from, target_move, data['form']['period_length'])
#        print'movelines, total, dummy',movelines
        data['form'].update({'get_partner_lines':movelines})
        data['form'].update({'get_direction':total})
            
#            print'lines@@AccountReportGeneralLedger@@@@',lines
        print'form@@AccountReportGeneralLedger@@@@',data['form']
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account_report_xls.aged_partner_balance_xls.xls',
            'datas': data['form'],
            'name': 'AgedPartnerBalance'
        }