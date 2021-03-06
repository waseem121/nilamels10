# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountCommonReport(models.TransientModel):
    _inherit = "account.common.report"
    
    # inherited to add level in the context, its used in gts_coa _get_accounts()
    def _build_contexts(self, data):
        result = super(AccountCommonReport, self)._build_contexts(data)
        result['level'] = 'level' in data['form'] and data['form']['level'] or False
        return result

    # inherited to add level in the context, its used in gts_coa _get_accounts()
    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'level', 'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self._print_report(data)
