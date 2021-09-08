# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.depends('quant_ids')
    def _compute_default_location(self):
        for lot in self:
            if lot.quant_ids:
                for quant in lot.quant_ids:
                    if quant.location_id.usage == 'internal':
                        print "inside for"
                        lot.location_id = quant.location_id.id


    location_id = fields.Many2one(
        'stock.location', 'Default Quant Location', compute='_compute_default_location', store=True)

    @api.multi
    @api.depends('name', 'life_date')
    def name_get(self):
        result = []
        for lot in self:
            name = lot.name
            if lot.life_date:
                name += ', ' + str(lot.life_date[:10])
            result.append((lot.id, name))
        return result
