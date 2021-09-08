from odoo import models, fields, api,_

class forecast_sale_rule_ept(models.Model):
    _name = "forecast.sale.rule.ept"
    _description = "Forecast Sale Rule"
    _order = "warehouse_id, period_id desc"
    
    name = fields.Char(string='Name', copy=False ,required=True, readonly=True, index=True, default=lambda self: _('New'))
    warehouse_id = fields.Many2one("stock.warehouse",string="Warehouse")
    period_id = fields.Many2one("requisition.period.ept",string="Period",copy=False)
    global_sale_ratio = fields.Float(string="Global Ratio")
    forecast_sale_rule_line_ids = fields.One2many("forecast.sale.rule.line.ept",'forecast_sale_rule_id',string="Rule line",copy=True)
    product_id=fields.Many2one(string="Products",related="forecast_sale_rule_line_ids.product_id")

    @api.multi
    @api.constrains('warehouse_id','period_id')
    def check_product_exist(self):
    
        product_ids_list = []
        rule_id_list =[]
        
        for rule in self.search([('warehouse_id','=',self.warehouse_id.id),('period_id','=',self.period_id.id)]):
            rule_id_list.append(rule.id)
            if len(rule_id_list) >1:
                raise ValueError("Same Warehouse with Same Period Already Exist")
        
        for lines in self.forecast_sale_rule_line_ids:
            if lines.product_id.id in product_ids_list:
                raise ValueError("Same Product not allowed for Multiple rule in Same Warehouse and Period")
            else:
                product_ids_list.append(lines.product_id.id)
        return product_ids_list
    
    @api.model
    def create(self, vals):
        res = super(forecast_sale_rule_ept, self).create(vals)
        rule_seq = self.env['ir.sequence'].next_by_code('forecast.sale.rule.ept') or 'New'
        res.name = rule_seq
        return res
       
    @api.multi
    def do_open_wizard(self):
        context = self._context.copy()
        context.update({'products_list': self.check_product_exist()})
        return {
                'name': 'Add Multiple Products',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'forecast.sale.rule.add.product',
                'context': context,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id':self.env.ref('inventory_coverage_report_ept.view_forecast_sales_rule_add_product').id,
                'target':'new',
            }
    