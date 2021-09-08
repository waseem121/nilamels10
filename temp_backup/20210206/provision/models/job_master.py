# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

class JobMaster(models.Model):
    _name = 'job.master'
    
    name = fields.Char(string='Job Number', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    ref = fields.Char(string='Reference', copy=False)
    date = fields.Date(string='Date', copy=False, default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', string='Customer')
    salesman_id = fields.Many2one('res.users', string='Salesman')
    amount = fields.Float('Amount', digits=dp.get_precision('Product Price'), default=0.0)
    description = fields.Text(string='Description', copy=False)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('job.master') or _('New')
        result = super(JobMaster, self).create(vals)
        return result
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.salesman_id = self.partner_id.user_id and self.partner_id.user_id.id or False