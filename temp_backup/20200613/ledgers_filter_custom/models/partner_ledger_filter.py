from odoo import models, fields, api
import time


class partner_ledger_filter_custom(models.TransientModel):
    _inherit = "account.report.partner.ledger"
    _description = "Account Partner Ledger filter based on accounts."

    partner_ids = fields.Many2many('res.partner', string="Partners")
    # ageing added on 2-may-2019 by Dhruvesh
    ageing = fields.Boolean(string="Ageing")

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'partner_ids': self.partner_ids.ids, })
        # ageing added on 2-may-2019 by Dhruvesh
        data['form']['ageing'] = self.ageing
        return super(partner_ledger_filter_custom, self)._print_report(data)


class ReportPartnerLedger(models.AbstractModel):
    _inherit = 'report.account.report_partnerledger'

    def render_html(self, docids, data=None):
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
        reconcile_clause = "" if data['form'].get('reconciled') else ' AND "account_move_line".reconciled = false '
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

        docargs = {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
            'end_date': data['form'].get('date_to'),
            # ageing added on 2-may-2019 by Dhruvesh
            'ageing': data['form'].get('ageing'),
        }
        return self.env['report'].render('account.report_partnerledger', docargs)

        # results, total, amls = self.env['report.account.report_agedpartnerbalance']._get_partner_move_lines(
        #     [self._context['account_type']], self._context['date_to'], 'posted', 30)
