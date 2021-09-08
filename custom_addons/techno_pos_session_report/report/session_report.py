# -*- coding: utf-8 -*-
from odoo import api, models

class ReportSession(models.AbstractModel):
    _name = 'report.techno_pos_session_report.report_pos_session_pdf'

    @api.model
    def render_html(self, docids, data=None):
        session_id = self.env['pos.session'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'pos.session',
            'docs': session_id,
        }
        return self.env['report'].render('techno_pos_session_report.report_pos_session_pdf', docargs)
