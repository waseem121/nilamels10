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

# from openerp.osv import osv,fields
from openerp import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, Warning
from odoo import SUPERUSER_ID
import pytz
from collections import defaultdict
import time
import odoo.addons.decimal_precision as dp


class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model
    def disp_prod_stock(self, product_id, shop_id):
        stock_line = []
        total_qty = 0
        shop_qty = 0
        quant_obj = self.env['stock.quant']
        for warehouse_id in self.search([]):
            product_qty = 0.0
            ware_record = warehouse_id
            location_id = ware_record.lot_stock_id.id
            if shop_id:
                loc_ids1 = self.env['stock.location'].search(
                    [('location_id', 'child_of', [shop_id])])
                stock_quant_ids1 = quant_obj.search([('location_id', 'in', [
                                                    loc_id.id for loc_id in loc_ids1]), ('product_id', '=', product_id)])
                for stock_quant_id1 in stock_quant_ids1:
                    shop_qty = stock_quant_id1.qty

            loc_ids = self.env['stock.location'].search(
                [('location_id', 'child_of', [location_id])])
            stock_quant_ids = quant_obj.search([('location_id', 'in', [
                                               loc_id.id for loc_id in loc_ids]), ('product_id', '=', product_id)])
            for stock_quant_id in stock_quant_ids:
                product_qty += stock_quant_id.qty
            stock_line.append([ware_record.name, product_qty,
                               ware_record.lot_stock_id.id])
            total_qty += product_qty
        return stock_line, total_qty, shop_qty


class stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'

    remaining_qty = fields.Float("Remaining Qty", compute="_compute_remaining_qty")
    active = fields.Boolean(string="Active", default=True)

    @api.model
    def create(self, vals):
        if not vals.get('life_date'):
            raise Warning(_('Can\'t create lot without life date.'))
        return super(stock_production_lot, self).create(vals)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('loc_id') and not self._context.get('direct_sale') and not self._context.get('from_invoice'):
            quant_ids = self.env['stock.quant'].search([('location_id', '=', self._context.get('loc_id'))])
            lot_ids = self.search([('quant_ids', 'in', [q.id for q in quant_ids])]).filtered(
                lambda l: l.remaining_qty > 0)
            if lot_ids:
                args += [('id', 'in', [lot.id for lot in lot_ids])]
        elif self._context.get('direct_sale') and self._context.get('product_id') and self._context.get('loc_id'):
            if self._context.get('product_id'):
                quant_ids = self.env['stock.quant'].search([('location_id', '=', self._context.get('loc_id')),
                                                            ('product_id', '=', self._context.get('product_id'))])
                lot_ids = self.search([('quant_ids', 'in', [q.id for q in quant_ids])]).filtered(lambda l: l.remaining_qty > 0)
                args += [('id', 'in', [lot.id for lot in lot_ids])]
                if lot_ids:
                    args += [('id', 'in', [lot.id for lot in lot_ids])]
        elif self._context.get('from_invoice') and self._context.get('product_id') and self._context.get('loc_id'):
            if not self._context.get('refund_without_invoice'):
                quant_ids = self.env['stock.quant'].search([('location_id', '=', self._context.get('loc_id')),
                                                            ('product_id', '=', self._context.get('product_id'))])

                lot_ids = self.search([('quant_ids', 'in', [q.id for q in quant_ids])]).filtered(lambda l: l.remaining_qty > 0)
                args += [('id', 'in', [lot.id for lot in lot_ids])]
                if lot_ids:
                    args += [('id', 'in', [lot.id for lot in lot_ids])]
            else:
                lot_ids = self.search([('product_id', '=', self._context.get('product_id'))])
                args += [('id', 'in', [lot.id for lot in lot_ids])]
                if lot_ids:
                    args += [('id', 'in', [lot.id for lot in lot_ids])]

