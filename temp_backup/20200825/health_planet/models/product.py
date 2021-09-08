# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    division = fields.Many2one('product.division', string='Division')
    potency = fields.Char(string='Potency')
    uom_potency = fields.Many2one('product.uom', string='Unit of Potency')
    measure_amount = fields.Float(string='Measure Amount')
    uom_form = fields.Many2one('product.uom', string='Form of Measure')
    benefits = fields.Many2one('product.benefits', string='Benefits')


class ProductDivision(models.Model):

    _name = 'product.division'

    name = fields.Char(string='Division')


class ProductBenefits(models.Model):

    _name = 'product.benefits'

    name = fields.Char('Benefits')