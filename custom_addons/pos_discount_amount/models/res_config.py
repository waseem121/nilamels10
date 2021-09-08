# -*- coding: utf-8 -*-
from odoo import fields, models, api


class PosConfiguration(models.TransientModel):
    _inherit = 'pos.config.settings'

    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    discount_type = fields.Selection([
        ('per', 'Percentage'),
        ('amount', 'Amount')
    ], related='company_id.discount_type', string="Discount Type",
        help="Select which type of discount you want to apply for pos order.")

    @api.onchange('discount_type')
    def onchange_discount_type(self):
        self.discount_type = self.discount_type
        self.company_id.discount_type = self.discount_type


PosConfiguration()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
