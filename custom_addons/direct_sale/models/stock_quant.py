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

from datetime import datetime

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_round
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

# adding user specified date as transaction date in moves and picking
class Quant(models.Model):
    _inherit = "stock.quant"

    @api.multi
    def _get_latest_move(self):
        history_ids = self.history_ids
        if len(history_ids):
            latest_move = self.history_ids[0]
            for move in self.history_ids:
                if move.date > latest_move.date:
                    latest_move = move
        else:
            move_ids = self.env['stock.move'].search([('product_id','=',self.product_id.id),
                        ('location_dest_id','=',self.location_id.id)])
            if not len(move_ids):
                move_ids = self.env['stock.move'].search([('product_id','=',self.product_id.id),
                            ('location_id','=',self.location_id.id)])
            if len(move_ids):
                latest_move = move_ids[0]
        return latest_move
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
