# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    group_free_qty = fields.Boolean(
        "Free Qty", group='base.group_user',
        implied_group='purchase_free_qty.group_free_qty',
        help="""shows free qty field on sales and purchase order lines.""")

