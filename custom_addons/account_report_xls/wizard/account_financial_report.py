# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountingReport(models.TransientModel):
    _inherit = "accounting.report"
    
    @api.multi
    def print_xls(self):
        report = self.check_report()
        print'report@@AccountReportGeneralLedger@@@@',report
        data = report['data']
        print'datas@@AccountReportGeneralLedger@@@@',data
#        data = self.pre_print_report(datas)
#        print'data@@AccountReportGeneralLedger@@@@',data
        users = self.env['res.users'].sudo().browse(self._uid)
        company = users.company_id
        
        target_moves = data['form']['target_move']
        if target_moves == 'posted':
            target_moves_name = 'All Posted Entries'
        elif target_moves == 'all':
            target_moves_name = 'All Entries'
            
        filter_cmp = data['form']['filter_cmp']
        if filter_cmp == 'filter_no':
            filter_cmp_name = 'No Filters'
        elif filter_cmp == 'filter_date':
            filter_cmp_name = 'Date'
            
            
        account_report_name = data['form']['account_report_id'][1].upper()
        print 'account_report_name',account_report_name
        
        debit_credit = data['form']['debit_credit']
        if debit_credit:
            debit_credit_name = 'Yes'
        else:
            debit_credit_name = 'No'
            
            
        
        data['form'].update({'report_name':account_report_name+' - '+company.name+'-'+company.currency_id.name})
        data['form'].update({'debit_credit_name':debit_credit_name})
        data['form'].update({'target_moves_name':target_moves_name})
        data['form'].update({'filter_cmp_name':filter_cmp_name})
        
        used_context = data['form']['used_context']
        accounts_res =  self.env['report.account.report_financial'].with_context(used_context).get_account_lines(data['form'])
#        print'accounts_res',accounts_res
        data['form'].update({'lines':accounts_res})
        print'fprrrrr',data['form']
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account_report_xls.profit_and_loss_xls.xls',
            'datas': data['form'],
            'name': account_report_name
        }
        
        