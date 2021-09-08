
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

from openerp import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT
from itertools import groupby
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = 'product.product'


    def _compute_invoices(self):
        quntity = 0
        if self.id:
            invoices = self.env['account.invoice.line'].search([('product_id', '=', self.id)])
            for invoice in invoices:
                quntity += invoice.quantity
        self.invoices_count = quntity

    def _compute_sale_order(self):
        quantity = 0
        if self.id:
            orders = self.env['sale.order.line'].search([('state', 'in', ['sale', 'done']),('product_id', '=', self.id)])
            for order in orders:
                quantity += order.qty_invoiced
        self.sales_order_count = quantity

    # @api.multi
    # def _sales_count(self):
    #     quntity = 0
    #     if self.id:
    #         orders = self.env['sale.order.line'].search(
    #             [('state', 'in', ['sale', 'done']), ('product_id', '=', self.id)])
    #         for order in orders:
    #             quntity += order.qty_invoiced
    #     self.sales_count = quntity
    invoices_count = fields.Float(string='Invoice lines', readonly=True, compute='_compute_invoices')
    sales_order_count = fields.Float(string='Sales', readonly=True, compute='_compute_sale_order')