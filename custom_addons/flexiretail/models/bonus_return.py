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
# 
# from openerp.osv import osv, fields
from openerp import models, fields, api, _
from datetime import timedelta
from datetime import datetime
import time

class bonus_return(models.Model):
    _name = "bonus.return"

    def _get_cust(self):
        users_obj = self.env['res.users'].browse(self._uid)
        company_id = users_obj.company_id.id
        return company_id

    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=_get_cust) 
    name = fields.Char('Description', size=128)
    date_create = fields.Date('Issue Date', readonly=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    date_expire = fields.Date('Expiry Date')
    date_expire_num = fields.Integer()
    bonus_amount = fields.Float('Amount')
    bonus_remaining_amt = fields.Float('Remaining Amount', readonly=True)
    bonus_history = fields.One2many('pos.bonus.history', 'bonus_return_id', string='History Lines', readonly=True)

    def create(self, vals):
        if context is None:
            context = {}
        date_create = time.strftime("%Y:%m:%d")
        date_formatted_create = datetime.strptime(date_create , '%Y:%m:%d')
        if vals.get('date_expire_num') > 0:
            date_expire = date_formatted_create + timedelta(days=int(vals.get('date_expire_num')))
        else:
            date_expire = 0
        vals.update({'date_expire' : date_expire})
        res = super(bonus_return, self).create(vals)
        return res

bonus_return()

class pos_bonus_history(models.Model):
    _name = "pos.bonus.history"

    name = fields.Char('Bonus Serial', size=264)
    used_amount = fields.Float('Used Amount')
    used_date = fields.Date('Used Date', default=lambda *a: time.strftime('%Y-%m-%d'))
    bonus_return_id = fields.Many2one('bonus.return', string='Bonus Coupon')
    pos_order = fields.Char('POS Order')


pos_bonus_history()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: