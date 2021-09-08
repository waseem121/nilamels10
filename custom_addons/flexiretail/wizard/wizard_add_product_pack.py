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

from odoo import models, fields, api , _
from odoo.exceptions import Warning


class wizard_add_product_pack(models.TransientModel):
    _name = 'wizard.add.product_pack'

    pack_id = fields.Many2one('product.template', string="Pack", required=True)
    quantity = fields.Float(string="Quantity", required=True, default=1)

    @api.one
    def add_product_pack(self):
        if self._context.get('active_id'):
            if self.quantity > self.pack_id.pack_product_qty:
                warning_mess = {
                    'title': _('Not enough inventory!'),
                    'message' : _('You plan to sell %s of %s but you only have %s %s pack available!') % \
                        (self.quantity, self.pack_id.name, self.pack_id.pack_product_qty,self.pack_id.uom_id.name)
                }
                raise Warning(_(warning_mess['message']))
            order_lines = []
            order_id = self.env['sale.order'].browse(self._context.get('active_id'))
            order_lines = [(0, 0, {'product_id': self.env['product.product'].search([('product_tmpl_id', '=', self.pack_id.id)], limit=1).id,
                                   'product_uom_qty': self.quantity})]
            if order_lines:
                order_id.write({'order_line':order_lines})
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
