# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"

    receipt_no = fields.Char(string='Receipt No', required=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: