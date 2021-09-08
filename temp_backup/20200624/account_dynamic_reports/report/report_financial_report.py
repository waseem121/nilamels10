# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class FinancialReportPdf(models.AbstractModel):
    """ Abstract model for generating PDF report value and send to template common for P and L and Balance Sheet"""

    _name = 'report.account_dynamic_reports.ins_report_financial'
    _description = 'Financial Report'

    @api.model
    def render_html(self, docids, data=None):
        if self.env.context.get('from_js'):
            if data.get('js_data'):
                docargs = {
                    'data': data.get('js_data'),
                    'report_lines': data['js_data']['report_lines'],
                    'account_report': data['js_data']['form']['account_report_id'][1],
                    'currency': data['js_data']['currency'],
                }
                return self.env['report'].render('account_dynamic_reports.ins_report_financial', docargs)

        docargs = {
            'data': data,
            'report_lines': data['report_lines'],
            'account_report': data['form']['account_report_id'][1],
            'currency': data['currency'],
        }
        return self.env['report'].render('account_dynamic_reports.ins_report_financial', docargs)