#                 Lots = self.env['stock.production.lot']
#                 self._cr.execute(''' select product_id,serial_number from stock_history 
#                 where product_id = %s and location_id=%s ''' % (self._context.get('product_id') , self._context.get('loc_id')))
#                 result = self._cr.fetchall()
#                 for each in result:
#                     Lots |= Lots.search([('name', '=', each[1]), ('product_id', '=', each[0])])
#                 args += [('id', 'in', [lot.id for lot in Lots])]

        return super(stock_production_lot, self).name_search(name=name, args=args, operator=operator, limit=limit)

    @api.multi
    @api.depends('name', 'remaining_qty')
    def name_get(self):
        result = []
        if self._context.get('direct_sale') or self._context.get('from_invoice'):
            if self._context.get('loc_id'):
                location_id = self._context.get('loc_id')
                if self._context.get('refund_without_invoice'):
                    location_id = self.env['res.partner'].browse(self._context.get('partner_id')).property_stock_customer.id
                for lot_data in self:
                    name = lot_data.name
                    if lot_data.life_date:
                        tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
                        life_date = datetime.strptime(lot_data.life_date, DEFAULT_SERVER_DATETIME_FORMAT)
                        life_date = pytz.utc.localize(life_date)
                        life_date = life_date.astimezone(tz).date()
                        life_date = life_date.strftime('%d-%m-%Y')
                        if not life_date:
                            date = datetime.strptime(lot_data.life_date[:10], '%Y-%m-%d').strftime('%d-%m-%Y')
                            name += ' : (' + date + ')'
                        else:
                            name += ' : (' + life_date + ')'
                    lot_remaining_qty = lot_data.product_id.with_context({'location': location_id,
                                                  'lot_id': lot_data.id,
                                                  'compute_child': False}).qty_available
                    name += ' : [' + str(int(lot_remaining_qty)) + ']'
                    result.append((lot_data.id, name))
                return result
            else:
                raise  Warning(_('Please Select Source Location First!!!!'))
        return super(stock_production_lot, self).name_get()

    def _compute_remaining_qty(self):
        for each in self:
            each.remaining_qty = 0
            for quant_id in each.quant_ids:
                if quant_id and quant_id.location_id and quant_id.location_id.usage == 'internal':
                    each.remaining_qty += quant_id.qty
        return


class stock_location(models.Model):
    _inherit = 'stock.location'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self.env.user.id != SUPERUSER_ID and self._context.get('from_direct_sale_loc'):
            if self.env.user.has_group('stock.group_stock_user') and self.env.user.restrict_wh_locations:
                args.append(('id', 'in', [x.id for x in self.env.user.allowed_location_ids_computed]))
        return super(stock_location, self).name_search(name, args=args, operator=operator, limit=limit)


class stock_picking_type(models.Model):
    _inherit = 'stock.picking.type'

    reserve_batches_automatically = fields.Boolean(string="Reserve Batches Automatically")
    group_by_account = fields.Boolean(string="Account Group", default=True)


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    account_move_id = fields.Many2one('account.move', string='Journal Entry',
        readonly=True, index=True, copy=False,
        help="Link to the automatically generated Journal Items.")
        
    max_line_sequence = fields.Integer(string='Max sequence in lines',
                                       compute='_compute_max_line_sequence')
    picking_cost = fields.Float('Picking Cost', compute='_get_picking_cost',digits=dp.get_precision('Discount'))
    
    @api.one
    def _get_picking_cost(self):
        cost = 0.0
        scrap_ids = self.env['stock.scrap'].search([('picking_id', '=', self.id)])
        if scrap_ids:
            for scrap in scrap_ids:
                m = scrap.move_id
                cost += (m.price_unit * m.product_qty)
        else:
            for m in self.move_lines:
#                print"mPrice Unit: ",m.price_unit
#                print"m Quantity: ",m.product_qty
                cost += (m.price_unit * m.product_qty)
