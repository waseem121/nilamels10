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
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, Warning
from collections import namedtuple

class stock_location(models.Model):
    _inherit = "stock.location"

    cashier_ids = fields.Many2many('res.users','location_partner_rel','location_id','partner_id', string='Cashier')

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


class stock_picking(models.Model):
    _inherit = "stock.picking"

    def do_detailed_internal_transfer(self, vals):
        move_lines = [] 
        if vals and vals.get('data'):
            for move_line in vals.get('data').get('moveLines'):
                move_lines.append((0,0,move_line))
            picking_vals = {'location_id': vals.get('data').get('location_src_id'),
                            'state':'draft', 
                            'move_lines': move_lines,
                            'location_dest_id': vals.get('data').get('location_dest_id'),
                            'picking_type_id': vals.get('data').get('picking_type_id')}
            picking_id = self.create(picking_vals)
            if picking_id:
                if vals.get('data').get('state') == 'confirmed':
                    picking_id.action_confirm()
#                 if vals.get('data').get('state') == 'done':
#                     picking_id.action_confirm()
#                     picking_id.force_assign()
#                     picking_id.do_new_transfer()
#                     stock_transfer_id = self.env['stock.immediate.transfer'].search([('pick_id', '=', picking_id.id)], limit=1).process()
#                     if stock_transfer_id:
#                         stock_transfer_id.process()
        return picking_id.read()

    @api.multi
    def do_transfer(self):
        """ If no pack operation, we do simple action_done of the picking.
        Otherwise, do the pack operations. """
        if self.location_id.usage == 'internal':
            pack_op_picking_ids = self.filtered(lambda picking: picking.pack_operation_ids)
            for ope in pack_op_picking_ids.pack_operation_ids.filtered(lambda l:l.product_id.tracking != 'none'):
                for each in ope.pack_lot_ids:
                    rqty = ope.product_id.with_context({'location': ope.picking_id.location_id.id,
                                                      'lot_id': each.lot_id.id,
                                                      'compute_child': False})._product_available()
                    if each.lot_id and rqty[ope.product_id.id]['qty_available'] < each.qty:
                        raise Warning(_("You can not enter the quantity beyond the available quantity for product %s .") % (ope.product_id.name))

        # TDE CLEAN ME: reclean me, please
        self._create_lots_for_picking()

        no_pack_op_pickings = self.filtered(lambda picking: not picking.pack_operation_ids)
        no_pack_op_pickings.action_done()
        other_pickings = self - no_pack_op_pickings
        for picking in other_pickings:
            need_rereserve, all_op_processed = picking.picking_recompute_remaining_quantities()
            todo_moves = self.env['stock.move']
            toassign_moves = self.env['stock.move']

            # create extra moves in the picking (unexpected product moves coming from pack operations)
            if not all_op_processed:
                todo_moves |= picking._create_extra_moves()

            if need_rereserve or not all_op_processed:
                moves_reassign = any(x.origin_returned_move_id or x.move_orig_ids for x in picking.move_lines if x.state not in ['done', 'cancel'])
                if moves_reassign and picking.location_id.usage not in ("supplier", "production", "inventory"):
                    # unnecessary to assign other quants than those involved with pack operations as they will be unreserved anyways.
                    picking.with_context(reserve_only_ops=True, no_state_change=True).rereserve_quants(move_ids=todo_moves.ids)
                picking.do_recompute_remaining_quantities()

            # split move lines if needed
            pack_moves = []
            for move in picking.move_lines:
                rounding = move.product_id.uom_id.rounding
                remaining_qty = move.remaining_qty
                # if the management of stock is pack product, then transfer the related stock moves.
                if move.group_id and move.product_id.is_product_pack and move.product_id.pack_management == 'pack_product':
                    pack_moves = self.env['stock.move'].search([('state', '!=', 'done'), ('group_id', '=', move.group_id.id), ('id', '!=', move.id)])
                    for packmove in pack_moves:
                        for packline in move.product_id.product_pack_ids:
                            if packline.product_id.id == packmove.product_id.id:
                                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                                product_qty = remaining_qty * packline.quantity
                                if float_compare(product_qty, 0,  precision_rounding=rounding) == 0:
                                    packmove.action_done()
                                elif float_compare(product_qty, 0, precision_rounding=rounding) > 0 and float_compare(product_qty, packmove.product_uom_qty, precision_rounding=rounding) < 0:
                                    new_move = packmove.copy().action_confirm()
                                    packmove.write({'product_uom_qty': new_move.product_uom_qty - product_qty})
                                    packmove.action_done()
                                    new_move.write({'picking_id': False, 'product_uom_qty': product_qty})
                if move.state in ('done', 'cancel'):
                    # ignore stock moves cancelled or already done
                    continue
                elif move.state == 'draft':
                    toassign_moves |= move
                if float_compare(remaining_qty, 0,  precision_rounding=rounding) == 0:
                    if move.state in ('draft', 'assigned', 'confirmed'):
                        todo_moves |= move
                elif float_compare(remaining_qty, 0, precision_rounding=rounding) > 0 and float_compare(remaining_qty, move.product_qty, precision_rounding=rounding) < 0:
                    # TDE FIXME: shoudl probably return a move - check for no track key, by the way
                    new_move_id = move.split(remaining_qty)
                    new_move = self.env['stock.move'].with_context(mail_notrack=True).browse(new_move_id)
                    todo_moves |= move
                    # Assign move as it was assigned before
                    toassign_moves |= new_move
            # TDE FIXME: do_only_split does not seem used anymore
            if todo_moves and not self.env.context.get('do_only_split'):
                todo_moves.action_done()
            elif self.env.context.get('do_only_split'):
                picking = picking.with_context(split=todo_moves.ids)
            picking._create_backorder()
        return True

    def check_pack_operation_product_ids(self):
        # check the quantity as per configure into that particular pack product
        qty_dict = {}
        for operation in self.pack_operation_product_ids:
            if operation.pack_product_id:
                if qty_dict.has_key(operation.pack_product_id):
                    qty_dict[operation.pack_product_id].update({operation.product_id.id: operation.qty_done})
                else:
                    qty_dict.update({operation.pack_product_id: {operation.product_id.id: operation.qty_done}})
        for each in qty_dict:
            if all(qty == 0 for qty in qty_dict[each].values()):
                continue
            else:
                check_qty_lst = []
                for packline in each.product_pack_ids:
                    if packline.product_id.id in qty_dict[each]:
                        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                        product_qty = packline.product_id.uom_id._compute_quantity(qty_dict[each][packline.product_id.id], packline.product_id.uom_id)
                        if (qty_dict[each][packline.product_id.id] % packline.quantity) != 0:
                            raise Warning(_('Please enter proper pack quantities !'))
                        check_qty_lst.append(qty_dict[each][packline.product_id.id] / packline.quantity)
                if not all(x == check_qty_lst[0] for x in check_qty_lst):
                    raise Warning(_('Please manage component quantity of pack !'))
    @api.multi
    def do_new_transfer(self):
        self.check_pack_operation_product_ids()
        lines = self.env['purchase.cost.distribution.line'].search([('picking_id', '=', self.id)], limit=1)
        if lines and lines.distribution and lines.distribution.state != 'done':
            raise Warning(_('Please make sure landed cost done state.'))
        return super(stock_picking, self).do_new_transfer()

    def _prepare_pack_ops(self, quants, forced_qties):
        """ Prepare pack_operations, returns a list of dict to give at create """
        # TDE CLEANME: oh dear ...
        valid_quants = quants.filtered(lambda quant: quant.qty > 0)
        _Mapping = namedtuple('Mapping', ('product', 'package', 'owner', 'location', 'location_dst_id'))

        all_products = valid_quants.mapped('product_id') | self.env['product.product'].browse(p.id for p in forced_qties.keys()) | self.move_lines.mapped('product_id')
        computed_putaway_locations = dict(
            (product, self.location_dest_id.get_putaway_strategy(product) or self.location_dest_id.id) for product in all_products)

        product_to_uom = dict((product.id, product.uom_id) for product in all_products)
        picking_moves = self.move_lines.filtered(lambda move: move.state not in ('done', 'cancel'))
        for move in picking_moves:
            # If we encounter an UoM that is smaller than the default UoM or the one already chosen, use the new one instead.
            if move.product_uom != product_to_uom[move.product_id.id] and move.product_uom.factor > product_to_uom[move.product_id.id].factor:
                product_to_uom[move.product_id.id] = move.product_uom
        if len(picking_moves.mapped('location_id')) > 1:
            raise UserError(_('The source location must be the same for all the moves of the picking.'))
        if len(picking_moves.mapped('location_dest_id')) > 1:
            raise UserError(_('The destination location must be the same for all the moves of the picking.'))

        pack_operation_values = []
        # find the packages we can move as a whole, create pack operations and mark related quants as done
        top_lvl_packages = valid_quants._get_top_level_packages(computed_putaway_locations)
        for pack in top_lvl_packages:
            pack_quants = pack.get_content()
            pack_operation_values.append({
                'picking_id': self.id,
                'package_id': pack.id,
                'product_qty': 1.0,
                'location_id': pack.location_id.id,
                'location_dest_id': computed_putaway_locations[pack_quants[0].product_id],
                'owner_id': pack.owner_id.id,
            })
            valid_quants -= pack_quants

        # Go through all remaining reserved quants and group by product, package, owner, source location and dest location
        # Lots will go into pack operation lot object
        qtys_grouped = {}
        lots_grouped = {}
        for quant in valid_quants:
            key = _Mapping(quant.product_id, quant.package_id, quant.owner_id, quant.location_id, computed_putaway_locations[quant.product_id])
            qtys_grouped.setdefault(key, 0.0)
            qtys_grouped[key] += quant.qty
            if quant.product_id.tracking != 'none' and quant.lot_id:
                lots_grouped.setdefault(key, dict()).setdefault(quant.lot_id.id, 0.0)
                lots_grouped[key][quant.lot_id.id] += quant.qty
        # Do the same for the forced quantities (in cases of force_assign or incomming shipment for example)
        for product, qty in forced_qties.items():
            if qty <= 0.0:
                continue
            key = _Mapping(product, self.env['stock.quant.package'], self.owner_id, self.location_id, computed_putaway_locations[product])
            qtys_grouped.setdefault(key, 0.0)
            qtys_grouped[key] += qty

        # Create the necessary operations for the grouped quants and remaining qtys
        Uom = self.env['product.uom']
        product_id_to_vals = {}  # use it to create operations using the same order as the picking stock moves
        for mapping, qty in qtys_grouped.items():
            uom = product_to_uom[mapping.product.id]
            val_dict = {
                'picking_id': self.id,
                'product_qty': mapping.product.uom_id._compute_quantity(qty, uom),
                'product_id': mapping.product.id,
                'package_id': mapping.package.id,
                'owner_id': mapping.owner.id,
                'location_id': mapping.location.id,
                'location_dest_id': mapping.location_dst_id,
                'product_uom_id': uom.id,
                'pack_lot_ids': [
                    (0, 0, {'lot_id': lot, 'qty': 0.0, 'qty_todo': lots_grouped[mapping][lot]})
                    for lot in lots_grouped.get(mapping, {}).keys()],
            }
            product_id_to_vals.setdefault(mapping.product.id, list()).append(val_dict)

        for move in self.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')):
            values = product_id_to_vals.pop(move.product_id.id, [])
            # Added the pack product into operation, so when validate the picking at time check the quantity
            if move.pack_product_id and values:
                values[0].update({'pack_product_id':move.pack_product_id.id})
            pack_operation_values += values
        return pack_operation_values

    @api.onchange('pack_operation_product_ids')
    def change_combo_product_qty(self):
        # Auto update the component products delivery quantity when user enter the pack product's delivery quantity
        prd_qty = {}
        for operation in self.pack_operation_product_ids.filtered(lambda op: op.product_id.is_product_pack):
            prd_qty.update({operation.product_id: operation.qty_done})
        for operation in self.pack_operation_product_ids.filtered(lambda op: op.pack_product_id):
            if operation.pack_product_id in prd_qty:
                for packline in operation.pack_product_id.product_pack_ids:
                    if packline.product_id.id == operation.product_id.id:
                        operation.write({'qty_done': packline.product_id.uom_id._compute_quantity(prd_qty[operation.pack_product_id] * packline.quantity, packline.product_id.uom_id)})

class stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'
    
    remaining_qty = fields.Float("Remaining Qty", compute="_compute_remaining_qty")
    
    def _compute_remaining_qty(self):
        for each in self:
            each.remaining_qty = 0
            for quant_id in each.quant_ids:
                if quant_id and quant_id.location_id and quant_id.location_id.usage == 'internal':
                    each.remaining_qty += quant_id.qty
        return

class stock_move(models.Model):
    _inherit = 'stock.move'

    pack_product_id = fields.Many2one('product.product', 'Pack Product')

class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    pack_product_id = fields.Many2one('product.product', 'Pack Product')

    @api.multi
    def save(self):
        if not self._context.get('from_invoice_picking'):
            for pack in self:
#                 if pack.product_id.tracking != 'none' and pack.picking_id.picking_type_id.code != 'incoming' and not pack.picking_id.picking_type_id.reserve_batches_automatically:
                if pack.product_id.tracking != 'none' and pack.picking_id.picking_type_id.code != 'incoming':
                    for each in pack.pack_lot_ids:
                        rqty = pack.product_id.with_context({'location': pack.picking_id.location_id.id,
                                                      'lot_id': each.lot_id.id,
                                                      'compute_child': False})._product_available()
                        if each.lot_id and rqty[pack.product_id.id]['qty_available'] < each.qty:
                            raise Warning(_("You can not enter the quantity beyond the available quantity for %s.") % pack.product_id.name)
                    pack.write({'qty_done': sum(pack.pack_lot_ids.mapped('qty'))})
                else:
                    super(stock_pack_operation, self).save()
        else:
            super(stock_pack_operation, self).save()
#             return {'type': 'ir.actions.act_window_close'}


class procurement_order(models.Model):
    _inherit = 'procurement.order'

    def _get_stock_move_values_aspl(self):
        # This method create component product's move
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'move') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        group_id = False
        if self.rule_id.group_propagation_option == 'propagate':
            group_id = self.group_id.id
        elif self.rule_id.group_propagation_option == 'fixed':
            group_id = self.rule_id.group_id.id
        date_expected = (datetime.strptime(self.date_planned, DEFAULT_SERVER_DATETIME_FORMAT) - relativedelta(days=self.rule_id.delay or 0)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # it is possible that we've already got some move done, so check for the done qty and create
        # a new move with the correct qty
        product_id = self._context.get('product_id')
        qty_done = sum(self.move_ids.filtered(lambda move: move.state == 'done').mapped('product_uom_qty'))
        qty_left = max(self._context.get('product_qty') * self.product_qty - qty_done, 0)
        return {
            'name': self.name,
            'company_id': self.rule_id.company_id.id or self.rule_id.location_src_id.company_id.id or self.rule_id.location_id.company_id.id or self.company_id.id,
            'product_id': product_id.id,
            'product_uom': product_id.uom_id.id,
            'product_uom_qty': qty_left,
            'partner_id': self.rule_id.partner_address_id.id or (self.group_id and self.group_id.partner_id.id) or False,
            'location_id': self.rule_id.location_src_id.id,
            'location_dest_id': self.location_id.id,
            'move_dest_id': self.move_dest_id and self.move_dest_id.id or False,
            'procurement_id': self.id,
            'rule_id': self.rule_id.id,
            'procure_method': self.rule_id.procure_method,
            'origin': self.origin,
            'picking_type_id': self.rule_id.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, route.id) for route in self.route_ids],
            'warehouse_id': self.rule_id.propagate_warehouse_id.id or self.rule_id.warehouse_id.id,
            'date': date_expected,
            'date_expected': date_expected,
            'propagate': self.rule_id.propagate,
            'priority': self.priority,
            'pack_product_id': self.product_id.id
        }

    @api.multi
    def _run(self):
        if self.rule_id.action == 'move':
            if not self.rule_id.location_src_id:
                self.message_post(body=_('No source location defined!'))
                return False
            # create the move as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            # From here, based on the pack product's management stock option, the moves are create.
            move_obj = self.env['stock.move']
            if self.product_id.is_product_pack:
                if self.product_id.pack_management == 'component_product':
                    for line in self.product_id.product_pack_ids:
                        move_id = move_obj.sudo().create(self.with_context({'product_id': line.product_id, 'product_qty': line.quantity})._get_stock_move_values_aspl())
                        move_id.action_confirm()
                elif self.product_id.pack_management == 'pack_product':
                    move = move_obj.sudo().create(self._get_stock_move_values())
                    for line in self.product_id.product_pack_ids:
                        move_id = move_obj.sudo().create(self.with_context({'product_id': line.product_id, 'product_qty': line.quantity})._get_stock_move_values_aspl())
                        move_id.action_confirm()
                        if move_id.picking_id:
                            move_id.write({'picking_id': False})
                elif self.product_id.pack_management == 'both':
                    for line in self.product_id.product_pack_ids:
                        move_id = move_obj.sudo().create(self.with_context({'product_id': line.product_id, 'product_qty': line.quantity})._get_stock_move_values_aspl())
                        move_id.action_confirm()
                    move = move_obj.sudo().create(self._get_stock_move_values())
            else:
                move_obj.sudo().create(self._get_stock_move_values())
            return True
        return super(procurement_order, self)._run()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: