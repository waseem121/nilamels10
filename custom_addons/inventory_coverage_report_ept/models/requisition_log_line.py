from odoo import models,fields

class requisition_log_line(models.Model):
    _name='requisition.log.line'
    _description = "Reorder Log Line"
    
    log_type=fields.Selection([
                               ('Import_forcasted_sales','Import forecasted sales'),
                               ('Export_forcasted_sales','Export forecasted sales'),
                               ('Import_forcasted_sales_rule','Import forcasted sales rule')],string='Log Type')
    message=fields.Text(string='Message')
    log_id=fields.Many2one('requisition.log',string='Log')
    