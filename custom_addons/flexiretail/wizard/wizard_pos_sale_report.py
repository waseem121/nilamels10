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

from openerp import fields, models, api, _
from openerp.exceptions import Warning


class wizard_pos_sale_report(models.TransientModel):
    _name = 'wizard.pos.sale.report'

    @api.model
    def get_ip(self):
        proxy_ip = self.env['res.users'].browse([self._uid]).company_id.report_ip_address or''
        return proxy_ip

    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    session_ids = fields.Many2many('pos.session', 'pos_session_list', 'wizard_id', 'session_id', string="Session(s)")
    report_type = fields.Selection([('thermal', 'Thermal'),
                                    ('pdf', 'PDF')], default='thermal', string="Report Type")
    proxy_ip = fields.Char(string="Proxy IP", default=get_ip)

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise Warning(_('End date should be greater than start date.'))

    @api.multi
    def print_pos_sale_action(self):
        if self.start_date > self.end_date:
            raise Warning(_('End date should be greater than start date.'))
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
