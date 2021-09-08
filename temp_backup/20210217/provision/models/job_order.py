# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

class JobOrder(models.Model):
    _name = 'job.order'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Job Order'
    
    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id
    
    name = fields.Char(string='Job Number', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    ref = fields.Char(string='Reference', copy=False)
    date = fields.Date(string='Date', copy=False, default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', string='Customer')
    salesman_id = fields.Many2one('res.users', string='Salesman')
    amount = fields.Float('Amount', digits=dp.get_precision('Credit Debit Value'), default=0.0)
    description = fields.Text(string='Description', copy=False)
    state = fields.Selection([
        ('open', 'Open'),
        ('started', 'Started'),
        ('invoiced', 'Invoiced'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='open')
    job_lines = fields.One2many('job.order.line', 'job_id', string='Job Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'open': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
        

    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('job.order') or _('New')
        result = super(JobOrder, self).create(vals)
        return result
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.salesman_id = self.partner_id.user_id and self.partner_id.user_id.id or False
            
            
    def action_start(self):
        self.state = 'started'
        
    def action_complete(self):
        self.state = 'completed'
        
    def action_cancel(self):
        self.state = 'cancel'
        
    def action_invoiced(self):
        for job in self:
            job.state = 'invoiced'
            
class JobOrderLine(models.Model):
    _name = 'job.order.line'
    _description = 'Job Order Line'
    
    @api.depends('qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.update({
                'price_subtotal': line.price_unit * line.qty,
            })
        
    
    job_id = fields.Many2one('job.order', string='Job Order', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    currency_id = fields.Many2one('res.currency', related='job_id.currency_id', store=True, related_sudo=False)
    
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    price_subtotal = fields.Monetary(compute=_compute_subtotal, string='Subtotal', readonly=True)
    
    @api.onchange('product_id')
    def _onchange_product(self):
        name,uom_id, price_unit = False, False, 0.0
        if self.product_id:
            product = self.product_id
            name = product.name
            uom_id = product.uom_so_id and product.uom_so_id.id or False
            if not uom_id:
                uom_id = product.uom_id and product.uom_id.id or False
            price_unit = product.lst_price
            
        self.name = name
        self.uom_id = uom_id
        self.price_unit = price_unit
        