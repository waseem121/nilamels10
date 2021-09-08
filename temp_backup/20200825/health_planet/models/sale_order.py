


from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    instructor_id = fields.Many2one('res.partner', string='Doctor')