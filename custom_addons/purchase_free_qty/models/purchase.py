from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import Warning
from datetime import datetime
from odoo.tools.float_utils import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    free_qty = fields.Float(string="Free Qty")

    @api.multi
    def _prepare_stock_moves_old(self, picking):
        res = super(PurchaseOrderLine,self)._prepare_stock_moves(picking)
        if res and self.free_qty > 0 and res[0].get('product_uom_qty'):
            res[0]['product_uom_qty'] = res[0].get('product_uom_qty') + self.free_qty
        return res
    
    @api.multi
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0

        price_unit = self._get_stock_move_price_unit()
        if self.product_qty==0:
            price_unit = 0.0
        for move in self.move_ids.filtered(lambda x: x.state != 'cancel'):
            qty += move.product_qty
        template = {
            'name': self.name or '',
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_id': False,
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'procurement_id': False,
            'origin': self.order_id.name,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
        }
        # Fullfill all related procurements with this po line
        ## custom changes here
        if self.product_qty==0.0:
            diff_quantity = (self.free_qty) - qty
        else:
            diff_quantity = (self.product_qty+self.free_qty) - qty
        for procurement in self.procurement_ids.filtered(lambda p: p.state != 'cancel'):
            # If the procurement has some moves already, we should deduct their quantity
            sum_existing_moves = sum(x.product_qty for x in procurement.move_ids if x.state != 'cancel')
            existing_proc_qty = procurement.product_id.uom_id._compute_quantity(sum_existing_moves, procurement.product_uom)
            procurement_qty = procurement.product_uom._compute_quantity(procurement.product_qty, self.product_uom) - existing_proc_qty
            if float_compare(procurement_qty, 0.0, precision_rounding=procurement.product_uom.rounding) > 0 and float_compare(diff_quantity, 0.0, precision_rounding=self.product_uom.rounding) > 0:
                tmp = template.copy()
                tmp.update({
                    'product_uom_qty': min(procurement_qty, diff_quantity),
                    'move_dest_id': procurement.move_dest_id.id,  # move destination is same as procurement destination
                    'procurement_id': procurement.id,
                    'propagate': procurement.rule_id.propagate,
                })
                res.append(tmp)
                diff_quantity -= min(procurement_qty, diff_quantity)
        if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
            template['product_uom_qty'] = diff_quantity
            res.append(template)
        return res
    
    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        vals = []
        data = {}
        for line in self:
            data[line.product_id.id] = 0
            
        for line in self:
            val = line._prepare_stock_moves(picking)
            if len(val):
                vals.append(val[0])
            else:
                if line.free_qty>0 and line.product_qty==0:
                    data[line.product_id.id] += line.free_qty
            
        for val in vals:
            val['product_uom_qty'] += data.get(val['product_id'], 0.0)
            done += moves.create(val)
        return done

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Bills Received'),
        ], string='Billing Status', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')

    @api.depends('state', 'order_line.qty_invoiced', 'order_line.qty_received', 'order_line.product_qty','order_line.free_qty')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state not in ('purchase', 'done'):
                order.invoice_status = 'no'
                continue

            if any(float_compare(line.qty_invoiced, line.product_qty if line.product_id.purchase_method == 'purchase' else line.qty_received, precision_digits=precision) == -1 for line in order.order_line):
                order.invoice_status = 'to invoice'
                if any(line.free_qty for line in order.order_line) and order.invoice_ids:
                # if any(float_compare(line.free_qty,line.qty_received,precision_digits=precision) == -1 for line in order.order_line) and order.invoice_ids:
                    order.invoice_status = 'invoiced'
                if any(float_compare(line.product_qty or line.free_qty,
                                     line.qty_received if line.product_id.purchase_method == 'purchase' else line.free_qty,
                                     precision_digits=precision) == -1 for line in order.order_line):
                    order.invoice_status = 'invoiced'
            elif all(float_compare(line.qty_invoiced, line.product_qty if line.product_id.purchase_method == 'purchase' else line.qty_received, precision_digits=precision) >= 0 for line in order.order_line) and order.invoice_ids:
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'no'
    