#                if self.picking_type_id.default_location_dest_id.id == m.location_id.id:
#                    cost += (m.price_unit * m.product_qty)
        self.picking_cost = cost    
                                       
    @api.multi
    @api.depends('move_lines')
    def _compute_max_line_sequence(self):
        """Allow to know the highest sequence entered in move lines.
        Then we add 1 to this value for the next sequence, this value is
        passed to the context of the o2m field in the view.
        So when we create new move line, the sequence is automatically
        incremented by 1. (max_sequence + 1)
        """
        for picking in self:
            picking.max_line_sequence = (
                max(picking.mapped('move_lines.sequence') or [0]) + 1
                )
        
    @api.multi
    def _reset_sequence(self):
        for rec in self:
            current_sequence = 1
            for line in rec.move_lines:
                line.sequence = current_sequence
                current_sequence += 1
                
    @api.multi
    def copy(self, default=None):
        return super(stock_picking,
                     self.with_context(keep_line_sequence=True)).copy(default)
                     
    @api.multi
    def do_new_transfer(self):
        return super(stock_picking,
                     self.with_context(keep_line_sequence=True)
                     ).do_new_transfer()
                
        
    # delete, cost dist lines, pack operations etc
    @api.multi
    def unlink(self):
        for picking in self:
            if picking.state=='cancel':
                purchase_cost_ids = self.env['purchase.cost.distribution.line'].search([('picking_id','=',picking.id)])
                if len(purchase_cost_ids):
                    self.env.cr.execute("delete from purchase_cost_distribution_line where picking_id=%s",(picking.id,))
                pack_ids = self.env['stock.pack.operation'].search([('picking_id','=',picking.id)])
                if len(pack_ids):
                    self.env.cr.execute("delete from stock_pack_operation where picking_id=%s",(picking.id,))
        return super(stock_picking, self).unlink()

    @api.multi
    def do_prepare_partial(self):
        # TDE CLEANME: oh dear ...
        PackOperation = self.env['stock.pack.operation']

        # get list of existing operations and delete them
        existing_packages = PackOperation.search([('picking_id', 'in', self.ids)])  # TDE FIXME: o2m / m2o ?
        if existing_packages:
            existing_packages.unlink()
        for picking in self:
            forced_qties = {}  # Quantity remaining after calculating reserved quants
            picking_quants = self.env['stock.quant']
            # Calculate packages, reserved quants, qtys of this picking's moves
            for move in picking.move_lines:
                if move.state not in ('assigned', 'confirmed', 'waiting'):
                    continue
                move_quants = move.reserved_quant_ids
                picking_quants += move_quants
                forced_qty = 0.0
                if move.state == 'assigned':
                    qty = move.product_uom._compute_quantity(move.product_uom_qty, move.product_id.uom_id, round=False)
                    forced_qty = qty - sum([x.qty for x in move_quants])
                # if we used force_assign() on the move, or if the move is incoming, forced_qty > 0
                if float_compare(forced_qty, 0, precision_rounding=move.product_id.uom_id.rounding) > 0:
                    if forced_qties.get(move.product_id):
                        forced_qties[move.product_id] += forced_qty
                    else:
                        forced_qties[move.product_id] = forced_qty
            for vals in picking._prepare_pack_ops(picking_quants, forced_qties):
                vals['fresh_record'] = False
                PackOperation |= PackOperation.create(vals)
        # recompute the remaining quantities all at once

        if self.picking_type_id and self.picking_type_id.reserve_batches_automatically:
            if PackOperation:
                for each_op in PackOperation:
                    lot_list = []
                    total_qty = each_op.ordered_qty
                    each_op.pack_lot_ids = False

                    lot_ids = self.env['stock.production.lot'].search([('product_id', '=', each_op.product_id.id)], order='life_date')
#                     lot_ids = lot_ids.filtered(lambda l:l.remaining_qty > 0).sorted(lambda l:l.life_date)

                    for each_lot in lot_ids:
                        quant = each_lot.quant_ids.filtered(lambda l:l.qty > 0 and l.location_id.id == self.location_id.id)
                        if quant:
                            sum_quant_qty = sum(quant.mapped('qty'))
                            if total_qty >= sum_quant_qty:
                                lot_list.append((0, 0, {'lot_id':quant[0].lot_id.id, 'qty':sum_quant_qty, 'qty_todo':sum_quant_qty}))
                                total_qty -= sum_quant_qty
                            elif total_qty > 0:
                                lot_list.append((0, 0, {'lot_id':quant[0].lot_id.id, 'qty':total_qty, 'qty_todo':total_qty}))
                                total_qty -= total_qty

                    each_op.write({'pack_lot_ids':lot_list})
                    each_op.save()

        self.do_recompute_remaining_quantities()
        for pack in PackOperation:
            pack.ordered_qty = sum(
                pack.mapped('linked_move_operation_ids').mapped('move_id').filtered(lambda r: r.state != 'cancel').mapped('ordered_qty')
            )
        self.write({'recompute_pack_op': False})
        
    # getting used from Scrapextension module
#    @api.multi
#    def button_scrap(self):
#        self.ensure_one()
#        return {
#            'name': _('Scrap'),
#            'view_type': 'form',
#            'view_mode': 'form',
#            'res_model': 'stock.scrap',
#            'view_id': self.env.ref('stock.stock_scrap_form_view2').id,
#            'type': 'ir.actions.act_window',
#            'context': {'default_picking_id': self.id, 
#                'product_ids': self.pack_operation_product_ids.mapped('product_id').ids,
#                'default_scrap_date':self.min_date},
#            'target': 'new',
#        }
        
    @api.multi
    def _create_backorder(self, backorder_moves=[]):
        """ Move all non-done lines into a new backorder picking. If the key 'do_only_split' is given in the context, then move all lines not in context.get('split', []) instead of all non-done lines.
        """
        # TDE note: o2o conversion, todo multi
        backorders = self.env['stock.picking']
        for picking in self:
            backorder_moves = backorder_moves or picking.move_lines
            if self._context.get('do_only_split'):
                not_done_bo_moves = backorder_moves.filtered(lambda move: move.id not in self._context.get('split', []))
            else:
                not_done_bo_moves = backorder_moves.filtered(lambda move: move.state not in ('done', 'cancel'))
            if not not_done_bo_moves:
                continue
            backorder_picking = picking.copy({
                'name': '/',
                'move_lines': [],
                'pack_operation_ids': [],
                'backorder_id': picking.id
            })
            picking.message_post(body=_("Back order <em>%s</em> <b>created</b>.") % (backorder_picking.name))
            backorder_picking.write({'min_date':picking.min_date})
            not_done_bo_moves.write({'picking_id': backorder_picking.id})
            if not picking.date_done:
                picking.write({'date_done': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
#            backorder_picking.action_confirm()
            backorder_picking.action_assign()
            backorders |= backorder_picking
        return backorders


class Move(models.Model):
    _inherit = 'stock.move'
    _order = 'sequence2 ASC, id'

    account_invoice_line_id = fields.Many2one('account.invoice.line', string="Invoice Line")
    from_location_qty = fields.Float(string="From Location Qty")
    to_location_qty = fields.Float(string="To Location Qty")    
    
    # re-defines the field to change the default
    sequence = fields.Integer(default=9999)
    # displays sequence on the stock moves
    sequence2 = fields.Integer(help="Shows the sequence in the Stock Move.",
                               related='sequence', readonly=True, store=True)
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        super(Move, self).onchange_product_id()
        if self.picking_id:
            location_id = self.picking_id.location_id.id
            location_dest_id = self.picking_id.location_dest_id.id
        else:
            location_id = self.location_id.id
            location_dest_id = self.location_dest_id.id
            
        from_product = self.product_id.with_context({'location': location_id, 'compute_child': False})
        to_product = self.product_id.with_context({'location': location_dest_id, 'compute_child': False})
        self.from_location_qty = from_product.qty_available
        self.to_location_qty = to_product.qty_available    
        
        
    @api.multi
    def action_done(self):
        res = super(Move, self).action_done()
        pickings = self.env['stock.picking']
        min_date = False
        for move in self:
            if move.picking_id:
                min_date = move.picking_id.min_date
                move.write({'date':min_date})
                # new change
                if move.picking_id.picking_type_id.code =='outgoing' and move.account_invoice_line_id:
                    move.account_invoice_line_id.cost_price = move.price_unit
                # new change
            if move.inventory_id:
                date = move.inventory_id.accounting_date or move.inventory_id.date
                move.write({'date':date})                
            pickings |= move.picking_id
        pickings.filtered(lambda picking: picking.state == 'done').write({'date_done': min_date})
        return res
    
    @api.model
    def create(self, vals):
        picking_id = vals.get('picking_id',False)
        if picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            min_date = picking.min_date
            if min_date:
                vals['date'] = min_date
                vals['date_expected'] = min_date
       
        inventory_id = vals.get('inventory_id',False)
        if inventory_id:
            inventory = self.env['stock.inventory'].browse(inventory_id)
            date = inventory.date
            if date:
                vals['date'] = date
                vals['date_expected'] = date
                
        move = super(Move, self).create(vals)
        # sequence changes
        if not self.env.context.get('keep_line_sequence', False):
            move.picking_id._reset_sequence()
        return move
    
    # to consider the negative qty while calculating the avg cost
#    @api.multi
#    def product_price_update_before_done(self):
#        tmpl_dict = defaultdict(lambda: 0.0)
#        # adapt standard price on incomming moves if the product cost_method is 'average'
#        std_price_update = {}
#        for move in self.filtered(lambda move: move.location_id.usage in ('supplier', 'production') and move.product_id.cost_method == 'average'):
#            product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]
#            print"product_tot_qty_available: ",product_tot_qty_available
#
#            # if the incoming move is for a purchase order with foreign currency, need to call this to get the same value that the quant will use.
#            if product_tot_qty_available <= 0:
#                new_std_price = move.get_price_unit()
#            else:
#                # Get the standard price
#                amount_unit = std_price_update.get((move.company_id.id, move.product_id.id)) or move.product_id.standard_price
#                new_std_price = ((amount_unit * product_tot_qty_available) + (move.get_price_unit() * move.product_qty)) / (product_tot_qty_available + move.product_qty)
#            
#            # custom code
#            amount_unit = std_price_update.get((move.company_id.id, move.product_id.id)) or move.product_id.standard_price
#            total_qty = product_tot_qty_available + move.product_qty
#            if float(total_qty) == 0.0:
#                total_qty = 1.0
#            std_price = ((product_tot_qty_available*amount_unit) + (move.product_qty * move.get_price_unit())) / (total_qty)
#            print"std_price New: ",std_price
#            if std_price < 0:# if -ve
#                std_price = new_std_price
#            new_std_price = std_price
#            
#            tmpl_dict[move.product_id.id] += move.product_qty
#            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
#            move.product_id.with_context(force_company=move.company_id.id).sudo().write({'standard_price': new_std_price})
#            std_price_update[move.company_id.id, move.product_id.id] = new_std_price
      
class stock_change_product_qty(models.TransientModel):
    _inherit = 'stock.change.product.qty'

    product_tracking = fields.Selection('Product Tracking', related='product_id.tracking')


class stock_quant(models.Model):
    _inherit = 'stock.quant'

    @api.multi
    def group_by_account(self, move, move_lines, credit_account_id, debit_account_id, journal_id):
        AccountMove = self.env['account.move']
        new_account_move = self.env['account.move']
        name = False
        if move.inventory_id:
            name = move.inventory_id.name
        else:
            name = move.picking_id.name
        AccountMove = AccountMove.search([('ref', '=', name)])
        picking = move.picking_id or False
        if not AccountMove:
            for each in move_lines:
                if each[2]:
                    each[2]['name'] = '/'
                    if move.inventory_id:
                        each[2]['name'] = move.inventory_id.name
                    elif move.purchase_line_id:
                        each[2]['name'] = move.purchase_line_id.order_id.name
                        if not move.purchase_line_id.order_id.has_default_currency:
                            each[2]['exchange_rate'] = move.purchase_line_id.order_id.exchange_rate
                    each[2]['product_id'] = False
                    each[2]['product_uom_id'] = False
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.create({
                'journal_id': journal_id,
                'line_ids': move_lines,
#                'date': date,
                'date': move.picking_id and move.picking_id.min_date or date,
                'ref': name})
            if not new_account_move.ref:
                new_account_move.ref = name
            new_account_move.post()
            if picking:
                picking.write({'account_move_id':new_account_move.id})
        else:
            AccountMove.button_cancel()
            for each in move_lines:
                if each[2]:
                    line_ids = AccountMove.line_ids.filtered(lambda l:l.account_id.id == each[2]['account_id'])
                    credit_line_ids = AccountMove.line_ids.filtered(lambda l:l.account_id.id == each[2]['account_id'] and l.credit)
                    debit_line_ids = AccountMove.line_ids.filtered(lambda l:l.account_id.id == each[2]['account_id'] and l.debit)
                    qty = sum(line_ids.mapped('quantity')) + each[2].get('quantity', 0.00)

                    if credit_line_ids and each[2]['credit']:
                        credit = sum(credit_line_ids.mapped('credit')) + each[2]['credit']
                        credit_line_ids.with_context({'check_move_validity':False}).write({'credit':credit,
                                                                                'debit':0,
                                                                                'quantity':qty
                                                                                })

                    elif debit_line_ids and each[2]['debit']:
                        debit = sum(debit_line_ids.mapped('debit')) + each[2]['debit']
                        debit_line_ids.with_context({'check_move_validity':False}).write({'credit':0,
                                                                                'debit':debit,
                                                                                'quantity':qty
                                                                                })

#                         line_ids.with_context({'check_move_validity':False}).write({'credit':credit,
#                                                                                     'debit':debit,
#                                                                                     'quantity':qty
#                                                                                     })
                    else:
                        each[2]['name'] = '/'
                        each[2]['product_id'] = False
                        each[2]['product_uom_id'] = False
                        each[2]['move_id'] = AccountMove.id
                        line_id = self.env['account.move.line'].with_context({'check_move_validity':False}).create(each[2])
                        
        if AccountMove:
            AccountMove.post()
#            print"after posttt"
            if picking:
                picking.write({'account_move_id':AccountMove.id})
                print"AccountMove: ",AccountMove
                print"entry attached exit"

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
        print"direct_sale _create_account_move_line called"
        ## if its scrap transaction, Debit the damage expense account
        if move.location_dest_id.scrap_location:
            damage_account_ids = self.env['account.account'].search([('name','=','Damages Expenses')])
            if damage_account_ids:
                debit_account_id = damage_account_ids[0].id
        picking = move.picking_id or False
        # group quants by cost
        quant_cost_qty = defaultdict(lambda: 0.0)
        for quant in self:
            quant_cost_qty[quant.cost] += quant.qty

        AccountMove = self.env['account.move']
        new_account_move = self.env['account.move']
        add_expense=True
        for cost, qty in quant_cost_qty.iteritems():
            print"CCCCCCCCCCCCCCCcccost: ",cost
            new_lst = []
            move_lines = move._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
#            print"direct_sale/stock.py _create_account_move_line move_lines: ",move_lines
            if move_lines:
                if move.inventory_id and move.inventory_id.group_by_account and not self._context.get('active_model') == 'product.product':
                    self.group_by_account(move, move_lines, credit_account_id, debit_account_id, journal_id)
                elif move.picking_id and move.picking_id.picking_type_id.group_by_account:
                    self.group_by_account(move, move_lines, credit_account_id, debit_account_id, journal_id)
                else:
                    date = self._context.get('force_period_date', fields.Date.context_today(self))
                    picking = move.picking_id or False
                    if picking:
                        date = picking.min_date
                    new_account_move = AccountMove.create({
                        'journal_id': journal_id,
                        'line_ids': move_lines,
                        'date': date,
                        'ref': move.picking_id.name})
                    new_account_move.post()
                    if picking:
                        picking.write({'account_move_id':new_account_move.id})


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    group_by_account = fields.Boolean(string="Account Group", default=True)
    date = fields.Datetime(
        'Inventory Date',
        required=True,readonly=False,
        default=fields.Datetime.now,
        help="The date that will be used for the stock level check of the products and the validation of the stock move related to this inventory.")    
    
    
    @api.multi
    def recalculate_qty(self):
#        for line in self.line_ids_two:
        for line in self.line_ids:
#            # Theoretical qty
            theoretical_qty = sum([x.qty for x in line._get_quants()])
            if theoretical_qty and line.product_uom_id and line.product_id.uom_id != line.product_uom_id:
                theoretical_qty = line.product_id.uom_id._compute_quantity(theoretical_qty, line.product_uom_id)
            line.theoretical_qty = theoretical_qty
#            print"theoretical_qty: ",theoretical_qty
#            
            # Real qty
#            if line.product_id and line.location_id and line.product_id.uom_id.category_id == line.product_uom_id.category_id:  # TDE FIXME: last part added because crash
#                line._compute_theoretical_qty()
#                line.product_qty = line.theoretical_qty            


    # inherited to check if there are any open transactions present.
    @api.multi
    def action_done(self):
        negative = next((line for line in self.mapped('line_ids') if line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        if negative:
            raise UserError(_('You cannot set a negative product quantity in an inventory line:\n\t%s - qty: %s') % (negative.product_id.name, negative.product_qty))
        # custom code start
        move_obj = self.env['stock.move']
        out_message = 'Please close below transactions for products:'
        raise_message = False
        for inventory in self:
            location = inventory.location_id
            message = ''
            count = 1
            for line in inventory.line_ids:
                product = line.product_id
                in_moves = move_obj.search([('product_id','=',product.id),
                            ('location_dest_id','=',location.id),
                            ('state','not in',('done','cancel')),
                            ('date','<=',inventory.date)
                            ])
                moves = []
                if len(in_moves):
                    moves = in_moves
                out_moves = move_obj.search([('product_id','=',product.id),
                            ('location_id','=',location.id),
                            ('state','not in',('done','cancel')),
                            ('date','<=',inventory.date)
                            ])
                if len(out_moves):
                    moves += out_moves
                pickings = ''
                for move in moves:
                    picking = move.picking_id
                    if len(pickings):
                        pickings = pickings+', '+picking.name
                    else:
                        pickings = picking.name
                if len(pickings):
                    message = message+'\n'+str(count)+') '+product.name+'\n'+str(pickings)
                    raise_message=True
                    count+=1
                    
                    
        out_message = out_message+message
        raise_message = False   # TODO comment it out after inventory adjustment
        if raise_message:
            raise UserError(_(out_message))
        # custom code ends
        self.action_check()
        self.write({'state': 'done'})
        self.post_inventory()
        return True
    
    # to use the inventory date
    @api.multi
    def post_inventory(self):
        for inventory in self:
            res = super(StockInventory, inventory.with_context(force_period_date=inventory.accounting_date or inventory.date)).post_inventory()
        return res
    
    # to use the inventory date
    @api.multi
    def action_start(self):
        for inventory in self:
            vals = {'state': 'confirm', 'date': inventory.accounting_date or inventory.date}
            if (inventory.filter != 'partial') and not inventory.line_ids:
                vals.update({'line_ids': [(0, 0, line_values) for line_values in inventory._get_inventory_lines_values()]})
            inventory.write(vals)
    prepare_inventory = action_start
    
class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"
    
    # use the accounting date
    def _get_move_values(self, qty, location_id, location_dest_id):
        self.ensure_one()
        date = self.inventory_id.accounting_date or self.inventory_id.date
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': qty,
#            'date': self.inventory_id.date,
            'date': date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'confirmed',
            'restrict_lot_id': self.prod_lot_id.id,
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: