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

from odoo import tools, fields, models, api
import odoo.addons.decimal_precision as dp


class report_pos_order_payment(models.Model):
    _name = "report.pos.order.payment"
    _description = "Point of Sale Payment Analysis"
    _auto = False

    pos_session_id = fields.Many2one('pos.session', string='Session')
    pos_config_id = fields.Many2one('pos.config', string='Point of Sale')
    statement_name = fields.Char(string='Reference')
    date = fields.Date(string='Date')
    journal_id = fields.Many2one('account.journal', string='Journal')
    balance_start = fields.Float(string='Starting Balance', digits=dp.get_precision('Account'))
    balance_end_real = fields.Float(string='Ending Balance', digits=dp.get_precision('Account'))
    currency_id = fields.Many2one('res.currency', string='Currency')
    company_id = fields.Many2one('res.company', string='Company')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_pos_order_payment')
        self._cr.execute("""
                create or replace view report_pos_order_payment as (
                    select
                        min(bs.id) as id,
                        count(*) as nbr,
                        bs.pos_session_id as pos_session_id,
                        ps.config_id as pos_config_id,
                        bs.name as statement_name,
                        bs.date as date,
                        bs.journal_id as journal_id,
                        bs.balance_start as balance_start,
                        bs.balance_end_real as balance_end_real,
                        bs.company_id as company_id,
                        aj.currency_id as currency_id                        
                    from pos_session as ps
                        left join account_bank_statement bs on (bs.pos_session_id=ps.id)
                        left join res_company aj on (bs.company_id = aj.id) 
                    group by
                        bs.pos_session_id, ps.config_id, bs.name, bs.date, bs.journal_id,  bs.balance_start,
                        bs.balance_end_real, bs.company_id, aj.currency_id)""")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: