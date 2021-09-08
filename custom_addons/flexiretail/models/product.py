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
from datetime import datetime
from odoo.exceptions import UserError


class product_template(models.Model):
    _inherit = "product.template"

    @api.one
    @api.depends('product_pack_ids.quantity')
    def _get_pack_product_qty(self):
        if self.is_product_pack:
            qty_lst = []
            for pack in self.product_pack_ids:
                if pack.quantity:
                    result = pack.product_id.qty_available / pack.quantity
                    qty_lst.append(int(result))
            if qty_lst:
                self.pack_product_qty = min(qty_lst)

    @api.onchange('is_product_pack')
    def onchange_is_product_pack(self):
        if self.is_product_pack:
            self.type = 'consu'

    @api.model
    def create(self, vals):
        res = super(product_template, self).create(vals)
        if res:
            if not vals.get('barcode') and self.env['sale.config.settings'].search([], limit=1, order="id desc").gen_ean13:
                barcode_str = self.env['barcode.nomenclature'].sanitize_ean("%s%s" % (res.id, datetime.now().strftime("%d%m%y%H%M")))
                res.write({'barcode' : barcode_str})
        return res
    
    is_packaging = fields.Boolean("Is Packaging")
    is_delivery = fields.Boolean("Is Delivery")
    can_not_return = fields.Boolean('Can not Return')
    is_product_pack = fields.Boolean(string="Is Product Pack")
    product_pack_ids = fields.One2many('products.pack', 'product_tmpl_id', string="Pack Products")
    pack_management = fields.Selection([('pack_product', 'Add Pack Product'),
                                       ('component_product', 'Add Components Product'),
                                       ('both', 'Add Both')], string="Management of Pack")
    pack_product_qty = fields.Float(compute='_get_pack_product_qty', string="Available Pack Product Quantity")

    @api.model
    def create_from_ui(self, product):
        if product.get('image'):
            product['image'] = product['image'].split(',')[1]
        id = product.get('id')
        if id:
            product_tmpl_id = self.env['product.product'].browse(id).product_tmpl_id
            if product_tmpl_id:
                product_tmpl_id.write(product)
        else:
            id = self.env['product.product'].create(product).id
        return id

    def assign_lot(self, data):
        if data.get('serial_no') :
           prod_id = self.env['product.product'].search([('product_tmpl_id','=',self.id)])
           if prod_id and data.get('location_id'):
               lot_id = self.env['stock.production.lot'].create({'product_id':prod_id.id,'name':data.get('serial_no')})
               update_qty_id = self.env['stock.change.product.qty'].create({'product_id' : prod_id.id,
                                                                            'location_id' : data.get('location_id'),
                                                                            'new_quantity':data.get('qty'),'lot_id' : lot_id.id})
               update_qty_id.change_product_qty()
               return True
           return False


class product_product(models.Model):
    _inherit = "product.product"

    @api.model
    def create(self, vals):
        res = super(product_product, self).create(vals)
        if res:
            if not vals.get('barcode') and self.env['sale.config.settings'].search([], limit=1, order="id desc").gen_ean13:
                barcode_str = self.env['barcode.nomenclature'].sanitize_ean("%s%s" % (res.id, datetime.now().strftime("%d%m%y%H%M")))
                res.write({'barcode' : barcode_str})
        return res

    @api.model
    def calculate_product(self):
        self._cr.execute("""
                        SELECT count(id) from product_product where product_tmpl_id in (SELECT id FROM PRODUCT_TEMPLATE where available_in_pos='t' and sale_ok='t' and active='t') and active='t';
                        """)
        total_product = self._cr.fetchall()
        return total_product

    @api.model
    def get_product_price(self, pricelist_id, lines):
        pricelist = self.env['product.pricelist'].browse(pricelist_id)
        res = []
        if pricelist:
            for line in lines:
                new_price = pricelist.price_get(line.get('id'), line.get('qty'))
                if new_price:
                    res.append({
                        'product_id': line.get('id'),
                        'new_price': new_price.get(pricelist_id)
                    })
        if res:
            return res
        return False

class generate_product_ean13(models.TransientModel):
    _name = 'generate.product.ean13'

    overwrite_ean13 = fields.Boolean(String="Overwrite Exists Ean13")

    @api.multi
    def generate_product_ean13(self):
        for rec in self.env['product.product'].browse(self._context.get('active_ids')):
            if not self.overwrite_ean13 and rec.barcode:
                continue
            rec.write({'barcode': self.env['barcode.nomenclature'].sanitize_ean("%s%s" % (rec.id, datetime.now().strftime("%d%m%y%H%M")))
            })
        return True

class products_pack(models.Model):
    _name = 'products.pack'
    _rec_name = 'product_id'

    @api.constrains('quantity')
    def check_quantity(self):
        if self.quantity < 1:
            raise UserError(_('Enter atleast 1 quantity into pack quantity.'))

    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_tmpl_id = fields.Many2one('product.template', string="Product Relation")
    quantity = fields.Float(string="Quantity", required=True, default=1)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: