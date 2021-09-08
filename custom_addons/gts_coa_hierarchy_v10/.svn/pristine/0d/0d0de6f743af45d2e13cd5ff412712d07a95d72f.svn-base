from odoo import fields, models


class AccountBalanceReport(models.TransientModel):
    _inherit = 'account.balance.report'

    level = fields.Selection([('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5')], string='Account Level')
