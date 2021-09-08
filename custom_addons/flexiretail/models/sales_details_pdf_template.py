# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from openerp import models, api, _

class sale_details_pdf_template(models.AbstractModel):
    _name = 'report.flexiretail.sales_details_pdf_template'

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('flexiretail.sales_details_pdf_template')
        docargs = {
            'doc_ids': self.env["wizard.sales.details"].browse(docids[0]),
            'doc_model': report.model,
            'docs': self,
            'data': data
        }
        return report_obj.render('flexiretail.sales_details_pdf_template', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
