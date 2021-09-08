from odoo import models, fields, api


class forecast_sale_rule_line_ept(models.Model):
    _name = "forecast.sale.rule.line.ept"
    _description="Forecast Sale Rule Line"
    _order = "product_id"
           
    @api.multi
    @api.constrains('product_id')
    def check_product(self):
        for record in self:
            record.forecast_sale_rule_id.check_product_exist()

    forecast_sale_rule_id = fields.Many2one("forecast.sale.rule.ept",string="Forecast Sale Rule",ondelete='cascade',index=True, copy=False)
    product_id = fields.Many2one("product.product",string="Product")
    sale_ratio = fields.Float(string="Sale Ratio")
    
    