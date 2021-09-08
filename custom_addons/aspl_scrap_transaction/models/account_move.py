# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self, vals):
        print "vals===============>>>>", vals
        res = super(AccountMove, self).create(vals)
        print"created!! "
        if self._context.get('from_scrap_adjustment', False):
            if not res.name or res.name == '/':
                res.name = self.env['ir.sequence'].next_by_code('account.move.sequence')
        return res
