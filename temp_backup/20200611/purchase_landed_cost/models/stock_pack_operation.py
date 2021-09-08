# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import api, fields, models, _

class PackOperation(models.Model):
    _inherit = "stock.pack.operation"
    
    # inherited to add the qty done by default
    @api.model
    def create(self, vals):
        vals['ordered_qty'] = vals.get('product_qty')
        vals['qty_done'] = vals.get('product_qty')
        return super(PackOperation, self).create(vals)
