# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    # global_discount = fields.Selection([
    #     (0, 'Disable Purchase Discount'), (1, 'Enable Purchase Discount')],
    #     string="Purchase Discount",
    #     implied_group='purchase_discount.group_purchase_discount')

    group_purchase_discount = fields.Boolean(
        "Purchase Discount", group='base.group_user',
        implied_group='purchase_discount.group_purchase_discount',
        help="""Purchase Discount.""")

