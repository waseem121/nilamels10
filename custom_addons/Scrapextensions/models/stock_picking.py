from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import Warning
from datetime import datetime


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _get_accounting_data_for_valuation(self):
        journal_id, acc_src, acc_dest, acc_valuation = super(StockMove, self)._get_accounting_data_for_valuation()
        if self._context.get('from_picking_scrap'):
            if not self.product_id.categ_id.property_inventory_adjustment_scrap_account:
                raise Warning(_('Please define the Scrap(Damage) Adjustment Account in product category'))
            acc_dest = self.product_id.categ_id.property_inventory_adjustment_scrap_account.id
        return journal_id, acc_src, acc_dest, acc_valuation


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_scrap(self):
        self.ensure_one()
        lst = []
        for each in self.pack_operation_product_ids:
            lst.append((0,0,{
                'product_id':each.product_id.id,
                'uom_id':each.product_uom_id.id,
                'scrap_qty':each.product_qty
            }))
        return {
            'name': _('Scrap'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.scrap.custom',
            'view_id': self.env.ref('Scrapextensions.stock_scrap_form_view2_custom').id,
            'type': 'ir.actions.act_window',
            'context': {'default_picking_id': self.id,
                        'product_ids': self.pack_operation_product_ids.mapped('product_id').ids,
                        'default_product_scrap_line_ids':lst
                        },
            'target': 'new',
        }

class ProductScrapLines(models.Model):
    _name = 'product.scrap.line'

    product_id = fields.Many2one('product.product', string="Product")
    uom_id = fields.Many2one('product.uom', string="Unit")
    scrap_qty = fields.Float(string="Scrap Qty")
    stock_scrap_custom_id = fields.Many2one('stock.scrap.custom')


class StockScrapCustom(models.Model):
    _name = 'stock.scrap.custom'
    _order = 'id desc'

    def _get_default_scrap_location_id(self):
        return self.env['stock.location'].search([('scrap_location', '=', True), ('company_id', 'in', [self.env.user.company_id.id, False])], limit=1).id

    def _get_origin_moves(self):
        return self.picking_id and self.picking_id.move_lines.filtered(lambda x: x.product_id == self.product_id)

    def _get_default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return None

    name = fields.Char(
        'Reference',  default=lambda self: _('New'),
        copy=False, readonly=True, required=True,
        states={'done': [('readonly', True)]})
    origin = fields.Char(string='Source Document')
    product_id = fields.Many2one(
        'product.product', 'Product',
        states={'done': [('readonly', True)]})
    product_uom_id = fields.Many2one(
        'product.uom', 'Unit of Measure',
         states={'done': [('readonly', True)]})
    tracking = fields.Selection('Product Tracking', readonly=True, related="product_id.tracking")
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot',
        states={'done': [('readonly', True)]}, domain="[('product_id', '=', product_id)]")
    package_id = fields.Many2one(
        'stock.quant.package', 'Package',
        states={'done': [('readonly', True)]})
    owner_id = fields.Many2one('res.partner', 'Owner', states={'done': [('readonly', True)]})
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Picking', states={'done': [('readonly', True)]})
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'internal')]",
        required=True, states={'done': [('readonly', True)]}, default=_get_default_location_id)
    scrap_location_id = fields.Many2one(
        'stock.location', 'Scrap Location', default=_get_default_scrap_location_id,
        domain="[('scrap_location', '=', True)]", states={'done': [('readonly', True)]})
    scrap_qty = fields.Float('Quantity', default=1.0, required=True, states={'done': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')], string='Status', default="draft")
    date_expected = fields.Datetime('Expected Date', default=fields.Datetime.now)
    scrap_date = fields.Datetime('Scrap Date',default=datetime.now())
    product_scrap_line_ids = fields.One2many('product.scrap.line', 'stock_scrap_custom_id')

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            self.location_id = (self.picking_id.state == 'done') and self.picking_id.location_dest_id.id or self.picking_id.location_id.id

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id

    @api.model
    def create(self, vals):
        scrap = super(StockScrapCustom, self).create(vals)
        if scrap.product_scrap_line_ids:
            for each in scrap.product_scrap_line_ids:
                if each.scrap_qty > 0:
                    wiz_id = self.env['stock.scrap'].with_context(from_picking_scrap='True').create({
                        'product_id':each.product_id.id,
                        'product_uom_id':each.uom_id.id,
                        'lot_id':scrap.lot_id.id if scrap.lot_id else False,
                        'origin':scrap.picking_id.name,
                        'package_id':scrap.package_id.id if scrap.package_id else False,
                        'location_id':scrap.location_id.id if scrap.location_id else False,
                        'owner_id':scrap.owner_id.id if scrap.owner_id else False,
                        'move_id':scrap.move_id.id.id if  scrap.move_id else False,
                        'picking_id':scrap.picking_id.id if scrap.picking_id else False,
                        'scrap_location_id':scrap.scrap_location_id.id if scrap.scrap_location_id else False,
                        'scrap_qty':each.scrap_qty,
                        'state':scrap.state,
                        'date_expected':scrap.date_expected,
                        'scrap_date':self.scrap_date
                    })
        return scrap

    @api.multi
    def action_done(self):
        return {'type': 'ir.actions.act_window_close'}
