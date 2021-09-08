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
import time


class product_cross_selling(models.Model):
    _name = 'product.cross.selling'

    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('available_in_pos', '=', True)]")
    lines = fields.One2many('product.cross.selling.line', 'cross_sell_id', 'Lines')
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('product_cross_selling', 'unique(product_id)', 'This product is already configured!'),
    ]

    @api.model
    def find_cross_selling_products(self, product_id):
        lines = self.env['product.cross.selling.line'].search([('cross_sell_id.product_id', '=', product_id),
                                                               ('is_active', '=', 'yes'),
                                                               ('cross_sell_id.active', '=', True)])
        if not lines:
            return False
        cross_products = []
        for l in lines:
            cross_products.append([l.product_id.id, l.price_subtotal])
        return cross_products


class product_cross_selling_line(models.Model):
    _name = 'product.cross.selling.line'

    @api.one
    @api.depends('discount', 'price', 'discount_type')
    def _compute_price(self):
        if self.discount_type:
            if self.discount_type == 'fixed':
                self.price_subtotal = self.price - self.discount
            else:
                disc = (self.price * self.discount) / 100
                self.price_subtotal = self.price - disc

    cross_sell_id = fields.Many2one('product.cross.selling', string='Cross Selling')
    product_id = fields.Many2one('product.product', string='Product')
    is_active = fields.Selection([('yes', 'Yes'),
                                  ('no', 'No')],
                                 string='Active', default='yes')
    discount_type = fields.Selection([('fixed', 'Fixed'),
                                      ('percentage', 'Percentage')],
                                     string='Discount Type', default='percentage')
    discount = fields.Float('Discount')
    price = fields.Float('Price')
    price_subtotal = fields.Float(string='Sub Total', readonly=True,
                                  compute='_compute_price')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            if self.product_id.attribute_value_ids:
                self.price = self.product_id.lst_price
            else:
                self.price = self.product_id.list_price

    @api.onchange('discount')
    def onchange_discount(self):
        if self.discount and self.discount_type and \
                        self.discount_type == 'percentage':
            if self.discount > 100:
                self.discount = 0


class product_cross_selling_history(models.Model):
    _name = 'product.cross.selling.history'
    _order = 'date desc'

    order_id = fields.Many2one('pos.order', 'POS Order')
    user_id = fields.Many2one('res.users', 'Cashier')
    product_ids = fields.Many2many('product.product', 'rel_pcsh_product',
                                   'history_id', 'product_id', string='Products')
    date = fields.Date('Date')
    sell_time = fields.Char('Time')

