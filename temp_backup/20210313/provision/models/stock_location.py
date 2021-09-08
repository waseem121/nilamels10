# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Location(models.Model):
    _inherit = "stock.location"
    
    sequence_id = fields.Many2one('ir.sequence', 'Sequence for Invoices')
