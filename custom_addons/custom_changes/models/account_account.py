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

from odoo import models, api, fields, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    partner_id = fields.Many2one(comodel_name='res.partner', string="Parnter")


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('account_id')
    def get_partner(self):
        if self.account_id:
            if self.account_id.partner_id:
                self.partner_id = self.account_id.partner_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
