# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from openerp import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from odoo.addons import decimal_precision as dp


class product_product(models.Model):
    _inherit = "product.product"
    
    virtual_available_inv = fields.Float(
        'Forecast Quantity Inv', compute='_compute_quantities',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Forecast quantity (computed as Quantity On Hand "
             "- Outgoing - Draft Invoice qty)\n"
             "In a context with a single Stock Location, this includes "
             "goods stored in this location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods stored in the Stock Location of this Warehouse, or any "
             "of its children.\n"
             "Otherwise, this includes goods stored in any Stock Location "
             "with 'internal' type.")
    
    # inherited to add virtual_available_inv
    @api.depends('stock_quant_ids', 'stock_move_ids')
    def _compute_quantities(self):
        res = self._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
        for product in self:
            product.qty_available = res[product.id]['qty_available']
            product.incoming_qty = res[product.id]['incoming_qty']
            product.outgoing_qty = res[product.id]['outgoing_qty']
            product.virtual_available = res[product.id]['virtual_available']
            product.virtual_available_inv = res[product.id]['virtual_available_inv']
    
    @api.multi
    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
        dates_in_the_past = False
        if to_date and to_date < fields.Datetime.now():  # Only to_date as to_date will correspond to qty_available
            dates_in_the_past = True

        domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc
        if self._context.get('location_id'):
            domain_quant += [('location_id', '=', self._context.get('location_id'))]
            domain_move_in += [('location_id', '=', self._context.get('location_id'))]
            domain_move_out += [('location_id', '=', self._context.get('location_id'))]
        if lot_id:
            domain_quant += [('lot_id', '=', lot_id)]
        if owner_id:
            domain_quant += [('owner_id', '=', owner_id)]
            domain_move_in += [('restrict_partner_id', '=', owner_id)]
            domain_move_out += [('restrict_partner_id', '=', owner_id)]
        if package_id:
            domain_quant += [('package_id', '=', package_id)]
        if dates_in_the_past:
            domain_move_in_done = list(domain_move_in)
            domain_move_out_done = list(domain_move_out)
        if from_date:
            domain_move_in += [('date', '>=', from_date)]
            domain_move_out += [('date', '>=', from_date)]
        if to_date:
            domain_move_in += [('date', '<=', to_date)]
            domain_move_out += [('date', '<=', to_date)]

        Move = self.env['stock.move']
        Quant = self.env['stock.quant']
        domain_move_in_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_move_in
        domain_move_out_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_move_out
        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in
                            Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'],
                                            orderby='id'))
        moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in
                             Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'],
                                             orderby='id'))
        quants_res = dict((item['product_id'][0], item['qty']) for item in
                          Quant.read_group(domain_quant, ['product_id', 'qty'], ['product_id'], orderby='id'))
        if dates_in_the_past:
            # Calculate the moves that were done before now to calculate back in time (as most questions will be recent ones)
            domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
            domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
            moves_in_res_past = dict((item['product_id'][0], item['product_qty']) for item in
                                     Move.read_group(domain_move_in_done, ['product_id', 'product_qty'], ['product_id'],
                                                     orderby='id'))
            moves_out_res_past = dict((item['product_id'][0], item['product_qty']) for item in
                                      Move.read_group(domain_move_out_done, ['product_id', 'product_qty'],
                                                      ['product_id'], orderby='id'))

        res = dict()
        for product in self.with_context(prefetch_fields=False):
            res[product.id] = {}
            if dates_in_the_past:
                qty_available = quants_res.get(product.id, 0.0) - moves_in_res_past.get(product.id,
                                                                                        0.0) + moves_out_res_past.get(
                    product.id, 0.0)
            else:
                qty_available = quants_res.get(product.id, 0.0)
            res[product.id]['qty_available'] = float_round(qty_available, precision_rounding=product.uom_id.rounding)
            res[product.id]['incoming_qty'] = float_round(moves_in_res.get(product.id, 0.0),
                                                          precision_rounding=product.uom_id.rounding)
            res[product.id]['outgoing_qty'] = float_round(moves_out_res.get(product.id, 0.0),
                                                          precision_rounding=product.uom_id.rounding)
            virtual_available = float_round(
                qty_available + res[product.id]['incoming_qty'] - res[product.id]['outgoing_qty'],
                precision_rounding=product.uom_id.rounding)
            res[product.id]['virtual_available'] = float_round(
                qty_available + res[product.id]['incoming_qty'] - res[product.id]['outgoing_qty'],
                precision_rounding=product.uom_id.rounding)
            
#            print"res[product.id]['incoming_qty']: ",res[product.id]['incoming_qty']
            location_id = self.env.context.get('location', False)
            draft_inv_qty = self.get_draft_invoice_qty(product,location_id)
            res[product.id]['virtual_available_inv'] = (float_round(qty_available - res[product.id]['outgoing_qty'],
                precision_rounding=product.uom_id.rounding)) - draft_inv_qty
                
        return res
    
    def get_draft_invoice_qty(self,  product, location):
        if not location:
            return 0.0
        if isinstance(location, (int, long)):
            location_ids = [location]
        else:
            location_ids = location
            
        self._cr.execute("select l.id from account_invoice_line l, account_invoice a where l.invoice_id=a.id "\
            "and a.state in ('draft','proforma','proforma2') and a.type in ('out_invoice', 'out_refund') and l.product_id=%s and "\
            "a.location_id in %s",(product.id,tuple(location_ids)))
        res = self._cr.fetchall()
        if not res:
            return 0.0
        line_ids = [r[0] for r in res]
        in_qty, out_qty, total_draft_qty = 0.0,0.0,0.0
        line_obj = self.env['account.invoice.line']
        for line in line_obj.browse(line_ids):
            qty = line.quantity
            if line.uom_id.uom_type == 'bigger':
                qty = qty * line.uom_id.factor_inv
            if line.uom_id.uom_type == 'smaller':
                qty = qty / line.uom_id.factor_inv
            
            if line.invoice_id.refund_without_invoice:
                in_qty += qty
            else:
                out_qty += qty
      
        total_draft_qty =out_qty-in_qty
        return total_draft_qty
    
class ProductPriceHistory(models.Model):
    _inherit = 'product.price.history'
    
    # adding transaction date to the cost price history
    @api.model
    def create(self, vals):
        force_period_date = self._context.get('force_period_date', False)
        if force_period_date:
            vals['datetime'] = force_period_date
        return super(ProductPriceHistory, self).create(vals)