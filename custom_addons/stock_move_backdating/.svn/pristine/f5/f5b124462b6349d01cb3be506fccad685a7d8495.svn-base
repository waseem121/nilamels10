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
              
class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    date_backdating = fields.Datetime(string='Actual Movement Date')

    @api.multi
    def process(self):
        force_period_date=self.date_backdating or self.pick_id.date_done or time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        check_date(self.date_backdating)
        
        print'self.pick_id.state',self.pick_id.state
        if self.pick_id.state in ['confirmed','partially_available']:        
            self.pick_id.action_assign()
            
        for pack in self.pick_id.pack_operation_ids:
            pack.write({'date': force_period_date })
            
        res = super(StockImmediateTransfer, self.with_context(force_period_date=force_period_date)).process()
        self.pick_id.write({'date_done': force_period_date})
        self._cr.commit()
        return res
