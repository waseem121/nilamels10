# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time

def check_date(date):
    now = fields.Datetime.now()
    if date > now:
        raise UserError(
            _("You can not process an actual "
              "movement date in the future."))
              
class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    date_backdating = fields.Datetime(string='Actual Movement Date')
    
    @api.one
    def _process(self, cancel_backorder=False):
        force_period_date=self.date_backdating or time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        check_date(self.date_backdating)
        for pack in self.pick_id.pack_operation_ids:
            pack.write({'date':self.date_backdating}) ## added 
        res = super(StockBackorderConfirmation, self.with_context(force_period_date=force_period_date))._process(cancel_backorder=cancel_backorder)    
        self.pick_id.write({'date_done':self.date_backdating})
        return res