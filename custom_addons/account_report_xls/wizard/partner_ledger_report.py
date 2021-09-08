
from odoo import models, fields, api
import time

class AccountReportPartnerLedger(models.TransientModel):
    _inherit = "account.report.partner.ledger"
    def get_partners_data(self,data=None):
        data['computed'] = {}

        obj_partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']

        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.internal_type IN %s
            AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [a for (a,) in self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']), tuple(data['computed']['account_ids'])] + query_get_data[2]
        reconcile_clause = "" if data['form']['reconciled'] else ' AND "account_move_line".reconciled = false '
        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND NOT account.deprecated
                AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))
        
        
        partner_ids = data['form']['partner_ids']
        if not partner_ids:
            partner_ids = [res['partner_id'] for res in self.env.cr.dictfetchall()]
        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref, x.name))
        print'partners',partners
        return partners
    
    def print_xls(self):
        report = self.check_report()
        print'report@@AccountReportGeneralLedger@@@@',report
        datas = report['data']
        print'datas@@AccountReportGeneralLedger@@@@',datas
        data = self.pre_print_report(datas)
        print'data@@AccountReportGeneralLedger@@@@',data
        partners = self.get_partners_data(data)
        print'partners@@AccountReportGeneralLedger@@@@',partners
        
        users = self.env['res.users'].sudo().browse(self._uid)
        company = users.company_id
#        if not data['form']['date_from'] or not data['form']['date_to']:
#            raise UserError("Please Difine Start Date and End Date.")
        
        target_moves = data['form']['target_move']
        if target_moves == 'posted':
            target_moves_name = 'All Posted Entries'
        elif target_moves == 'all':
            target_moves_name = 'All Entries'
        
        journal_code =[]
        for journal in self.env['account.journal'].sudo().browse(data['form']['journal_ids']):
            journal_code.append(journal.code)
        journal_name = ','.join(journal_code)
        
        data['form'].update({'report_name':'PARTNER LEDGER - '+company.name+'-'+company.currency_id.name})
        data['form'].update({'journal_name':journal_name})
        data['form'].update({'target_moves_name':target_moves_name})
        data['form'].update({'lines':{}})
        data['form'].update({'sum_lines':{}})
        for partner in partners:
            debit = self.env['report.account.report_partnerledger']._sum_partner(data,partner,'debit')
            credit = self.env['report.account.report_partnerledger']._sum_partner(data,partner,'credit')
            balance = self.env['report.account.report_partnerledger']._sum_partner(data,partner,'debit - credit')
            print'debit,credit,balance',debit,credit,balance
            sum_partner_lager = {'credit':credit, 'code': '', 'debit':debit, 'date': '', 'progress':balance, 'a_code': '', 'naration': '', 'displayed_name': partner.name}
            data['form']['sum_lines'].update({partner.name:sum_partner_lager})
            
            lines = self.env['report.account.report_partnerledger']._lines(data,partner)
            data['form']['lines'].update({partner.name:lines})
            
#            print'lines@@AccountReportGeneralLedger@@@@',lines
        print'form@@AccountReportGeneralLedger@@@@',data['form']
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account_report_xls.partner_ledger_xls.xls',
            'datas': data['form'],
            'name': 'PartnerLedger'
        }