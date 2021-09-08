from openerp import api, fields, models, _

class PosOrderLine(models.Model):

    _inherit = "pos.order.line"

    promotion = fields.Boolean('Promotion Gift')
    reason = fields.Char('Reason', readonly=1)
    orig_price_unit = fields.Float(string='Orig Unit Price', digits=0)

