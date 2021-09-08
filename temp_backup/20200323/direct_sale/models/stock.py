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
    
    
class PackOperation(models.Model):
    _inherit = 'stock.pack.operation'  
    
    # inherited to add the picking date
    @api.model
    def create(self, vals):
        if vals.get('picking_id',False):
            picking = self.env['stock.picking'].browse(vals['picking_id'])
            vals['date'] = picking.min_date

        return super(PackOperation, self).create(vals)


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
    
    
    # do comment this in default stock/sock_picking.py
    @api.one
    def _compute_dates(self):
        min_date=False
        if not self.min_date:
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
        self.move_lines.write({'date_expected': self.min_date,'date':self.min_date})
        
    @api.onchange('min_date')
    def onchange_min_date(self):
        for move in self.move_lines:
            move.date = self.min_date
            move.date_expected = self.min_date
            move.write({'date':self.min_date,'date_expected':self.min_date})        
        for p in self.pack_operation_product_ids:
            p.date = self.min_date
            p.write({'date':self.min_date})
#    
#    min_date = fields.Datetime(
#        'Scheduled Date', compute='_compute_dates', inverse='_set_min_date', store=True,
#        index=True, track_visibility='onchange',
#        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
#        default=_default_min_date,
#        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")
    min_date = fields.Datetime(
        'Scheduled Date', compute='_compute_dates', inverse='_set_min_date', store=True,
        index=True, track_visibility='onchange',default=_default_min_date,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, copy=True,
        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")        
    invoice_type = fields.Selection([('normal', 'Normal Invoice'), ('sample', 'Sample Invoice')], string='Invoice Type',
                                     default='normal')
    account_move_id = fields.Many2one('account.move', string='Journal Entry',
        readonly=True, index=True, copy=False,
        help="Link to the automatically generated Journal Items.")                                     


class Move(models.Model):
    _inherit = 'stock.move'

    account_invoice_line_id = fields.Many2one('account.invoice.line', string="Invoice Line")
    from_location_qty = fields.Float(string="From Location Qty")
    to_location_qty = fields.Float(string="To Location Qty")
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        super(Move, self).onchange_product_id()
        from_product = self.product_id.with_context({'location': self.location_id.id, 'compute_child': False})
        to_product = self.product_id.with_context({'location': self.location_dest_id.id, 'compute_child': False})
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
                print"min_date: ",min_date
            if move.inventory_id:
                date = move.inventory_id.date
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
                
        return super(Move, self).create(vals)    
   

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
        partner = False
        new_move_name = False
        if picking:
            partner = picking.partner_id or False
            if picking.invoice_type == 'sample':
                new_move_name = picking.origin or False
        if not AccountMove:
            for each in move_lines:
                if each[2]:
                    each[2]['name'] = '/'
                    if move.inventory_id:
                        each[2]['name'] = move.inventory_id.name
                    elif move.purchase_line_id:
                        each[2]['name'] = move.purchase_line_id.order_id.name
                    if new_move_name:
                        each[2]['name'] = new_move_name
                    each[2]['product_id'] = False
                    each[2]['product_uom_id'] = False
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            move_vals = {
                'journal_id': journal_id,
                'line_ids': move_lines,
#                'date': date,
                'date': move.picking_id and move.picking_id.min_date or date,
                'ref': name}
            if partner:
                move_vals['salesman_id'] = partner.user_id and partner.user_id.id or False
                move_vals['division_id'] = partner.customer_division_id and partner.customer_division_id.id or False
            new_account_move = AccountMove.create(move_vals)
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
            if picking:
                picking.write({'account_move_id':AccountMove.id})

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
        picking = move.picking_id or False
        partner = False
        if picking and picking.invoice_type:
            if picking.invoice_type == 'sample':
                dental_account_ids = self.env['account.account'].search([('name','=','Cost of Dental Samples')])
                pharma_account_ids = self.env['account.account'].search([('name','=','Cost of Pharma Samples')])

                partner = picking.partner_id or False
                if partner:
                    customer_division = partner.customer_division_id or False
                    if customer_division:
                        if customer_division.name == 'Dental':
                            if len(dental_account_ids):
                                debit_account_id = dental_account_ids[0].id
                        if customer_division.name == 'Pharma':
                            if len(pharma_account_ids):
                                debit_account_id = pharma_account_ids[0].id
        
        # group quants by cost
        quant_cost_qty = defaultdict(lambda: 0.0)
        for quant in self:
            quant_cost_qty[quant.cost] += quant.qty

        AccountMove = self.env['account.move']
        new_account_move = self.env['account.move']
        for cost, qty in quant_cost_qty.iteritems():
            new_lst = []
            move_lines = move._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
            if move_lines:
                if move.inventory_id and move.inventory_id.group_by_account and not self._context.get('active_model') == 'product.product':
                    self.group_by_account(move, move_lines, credit_account_id, debit_account_id, journal_id)
                elif move.picking_id and move.picking_id.picking_type_id.group_by_account:
                    self.group_by_account(move, move_lines, credit_account_id, debit_account_id, journal_id)
                else:
                    date = self._context.get('force_period_date', fields.Date.context_today(self))
                    if picking:
                        date = picking.min_date
                    vals = {
                        'journal_id': journal_id,
                        'line_ids': move_lines,
                        'date': date,
                        'ref': move.picking_id.name}
                    if partner:
                        vals['salesman_id'] = partner.user_id and partner.user_id.id or False
                        vals['division_id'] = partner.customer_division_id and partner.customer_division_id.id or False
#                        vals['department_id']
                    new_account_move = AccountMove.create(vals)
                    new_account_move.post()
                    if picking:
                        picking.write({'account_move_id':new_account_move.id})


class stock_inventory(models.Model):
    _inherit = "stock.inventory"

    group_by_account = fields.Boolean(string="Account Group", default=True)
    
    @api.multi
    def recalculate_qty(self):
        for line in self.line_ids_two:
#            # Theoretical qty
            theoretical_qty = sum([x.qty for x in line._get_quants()])
            if theoretical_qty and line.product_uom_id and line.product_id.uom_id != line.product_uom_id:
                theoretical_qty = line.product_id.uom_id._compute_quantity(theoretical_qty, line.product_uom_id)
            line.theoretical_qty = theoretical_qty
            print"theoretical_qty: ",theoretical_qty
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
        if raise_message:
            raise UserError(_(out_message))
        # custom code ends
        self.action_check()
        self.write({'state': 'done'})
        self.post_inventory()
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: