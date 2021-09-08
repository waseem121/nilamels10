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

from odoo import models, api, _
from odoo.tools.amount_to_text_en import amount_to_text

class account_voucher(models.Model):
    _inherit = 'account.voucher'

    @api.one
    def get_amount_word(self):
        amount_text = amount_to_text(self.amount, currency=self.currency_id.name)
        if self.currency_id.name == 'KWD':
            amount_text = amount_text.replace('Cent', 'Fils')
            amount_text = amount_text.replace('Cents', 'Fils')
        return str(amount_text)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: