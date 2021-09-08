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
from odoo.exceptions import UserError
from odoo.exceptions import Warning, ValidationError

# adding user specified date as transaction date in moves and picking
class Picking(models.Model):
    _inherit = "stock.picking"
    
    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = default or {}
        default['min_date'] = self.min_date
        return super(Picking, self).copy(default=default)    
    
    # do comment this in default stock/sock_picking.py
    @api.one
    def _compute_dates(self):
        min_date=False
        if not self.min_date:
            if len(self.move_lines):
                min_date = min(self.move_lines.mapped('date_expected') or [False])
                if min_date:
                    self.min_date = min_date
                    self.max_date = min_date
                else:
    #                invoice_ids = self.env['account.invoice'].search([('invoice_picking_id','=',self.id)])
    #                if len(invoice_ids):
    #                    min_date = invoice_ids[0].date_invoice
                    if self.env.user.transaction_date:
                        min_date = self.env.user.transaction_date
                    if min_date:
                        self.min_date = min_date
                        self.max_date = min_date
                    else:
                        self.min_date = min(self.move_lines.mapped('date_expected') or [False])
                        self.max_date = max(self.move_lines.mapped('date_expected') or [False])    
        
    @api.model
    def _default_min_date(self):
        if not self.min_date:
            return self.env.user.transaction_date
    
    
    @api.one
    def _set_min_date(self):
        if len(self.move_lines):
            if self.min_date:
                self.move_lines.write({'date_expected': self.min_date,'date':self.min_date})
        
    @api.onchange('min_date')
    def onchange_min_date(self):
        if len(self.move_lines):
            for move in self.move_lines:
                move.date = self.min_date
                move.date_expected = self.min_date
#                move.write({'date':self.min_date,'date_expected':self.min_date})    

#    @api.one
#    def _get_picking_cost(self):
#        cost = 0.0
##        self.picking_cost = sum([l.price_unit*l.product_qty for l in self.move_lines])
#        for l in self.move_lines:
#            cost += (l.price_unit * l.product_qty)
#        self.picking_cost = cost

    
    min_date = fields.Datetime(
        'Scheduled Date', compute='_compute_dates', inverse='_set_min_date', store=True,
        index=True, track_visibility='onchange',default=_default_min_date,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")
#    picking_cost = fields.Float('Picking Cost', compute='_get_picking_cost')


    @api.multi
    def reset_draft(self):
#        message = 'Not allowed for now. please try later.'
#        raise UserError(_(message))
    
        state = self.state
        self.do_unreserve()
        # first check for available qty validation, before deleting quants
        stock_quant_sudo = self.env['stock.quant'].sudo()
        user = self.env['res.users'].browse(self.env.uid)
        allow_negative = user.has_group('direct_sale.group_allow_negative_qty')
        if state=='done':
            if not allow_negative:
                for move in self.move_lines:
                    available_qty = move.product_id.with_context(
                        {'location': move.location_dest_id.id, 'compute_child': False}).qty_available
                    print"available_qty: ",available_qty
                    if float(available_qty)<=0.0:
                        message = 'No enough stock for '+'"'+str(move.product_id.name)+'"'+' in '+'"'+str(move.location_dest_id.name)+'"'
                        raise UserError(_(message))

            # adjust the stock quants
            for move in self.move_lines:            
                # add qty in source location quant
                if move.location_id.usage=='internal':
                    add_qty_quant_ids = []
                    self._cr.execute("""SELECT id FROM stock_quant WHERE 
                        product_id = %s and location_id=%s ORDER BY id DESC""", 
                        (move.product_id.id,move.location_id.id))
                    res = self._cr.fetchall()
                    if len(res):
                        add_qty_quant_ids = [x[0] for x in res]

                    print"add_qty_quant_ids: ",add_qty_quant_ids
                    if len(add_qty_quant_ids):
                        add_qty_quant = stock_quant_sudo.browse(add_qty_quant_ids[0])
                        add_qty_quant.write({'qty':float(add_qty_quant.qty+move.product_qty)})

                    else:
                        quant_created = stock_quant_sudo.create({'product_id':move.product_id.id,
                                        'location_id':move.location_id.id,
                                        'qty':move.product_qty,
                                        'in_date':move.picking_id and move.picking_id.min_date or ''})

                # substract qty from dest location quant
                if move.location_dest_id.usage=='internal':
                    sub_qty_quant_ids = []
                    self._cr.execute("""SELECT id FROM stock_quant WHERE 
                        product_id = %s and location_id=%s ORDER BY id DESC""", 
                        (move.product_id.id,move.location_dest_id.id))
                    res = self._cr.fetchall()
                    if len(res):
                        sub_qty_quant_ids = [x[0] for x in res]

                    if len(sub_qty_quant_ids):
                        qty_substracted=False
                        for q in stock_quant_sudo.browse(sub_qty_quant_ids):
                            if q.qty > move.product_qty:
                                q.write({'qty':float(q.qty-move.product_qty)})
                                qty_substracted=True
                        print"qty_substracted: ",qty_substracted
                        if not qty_substracted:
                            move_qty = move.product_qty
                            print"move_qty org: ",move_qty
                            for q in stock_quant_sudo.browse(sub_qty_quant_ids):
                                print"move_qty:  :",move_qty
                                if move_qty<=0:
                                    continue
                                print"q.qty: ",q.qty
                                if q.qty>0:
                                    new_qty = q.qty - move_qty
                                    print"new_qty: ",new_qty
                                    move_qty -= q.qty
                                    if new_qty <=0:
                                        print"q deleted"
                                        self._cr.execute("""DELETE FROM stock_quant WHERE id IN %s""", (tuple([q.id]),))
                                        self._cr.execute("""DELETE FROM stock_quant_move_rel WHERE quant_id IN %s""", (tuple([q.id]),))
                                    else:
                                        print"move qty updated"
                                        q.write({'qty':float(new_qty)})
                            print"mvoe qty last: ",move_qty
                            if move_qty > 0:
                                print"if move_qty>0"
                                if not allow_negative:
                                    raise Warning(_('No stock available for %s in %s') % (move.product_id.name,move.location_dest_id.name),)

                                quant_created = stock_quant_sudo.create({'product_id':move.product_id.id,
                                                'location_id':move.location_dest_id.id,
                                                'qty':move_qty*-1,
                                                'in_date':move.picking_id and move.picking_id.min_date or ''})
                                print"quant_created yesssss: ",quant_created

                    else:
                        if not allow_negative:
                            raise Warning(_('No stock available for %s in %s') % (move.product_id.name,move.location_dest_id.name),)
                        move_qty = move.product_qty
                        quant_created = stock_quant_sudo.create({'product_id':move.product_id.id,
                                        'location_id':move.location_dest_id.id,
                                        'qty':move_qty*-1,
                                        'in_date':move.picking_id and move.picking_id.min_date or ''})
            
        for move in self.move_lines:
            move.write({'state':'draft'})
        self.write({'state':'draft'})
        
        # delete the accounting entry if any
        account_move_sudo = self.env['account.move'].sudo()
        account_moves = account_move_sudo.search([('ref','=',self.name)])
        if len(account_moves):
            for account_move in account_moves:
                account_move.write({'state':'draft'})
                account_move.unlink()
                
        return True        
    
    @api.multi
    def action_confirm(self):
        print"Picking: foodex action_confirm called: ",self
        res = super(Picking, self).action_confirm()
        # if allow negative qty feature
        user = self.env['res.users'].browse(self.env.uid)
        allow_negative = user.has_group('direct_sale.group_allow_negative_qty')
        if self.picking_type_id.code !='incoming' and allow_negative:
            if self.state not in ('assigned','confirmed','done','cancel'):
                print"calling ffffffffffffffffffffffffffffffffffff a and act confirm formn act Confirm() state---",self.state
                self.force_assign()
#        for picking in self:
#            if picking.picking_type_id.code == 'internal':
#                picking.action_assign()
#                picking.do_new_transfer()

        return res
    
    @api.multi
    def action_assign(self):
        print"Picking: foodex action_assign called"
        user = self.env['res.users'].browse(self.env.uid)
        allow_negative = user.has_group('direct_sale.group_allow_negative_qty')
        if not allow_negative:
            for picking in self:
                if picking.picking_type_id.code =='incoming':
                    continue
                for move in picking.move_lines:
                    product = move.product_id
                    available_stock = product.with_context(
                        {'location': move.location_id.id, 'compute_child': False}).qty_available
                    if move.product_qty > available_stock:
                        raise Warning(('Not enough quantity for %s .') % (product.name))
                    
        res = super(Picking, self).action_assign()
        # if allow negative qty feature
        if allow_negative:
            if self.state not in ('assigned','done','cancel'):
                print"calling ffffffffffffffffffffffffffffffffffff a and act confirm state: ",self.state
                self.force_assign()
#                self.action_confirm()
        return res
        
        
class Move(models.Model):
    _inherit = "stock.move"
    
    @api.model
    def create(self, vals):
        picking_id = vals.get('picking_id',False)
        if picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            min_date = picking.min_date
            if min_date:
                vals['date'] = min_date
                vals['date_expected'] = min_date
                
        return super(Move, self).create(vals)
            
    
    # inhertied to allow customer location move tobe in available state
    @api.multi
    def action_assign(self, no_prepare=False):
        print"Move: foodex action_assign called"
        """ Checks the product type and accordingly writes the state. """
        # TDE FIXME: remove decorator once everything is migrated
        # TDE FIXME: clean me, please
        main_domain = {}

        Quant = self.env['stock.quant']
        Uom = self.env['product.uom']
        moves_to_assign = self.env['stock.move']
        moves_to_do = self.env['stock.move']
        operations = self.env['stock.pack.operation']
        ancestors_list = {}

        # work only on in progress moves
        moves = self.filtered(lambda move: move.state in ['confirmed', 'waiting', 'assigned'])
        moves.filtered(lambda move: move.reserved_quant_ids).do_unreserve()
        user = self.env['res.users'].browse(self.env.uid)
        allow_negative = user.has_group('direct_sale.group_allow_negative_qty')
        for move in moves:
            # custom
            if move.location_id.usage !='incoming' and allow_negative:
                moves_to_assign |= move
            # custom
            if move.location_id.usage in ('supplier', 'inventory', 'production','customer'):
                moves_to_assign |= move
                # TDE FIXME: what ?
                # in case the move is returned, we want to try to find quants before forcing the assignment
                if not move.origin_returned_move_id:
                    continue
            # if the move is preceeded, restrict the choice of quants in the ones moved previously in original move
            ancestors = move.find_move_ancestors()
            if move.product_id.type == 'consu' and not ancestors:
                moves_to_assign |= move
                continue
            else:
                moves_to_do |= move

                # we always search for yet unassigned quants
                main_domain[move.id] = [('reservation_id', '=', False), ('qty', '>', 0)]

                ancestors_list[move.id] = True if ancestors else False
                if move.state == 'waiting' and not ancestors:
                    # if the waiting move hasn't yet any ancestor (PO/MO not confirmed yet), don't find any quant available in stock
                    main_domain[move.id] += [('id', '=', False)]
                elif ancestors:
                    main_domain[move.id] += [('history_ids', 'in', ancestors.ids)]

                # if the move is returned from another, restrict the choice of quants to the ones that follow the returned move
                if move.origin_returned_move_id:
                    main_domain[move.id] += [('history_ids', 'in', move.origin_returned_move_id.id)]
                for link in move.linked_move_operation_ids:
                    operations |= link.operation_id

        # Check all ops and sort them: we want to process first the packages, then operations with lot then the rest
        operations = operations.sorted(key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (x.package_id and -2 or 0) + (x.pack_lot_ids and -1 or 0))
        for ops in operations:
            # TDE FIXME: this code seems to be in action_done, isn't it ?
            # first try to find quants based on specific domains given by linked operations for the case where we want to rereserve according to existing pack operations
            if not (ops.product_id and ops.pack_lot_ids):
                for record in ops.linked_move_operation_ids:
                    move = record.move_id
                    if move.id in main_domain:
                        qty = record.qty
                        domain = main_domain[move.id]
                        if qty:
                            quants = Quant.quants_get_preferred_domain(qty, move, ops=ops, domain=domain, preferred_domain_list=[])
                            Quant.quants_reserve(quants, move, record)
            else:
                lot_qty = {}
                rounding = ops.product_id.uom_id.rounding
                for pack_lot in ops.pack_lot_ids:
                    lot_qty[pack_lot.lot_id.id] = ops.product_uom_id._compute_quantity(pack_lot.qty, ops.product_id.uom_id)
                for record in ops.linked_move_operation_ids:
                    move_qty = record.qty
                    move = record.move_id
                    domain = main_domain[move.id]
                    for lot in lot_qty:
                        if float_compare(lot_qty[lot], 0, precision_rounding=rounding) > 0 and float_compare(move_qty, 0, precision_rounding=rounding) > 0:
                            qty = min(lot_qty[lot], move_qty)
                            quants = Quant.quants_get_preferred_domain(qty, move, ops=ops, lot_id=lot, domain=domain, preferred_domain_list=[])
                            Quant.quants_reserve(quants, move, record)
                            lot_qty[lot] -= qty
                            move_qty -= qty

        # Sort moves to reserve first the ones with ancestors, in case the same product is listed in
        # different stock moves.
        for move in sorted(moves_to_do, key=lambda x: -1 if ancestors_list.get(x.id) else 0):
            # then if the move isn't totally assigned, try to find quants without any specific domain
            if move.state != 'assigned' and not self.env.context.get('reserve_only_ops'):
                qty_already_assigned = move.reserved_availability
                qty = move.product_qty - qty_already_assigned

                quants = Quant.quants_get_preferred_domain(qty, move, domain=main_domain[move.id], preferred_domain_list=[])
                Quant.quants_reserve(quants, move)

        # force assignation of consumable products and incoming from supplier/inventory/production
        # Do not take force_assign as it would create pack operations
        if moves_to_assign:
            moves_to_assign.write({'state': 'assigned'})
        if not no_prepare:
            self.check_recompute_pack_op()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
