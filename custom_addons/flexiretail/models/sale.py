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

from odoo import models, api, _
from odoo.exceptions import Warning
from odoo.addons.sale_stock.models.sale_order import SaleOrderLine


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.category_id.id != self.product_uom.category_id.id):
            vals['product_uom'] = self.product_id.uom_id

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product), product.taxes_id, self.tax_id)
        self.update(vals)

        # check selected pack product's available stock
        if product.is_product_pack:
            if self.product_uom_qty > product.pack_product_qty:
                warning_mess = {'title': _('Not enough inventory!'),
                                'message' : _('You plan to sell %s of %s but you only have %s %s pack available!') % \
                                            (self.product_uom_qty, product.name, product.pack_product_qty, product.uom_id.name)
                }
                return {'warning': warning_mess}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            if product.sale_line_warn == 'block':
                self.product_id = False
            return {'warning': warning}
        return {'domain': domain}

@api.multi
def _get_delivered_qty(self):
    """Computes the delivered quantity on sale order lines, based on done stock moves related to its procurements
    """
    self.ensure_one()
    super(SaleOrderLine, self)._get_delivered_qty()
    qty = 0.0
    # calculate the delivered quantity of pack product in order line
    if self.product_id.is_product_pack and self.product_id.product_pack_ids:
        for packline in self.product_id.product_pack_ids[0]:
            for move in self.procurement_ids.mapped('move_ids').filtered(lambda r: r.state == 'done' and not r.scrapped):
                if move.product_id.id == packline.product_id.id:
                    if move.location_dest_id.usage == "customer":
                        qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom) / packline.quantity
                    elif move.location_dest_id.usage == "internal" and move.to_refund_so:
                        qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom) / packline.quantity
    else:
        for move in self.procurement_ids.mapped('move_ids').filtered(lambda r: r.state == 'done' and not r.scrapped):
            if move.location_dest_id.usage == "customer":
                qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom)
            elif move.location_dest_id.usage == "internal" and move.to_refund_so:
                qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom)
    return qty
    
SaleOrderLine._get_delivered_qty = _get_delivered_qty
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
