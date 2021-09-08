# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##################################################################################

from odoo import models, fields, api
from odoo.exceptions import Warning


class MultipleMOS(models.Model):
    _name = 'multiple.mos.wizard'

    raw_meterial_id = fields.Many2one(comodel_name='product.product', string='Raw Material', required=True)
    mfg_product_ids = fields.One2many(comodel_name='multiple.mos.products', inverse_name='mos_id')

    @api.onchange('raw_meterial_id')
    def find_products(self):
        if self.raw_meterial_id:
            boms = self.env['mrp.bom'].search([])
            self.env['multiple.mos.products'].search([('mos_id', '=', self.id)]).unlink()
            for each in boms:
                if each.bom_line_ids:
                    if each.bom_line_ids[0].product_id.id == self.raw_meterial_id.id:
                        if len(each.bom_line_ids.ids) == 1:
                            self.env['multiple.mos.products'].create({'mos_id': self.id,
                                                                      'bom_id': each.id,
                                                                      'product_qty': 0.0, })
            return {'type': "ir.actions.act_window",
                    'name': "Multiple MO's",
                    'res_model': "multiple.mos.wizard",
                    'view_mode': "form",
                    'res_id': self.id,
                    'target': 'new'}

    def create_mos(self):
        flag = False
        for each in self.mfg_product_ids:
            if each.product_qty > 0:
                if self.env['mrp.production'].create({'product_id': each.product_id.id,
                                                      'product_qty': each.product_qty,
                                                      'bom_id': each.bom_id.id,
                                                      'product_uom_id': each.product_uom_id.id}):
                    flag = True
        if not flag:
            raise Warning("There is no manufacturing order created.")


class ProductsManufacture(models.Model):
    _name = 'multiple.mos.products'

    mos_id = fields.Many2one(comodel_name='multiple.mos.wizard')
    product_id = fields.Many2one(comodel_name='product.product', string='Product',
                                 related='product_tmpl_id.product_variant_id',
                                 readonly=True)
    product_uom_id = fields.Many2one(comodel_name='product.uom', related="product_id.uom_id", required=True)
    product_tmpl_id = fields.Many2one(comodel_name='product.template', string='Product Template',
                                      required=True, related='bom_id.product_tmpl_id', readonly=True)
    product_qty = fields.Float('Quantity To Produce', default=1.0, required=True)
    bom_id = fields.Many2one(comodel_name='mrp.bom', context="{'product': True}", string='Bill of Material',
                             required=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
