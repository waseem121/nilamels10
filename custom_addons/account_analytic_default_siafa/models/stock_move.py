from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = "stock.move"
    
    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(StockMove,self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        if not res:
            return res
        location_id = (self.location_id.usage == 'internal' and self.location_id.id) or \
                        (self.location_dest_id.usage == 'internal' and self.location_dest_id.id) or False
        res[0][2]['location_id'] = location_id
        res[1][2]['location_id'] = location_id
        return res