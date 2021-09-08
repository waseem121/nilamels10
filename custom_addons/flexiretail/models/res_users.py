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

from openerp import models, fields, api, _

class res_users(models.Model):
    _inherit = "res.users"

    can_give_discount = fields.Boolean("Can Give Discount")
#     can_change_qty = fields.Boolean("Can Change Quantity")
    can_change_price = fields.Boolean("Can Change Price")
    user_discount = fields.Float("Maximum Discount")
    default_pos = fields.Many2one('pos.config',string='Default Point Of Sale')