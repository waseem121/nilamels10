# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class InsReportTrialBalance(models.AbstractModel):
    _name = 'report.account_dynamic_reports.trial_balance'

    @api.model
    def render_html(self, docids, data=None):
        if self.env.context.get('from_js'):
            if data.get('js_data'):
                docargs = {'Ledger_data': data.get('js_data')[1],
                             'Retained': data.get('js_data')[2],
                             'Subtotal': data.get('js_data')[3],
                             'Filters': data.get('js_data')[0],
                             }
                return self.env['report'].render('account_dynamic_reports.trial_balance', docargs)

        docargs = {'Ledger_data': data.get('Ledger_data'),
                             'Retained': data.get('Retained'),
                             'Subtotal': data.get('Subtotal'),
                             'Filters': data.get('Filters'),
                             }
        return self.env['report'].render('account_dynamic_reports.trial_balance', docargs)
