from odoo import api, fields, models


class AccountingReport(models.TransientModel):
    _inherit = "accounting.report"

    level = fields.Selection([('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5')], string='Account Level')
    
    # inherited to add level in the context, its used in gts_coa _compute_account_balance()
    def _build_comparison_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['level'] = 'level' in data['form'] and data['form']['level'] or False
        if data['form']['filter_cmp'] == 'filter_date':
            result['date_from'] = data['form']['date_from_cmp']
            result['date_to'] = data['form']['date_to_cmp']
            result['strict_range'] = True
        return result
    
    # inherited to add level in the context, its used in gts_coa _compute_account_balance()
    @api.multi
    def check_report(self):
        res = super(AccountingReport, self).check_report()
        data = {}
        data['form'] = self.read(['account_report_id', 'date_from_cmp', 'level', 'date_to_cmp', 'journal_ids', 'filter_cmp', 'target_move'])[0]
        for field in ['account_report_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        comparison_context = self._build_comparison_context(data)
        res['data']['form']['comparison_context'] = comparison_context
        return res