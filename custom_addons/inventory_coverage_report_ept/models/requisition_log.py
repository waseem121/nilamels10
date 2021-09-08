from odoo import fields,models,api
from datetime import date

class requisition_log(models.Model):
    _name='requisition.log'
    _description = "Reorder Log"
    _order = 'id desc'
    
    name=fields.Char(string='Name')
    log_date=fields.Date(string='Log Date',default= date.today())
    user_id=fields.Many2one('res.users',string='Responsible',index=True,default=lambda self:self.env.uid)
    log_type=fields.Selection([('success','Success'),('failure','Failure'),
                               ('Import_forcasted_sales','Import forecasted sales'),
                               ('Import_forcasted_sales_rule','Import forecasted sales rule'),
                               ('Export_forcasted_sales','Export forecasted sales')],string='Log Type')
    message=fields.Text(string='Result')
    line_ids=fields.One2many('requisition.log.line','log_id',string='Logs')
    state = fields.Selection([
        ('success', 'Succeed'),
        ('fail', 'Failure')
    ], string='Status',
        copy=False,readonly=True,
        help=" * Succeed: Process Done Successfully .\n"
             " * Failure: Some issue Generated while proccessing Please refer log.\n")
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('requisition.log')
        result = super(requisition_log,self).create(vals)
        return result
