
from openerp import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT
from itertools import groupby
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError

class account_reports_invoice1_template(models.AbstractModel):
    _name = 'report.account_reports.report_invoice1'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('account_reports.report_invoice1')
        record_id = self.env['account.invoice'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': record_id,
        }
        return report_obj.render('account_reports.report_invoice1', docargs)
