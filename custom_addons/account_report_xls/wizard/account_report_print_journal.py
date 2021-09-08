
from odoo import models, fields, api
import time

class AccountPrintJournal(models.TransientModel):
    _inherit = "account.print.journal"
    
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
        
        target_moves = data['form']['target_move']
        if target_moves == 'posted':
            target_moves_name = 'All Posted Entries'
        elif target_moves == 'all':
            target_moves_name = 'All Entries'
            
        entries_sorted_by = data['form']['sort_selection']
        if entries_sorted_by == 'date':
            entries_sorted_by_name = 'Date'
        elif entries_sorted_by == 'move_name':
            entries_sorted_by_name = 'Journal Entry Number'
        
        journal_code =[]
        sum = {}
        data['form'].update({'get_taxes':{}})
        journal_ids = self.env['account.journal'].sudo().browse(data['form']['journal_ids'])
        for journal in journal_ids:
            journal_code.append(journal.code)
            get_taxes = self.env['report.account.report_journal']._get_taxes(data,journal)
            sum_credit = self.env['report.account.report_journal']._sum_credit(data,journal)
            sum_debit = self.env['report.account.report_journal']._sum_debit(data,journal)    
            sum[journal.id]={'sum_credit':sum_credit,'sum_debit':sum_debit}
            print'get_taxes',get_taxes
            print'get_taxes',get_taxes.keys()
            tax_details={}
            for tx in get_taxes.keys():
                tax_details[tx.id]=get_taxes[tx]
                
            data['form']['get_taxes'].update({journal.name:tax_details})
        journal_name = ','.join(journal_code)
        
        data['form'].update({'report_name':'JOURNAL - '+company.name+'-'+company.currency_id.name})
        data['form'].update({'journal_name':journal_name})
        data['form'].update({'target_moves_name':target_moves_name})
        data['form'].update({'entries_sorted_by_name':entries_sorted_by_name})
        
        
        target_move = data['form'].get('target_move', 'all')
        sort_selection = data['form'].get('sort_selection', 'date')

        res = {}
        
        for journal in data['form']['journal_ids']:
            res[journal] =  self.env['report.account.report_journal'].with_context(data['form'].get('used_context', {})).lines(target_move, journal, sort_selection, data).ids
            
        
        print'sum_credit',sum_credit
        print'sum_debit',sum_debit
        data['form'].update({'lines':res})
        data['form'].update({'sums':sum})
#        print'form@@AccountReportGeneralLedger@@@@',data['form']
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account_report_xls.account_report_print_journal_xls.xls',
            'datas': data['form'],
            'name': 'PrintJournal'
        }