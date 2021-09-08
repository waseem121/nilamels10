from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import Warning
from datetime import datetime
from odoo.tools.float_utils import float_compare

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    free_qty = fields.Float(string="Free Qty")
    
    @api.onchange('free_qty')
    def _onchange_free_qty(self):
        if float(self.quantity) == 0.0:
            self.price_unit = 0.0
            self.quantity = 0.0
        if float(self.free_qty) > 0.0:
            self.quantity = 0.0
    
    def _create_stock_moves_transfer(self, picking, zero_stock_product_ids):
        move_obj = self.env['stock.move']
        for each_line in self:
            if each_line.product_id.id in zero_stock_product_ids:
                continue
            location_id = picking.location_id.id
            location_dest_id = each_line.invoice_id.partner_id.property_stock_customer.id
            if each_line.invoice_id.refund_without_invoice:
                location_id = picking.location_id.id
                location_dest_id = picking.picking_type_id.default_location_dest_id.id
                
#            if not picking.location_id.usage=='customer':
#                available_qty = each_line.product_id.with_context(
#                    {'location': picking.location_id.id, 'compute_child': False}).qty_available
#                if available_qty < (each_line.quantity + each_line.free_qty):
#                    print"less qty continue"
#                    continue
            
            template = {
                'name': each_line.name or '',
                'product_id': each_line.product_id.id,
                'product_uom': each_line.uom_id.id,
                'location_id':location_id,
                'location_dest_id':location_dest_id,
                'picking_id': picking.id,
                'product_uom_qty': each_line.quantity+each_line.free_qty,
                'company_id': each_line.invoice_id.company_id.id,
                'price_unit': each_line.price_unit,
                'picking_type_id': picking.picking_type_id.id,
                'lot_ids': [(6, 0, [x.id for x in each_line.lot_ids])],
                'warehouse_id': picking.picking_type_id.warehouse_id.id,
                'account_invoice_line_id': each_line.id,
            }
            move_obj |= move_obj.create(template)
        return move_obj
    
    def _create_stock_moves_transfer_no_stock(self, picking, zero_stock_product_ids):
        move_obj = self.env['stock.move']
        for each_line in self:
            if each_line.product_id.id in zero_stock_product_ids:
                location_id = picking.location_id.id
                location_dest_id = each_line.invoice_id.partner_id.property_stock_customer.id
                if each_line.invoice_id.refund_without_invoice:
                    location_id = picking.location_id.id
                    location_dest_id = picking.picking_type_id.default_location_dest_id.id

                template = {
                    'name': each_line.name or '',
                    'product_id': each_line.product_id.id,
                    'product_uom': each_line.uom_id.id,
                    'location_id':location_id,
                    'location_dest_id':location_dest_id,
                    'picking_id': picking.id,
                    'product_uom_qty': each_line.quantity+each_line.free_qty,
                    'company_id': each_line.invoice_id.company_id.id,
                    'price_unit': each_line.price_unit,
                    'picking_type_id': picking.picking_type_id.id,
                    'lot_ids': [(6, 0, [x.id for x in each_line.lot_ids])],
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                    'account_invoice_line_id': each_line.id,
                }
                move_obj |= move_obj.create(template)
        return move_obj


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(AccountInvoice,self)._prepare_invoice_line_from_po_line(line)
        if data.get('quantity'):
            data['quantity'] = data['quantity'] - line.free_qty
            data['free_qty'] = line.free_qty
            
        price_unit = line.price_subtotal / ((line.product_qty + line.free_qty) * (line.product_uom.factor_inv))
        if self.currency_id.id != line.order_id.currency_id.id:
            if line.order_id.exchange_rate:
                price_unit = line.order_id.currency_id.with_context(date=self.date_invoice).compute_custom(price_unit, self.currency_id, line.order_id.exchange_rate, round=False)
            else:
                price_unit = line.order_id.currency_id.with_context(date=self.date_invoice).compute_custom(price_unit, self.currency_id, line.order_id.exchange_rate, round=False)
        else:
#            price = line.order_id.currency_id.with_context(date=self.date_invoice).compute(line.price_unit, self.currency_id, round=False)
            price_unit = line.order_id.currency_id.with_context(date=self.date_invoice).compute(price_unit, self.currency_id, round=False)
        data['price_unit'] = price_unit
        print"price_unit: ",price_unit
        return data
    
    
    # to add the Free qty changes
    @api.multi
    def action_create_sales_order(self):
        warehouse = self.location_id.get_warehouse()
        if not warehouse:
            warehouse = self.env['stock.warehouse'].search([('lot_stock_id','=',self.location_id.id)],limit=1)
        so_vals = {'partner_id':self.partner_id.id,
                'date_order':self.date_invoice,
                'user_id':self.user_id.id,
                'location_id':self.location_id.id,
                'pricelist_id':self.pricelist_id.id,
                'team_id':self.team_id and self.team_id.id or False,
                'warehouse_id':warehouse.id,
                'picking_policy':'direct',
                'invoice_status':'no',
                'state':'draft',
                
        }
        saleorder = self.env['sale.order'].create(so_vals)
        for line in self.invoice_line_ids:
            line_vals = {
                'product_id':line.product_id.id,
                'product_uom_qty':line.quantity,
                'free_qty':line.free_qty,
                'product_uom':line.uom_id.id,
                'price_unit':line.price_unit,
                'name':line.name,
                'order_id':saleorder.id
            }
            so_line = self.env['sale.order.line'].create(line_vals)
            line.write({'sale_line_ids':[(6, 0, [so_line.id])]})
        
        context = self.env.context.copy()
        context.update({'no_picking':True})
        saleorder.with_context(context).action_confirm()    # this gets called of multi_uom_pricelist
        return True