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

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockScrap(models.Model):
    _inherit = 'stock.scrap'
    
    scrap_date = fields.Datetime('Scrap Date')
    
    # inherited to add the scrap date in moves
    @api.multi
    def do_scrap(self):
        for scrap in self:
            moves = scrap._get_origin_moves() or self.env['stock.move']
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            user = self.env['res.users'].browse(self.env.uid)
            allow_negative = user.has_group('direct_sale.group_allow_negative_qty')
            if move.product_id.type == 'product' and not allow_negative:
                quants = self.env['stock.quant'].quants_get_preferred_domain(
                    move.product_qty, move,
                    domain=[
                        ('qty', '>', 0),
                        ('lot_id', '=', self.lot_id.id),
                        ('package_id', '=', self.package_id.id)],
                    preferred_domain_list=scrap._get_preferred_domain())
                if any([not x[0] for x in quants]):
                    raise UserError(_('You cannot scrap a move without having available stock for %s. You can correct it with an inventory adjustment.') % move.product_id.name)
                self.env['stock.quant'].quants_reserve(quants, move)
            if allow_negative:
                move.action_assign()
                move.force_assign()
                move.action_confirm()
            move.action_done()
            scrap.write({'move_id': move.id, 'state': 'done', 
                'date':scrap.scrap_date,'date_expected':scrap.scrap_date,
                'date_expected':scrap.scrap_date})
            moves.recalculate_move_state()
        return True