# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError


class OrderAnalysis(models.TransientModel):
    _name = 'order.analysis.wizard'
    _description = 'Open Sale Details Report'

    start_date = fields.Datetime(required=True, default=fields.Datetime.now)
    end_date = fields.Datetime(required=True, default=fields.Datetime.now)

    @api.multi
    def generate_report(self):
	print self.start_date,'===============self.start_date,'
	print self.end_date,'========self.end_date'
        data = {'date_start': self.start_date, 'date_stop': self.end_date}
        data.update(pos_order = self.env['report.pos_report.report_order_analysis'].get_order_details(self.start_date, self.end_date))
        print data,'===========222222===data'
	#return self.env['report'].render('pos_report.report_order_analysis', data)
        return self.env['report'].get_action([],'pos_report.report_order_analysis', data=data)
