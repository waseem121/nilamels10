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

from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    @api.model
    @api.depends('currency_id')
    def _default_has_default_currency(self):
        has_default_currency=False
        if self.currency_id:
            if self.currency_id.id == self.company_id.currency_id.id:
                has_default_currency=True
        self.has_default_currency = has_default_currency

    exchange_rate = fields.Float(default=0.0, digits=dp.get_precision('Credit Debit Value'))
    has_default_currency = fields.Boolean(string='Has Default Currency',compute='_default_has_default_currency')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: