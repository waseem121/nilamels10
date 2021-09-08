# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time

class Quant(models.Model):
    _inherit = "stock.quant"
    
    @api.model
    def create(self, vals):
        if self._context.get('force_period_date',False):
            vals['in_date'] = self._context['force_period_date']

        return super(Quant, self).create(vals)
    
        
