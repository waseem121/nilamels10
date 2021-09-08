from odoo import fields,models,api
from odoo.tools.safe_eval import safe_eval

class res_config(models.TransientModel): 
    _inherit='stock.config.settings'
    
    requisition_sales_past_days=fields.Integer(string = 'Use Past Sales Of X Days', help = "Number of days for past sales.",default=30)
    default_requisition_backup_stock_days=fields.Integer(string = 'Keep Stock of X Days',help = "Default Backup stock days",default=60)
    use_forecasted_sales_for_requisition = fields.Boolean(string='Use Forecasted Sales',help = "If Set use Forecasted Sales otherwise use Past Sales.",default=False)
    auto_forecast_use_warehouse = fields.Boolean(string="Forecast Sales for Only Mapped Warehouses",help = "Use Warehouse from Product when Auto Create Forecasted Sales.",default=False)
    use_out_stock_percent = fields.Boolean(string="Out of Stock Ratio",help = "Consider product in recommendation only if out of stock days are more than Out of stock ratio (%)",default=False)
    out_stock_percent = fields.Float(string="Out of Stock Percent",help='Consider product in recommendation only if out of stock days are more than "Out of stock ratio (%)"')
    
    
    @api.model
    def get_default_values_coverage_report_ept(self, fields):
        res = {}
        params = self.env['ir.config_parameter'].sudo()
        res.update(
                    use_forecasted_sales_for_requisition=safe_eval(params.get_param('inventory_coverage_report_ept.use_forecasted_sales_for_requisition',default='False')),
                    requisition_sales_past_days=safe_eval(params.get_param('inventory_coverage_report_ept.requisition_sales_past_days',default=30)),
                    default_requisition_backup_stock_days=safe_eval(params.get_param('inventory_coverage_report_ept.default_requisition_backup_stock_days',default=60)),
                    auto_forecast_use_warehouse=safe_eval(params.get_param('inventory_coverage_report_ept.auto_forecast_use_warehouse',default='False')),
                    use_out_stock_percent=safe_eval(params.get_param('inventory_coverage_report_ept.use_out_stock_percent',default='False')),
                    out_stock_percent=safe_eval(params.get_param('inventory_coverage_report_ept.out_stock_percent',default='0')),                    
                   )
        return res
    

    @api.multi
    def set_values_coverage_report_ept(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("inventory_coverage_report_ept.use_forecasted_sales_for_requisition",repr(self.use_forecasted_sales_for_requisition))
        ICPSudo.set_param("inventory_coverage_report_ept.requisition_sales_past_days",repr(self.requisition_sales_past_days))
        ICPSudo.set_param("inventory_coverage_report_ept.default_requisition_backup_stock_days",repr(self.default_requisition_backup_stock_days))
        ICPSudo.set_param("inventory_coverage_report_ept.auto_forecast_use_warehouse",repr(self.use_forecasted_sales_for_requisition))
        ICPSudo.set_param("inventory_coverage_report_ept.use_out_stock_percent",repr(self.use_out_stock_percent))
        ICPSudo.set_param("inventory_coverage_report_ept.out_stock_percent",repr(self.out_stock_percent))
        
    """
    @api.multi
    def set_requisition_sales_past_days(self):
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'requisition_sales_past_days', self.requisition_sales_past_days)
      
    @api.multi
    def set_default_requisition_backup_stock_days(self):
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'default_requisition_backup_stock_days', self.default_requisition_backup_stock_days)
    
    
    @api.multi
    def set_use_forecasted_sales_for_requisition(self):
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'use_forecasted_sales_for_requisition', self.use_forecasted_sales_for_requisition)


    @api.multi
    def set_auto_forecast_use_warehouse(self):
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'auto_forecast_use_warehouse', self.auto_forecast_use_warehouse)
           
    
    @api.multi
    def set_use_out_stock_percent(self):
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'use_out_stock_percent', self.use_out_stock_percent)
        
    @api.multi
    def set_out_stock_percent(self):
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'out_stock_percent', self.out_stock_percent)     
            
            """     