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
from openerp import fields, models, api, _
from datetime import timedelta
from datetime import datetime
import time


class pos_coupon(models.Model):
    _name = "pos.coupon"

    @api.multi
    def _get_cust(self):
        users_obj = self.env['res.users'].browse(self._uid)
        company_id = users_obj.company_id.id
        return company_id

    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=_get_cust)
    name = fields.Char('Description', size=128)
    validity = fields.Integer('Validity (in days)')
    line_ids = fields.One2many('pos.coupon.line', 'coupon_id', 'Lines')
    coupon_history = fields.One2many('pos.coupon.history', 'coupon_id', 'History Lines', readonly=True)
    coupon_note = fields.Text(string="Note")


class pos_coupon_line(models.Model):
    _name = "pos.coupon.line"

    @api.one
    def _compute_is_manager_default(self):
        group_id = self.env['ir.model.data'].get_object_reference('flexiretail', 'group_coupon_manager')[1]
        group = self.env['res.groups'].browse(group_id)
        if self.env.user in group.users:
            self.group_coupon_manager = True
            return True
        self.group_coupon_manager = False
        return False

    @api.multi
    def _compute_is_manager(self):
        group_id = self.env['ir.model.data'].get_object_reference('flexiretail', 'group_coupon_manager')[1]
        group = self.env['res.groups'].browse(group_id)
        for res in self:
            if res.env.user in group.users:
                res.group_coupon_manager = True
                return True
            res.group_coupon_manager = False
        return False

    name = fields.Char('Coupon Serial', size=264)
    amount = fields.Float('Amount')
    remaining_amt = fields.Float('Remaining Amount', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    coupon_id = fields.Many2one('pos.coupon', 'Coupon', ondelete="cascade")
    validity = fields.Integer(string="Validity", readonly=True,related="coupon_id.validity")
    date_create_line = fields.Date(string="Issue Date", readonly=True)
    date_expiry_line = fields.Date(string="Expiry Date", readonly=True)
    group_coupon_manager = fields.Boolean('Coupon Manager', compute='_compute_is_manager',
                                          default=_compute_is_manager_default)

    @api.model
    def create(self, vals):
        if self._context is None:
            self._context = {}
        new_rec = super(pos_coupon_line, self).create(vals)
        date_create = time.strftime("%Y:%m:%d")
        date_formatted_create = datetime.strptime(date_create , '%Y:%m:%d')
        validity = new_rec.validity
        new_rec.date_create_line = date_formatted_create
        new_rec.date_expiry_line = date_formatted_create + timedelta(days=new_rec.validity)
        return new_rec

pos_coupon_line()


class pos_coupon_history(models.Model):
    _name = "pos.coupon.history"

    name = fields.Char('Coupon Serial', size=264)
    used_amount = fields.Float('Used Amount')
    used_date = fields.Date('Used Date', default=time.strftime('%Y-%m-%d'))
    coupon_id = fields.Many2one('pos.coupon', 'Coupon')
    pos_order = fields.Char('POS Order')

    @api.model
    def create(self, vals):
        history_obj = super(pos_coupon_history, self).create(vals)
        order_obj = self.env['pos.order'].search([('pos_reference', '=', history_obj.pos_order)])
        # if order_obj:
        #     order_obj.applied_coupon_ref += history_obj
        return history_obj


    @api.model
    def recharge_returned_coupon(self, coupon_id):
        if coupon_id:
            coupon_obj = self.browse(coupon_id)
            if coupon_obj:
                coupon_line_obj = self.env['pos.coupon.line'].search([('name', '=', coupon_obj.name)])
                if coupon_line_obj:
                    new_amt = coupon_line_obj.remaining_amt + coupon_obj.used_amount
                    coupon_line_obj.write({
                       'remaining_amt' : new_amt
                    })
                    return True
        return False

pos_coupon_history()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: