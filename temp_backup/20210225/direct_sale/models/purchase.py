from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'min_date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
        }
        
    
class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    # calling compute custom to use the purchase order exchange rate
    @api.multi
    def _get_stock_move_price_unit(self):
        self.ensure_one()
        line = self[0]
        order = line.order_id
#        price_unit = line.price_unit
        price_unit = line.price_subtotal / ((line.product_qty + line.free_qty) * (line.product_uom.factor_inv))
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id, partner=line.order_id.partner_id
            )['total_excluded']
        if line.product_uom.id != line.product_id.uom_id.id:
#            print"line.product_uom name: ",line.product_uom.name
#            print"line.product_uom factor: ",line.product_uom.factor
#            print"line.product_id.uom_id name: ",line.product_id.uom_id.name
#            print"line.product_id.uom_id.factor: ",line.product_id.uom_id.factor
#            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
#            print"price_unit: ",price_unit
            
            price_unit = line.price_subtotal / ((line.product_qty + line.free_qty) * (line.product_uom.factor_inv))
        if order.currency_id != order.company_id.currency_id:
            if order.exchange_rate:
                price_unit = order.currency_id.compute_custom(price_unit, order.company_id.currency_id, order.exchange_rate, round=False)
            else:
                price_unit = order.currency_id.compute(price_unit, order.company_id.currency_id, round=False)
        return price_unit