# -*- coding: utf-8 -*-

from openerp import models, api, fields, exceptions


class ResCompany(models.Model):
    _inherit = 'res.company'

    discount_type = fields.Selection([
        ('per', 'Percentage'),
        ('amount', 'Amount')
    ], default='per', string="Discount Type",
    help="Select which type of discount you want to apply for pos order.")


ResCompany()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
