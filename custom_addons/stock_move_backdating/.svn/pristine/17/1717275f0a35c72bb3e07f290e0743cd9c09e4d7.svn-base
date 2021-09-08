# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare

import time
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = "stock.move"
    
    @api.multi
    def action_done(self):
        force_period_date = self._context.get('force_period_date', fields.Date.context_today(self))
        print "context force_period_date: ", self._context, force_period_date
        res = super(StockMove, self).action_done()
        self.write({'date': force_period_date})
        # aaa
        return res