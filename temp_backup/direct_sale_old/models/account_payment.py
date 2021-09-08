# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp

class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"
    
    salesman_id = fields.Many2one('res.partner', string='Salesman',domain=[('is_salesman', '=', True)])
    collector_id = fields.Many2one('res.partner', string='Collector',domain=[('is_collector', '=', True)])
   


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: