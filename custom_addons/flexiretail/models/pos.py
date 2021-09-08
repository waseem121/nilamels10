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
import logging
# import datetime
import psycopg2
import time
import pytz

# from openerp.osv import osv,fields as field7
from openerp import netsvc, tools, models, SUPERUSER_ID, fields, api, tools, _
from openerp.tools import float_is_zero
from openerp.exceptions import Warning, UserError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from pytz import timezone
from datetime import datetime, date, time, timedelta
import time
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

def decimalAdjust(value):
    split_value = [int(ele) for ele in str("{0:.2f}".format(round(value, 2))).split('.')]
    reminder_value = split_value[1] % 10
    division_value = int(split_value[1] / 10)
    rounding_value = 0
    nagative_sign = False
    if split_value[0] == 0 and  value < 0:
        nagative_sign = True
    if reminder_value in range(0, 5):
        rounding_value = eval(str(split_value[0]) + '.' + str(division_value) + '0')
    elif reminder_value in range(5, 10):
        rounding_value = eval(str(split_value[0]) + '.' + str(division_value) + '5')
    if nagative_sign :
        return -rounding_value
    return rounding_value

class pos_order(models.Model):
    _inherit = "pos.order"

    @api.model
    def sales_report_doctor(self,config_id,s_date,e_date):
        session_ids = self.env['pos.session'].search([('config_id', '=', config_id)])
        pos_order_ids = self.search([('session_id', 'in', session_ids.ids),
                                    ('date_order', '>=', s_date + " 00:00:00"),
                                   ('date_order', '<=', e_date + " 23:59:59")])
        res = {'Other': []}
        if pos_order_ids:
            for order in pos_order_ids:
                if order.instructor_id:
                    if order.instructor_id.id not in res:
                        res.update({order.instructor_id.id: []})
                    res[order.instructor_id.id].append({'receipt_ref': order.pos_reference,
                                                        'order_ref' : order.name,
                                                        'date': datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y'),
                                                        'amount': order.amount_total
                                                        })
                else:
                    res['Other'].append({'receipt_ref': order.pos_reference,
                                         'order_ref' : order.name,
                                         'date': datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y'),
                                         'amount': order.amount_total
                                         })
            summary = {}
            for doctor, vals in res.items():
                summary.update({doctor: sum([x['amount'] for x in vals])})
            return {'orders': res, 'summary': summary}
        else:
            return False

    def set_pack_operation_lot(self, picking=None):
        """Set Serial/Lot number in pack operations to mark the pack operation done."""
        StockProductionLot = self.env['stock.production.lot']
        PosPackOperationLot = self.env['pos.pack.operation.lot']
        for order in self:
            for pack_operation in (picking or self.picking_id).pack_operation_ids:
                qty = 0
                qty_done = 0
                pack_lots = []
                production_lot = False
                # merged_prod_lots = {}
                if self.session_id.config_id and not self.session_id.config_id.enable_pos_serial:
                    if pack_operation.product_id.tracking == 'lot':
                        stock_production_lots = StockProductionLot.search([('product_id', '=', pack_operation.product_id.id)], \
                                                                          order='life_date ASC')
                        for lot in stock_production_lots:
                            if any(q.location_id == pack_operation.location_id and q.qty > float(pack_operation.ordered_qty) for q in
                                   lot.quant_ids):
                                production_lot = lot
                                break
                        if production_lot:
                            qty_done = pack_operation.ordered_qty
                            pack_lots.append({'lot_id': production_lot.id, 'qty': pack_operation.ordered_qty})
    
                        pack_operation.write({'pack_lot_ids': map(lambda x: (0, 0, x), pack_lots), 'qty_done': qty_done})
                    else:
                        pack_operation.write({'qty_done': qty_done})
                else:
                    pos_pack_lots = PosPackOperationLot.search([('order_id', '=', order.id), ('product_id', '=', pack_operation.product_id.id)])
                    pack_lot_names = [pos_pack.lot_name for pos_pack in pos_pack_lots]
                    if pack_lot_names:
                        for lot_name in list(set(pack_lot_names)):
                            stock_production_lot = StockProductionLot.search([('name', '=', lot_name), ('product_id', '=', pack_operation.product_id.id)])
                            if stock_production_lot:
                                if stock_production_lot.product_id.tracking == 'lot':
                                    qty = pack_lot_names.count(lot_name)
                                else:
                                    qty = 1.0
                                qty_done += qty
                                pack_lots.append({'lot_id': stock_production_lot.id, 'qty': qty})
                    else:
                        qty_done = pack_operation.product_qty
                    pack_operation.write({'pack_lot_ids': map(lambda x: (0, 0, x), pack_lots), 'qty_done': qty_done})

    @api.multi
    @api.depends('partner_id')
    def get_remaining_points(self):
        for each in self:
            if each.partner_id and each.partner_id.remaining_points:
                each.remaining_points += each.partner_id.remaining_points

#     @api.model
#     def get_lot_near_by_expiry(self, qty, product_id):
#         print "\n\n qty", qty, product_id,
#         date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         print "\n\n --date---", date
#         if qty and product_id:
#             lot_id = self.env['stock.production.lot'].search([('product_id', '=', product_id), ('product_qty', '>', 0)], order='life_date desc')
#             print "\n\n --lot_id--", lot_id
#             for each_lot in lot_id.filtered(lambda l:l.life_date >= date).sorted(key=lambda l: l.life_date):
# #                 sorted_moves = sorted(self, key=lambda a: a.date)
# #             if lot_id.life_date >= date:
#                 print "\n\n --if--lot---", each_lot
#         return True

    @api.multi
    def get_ip(self, order_id):
        if not order_id:
            return False
        order = self.browse(order_id)
        return {
            'ip':order.session_id.config_id.proxy_ip or False,
            'print_via_proxy':order.session_id.config_id.iface_print_via_proxy or False,
        }

    @api.multi
    def get_journal_amt(self, order_id):
        data = {}
        sql = """ select aj.name,absl.amount as amt from account_bank_statement as abs
                        LEFT JOIN account_bank_statement_line as absl ON abs.id = absl.statement_id
                        LEFT JOIN account_journal as aj ON aj.id = abs.journal_id
                        WHERE absl.pos_statement_id =%d""" % (order_id)
        self._cr.execute(sql)
        data = self._cr.dictfetchall()
        return data

    @api.multi
    def _get_is_refundable(self):
        for self_rec in self:
            self_rec.is_refundable = 'yes'
            if self_rec.refund_order_id or self_rec.state == 'draft':
                self_rec.is_refundable = 'no'
                continue
            refund_order_ids = self.search([('refund_order_id', '=', self_rec.id)])
            line_dict = {}
            org_line = dict([(x.product_id.id, -1 * x.qty) for x in
                             self_rec.lines])
            for refund_order_id in refund_order_ids:
                for ref_line in refund_order_id.lines:
                    if ref_line.product_id.id not in line_dict:
                        line_dict[ref_line.product_id.id] = 0
                    line_dict[ref_line.product_id.id] += ref_line.qty
            for process_line in org_line:
                if (process_line in line_dict and
                    org_line[process_line] >= line_dict[process_line]):
                    self_rec.is_refundable = 'no'
                    continue
                self_rec.is_refundable = 'yes'
                break

    parent_return_order = fields.Char('Return Order ID', size=64)
    return_seq = fields.Integer('Return Sequence')
    return_process = fields.Boolean('Return Process')
    back_order = fields.Char('Back Order', size=256, default=False, copy=False)
    refund_order_id = fields.Many2one('pos.order', 'Refund Order')
    is_refundable = fields.Selection([('yes', 'yes'), ('no', 'no')],
                                     string="Is Refundable", compute='_get_is_refundable')
    ref_cust_id = fields.Many2one('res.partner', 'Reference of')
    points_to_use = fields.Float(string='Points to Use')
    remaining_points = fields.Float(compute='get_remaining_points', string="Remaining Points")
    redeem_point_amt = fields.Float('Redeem Point Amount', readonly=True)
    # gift_coupon_amt =  fields.Float('Gift Coupon Amt', readonly=True)
    delivery_date = fields.Char("Delivery Date")
    delivery_time = fields.Char("Delivery Time")
    ret_to_bonus = fields.Boolean('Return to Bonus')
    # applied_coupon_ref = fields.Many2many('pos.coupon.history', string="Applied Coupon Ref.")
    customer_email = fields.Char('Customer Email')
    reserved = fields.Boolean("Reserved", readonly=True)
    order_booked = fields.Boolean("Booked", readonly=True)
    unreserved = fields.Boolean("Unreserved")
    amount_due = fields.Float(string='Amount Due', compute='_compute_amount_due')
    cancel_order = fields.Char('Cancel Order')
    order_status = fields.Selection([('full', 'Fully Cancelled'), ('partial', 'Partially Cancelled')],
                                    'Order Status', compute="_find_order_status")
    fresh_order = fields.Boolean("Fresh Order")
    partial_pay = fields.Boolean("Partial Pay", readonly=True)
    is_rounding = fields.Boolean("Is Rounding")
    rounding_option = fields.Char("Rounding Option")
    rounding = fields.Float(string='Rounding', digits=dp.get_precision('Product Price'))
    amount_tax = fields.Float(compute='_compute_amount_all', string='Taxes', digits=dp.get_precision('Product Price'))
    amount_total = fields.Float(compute='_compute_amount_all', string='Total', digits=dp.get_precision('Product Price'))
    amount_paid = fields.Float(compute='_compute_amount_all', string='Paid', states={'draft': [('readonly', False)]}, readonly=True,digits=dp.get_precision('Product Price'))
    # aspl_pos_stock
    picking_ids = fields.Many2many(
        "stock.picking",
        string="Multiple Picking",
        copy=False)
    
#     amount_due = fields.Float(
#         string='Amount Due',
#         compute='_compute_amount_due')
    rounding = fields.Float(string='Rounding', digits=0)
#     amount_tax = fields.Float(
#         compute='_compute_amount_all',
#         string='Taxes',
#         digits=0)
#     amount_total = fields.Float(
#         compute='_compute_amount_all',
#         string='Total',
#         digits=0)
#     amount_paid = fields.Float(
#         compute='_compute_amount_all',
#         string='Paid',
#         digits=0)
#     amount_return = fields.Float(
#         compute='_compute_amount_all',
#         string='Returned',
#         digits=0)
    picking_ids = fields.Many2many(
        "stock.picking",
        string="Multiple Picking",
        copy=False)

    def _order_fields(self, ui_order):
        res = super(pos_order, self)._order_fields(ui_order)
        res.update({
            'return_order':         ui_order.get('return_order', ''),
            'back_order':           ui_order.get('back_order', ''),
            'parent_return_order':  ui_order.get('parent_return_order', ''),
            'return_seq':           ui_order.get('return_seq', ''),
            'note':                 ui_order.get('order_note') or False,
            'ref_cust_id':          ui_order.get('ref_cust_id') or False,
            'points_to_use':        ui_order.get('points_to_use') or False,
            'redeem_point_amt':     ui_order.get('redeem_point_amt') or 0.0,
            # 'gift_coupon_amt':      ui_order.get('gift_coupon_amt') or 0.0,
            'delivery_date':        ui_order.get('delivery_date') or False,
            'delivery_time':        ui_order.get('delivery_time') or False,
            'ret_to_bonus':         ui_order.get('bonus_from_ret'),
            'customer_email':       ui_order.get('customer_email'),
            'order_booked' :        ui_order.get('reserved') or False,
            'reserved':             ui_order.get('reserved') or False,
            'cancel_order':         ui_order.get('cancel_order_ref') or False,
            'fresh_order':          ui_order.get('fresh_order') or False,
            'partial_pay':          ui_order.get('partial_pay') or False,
            'is_rounding':          ui_order.get('is_rounding') or False,
            'rounding_option':      ui_order.get('rounding_option') or False,
        })
        return res

    @api.model
    def check_valid_session(self,session_id):
        pos_session = self.env['pos.session'].search([('id','=',session_id)])
        if pos_session.state != 'closing_control' and pos_session.state != 'closed':
            return False
        else:
            return True

    @api.model
    def _process_order(self, order):
        config_obj = self.env['pos.session'].browse(order.get('pos_session_id')).config_id
        # gift_coupon_amt = 0.0
        pos_session = self.env['pos.session'].browse(order['pos_session_id'])
#         if pos_session.state == 'closing_control' or pos_session.state == 'closed':
#             raise UserError(_("You can not make an order in closed session!! Please logout and login again."))
#             order['pos_session_id'] = self._get_valid_session(order).id

        redeem_amount = 0.0
        pos_line_obj = self.env['pos.order.line']
        move_obj = self.env['stock.move']
        picking_obj = self.env['stock.picking']
        stock_imm_tra_obj = self.env['stock.immediate.transfer']
        draft_order_id = order.get('old_order_id')
        picking_type_id = False
        picking_id_cust = False
        picking_id_rev = False
        if order.get('draft_order'):
            if not draft_order_id:
                order.pop('draft_order')
                order_id = self.with_context({ 'from_pos':True }).create(self._order_fields(order))
                return order_id
            else:
                order_id = draft_order_id
                pos_line_ids = pos_line_obj.search([('order_id', '=', order_id)])
                if pos_line_ids:
                    pos_line_obj.unlink(pos_line_ids)
                order_id.write({'lines': order['lines'],
                            'partner_id': order.get('partner_id')})
                return order_id
        if not order.get('draft_order') and draft_order_id and order.get('cancel_order'):
            order_obj = self.browse(draft_order_id)
            pos_line_ids = pos_line_obj.search([('order_id', '=', draft_order_id)])
            temp = order.copy()
            temp.pop('statement_ids', None)
            temp.pop('name', None)
            temp.update({
                'date_order': order.get('creation_date')
            })
            warehouse_id = self.env['stock.warehouse'].search([
                    ('lot_stock_id', '=', order_obj.config_id.stock_location_id.id)], limit=1)
            location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()
            if warehouse_id:
                picking_type_id = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', warehouse_id.id), ('code', '=', 'internal')])
            for line in order.get('lines'):
                prod_id = self.env['product.product'].browse(line[2].get('product_id'))
                prod_dict = line[2]
                if prod_id.type != 'service' and prod_dict and prod_dict.get('cancel_item'):
                    # customer delivery order
                    picking_type_out = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', order_obj.picking_id.picking_type_id.warehouse_id.id), ('code', '=', 'outgoing')], limit=1)
                    if picking_type_out:
                        picking_id_cust = picking_obj.create({
                                'name' : picking_type_out.sequence_id.next_by_id(),
                                'picking_type_id': picking_type_out.id,
                                'location_id': order_obj.config_id.reserve_stock_location_id.id,
                                'location_dest_id': location_dest_id.id,
                                'state': 'draft',
                                'origin':order_obj.name
                            })
                    if order_obj.picking_id:
                        # unreserve order
                        picking_id_rev = picking_obj.create({
                                'name' : picking_type_out.sequence_id.next_by_id(),
                                'picking_type_id': order_obj.picking_id.picking_type_id.id,
                                'location_id': order_obj.config_id.reserve_stock_location_id.id,
                                'location_dest_id': order_obj.config_id.stock_location_id.id,
                                'state': 'draft',
                                'origin':order_obj.name
                            })
                        if prod_dict.get('consider_qty') and not order_obj.order_status == 'partial' and not order.get('reserved'):
                            move_obj.create({
                                    'product_id': prod_id.id,
                                    'name': prod_id.name,
                                    'product_uom_qty': prod_dict.get('consider_qty'),
                                    'location_id': order_obj.config_id.reserve_stock_location_id.id,
                                    'location_dest_id': location_dest_id.id,
                                    'product_uom': prod_id.uom_id.id,
                                    'origin' : order_obj.name,
                                    'picking_id' : picking_id_cust.id
                                })
                        if prod_dict.get('cancel_qty'):
                            move_obj.create({
                                    'product_id': prod_id.id,
                                    'name': prod_id.name,
                                    'product_uom_qty': abs(prod_dict.get('cancel_qty')),
                                    'location_id': order_obj.config_id.reserve_stock_location_id.id,
                                    'location_dest_id': order_obj.config_id.stock_location_id.id,
                                    'product_uom': prod_id.uom_id.id,
                                    'origin' : order_obj.name,
                                    'picking_id' : picking_id_rev.id
                                })
            if picking_id_cust and picking_id_cust.move_lines:
                picking_id_cust.action_confirm()
                picking_id_cust.force_assign()
                picking_id_cust.do_new_transfer()
                stock_transfer_id = stock_imm_tra_obj.search([('pick_id', '=', picking_id_cust.id)], limit=1).process()
                if stock_transfer_id:
                    stock_transfer_id.process()
                order_obj.with_context({'out_order' :True}).write({'picking_id' : picking_id_cust.id, 'unreserved':True})
            elif picking_id_cust:
                picking_id_cust.unlink()
            if picking_id_rev and picking_id_rev.move_lines:
                picking_id_rev.action_confirm()
                picking_id_rev.force_assign()
                picking_id_rev.do_new_transfer()
                stock_transfer_id = stock_imm_tra_obj.search([('pick_id', '=', picking_id_rev.id)], limit=1).process()
                if stock_transfer_id:
                    stock_transfer_id.process()
                order_obj.with_context({'out_order' :True}).write({'picking_id' : picking_id_rev.id, 'unreserved':True})
            elif picking_id_rev:
                picking_id_rev.unlink()
            order_obj.write(temp)
            for payments in order['statement_ids']:
                order_obj.with_context({'from_pos':True}).add_payment(self._payment_fields(payments[2]))

            session = self.env['pos.session'].browse(order['pos_session_id'])
            if session.sequence_number <= order['sequence_number']:
                session.write({'sequence_number': order['sequence_number'] + 1})
                session.refresh()

            if not float_is_zero(order['amount_return'], self.env['decimal.precision'].precision_get('Account')) or order['cancel_order']:
                cash_journal = session.cash_journal_id
                if not cash_journal:
                    cash_journal_ids = filter(lambda st: st.journal_id.type == 'cash', session.statement_ids)
                    if not len(cash_journal_ids):
                        raise Warning(_('error!'),
                                             _("No cash statement found for this session. Unable to record returned cash."))
                    cash_journal = cash_journal_ids[0].journal_id
                order_obj.with_context({'from_pos':True}).add_payment({
                    'amount':-order['amount_return'],
                    'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_name': _('return'),
                    'journal': cash_journal.id,
                })
            return order_obj

        if not order.get('draft_order') and draft_order_id and not order.get('cancel_order'):
            order_id = self.browse(draft_order_id)
            
            pos_line_ids = pos_line_obj.search([('order_id', '=', order_id.id)])
            if pos_line_ids:
                for line_id in pos_line_ids:
                    line_id.unlink()

            warehouse_id = self.env['stock.warehouse'].search([
                    ('lot_stock_id', '=', order_id.config_id.stock_location_id.id)], limit=1)
            location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()
            if warehouse_id:
                picking_type_id = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', warehouse_id.id), ('code', '=', 'internal')])
            for line in order.get('lines'):
                prod_id = self.env['product.product'].browse(line[2].get('product_id'))
                prod_dict = line[2]
                if prod_id.type != 'service' and prod_dict and prod_dict.get('cancel_item'):
                    # customer delivery order
                    picking_type_out = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', order_id.picking_id.picking_type_id.warehouse_id.id), ('code', '=', 'outgoing')], limit=1)
                    if picking_type_out:
                        picking_id_cust = picking_obj.create({
                                'name' : picking_type_out.sequence_id.next_by_id(),
                                'picking_type_id': picking_type_out.id,
                                'location_id': order_id.config_id.reserve_stock_location_id.id,
                                'location_dest_id': location_dest_id.id,
                                'state': 'draft',
                                'origin':order_id.name
                            })
                    if order_id.picking_id:
                        # unreserve order
                        picking_id_rev = picking_obj.create({
                                'name' : picking_type_out.sequence_id.next_by_id(),
                                'picking_type_id': order_id.picking_id.picking_type_id.id,
                                'location_id': order_id.config_id.reserve_stock_location_id.id,
                                'location_dest_id': order_id.config_id.stock_location_id.id,
                                'state': 'draft',
                                'origin':order_id.name
                            })
                        if prod_dict.get('consider_qty') and not order_id.order_status == 'partial' and not order.get('reserved'):
                            move_obj.create({
                                    'product_id': prod_id.id,
                                    'name': prod_id.name,
                                    'product_uom_qty': prod_dict.get('consider_qty'),
                                    'location_id': order_id.config_id.reserve_stock_location_id.id,
                                    'location_dest_id': location_dest_id.id,
                                    'product_uom': prod_id.uom_id.id,
                                    'origin' : order_id.name,
                                    'picking_id' : picking_id_cust.id
                                })
                        if prod_dict.get('cancel_qty'):
                            move_obj.create({
                                    'product_id': prod_id.id,
                                    'name': prod_id.name,
                                    'product_uom_qty': abs(prod_dict.get('cancel_qty')),
                                    'location_id': order_id.config_id.reserve_stock_location_id.id,
                                    'location_dest_id': order_id.config_id.stock_location_id.id,
                                    'product_uom': prod_id.uom_id.id,
                                    'origin' : order_id.name,
                                    'picking_id' : picking_id_rev.id
                                })
            if picking_id_cust and picking_id_cust.move_lines:
                picking_id_cust.action_confirm()
                picking_id_cust.force_assign()
                picking_id_cust.do_new_transfer()
                stock_transfer_id = stock_imm_tra_obj.search([('pick_id', '=', picking_id_cust.id)], limit=1).process()
                if stock_transfer_id:
                    stock_transfer_id.process()
                order_id.with_context({'out_order' :True}).write({'picking_id' : picking_id_cust.id, 'unreserved':True})
            elif picking_id_cust:
                picking_id_cust.unlink()
            if picking_id_rev and picking_id_rev.move_lines:
                picking_id_rev.action_confirm()
                picking_id_rev.force_assign()
                picking_id_rev.do_new_transfer()
                stock_transfer_id = stock_imm_tra_obj.search([('pick_id', '=', picking_id_rev.id)], limit=1).process()
                if stock_transfer_id:
                    stock_transfer_id.process()
                order_id.with_context({'out_order' :True}).write({'picking_id' : picking_id_rev.id, 'unreserved':True})
            elif picking_id_rev:
                picking_id_rev.unlink()
            order_id.write({
                'lines': order['lines'],
                'partner_id': order.get('partner_id'),
                'reserved': order.get('reserved'),
                'partial_pay': order.get('partial_pay'),
            })
            for payments in order['statement_ids']:
                order_id.with_context({'from_pos':True}).add_payment(self._payment_fields(payments[2]))

            session = self.env['pos.session'].browse(order['pos_session_id'])
            if session.sequence_number <= order['sequence_number']:
                session.write({'sequence_number': order['sequence_number'] + 1})
                session.refresh()

            if not float_is_zero(order['amount_return'], self.env['decimal.precision'].precision_get('Account')):
                cash_journal = session.cash_journal_id
                if not cash_journal:
                    cash_journal_ids = filter(lambda st: st.journal_id.type == 'cash', session.statement_ids)
                    if not len(cash_journal_ids):
                        raise Warning(_('error!'),
                                             _("No cash statement found for this session. Unable to record returned cash."))
                    cash_journal = cash_journal_ids[0].journal_id
                order_id.add_payment({
                    'amount':-order['amount_return'],
                    'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_name': _('return'),
                    'journal': cash_journal.id,
                })
            return order_id
        if not order.get('draft_order') and not draft_order_id:
            # updated context value into order gift_coupon_amt and redeem_point_amt field
            # if self._context.get('gift_amount'):
                # gift_coupon_amt = self._context.get('gift_amount')
                # order.update({'gift_coupon_amt': gift_coupon_amt})
            if self._context.get('redeem_amount'):
                redeem_amount = self._context.get('redeem_amount')
                order.update({'redeem_point_amt': redeem_amount})
            # if self._context.get('bonus_amt'):
            #     bonus_discount = self._context.get('bonus_amt', 0.0)

            order_id = self.with_context({ 'from_pos':True }).create(self._order_fields(order))
            for payments in order['statement_ids']:
                if not order.get('sale_mode') and order.get('parent_return_order', ''):
                    payments[2]['amount'] = payments[2]['amount'] or 0.0
                order_id.add_payment(self._payment_fields(payments[2]))
            session = self.env['pos.session'].browse(order['pos_session_id'])
            if session.sequence_number <= order['sequence_number']:
                session.write({'sequence_number': order['sequence_number'] + 1})
                session.refresh()

            if not order.get('parent_return_order', '') and not float_is_zero(order['amount_return'], self.env['decimal.precision'].precision_get('Account')):
                cash_journal = session.cash_journal_id
                if not cash_journal:
                    cash_journal_ids = filter(lambda st: st.journal_id.type == 'cash' and st.journal_id.is_cashdrawer, session.statement_ids)
                    if not len(cash_journal_ids):
                        raise Warning(_('error!'),
                            _("No cash statement found for this session. Unable to record returned cash."))
                    cash_journal = cash_journal_ids[0].journal_id
                order_id.add_payment({
                    'amount':-order['amount_return'],
                    'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_name': _('return'),
                    'journal': cash_journal.id,
                })

            if order.get('parent_return_order', '') and not float_is_zero(order['amount_return'], self.env['decimal.precision'].precision_get('Account')):
                cash_journal = session.cash_journal_id
                if not cash_journal:
                    cash_journal_ids = filter(lambda st: st.journal_id.type == 'cash' and st.journal_id.is_cashdrawer, session.statement_ids)
                    if not len(cash_journal_ids):
                        raise Warning(_('error!'),
                            _("No cash statement found for this session. Unable to record returned cash."))
                    cash_journal = cash_journal_ids[0].journal_id
                order_id.add_payment({
                    'amount':-order['amount_return'],
                    'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_name': _('return'),
                    'journal': cash_journal.id,
                })

#             Bonus Coupon
#             if self._context.get('bonus_amt'):
#                 bonus_discount = self._context.get('bonus_amt', 0.0)
#                 if bonus_discount:
#                     bonus_discount_journal = self.env['account.journal'].search([('code', '=', 'BNSJ')])
#                     if bonus_discount_journal:
#                         order_id.with_context({'bonus_discount': True}).add_payment({
#                             'amount': bonus_discount,
#                             'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
#                             'payment_name': _('Discount'),
#                             'journal': bonus_discount_journal[0],
#         #                        'statement_id': payment['statement_id']    All payment journals will be same if we remove this comment.,
#                         })

            # for loyalty
            if order_id:
                if order.get('rounding'):
                    order_id.write({'rounding': order.get('rounding', 0.00)})
                    rounding_journal_id = order_id.session_id.config_id.rounding_journal_id
                    if rounding_journal_id:
                        order_id.add_payment({
                            'amount':order.get('rounding') * -1,
                            'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'payment_name': _('Rounding'),
                            'journal': rounding_journal_id.id,
                        })
                employee_id = False
                loyalty_group_obj = self.env['loyalty.group']
                order_rec = order_id
                if order_rec.user_id:
                    employee_id = self.env['hr.employee'].search([('user_id', '=', order_rec.user_id.id)], limit=1)
                amount_total = order_rec.amount_total - order_rec.redeem_point_amt
                if order_rec.partner_id:
                    # customer redeem point deduction line create
                    cust_cur_point = 0.0
                    if order_rec.points_to_use:
                        cust_redeem_points_data = {
                            'partner_id': order_rec.partner_id.id,
                            'ref_partner_id' : False,
                            'pos_order_id':order_rec.id,
                            'order_name':order_rec.name,
                            'sale_id':False,
                            'amount_total': amount_total,
                            'point': order_rec.points_to_use
                        }
                        self.env['res.partner.point.redeem'].create(cust_redeem_points_data)
                    # find group of customer group and calculate the points
                    group_id = loyalty_group_obj.search([('type', '=', 'customer_group'), ('customer_ids', 'in', order_rec.partner_id.id)])
                    if group_id:
                        group_rec = group_id
                        if not self._context.get('return_order'):
                            cust_cur_point = (amount_total * group_rec.customer_loyalty_point) / 100
                            if cust_cur_point > 0.0 and amount_total >= group_rec.minimum_purchase:
                                customer_points_data = {
                                    'partner_id': order_rec.partner_id.id,
                                    'ref_partner_id' : False,
                                    'pos_order_id':order_rec.id,
                                    'order_name':order_rec.name,
                                    'sale_id':False,
                                    'amount_total': amount_total,
                                    'point': cust_cur_point
                                }
                                self.env['res.partner.point'].create(customer_points_data)
                        else:
                            cust_return_point = (abs(amount_total) * abs(group_rec.customer_loyalty_point)) / 100
                            if cust_return_point > 0.0 and abs(amount_total) >= abs(group_rec.minimum_return):
                                customer_points_data = {
                                    'partner_id': order_rec.partner_id.id,
                                    'ref_partner_id' : False,
                                    'pos_order_id':order_rec.id,
                                    'order_name':order_rec.name,
                                    'sale_id':False,
                                    'amount_total': amount_total,
                                    'point': cust_return_point
                                }
                                self.env['res.partner.point.redeem'].create(customer_points_data)
                    if order_rec.ref_cust_id:
                        ref_cur_point = 0.0
                        group_id = loyalty_group_obj.search([('type', '=', 'ref_customer_group'),
                                                                      ('customer_ids', 'in', order_rec.ref_cust_id.id)])
                        if group_id:
                            group_rec = loyalty_group_obj.browse(group_id)
                            ref_cur_point = (amount_total * group_rec.id.referral_customer_point) / 100
                            if not group_rec.id.is_perpetuity:
                                point_lines = self.env['res.partner.point'].search([('partner_id' , '=', order_rec.ref_cust_id.id),
                                                                                                  ('ref_partner_id' , '=', order_rec.partner_id.id)])
                                if point_lines:
                                    total_refe_points = sum([line.point for line in self.env['res.partner.point'].browse(point_lines)])
                                    if total_refe_points < group_rec.ref_cust_maximum_points:
                                        left_max_points = group_rec.ref_cust_maximum_points - total_refe_points
                                        if left_max_points <= ref_cur_point:
                                            ref_cur_point = left_max_points
                                    else:
                                        ref_cur_point = 0.0
                            if ref_cur_point > 0.0 and amount_total >= group_rec.id.minimum_purchase:
                                ref_customer_points_data = {
                                    'partner_id': order_rec.ref_cust_id.id,
                                    'ref_partner_id' : order_rec.partner_id and order_rec.partner_id.id or False,
                                    'pos_order_id': order_rec.id,
                                    'sale_id': False,
                                    'amount_total': amount_total,
                                    'point': ref_cur_point
                                }
                                self.env['res.partner.point'].create(ref_customer_points_data)
                    if employee_id:
                        emp_cur_point = 0.0
                        group_id = loyalty_group_obj.search([('type', '=', 'employee_group'),
                                                                      ('employee_ids', 'in', employee_id.id)])
                        if group_id:
                            group_rec = group_id
                            emp_cur_point = (amount_total * group_rec.employee_loyalty_point) / 100
                        if emp_cur_point > 0.0 and amount_total >= group_rec.minimum_purchase:
                            employee_points_data = {
                                'employee_id': employee_id[0],
                                'pos_order_id': order_rec.id,
                                'order_name': order_rec.name,
                                'sale_id': False,
                                'amount_total': amount_total,
                                'point': emp_cur_point,
                            }
                            self.env['hr.employee.point'].create(employee_points_data)
                    if order.get('wallet_type'):
                        if order.get('change_amount_for_wallet'):
                            session_id = order_id.session_id
                            cash_register_id = session_id.cash_register_id
                            if not cash_register_id:
                                raise Warning(_('There is no cash register for this PoS Session'))
                            cash_bocx_in_obj = self.env['cash.box.in'].create({'name': 'Credit', 'amount': order.get('change_amount_for_wallet')})
                            cash_bocx_in_obj._run(cash_register_id)
                            vals = {
                                    'customer_id': order_id.partner_id.id,
                                    'type': order.get('wallet_type'),
                                    'order_id': order_id.id,
                                    'credit': order.get('change_amount_for_wallet'),
                                    'cashier_id': order.get('user_id'),
                                    }
                            self.env['wallet.management'].create(vals)
                        if order.get('used_amount_from_wallet'):
                            vals = {
                                    'customer_id': order_id.partner_id.id,
                                    'type': order.get('wallet_type'),
                                    'order_id': order_id.id,
                                    'debit': order.get('used_amount_from_wallet'),
                                    'cashier_id': order.get('user_id'),
                                    }
                            self.env['wallet.management'].create(vals)
            if order_id.reserved:
                order_id.do_internal_transfer()
            return order_id

    @api.one
    def scrap_picking(self, full=False, scrap_line=[]):
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        address = self.partner_id.address_get(['delivery']) or {}
        picking_type = self.picking_type_id
        return_pick_type = self.picking_type_id.return_picking_type_id or self.picking_type_id
        message = _("This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (self.id, self.name)
        if self.partner_id:
            source_location = self.partner_id.property_stock_customer.id
        else:
            if (not picking_type) or (not picking_type.default_location_dest_id):
                customerloc, supplierloc = StockWarehouse._get_partner_locations()
                source_location = customerloc.id
            else:
                source_location = picking_type.default_location_dest_id.id
        picking_vals = {
            'origin': self.name,
            'partner_id': address.get('delivery', False),
            'date_done': self.date_order,
            'picking_type_id': picking_type.id,
            'company_id': self.company_id.id,
            'move_type': 'direct',
            'note': self.note or "",
            'location_id': source_location,
            'location_dest_id': self.session_id.config_id.scrap_location_id.id,
        }
        return_vals = picking_vals.copy()
        return_vals.update({
            'location_id': source_location,
            'location_dest_id': self.session_id.config_id.scrap_location_id.id,
            'picking_type_id': return_pick_type.id
        })
        return_picking = Picking.create(return_vals)
        return_picking.message_post(body=message)
        for line in scrap_line:
            if line.product_id.is_product_pack:
                for product_pack_id in line.product_id.product_pack_ids:
                    Move.create({
                    'name': product_pack_id.product_id.name,
                    'product_uom': product_pack_id.product_id.uom_id.id,
                    'picking_id': return_picking.id,
                    'picking_type_id': return_pick_type.id,
                    'product_id': product_pack_id.product_id.id,
                    'product_uom_qty': abs(product_pack_id.quantity * line.qty),
                    'state': 'draft',
                    'location_id': source_location,
                    'location_dest_id': self.session_id.config_id.scrap_location_id.id,
                })
            else:
                Move.create({
                    'name': line.name,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': return_picking.id,
                    'picking_type_id': return_pick_type.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.qty),
                    'state': 'draft',
                    'location_id': source_location,
                    'location_dest_id': self.session_id.config_id.scrap_location_id.id,
                })
        if full:
            self.write({'picking_id' : return_picking.id})
        self._force_picking_done(return_picking)
        return True

    @api.model
    def add_payment_from_app(self, order_id, data):
        order = self.browse(order_id)
        statement_ids = []
        if order:
            for payment in data:
                statement_ids.append(order.add_payment(payment))
            if statement_ids:
                return statement_ids
        return False

    @api.model
    def add_payment(self, data):
        """Create a new payment for the order"""
        if data['amount'] == 0.0:
            return
        statement_line_obj = self.env['account.bank.statement.line']
        property_obj = self.env['ir.property']
        date = data.get('payment_date', time.strftime('%Y-%m-%d'))
#         date = datetime.strptime(str(data.get('payment_date')), "%Y-%m-%d %H:%M:%S").date() #.strftime('%Y-%m-%d')
        if len(date) > 10:
            timestamp = datetime.strptime(date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
            ts = fields.Datetime.context_timestamp(self, timestamp)
            date = ts.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        args = {
            'amount': data['amount'],
            'date': date,
            'name': self.name + ': ' + (data.get('payment_name', '') or ''),
            'partner_id': self.env["res.partner"]._find_accounting_partner(self.partner_id).id or False,
        }
        journal_id = data.get('journal', False)
        statement_id = data.get('statement_id', False)
        assert journal_id or statement_id, "No statement_id or journal_id passed to the method!"

        journal = self.env['account.journal'].browse(journal_id)
        # use the company of the journal and not of the current user
        account_def = property_obj.with_context({'force_company': journal.company_id.id}).get('property_account_receivable_id', 'res.partner')
        args['account_id'] = (self.partner_id and self.partner_id.property_account_receivable_id \
                             and self.partner_id.property_account_receivable_id.id) or (account_def and account_def.id) or False

        # Added code for redeem coupon.
        if self._context.get('redeem_point_amt'):
            account_pay = property_obj.get('property_account_payable_id', 'res.partner')
            args['account_id'] = (self.partner_id and self.partner_id.property_account_payable_id \
                             and self.partner_id.property_account_payable_id.id) or (account_pay and account_pay.id) or False
        # Code End for redeem coupon.

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account defined to make payment.')
            else:
                msg = _('There is no receivable account defined to make payment for the partner: "%s" (id:%d).') % (order.partner_id.name, order.partner_id.id,)
            raise UserError(msg)

#         context.pop('pos_session_id', False)

        for statement in self.session_id.statement_ids:
            if statement.id == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == journal_id:
                statement_id = statement.id
                break

        if not statement_id:
            raise UserError(_('You have to open at least one cashbox.'))

        args.update({
            'statement_id': statement_id,
            'pos_statement_id': self.id,
            'journal_id': journal_id,
            'ref': self.session_id.name,
        })
        statement_line_obj.create(args)
        return statement_id

    @api.model
    def check_connection(self):
        return True

    @api.model
    def create_from_ui(self, orders):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        pos_order = self.search([('pos_reference', 'in', submitted_references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]
        order_ids = []

        for tmp_order in orders_to_save:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            if to_invoice:
                self._match_payment_to_invoice(order)

            order_id = self._process_order(order)
            # start added retail code
            if order_id:
                pos_line_obj = self.env['pos.order.line']
                to_be_returned_items = {}
                to_be_cancelled_items = {}
                # create giftcard record
                if order.get('giftcard'):
                    for create_details in order.get('giftcard'):
                        vals = {
                            'card_no':create_details.get('giftcard_card_no'),
                            'card_value':create_details.get('giftcard_amount'),
                            'customer_id':create_details.get('giftcard_customer'),
                            'expire_date':create_details.get('giftcard_expire_date'),
                            'card_type':create_details.get('card_type'),
                        }
                        self.env['aspl.gift.card'].create(vals)

                #  create redeem giftcard for use
                if order.get('redeem'):
                    for redeem_details in order.get('redeem'):
                        redeem_vals = {
                                'order_name':order_id.name,
                                'order_date':order_id.date_order,
                                'customer_id':redeem_details.get('card_customer_id') or False,
                                'card_id':redeem_details.get('redeem_card_no'),
                                'amount':redeem_details.get('redeem_card_amount'),
                               }
                        use_giftcard = self.env['aspl.gift.card.use'].create(redeem_vals)
                        if use_giftcard:
                            use_giftcard.card_id.write({ 'card_value': use_giftcard.card_id.card_value - use_giftcard.amount})

                # recharge giftcard
                if order.get('recharge'):
                    for recharge_details in order.get('recharge'):
                        recharge_vals = {
                                'user_id':order_id.user_id.id,
                                'recharge_date':order_id.date_order,
                                'customer_id':recharge_details.get('card_customer_id') or False,
                                'card_id':recharge_details.get('recharge_card_id'),
                                'amount':recharge_details.get('recharge_card_amount'),
                               }
                        recharge_giftcard = self.env['aspl.gift.card.recharge'].create(recharge_vals)
                        if recharge_giftcard:
                            recharge_giftcard.card_id.write({ 'card_value': recharge_giftcard.card_id.card_value + recharge_giftcard.amount})

                for voucher in order.get('voucher'):
                    vals = {
                                'voucher_id':voucher.get('id') or False,
                                'voucher_code':voucher.get('voucher_code'),
                                'user_id':voucher.get('create_uid')[0],
                                'customer_id':order.get('partner_id'),
                                'order_name': order_id.name,
                                'order_amount': order_id.amount_total,
                                'voucher_amount': voucher.get('voucher_amount'),
                                'used_date': datetime.now(),
                            }
                    self.env['aspl.gift.voucher.redeem'].create(vals)
                for line in order.get('lines'):
                    if line[2].get('return_process'):
                        if to_be_returned_items.has_key(line[2].get('product_id')):
                            to_be_returned_items[line[2].get('product_id')] = to_be_returned_items[line[2].get('product_id')] + line[2].get('qty')
                        else:
                            to_be_returned_items.update({line[2].get('product_id'):line[2].get('qty')})
                        # Cancel Item
                    if line[2].get('cancel_process'):
                        if to_be_cancelled_items.has_key(line[2].get('product_id')):
                            to_be_cancelled_items[line[2].get('product_id')] = to_be_cancelled_items[line[2].get('product_id')] + line[2].get('qty')
                        else:
                            to_be_cancelled_items.update({line[2].get('product_id'):line[2].get('qty')})
                for line in order.get('lines'):
                    for item_id in to_be_returned_items:
                        return_lines = []
                        if line[2].get('return_process'):
                            if type(line[2].get('return_process')) == list:
                                return_lines = self.browse(line[2].get('return_process')[0]).lines
                            elif type(line[2].get('return_process')) == int:
                                return_lines = self.browse(line[2].get('return_process')).lines
                        for origin_line in return_lines:
                            if to_be_returned_items[item_id] == 0:
                                continue
                            if origin_line.return_qty > 0 and item_id == origin_line.product_id.id:
                                if (to_be_returned_items[item_id] * -1) >= origin_line.return_qty:
                                    ret_from_line_qty = 0
                                    to_be_returned_items[item_id] = to_be_returned_items[item_id] + origin_line.return_qty
                                else:
                                    ret_from_line_qty = to_be_returned_items[item_id] + origin_line.return_qty
                                    to_be_returned_items[item_id] = 0
                                origin_line.write({'return_qty': ret_from_line_qty})
                    for item_id in to_be_cancelled_items:
                        cancel_lines = []
                        if line[2].get('cancel_process'):
                            cancel_lines = self.browse([line[2].get('cancel_process')[0]]).lines
                        for origin_line in cancel_lines:
                            if to_be_cancelled_items[item_id] == 0:
                                continue
                            if origin_line.qty > 0 and item_id == origin_line.product_id.id:
                                if (to_be_cancelled_items[item_id] * -1) >= origin_line.qty:
                                    ret_from_line_qty = 0
                                    to_be_cancelled_items[item_id] = to_be_cancelled_items[item_id] + origin_line.qty
                                else:
                                    ret_from_line_qty = to_be_cancelled_items[item_id] + origin_line.qty
                                    to_be_cancelled_items[item_id] = 0
                                origin_line.write({'qty': ret_from_line_qty})
            # end added retail code
            order_ids.append(order_id.id)
            try:
                if order and not order.get('set_as_draft'):
                    order_id.action_pos_order_paid()
            except psycopg2.OperationalError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            if to_invoice:
                order_id.action_pos_order_invoice()
                order_id.invoice_id.sudo().action_invoice_open()
                order_id.account_move = order_id.invoice_id.move_id
        return order_ids

    # aspl_pos_stock && aspl_pos_product_pack && pos_return
    def create_picking(self):
        """Create a picking for each order and validate it."""
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        full_scrap = False
        for order in self:
            scrap_lines = order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and l.scrap_item and not float_is_zero(l.qty, precision_digits=l.product_id.uom_id.rounding))
            if scrap_lines:
                if len(scrap_lines) == len(order.lines):
                    full_scrap = True
                else:
                    full_scrap = False
                self.scrap_picking(full_scrap, scrap_lines)
                # custom multi location
            multi_loc = False
            for line_order in order.lines:
                if line_order.location_id and not line_order.product_id.is_product_pack:
                    multi_loc = True
                    break
            if multi_loc:
                order.multi_picking()
            else:
                if not order.lines.filtered(
                    lambda l: l.product_id.type in [
                        'product', 'consu']):
                    continue
                address = order.partner_id.address_get(['delivery']) or {}
                picking_type = order.picking_type_id
                return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
                order_picking = Picking
                return_picking = Picking
                moves = Move
                location_id = order.location_id.id
                if order.partner_id:
                    destination_id = order.partner_id.property_stock_customer.id
                else:
                    if (not picking_type) or (
                            not picking_type.default_location_dest_id):
                        customerloc, supplierloc = StockWarehouse._get_partner_locations()
                        destination_id = customerloc.id
                    else:
                        destination_id = picking_type.default_location_dest_id.id
                if picking_type:
                    message = _(
                        "This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
                    picking_vals = {
                        'origin': order.name,
                        'partner_id': address.get('delivery', False),
                        'date_done': order.date_order,
                        'picking_type_id': picking_type.id,
                        'company_id': order.company_id.id,
                        'move_type': 'direct',
                        'note': order.note or "",
                        'location_id': location_id,
                        'location_dest_id': destination_id,
                    }
                    pos_qty = any(
                        [x.qty > 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
                    if pos_qty:
                        order_picking = Picking.create(picking_vals.copy())
                        order_picking.message_post(body=message)
                    neg_qty = any(
                        [x.qty < 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
                    if neg_qty:
                        return_vals = picking_vals.copy()
                        return_vals.update({
                            'location_id': destination_id,
                            'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                            'picking_type_id': return_pick_type.id
                        })
                        return_picking = Picking.create(return_vals)
                        return_picking.message_post(body=message)

                for line in order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not l.scrap_item and not float_is_zero(l.qty, precision_digits=l.product_id.uom_id.rounding)):
                    if line.product_id.is_product_pack:
                        if line.product_id.pack_management == 'component_product':
                            for pack_line in line.product_id.product_pack_ids:
                                 moves |= Move.create({
                                    'name': line.name,
                                    'product_uom': pack_line.product_id.uom_id.id,
                                    'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                                    'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                                    'product_id': pack_line.product_id.id,
                                    'product_uom_qty': abs(pack_line.quantity * line.qty),
                                    'state': 'draft',
                                    'location_id': location_id if line.qty >= 0 else destination_id,
                                    'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                                })
                        elif line.product_id.pack_management == 'pack_product':
                            moves |= Move.create({
                                        'name': line.name,
                                        'product_uom': line.product_id.uom_id.id,
                                        'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                                        'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                                        'product_id': line.product_id.id,
                                        'product_uom_qty': abs(line.qty),
                                        'state': 'draft',
                                        'location_id': location_id if line.qty >= 0 else destination_id,
                                        'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                                    })
                            for pack_line in line.product_id.product_pack_ids:
                                 move_id = Move.create({
                                    'name': line.name,
                                    'product_uom': pack_line.product_id.uom_id.id,
                                    'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                                    'product_id': pack_line.product_id.id,
                                    'product_uom_qty': abs(pack_line.quantity * line.qty),
                                    'state': 'draft',
                                    'location_id': location_id if line.qty >= 0 else destination_id,
                                    'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                                })
                                 move_id.action_confirm()
                                 move_id.force_assign()
                                 move_id.action_done()
                        elif line.product_id.pack_management == 'both':
                            moves |= Move.create({
                                        'name': line.name,
                                        'product_uom': line.product_id.uom_id.id,
                                        'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                                        'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                                        'product_id': line.product_id.id,
                                        'product_uom_qty': abs(line.qty),
                                        'state': 'draft',
                                        'location_id': location_id if line.qty >= 0 else destination_id,
                                        'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                                    })
                            for pack_line in line.product_id.product_pack_ids:
                                 moves |= Move.create({
                                    'name': line.name,
                                    'product_uom': pack_line.product_id.uom_id.id,
                                    'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                                    'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                                    'product_id': pack_line.product_id.id,
                                    'product_uom_qty': abs(pack_line.quantity * line.qty),
                                    'state': 'draft',
                                    'location_id': location_id if line.qty >= 0 else destination_id,
                                    'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                                })
                    else:
                        moves |= Move.create({
                            'name': line.name,
                            'product_uom': line.product_id.uom_id.id,
                            'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                            'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                            'product_id': line.product_id.id,
                            'product_uom_qty': abs(line.qty),
                            'state': 'draft',
                            'location_id': location_id if line.qty >= 0 else destination_id,
                            'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        })
    
                # prefer associating the regular order picking, not the return
                order.write({'picking_id': order_picking.id or return_picking.id})
                if return_picking:
                    order._force_picking_done(return_picking)
                    return_picking.action_done()
                if order_picking:
                    order._force_picking_done(order_picking)
                    order_picking.action_done()
    
                # when the pos.config has no picking_type_id set only the moves will be created
                if moves and not return_picking and not order_picking:
                    tracked_moves = moves.filtered(lambda move: move.product_id.tracking != 'none')
                    untracked_moves = moves - tracked_moves
                    tracked_moves.action_confirm()
                    untracked_moves.action_assign()
                    moves.filtered(lambda m: m.state in ['confirmed', 'waiting']).force_assign()
                    moves.filtered(lambda m: m.product_id.tracking == 'none').action_done()
                    
            return True

    # aspl_pos_stock
    @api.one
    def multi_picking(self):
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        address = self.partner_id.address_get(['delivery']) or {}
        picking_type = self.picking_type_id
        order_picking = Picking
        return_picking = Picking
        moves = Move
        return_pick_type = self.picking_type_id.return_picking_type_id or self.picking_type_id
        message = _("This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (self.id, self.name)
        if self.partner_id:
            destination_id = self.partner_id.property_stock_customer.id
        else:
            if (not picking_type) or (
                    not picking_type.default_location_dest_id):
                customerloc, supplierloc = StockWarehouse._get_partner_locations()
                destination_id = customerloc.id
            else:
                destination_id = picking_type.default_location_dest_id.id
        lst_picking = []
        location_ids = list(set([line.location_id.id for line in self.lines]))
        for loc_id in location_ids:
            picking_vals = {
                'origin': self.name,
                'partner_id': address.get('delivery', False),
                'date_done': self.date_order,
                'picking_type_id': picking_type.id,
                'company_id': self.company_id.id,
                'move_type': 'direct',
                'note': self.note or "",
                'location_id': loc_id,
                'location_dest_id': destination_id,
            }
            pos_qty = any(
                [x.qty > 0 for x in self.lines if x.product_id.type in ['product', 'consu']])
            if pos_qty:
                order_picking = Picking.create(picking_vals.copy())
                order_picking.message_post(body=message)
            neg_qty = any(
                [x.qty < 0 for x in self.lines if x.product_id.type in ['product', 'consu']])
            if neg_qty:
                return_vals = picking_vals.copy()
                return_vals.update({
                    'location_id': destination_id,
                    'location_dest_id': loc_id,
                    'picking_type_id': return_pick_type.id
                })
                return_picking = Picking.create(return_vals)
                return_picking.message_post(body=message)
            for line in self.lines.filtered(
                lambda l: l.product_id.type in [
                    'product',
                    'consu'] and l.location_id.id == loc_id and not l.scrap_item and not float_is_zero(
                    l.qty,
                    precision_digits=l.product_id.uom_id.rounding)):
                if line.product_id.is_product_pack:
                    if line.product_id.pack_management == 'component_product':
                        for pack_line in line.product_id.product_pack_ids:
                             vals = {
                                'name': line.name,
                                'product_uom': pack_line.product_id.uom_id.id,
                                'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                                'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                                'product_id': pack_line.product_id.id,
                                'product_uom_qty': abs(pack_line.quantity * line.qty),
                                'state': 'draft',
                                'location_id': loc_id if line.qty >= 0 else destination_id,
                                'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or loc_id,
                            }
                             moves |= Move.create(vals)
                    elif line.product_id.pack_management == 'pack_product':
                        moves |= Move.create({
                                    'name': line.name,
                                    'product_uom': line.product_id.uom_id.id,
                                    'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                                    'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                                    'product_id': line.product_id.id,
                                    'product_uom_qty': abs(line.qty),
                                    'state': 'draft',
                                    'location_id': loc_id if line.qty >= 0 else destination_id,
                                    'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                                })
                        for pack_line in line.product_id.product_pack_ids:
                             move_id = Move.create({
                                'name': line.name,
                                'product_uom': pack_line.product_id.uom_id.id,
                                'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                                'product_id': pack_line.product_id.id,
                                'product_uom_qty': abs(pack_line.quantity * line.qty),
                                'state': 'draft',
                                'location_id': loc_id if line.qty >= 0 else destination_id,
                                'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                            })
                             move_id.action_confirm()
                             move_id.force_assign()
                             move_id.action_done()
                    elif line.product_id.pack_management == 'both':
                        moves |= Move.create({
                                    'name': line.name,
                                    'product_uom': line.product_id.uom_id.id,
                                    'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                                    'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                                    'product_id': line.product_id.id,
                                    'product_uom_qty': abs(line.qty),
                                    'state': 'draft',
                                    'location_id': loc_id if line.qty >= 0 else destination_id,
                                    'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                                })
                        for pack_line in line.product_id.product_pack_ids:
                             moves |= Move.create({
                                'name': line.name,
                                'product_uom': pack_line.product_id.uom_id.id,
                                'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                                'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                                'product_id': pack_line.product_id.id,
                                'product_uom_qty': abs(pack_line.quantity * line.qty),
                                'state': 'draft',
                                'location_id': loc_id if line.qty >= 0 else destination_id,
                                'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                            })
                else:
                    moves |= Move.create({
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                        'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': abs(line.qty),
                        'state': 'draft',
                        'location_id': loc_id if line.qty >= 0 else destination_id,
                        'location_dest_id': destination_id if line.qty >= 0 else loc_id,
                    })
            if return_picking:
                self.write({'picking_ids': [(4, return_picking.id)]})
                self._force_picking_done(return_picking)
                return_picking.action_done()
            if order_picking:
                self.write({'picking_ids': [(4, order_picking.id)]})
#                 self.write({'picking_ids' : [(6,0,self.picking_ids.ids.append(order_picking))]})
                self._force_picking_done(order_picking)
                order_picking.action_done()
            
        return True

    @api.multi
    def do_internal_transfer(self):
        for order in self:
            if order.config_id.reserve_stock_location_id and order.config_id.stock_location_id:
                # Move Lines
                temp_move_lines = []

                for line in order.lines:
                    if line.product_id.default_code:
                        name = [line.product_id.default_code]
                    else:
                        name = line.product_id.name
                    if line.product_id.type != "service":
                        move_vals = (0, 0, {
                            'product_id': line.product_id.id,
                            'name': name,
                            'product_uom_qty': line.qty,
                            'location_id': order.config_id.stock_location_id.id,
                            'location_dest_id': order.config_id.reserve_stock_location_id.id,
                            'product_uom': line.product_id.uom_id.id,
                        })
                        temp_move_lines.append(move_vals)
                warehouse_obj = self.env['stock.warehouse'].search([
                    ('lot_stock_id', '=', order.config_id.stock_location_id.id)], limit=1)
                if warehouse_obj:
                    picking_type_obj = self.env['stock.picking.type'].search([
                        ('warehouse_id', '=', warehouse_obj.id), ('code', '=', 'internal')])
                    if picking_type_obj and temp_move_lines:
                        picking_vals = {
                            'picking_type_id': picking_type_obj.id,
                            'location_id': order.config_id.stock_location_id.id,
                            'location_dest_id': order.config_id.reserve_stock_location_id.id,
                            'state': 'draft',
                            'move_lines': temp_move_lines,
                            'origin':order.name
                        }
                        picking_obj = self.env['stock.picking'].create(picking_vals)
                        if picking_obj:
                            picking_obj.action_confirm()
                            picking_obj.force_assign()
                            picking_obj.do_new_transfer()
                            stock_transfer_id = self.env['stock.immediate.transfer'].search([('pick_id', '=', picking_obj.id)], limit=1).process()
                            if stock_transfer_id:
                                stock_transfer_id.process()
                            order.picking_id = picking_obj.id

    @api.multi
    @api.depends('amount_total', 'amount_paid')
    def _compute_amount_due(self):
        for each in self:
            each.amount_due = each.amount_total - each.amount_paid

    @api.multi
    @api.depends('lines')
    def _find_order_status(self):
        for order in self:
            partial, full = [], []
            line_count = 0;
            line_partial = False
            for line in order.lines:
                if not line.cancel_item:
                    line_count += 1
                    if line.line_status == "partial":
                        order.order_status = "partial"
                        line_partial = True
                        break
                    if line.line_status == "full":
                        full.append(True)
            if len(full) == line_count:
                if not False in full and not line_partial:
                    order.order_status = "full"
            elif full:
                order.order_status = "partial"

#     Graph
    @api.model
    def graph_data(self, from_date, to_date, category, limit):
        try:
            if from_date and to_date:
                if category == 'top_customer':
                    
                    order_ids = self.env['pos.order'].search([('partner_id', '!=', False),
                                                              ('date_order', '>=', from_date),
                                                              ('date_order', '<=', to_date)], order='date_order desc')
                    result = []
                    record = {}
                    if order_ids:
#                         order_ids = self.pool.get('pos.order').browse(cr, uid, order_ids)
                        for each_order in order_ids:
                            if record.has_key(each_order.partner_id):
                                record.update({each_order.partner_id: record.get(each_order.partner_id) + each_order.amount_total})
                            else:
                                record.update({each_order.partner_id: each_order.amount_total})
                    if record:
                        result = [(k.name, v) for k, v in record.items()]
                        result = sorted(result, key=lambda x: x[1], reverse=True)
                    if limit == 'ALL':
                        return result
                    return result[:int(limit)]
                if category == 'top_products':
                    self._cr.execute("""
                        SELECT pt.name, sum(psl.qty), pp.id FROM pos_order_line AS psl
                        JOIN pos_order AS po ON (po.id = psl.order_id)
                        JOIN product_product AS pp ON (psl.product_id = pp.id)
                        JOIN product_template AS pt ON (pt.id = pp.product_tmpl_id)
                        WHERE po.date_order >= '%s'
                        AND po.date_order <= '%s'
                        AND psl.qty > 0
                        GROUP BY pt.name, pp.id
                        ORDER BY sum(psl.qty) DESC limit %s;
                        """ % ((from_date, to_date, limit)))
                    return self._cr.fetchall()
                if category == 'cashiers':
                    self._cr.execute("""
                        SELECT pc.name, SUM(absl.amount) FROM account_bank_statement_line absl
                        JOIN account_journal aj ON absl.journal_id = aj.id
                        JOIN pos_session as ps ON ps.name = absl.ref
                        JOIN pos_config as pc ON pc.id = ps.config_id
                        WHERE absl.create_date >= '%s' AND absl.create_date <= '%s'
                        GROUP BY pc.name
                        limit %s
                        """ % ((from_date, to_date, limit)))
                    return self._cr.fetchall()
                if category == 'sales_by_location':
                    self._cr.execute("""
                        SELECT (loc1.name || '/' || loc.name) as name, sum(psl.price_unit) FROM pos_order_line AS psl
                        JOIN pos_order AS po ON (po.id = psl.order_id)
                        JOIN stock_location AS loc ON (loc.id = po.location_id)
                        JOIN stock_location AS loc1 ON (loc.location_id = loc1.id)
                        WHERE po.date_order >= '%s'
                        AND po.date_order <= '%s'
                        GROUP BY loc.name, loc1.name
                        limit %s
                        """ % ((from_date, to_date, limit)))
                    return self._cr.fetchall()
                if category == 'income_by_journals':
                    self._cr.execute("""
                        select aj.name, sum(absl.amount) from account_bank_statement_line absl
                        join account_journal aj on absl.journal_id = aj.id
                        join pos_session as ps on ps.name = absl.ref
                        join pos_config as pc on pc.id = ps.config_id
                        where absl.create_date >= '%s' and absl.create_date <= '%s'
                        group by aj.name
                        limit %s
                        """ % ((from_date, to_date, limit)))
                    return self._cr.fetchall()
#                 if category == 'top_sale_location':
#                     cr.execute("""
#                        SELECT loc.name, sum(psl.price_unit) FROM pos_order_line AS psl
#                         JOIN pos_order AS po ON (po.id = psl.order_id)
#                         JOIN stock_location AS loc ON (loc.id = po.location_id)
#                         WHERE po.date_order >= '%s'
#                         AND po.date_order <= '%s'
#                         GROUP BY loc.name
#                         ORDER BY sum(psl.price_unit) DESC
#                         limit %s
#                         """%((from_date,to_date, limit)))
#                     return cr.fetchall()
                if category == 'top_category':
                    self._cr.execute("""
                        SELECT pc.name, sum((pol.price_unit * pol.qty) - pol.discount) 
                        FROM pos_category pc
                        join product_template pt on pc.id = pt.pos_categ_id
                        join product_product pp on pt.id = pp.product_tmpl_id
                        join pos_order_line pol on pp.id = pol.product_id
                        join pos_order po on pol.order_id = po.id
                        where pol.create_date >= '%s' and pol.create_date <= '%s'
                        group by pc.name
                        ORDER BY sum(pol.price_unit) DESC
                        limit %s
                        """ % ((from_date, to_date, limit)))
                    return self._cr.fetchall()
                else:
                    return False
        except:
           return {'error':'Function Call Problem...'}

    @api.model
    def ac_pos_search_read(self, domain):
        search_vals = self.search_read(domain)
        user_id = self.env['res.users'].browse(self._uid)
        tz = False
        if self._context and self._context.get('tz'):
            tz = timezone(self._context.get('tz'))
        elif user_id and user_id.tz:
            tz = timezone(user_id.tz)
        if tz:
            c_time = datetime.now(tz)
            hour_tz = int(str(c_time)[-5:][:2])
            min_tz = int(str(c_time)[-5:][3:])
            sign = str(c_time)[-6][:1]
            today_sale = 0.0
            result = []
            for val in search_vals:
                if sign == '-':
                    val.update({
                        'date_order':(datetime.strptime(val.get('date_order'), '%Y-%m-%d %H:%M:%S') - timedelta(hours=hour_tz, minutes=min_tz)).strftime('%Y-%m-%d %H:%M:%S')
                    })
                elif sign == '+':
                    val.update({
                        'date_order':(datetime.strptime(val.get('date_order'), '%Y-%m-%d %H:%M:%S') + timedelta(hours=hour_tz, minutes=min_tz)).strftime('%Y-%m-%d %H:%M:%S')
                    })
                result.append(val)
            return result
        else:
            return search_vals

    @api.model
    def create(self, values):
        order_id = super(pos_order, self).create(values)
        if values.get('customer_email') and order_id:
            try:
                template_id = self.env['ir.model.data'].get_object_reference('flexiretail', 'email_template_pos_ereceipt')
                template_obj = self.env['mail.template'].browse(template_id[1])
                template_obj.send_mail(order_id.id, force_send=True, raise_exception=True)
            except Exception, e:
                _logger.error('Unable to send email for order %s', e)
        if values.get('lines'):
            prod_cross_sell = []
            for line in values.get('lines'):
                if line[2].get('cross_sell_id'):
                    prod_cross_sell.append(line[2].get('product_id'))
            if prod_cross_sell:
                self.env['product.cross.selling.history'].create(
                                                        {'order_id': order_id.id,
                                                         'user_id': self._uid,
                                                         'date': time.strftime('%Y-%m-%d'),
                                                         'sell_time': time.strftime('%H:%M:%S'),
                                                         'product_ids': [(6, 0, prod_cross_sell)],
                                                        })
        return order_id


    @api.one
    def update_delivery_date(self, delivery_date):
        res = self.write({ 'delivery_date': datetime.strptime(delivery_date, '%Y-%m-%d') })
        if res:
            return self.read()[0]
        return False

    @api.multi
    def write(self, vals):
        res = super(pos_order, self).write(vals)
        if self._context.get('out_order'):
            return res
        for each in self:
            if vals.get('state') == 'paid' and each.reserved:
                picking_id = each.picking_id.copy()
                picking_type_id = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', each.picking_id.picking_type_id.warehouse_id.id), ('code', '=', 'outgoing')], limit=1)
                if picking_type_id:
                    location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()
                    name = self.env['stock.picking.type'].browse(vals.get('picking_type_id', picking_type_id.id)).sequence_id.next_by_id()
                    picking_id.write({'picking_type_id':picking_type_id.id, 'location_id':each.picking_id.location_dest_id.id,
                                      'location_dest_id': location_dest_id.id, 'name':name, 'origin':each.name})
                    if picking_id.pack_operation_pack_ids:
                        picking_id.pack_operation_pack_ids.write({'location_id':each.picking_id.location_dest_id.id,
                                      'location_dest_id': location_dest_id.id})
                    if picking_id.move_lines:
                        picking_id.move_lines.write({'location_id':each.picking_id.location_dest_id.id,
                                      'location_dest_id': location_dest_id.id, 'origin':each.name})
                    picking_id.action_confirm()
                    picking_id.force_assign()
                    picking_id.do_new_transfer()
                    stock_transfer_id = self.env['stock.immediate.transfer'].search([('pick_id', '=', picking_id.id)], limit=1).process()
                    if stock_transfer_id:
                        stock_transfer_id.process()
                    query = ''' UPDATE pos_order SET unreserved=True,
                       picking_id='%s'
                       WHERE id=%s''' % (picking_id.id, each.id)
                    self._cr.execute(query)
                    each.write({'picking_id' :picking_id.id})
        return res

    @api.multi
    def action_pos_order_paid(self):
        if not self.test_paid():
            raise UserError(_("Order is not paid."))
        self.write({'state': 'paid'})
        # custom code
        picking_id_cust = False
        location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()
        if self.order_status in ['full', 'partial'] or self.order_booked:
            for line in self.lines:
                if line.product_id.type != 'service' and not line.cancel_item and line.line_status == 'nothing':
                    # customer delivery order
                    picking_type_out = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', self.picking_id.picking_type_id.warehouse_id.id), ('code', '=', 'outgoing')], limit=1)
                    if picking_type_out:
                        picking_vals_rev = {
                                'name' : picking_type_out.sequence_id.next_by_id(),
                                'picking_type_id': picking_type_out.id,
                                'location_id': self.config_id.reserve_stock_location_id.id,
                                'location_dest_id': location_dest_id.id,
                                'state': 'draft',
                                'origin':self.name
                            }
                        if not picking_id_cust:
                            picking_id_cust = self.env['stock.picking'].create(picking_vals_rev)
                        self.env['stock.move'].create({
                                        'product_id': line.product_id.id,
                                        'name': line.product_id.name,
                                        'product_uom_qty': line.qty,
                                        'location_id': self.config_id.reserve_stock_location_id.id,
                                        'location_dest_id': location_dest_id.id,
                                        'product_uom': line.product_id.uom_id.id,
                                        'origin' : self.name,
                                        'picking_id' : picking_id_cust.id
                                    })
            if picking_id_cust and picking_id_cust.move_lines:
                picking_id_cust.action_confirm()
                picking_id_cust.force_assign()
                picking_id_cust.do_new_transfer()
                stock_transfer_id = self.env['stock.immediate.transfer'].search([('pick_id', '=', picking_id_cust.id)], limit=1).process()
                if stock_transfer_id:
                    stock_transfer_id.process()
                self.with_context({'out_order' :True}).write({'picking_id' : picking_id_cust.id, 'unreserved':True})
            elif picking_id_cust:
                picking_id_cust.unlink()
        return self.create_picking()

    @api.one
    def send_reserve_mail(self):
        if self and self.customer_email and self.reserved and self.fresh_order:
            try:
                template_id = self.env['ir.model.data'].get_object_reference('aspl_pos_order_reservation', 'email_template_pos_ereceipt')
                template_obj = self.env['mail.template'].browse(template_id[1])
                template_obj.send_mail(self.id, force_send=True, raise_exception=True)
            except Exception, e:
                _logger.error('Unable to send email for order %s', e)

class pos_order_line(models.Model):
    _inherit = "pos.order.line"

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
    def _compute_amount_line_all(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id
            tax_ids_after_fiscal_position = fpos.map_tax(line.tax_ids, line.product_id, line.order_id.partner_id) if fpos else line.tax_ids
#             price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.qty > 1:
                price = (line.price_unit * 1) - (line.discount_amount/line.qty)
#                 price_unit = line.price_unit + line.discount_amount
#                 line.write({'price_unit' : price_unit})
            else :
                price = (line.price_unit * 1) - line.discount_amount

            taxes = tax_ids_after_fiscal_position.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_subtotal_incl': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

#     @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
#     def _compute_amount_line_all(self):
#         for line in self:
#             if line.order_id.is_rounding and line.order_id.rounding_option == 'digits':
#                 currency = line.order_id.pricelist_id.currency_id
#                 taxes = line.tax_ids.filtered(
#                     lambda tax: tax.company_id.id == line.order_id.company_id.id)
#                 fiscal_position_id = line.order_id.fiscal_position_id
#                 if fiscal_position_id:
#                     taxes = fiscal_position_id.map_tax(
#                         taxes, line.product_id, line.order_id.partner_id)
#                 price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#                 line.price_subtotal = line.price_subtotal_incl = price * line.qty
#                 taxes = taxes.compute_all(
#                     price,
#                     currency,
#                     line.qty,
#                     product=line.product_id,
#                     partner=line.order_id.partner_id or False)
#                 line.price_subtotal = taxes['total_excluded']
#                 total_included_taxes = round(taxes['total_included'])#decimalAdjust(taxes['total_included'])
#                 line.price_subtotal_incl = total_included_taxes
#     
#                 line.price_subtotal = currency.round(line.price_subtotal)
#                 line.price_subtotal_incl = currency.round(line.price_subtotal_incl)
#             elif line.order_id.is_rounding and line.order_id.rounding_option == 'points':
#                 currency = line.order_id.pricelist_id.currency_id
#                 taxes = line.tax_ids.filtered(lambda tax: tax.company_id.id == line.order_id.company_id.id)
#                 fiscal_position_id = line.order_id.fiscal_position_id
#                 if fiscal_position_id:
#                     taxes = fiscal_position_id.map_tax(taxes, line.product_id, line.order_id.partner_id)
#                 price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#                 line.price_subtotal = line.price_subtotal_incl = price * line.qty
#                 taxes = taxes.compute_all(price, currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
#                 line.price_subtotal = taxes['total_excluded']
#                 total_included_taxes = decimalAdjust(taxes['total_included'])
#                 line.price_subtotal_incl = total_included_taxes
#     
#                 line.price_subtotal = currency.round(line.price_subtotal)
#                 line.price_subtotal_incl = currency.round(line.price_subtotal_incl)
#             else:
#                 fpos = line.order_id.fiscal_position_id
#                 tax_ids_after_fiscal_position = fpos.map_tax(line.tax_ids, line.product_id, line.order_id.partner_id) if fpos else line.tax_ids
#                 price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#                 taxes = tax_ids_after_fiscal_position.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty, product=line.product_id, partner=line.order_id.partner_id)
#                 line.update({
#                     'price_subtotal_incl': taxes['total_included'],
#                     'price_subtotal': taxes['total_excluded'],
#                 })

    @api.multi
    def _remaining_qty(self):
        for line in self:
            rqty = 0
            parent_ids = self.search([('parent_line_id', '=', line.id)])
            if parent_ids:
                rqty = sum(map(lambda a: (a.qty * -1), parent_ids))
            line.remaining_qty = line.qty - rqty

    @api.multi
    @api.constrains('qty')
    def _check_qty(self):
        for line in self:
            if line.parent_line_id:
                rqty = 0
                return_ids = self.search([('parent_line_id', '=', line.parent_line_id.id),
                                          ('id', '!=', line.id)])
                if return_ids:
                    rqty = sum(map(lambda a: (a.qty * -1), return_ids))
                if (line.qty * -1) > (line.parent_line_id.qty - rqty):
                    raise Warning(_('Return qty must be less than remaining qty of main order.'))

    @api.model
    def create(self, values):
        if values.get('product_id'):
            if self.env['pos.order'].browse(values['order_id']).session_id.config_id.prod_for_payment.id == values.get('product_id'):
                return
            if self.env['pos.order'].browse(values['order_id']).session_id.config_id.refund_amount_product_id.id == values.get('product_id'):
                return
        res = super(pos_order_line, self).create(values)
        if values.get('cancel_item_id'):
            line_id = self.browse(values.get('cancel_item_id'))
            if line_id and values.get('new_line_status'):
                line_id.write({'line_status': values.get('new_line_status')})
        return res
    price_unit = fields.Float(string='Unit Price', digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Float(compute='_compute_amount_line_all', digits=dp.get_precision('Product Price'), string='Subtotal w/o Tax')
    price_subtotal_incl = fields.Float(compute='_compute_amount_line_all', digits=dp.get_precision('Product Price'), string='Subtotal')
    discount_amount = fields.Float("Discount Amount", readonly=True, digits=dp.get_precision('Product Price'))
    item_discount_share = fields.Float("Discount Share", readonly=True, digits=dp.get_precision('Product Price'))
    item_discount_amount = fields.Float("Item Discount", readonly=True, digits=dp.get_precision('Product Price'))
    discount_share_per = fields.Float("Discount Share (%)", readonly=True, digits=dp.get_precision('Product Price'))
    product_mrp = fields.Float("MRP", readonly=True, digits=dp.get_precision('Product Price'))
    return_qty = fields.Integer('Return QTY', size=64)
    return_process = fields.Char('Return Process')
    back_order = fields.Char('Back Order', size=256, default=False, copy=False)
    scrap_item = fields.Boolean("Scrap Item")
    prodlot_id = fields.Many2one('stock.production.lot', "Serial No.")
    note = fields.Char('Comment', size=512)
    # pos return fields
    parent_line_id = fields.Many2one('pos.order.line', 'Order Line Ref')
    return_order_line = fields.Boolean('Return Order Line')
    remaining_qty = fields.Float(compute='_remaining_qty', string='Remaining Qty')
    deliver = fields.Boolean('Deliver', size=512)
    prodlot_id = fields.Many2one('stock.production.lot', "Serial No.")
    is_bag = fields.Boolean('Is Bag')
    is_delivery_product = fields.Boolean('Is Delivery Product')
    serial_nums = fields.Char("Serials")
    # Order Reservation
    cancel_item = fields.Boolean("Cancel Item")
    line_status = fields.Selection([('nothing', 'Nothing'), ('full', 'Fully Cancelled'), ('partial', 'Partially Cancelled')],
                                    'Order Status', default="nothing")
    # aspl_pos_stock
    location_id = fields.Many2one('stock.location', string='Location')
    product_cost_price = fields.Float(compute='_product_cost_price_cal', string="Product Cost Price", store=True)

    @api.multi
    @api.depends('product_id')
    def _product_cost_price_cal(self):
        for line in self:
            line.product_cost_price = line.product_id.standard_price

    @api.multi
    def write(self, vals):
        for line in self:
            if line.parent_line_id and vals.get('qty', False):
                if vals.get('qty') > 0:
                    raise Warning(_('Product qty must have negetive for return order.'))
            if line.parent_line_id and 'qty' not in vals:
                raise Warning(_('You can only modify qty for return order.'))
            return super(pos_order_line, line).write(vals)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user_rec = self.env['res.users'].browse(self._uid)
        erp_manager_id = self.env['ir.model.data'].get_object_reference('base',
                                                                         'group_erp_manager')[1]
        if user_rec and erp_manager_id not in user_rec.groups_id.ids:
            args += [('id', '=', user_rec.default_pos.id)]
            res = super(PosConfig, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
        else:
             res = super(PosConfig, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
        return res

    @api.onchange('sidebar_width', 'centerpane_width')
    def _onchange_sidebar_width(self):
        if self.sidebar_width < 7:
            self.sidebar_width = 7
        if self.sidebar_width > 66:
            self.sidebar_width = 66
        if self.centerpane_width < 34:
            self.centerpane_width = 34
        if self.centerpane_width > 93:
            self.centerpane_width = 93
        if (self.sidebar_width + self.centerpane_width) > 100:
            self.sidebar_width = 7
            self.centerpane_width = 34

    custom_discount = fields.Boolean('Custom Discount')
    doctor_report = fields.Boolean('Sales Report')
    discount_print_receipt = fields.Selection([('public_price', 'Public Price'), ('promo_price', 'Promo Price')], 'Discount Print Based on')
    store_discount_based_on = fields.Selection([('public_price', 'Public Price'), ('promo_price', 'Promo Price')], 'Store Discount Based on')
#     discount_product_id = fields.Many2one('product.product',string="Discount Product")
    enable_pos_serial = fields.Boolean('Enable POS Serial')
    show_pricelist = fields.Boolean('Show Price List')
    product_exp_days = fields.Integer("Product Expiry Days", default="0")
#     enable_product_return = fields.Boolean('Enable Product Return')
#     bonus_coupon_journal = fields.Many2one('account.journal', 'Bonus Coupon Journal', help="To use Product Return Functionality need to define journal for Bonus Coupon.")
    enable_order_note = fields.Boolean('Enable Order Note')
    enable_product_note = fields.Boolean('Enable Product / Line Note')
    display_warehouse_qty = fields.Boolean('Display Warehouse Product Qty')
    use_discount_rules = fields.Boolean('User Operation Restrict')
    # gift_coupon = fields.Boolean('Enable Gift Coupon')
    # gift_coupon_journal = fields.Many2one('account.journal', 'Gift Coupon Journal', help="To use Gift Coupon Functionality need to define journal for Gift Coupon.")
    enable_loyalty = fields.Boolean('Enable Loyalty')
    loyalty_journal = fields.Many2one('account.journal', 'Loyalty Journal', help="To use Loyalty Functionality need to define journal for Loyalty.")
    cash_put_out_in = fields.Boolean('Enable Cash Put In/Out')
    enable_cross_selling = fields.Boolean('Enable Cross-Selling')
    enable_pos_reorder = fields.Boolean("Enable Order History")
    req_cashier_login = fields.Boolean("Require Cashier login")
    enable_sale_report = fields.Boolean("Enable Sale Report")
    enable_bag_charges = fields.Boolean("Enable Bag Charges", default=False);
    enable_delivery_charges = fields.Boolean("Enable Delivery Charges", default=False);
    delivery_product_id = fields.Many2one('product.product', 'Delivery Product')
    pos_managers_ids = fields.Many2many('res.users', 'posconfig_partner_rel', 'location_id', 'partner_id', string='Managers')
    last_days = fields.Integer('')
    record_per_page = fields.Integer("Record Per Page")
    debt_dummy_product_id = fields.Many2one('product.product', string='Dummy Product for Debt')
    debt_journal = fields.Many2one('account.journal', 'Debit Journal', help="To use Debit functionality.")
    enable_bank_charges = fields.Boolean("Enable Bank Charges")
    payment_product_id = fields.Many2one('product.product', "Payment Charge Product")
    enable_ereceipt = fields.Boolean('Enable E-Receipt')
#     enable_product_variant = fields.Boolean("Enable Product Variant")
#     enable_z_report = fields.Boolean("Enable Print Sale Summary")
    enable_today_sale_report = fields.Boolean("Today Sale Report")
    enable_print_last_receipt = fields.Boolean("Print Last Receipt")
#     enable_clear_order = fields.Boolean("Enable Clear Cart")
    enable_qty_on_hand = fields.Boolean("Quantity On Hand")
    require_cashier = fields.Boolean("Enable POS Login")
    enable_graph_view = fields.Boolean("Enable Graph View")
    sidebar_width = fields.Integer("Sidebar Width (%)")
    centerpane_width = fields.Integer("Center Panel Width (%)")
    sidebar_button_width = fields.Integer("Sidebar Button Width (%)")
    sidebar_button_height = fields.Integer("Sidebar Button Height (%)")
    # coupon_product = fields.Many2one('product.product',string="Coupon Product")
    enable_wallet = fields.Boolean('Enable Wallet')
    wallet_product = fields.Many2one('product.product', string="Wallet Product")
#     enable_allow_return_coupon_order = fields.Boolean('Enable allow return Coupon used Order',
#                                         help="Allow Order Return for coupon used order")
    enable_create_theme = fields.Boolean("Create Theme")
    enable_customer_display = fields.Boolean("Enable Customer Display")
    enable_gift_voucher = fields.Boolean('Enable Gift Voucher')
    gift_voucher_journal_id = fields.Many2one("account.journal", string="Gift Voucher Journal")

    enable_gift_card = fields.Boolean('Enable Gift Card')
    gift_card_product_id = fields.Many2one('product.product', string="Gift Card Product")
    enable_journal_id = fields.Many2one('account.journal', string="Gift Card Journal")
    manual_card_number = fields.Boolean('Manual Card No.')
    default_exp_date = fields.Integer('Default Card Expire Months')
    msg_before_card_pay = fields.Boolean('Confirm Message Before Card Payment')
    print_x_report = fields.Boolean('Print Session Report')
    enable_chat = fields.Boolean('Enable Chat')
    enable_product_sync = fields.Boolean("Enable Product Sync")
    enable_gift_receipt = fields.Boolean('Enable Gift Receipt')

# quick payment

    enable_quick_cash_payment = fields.Boolean(string="Enable Quick Cash Payment")
    validate_on_click = fields.Boolean(string="Validate On Click")
    cash_method = fields.Many2one('account.journal', "Cash Payment Method")
    payment_buttons = fields.Many2many(comodel_name='quick.cash.payment',
                                           relation='amount_button_name',
                                           column1='payment_amt_id', column2='pos_config_id')
    enable_int_trans_stock = fields.Boolean(string="Internal Stock Transfer")
    enable_product_manage = fields.Boolean('Enable Product Management')

    enable_print_valid_days = fields.Boolean("Enable Print Product Return Valid days")
    default_return_valid_days = fields.Integer("Default Return Valid Days")

    # Order Reservation
    enable_order_reservation = fields.Boolean('Enable Order Reservation')
    reserve_stock_location_id = fields.Many2one('stock.location', 'Reserve Stock Location')
    cancellation_charges_type = fields.Selection([('fixed', 'Fixed'), ('percentage', 'Percentage')], 'Cancellation Charges Type')
    cancellation_charges = fields.Float('Cancellation Charges')
    cancellation_charges_product_id = fields.Many2one('product.product', 'Cancellation Charges Product')
    prod_for_payment = fields.Many2one('product.product', string='Paid Amount Product',
                                      help="This is a dummy product used when a customer pays partially. This is a workaround to the fact that Odoo needs to have at least one product on the order to validate the transaction.")
    refund_amount_product_id = fields.Many2one('product.product', 'Refund Amount Product')
    enable_pos_welcome_mail = fields.Boolean("Send Welcome Mail")
    allow_reservation_with_no_amount = fields.Boolean("Allow Reservation With 0 Amount")

    # aspl_pos_stock
    show_qty = fields.Boolean(string='Display Stock')
    restrict_order = fields.Boolean(string='Restrict Order When Out Of Stock')
    prod_qty_limit = fields.Integer(string="Restrict When Product Qty Remains")
    custom_msg = fields.Char(string="Custom Message")

    # aspl_pos_product_pack
    enable_pack_products = fields.Boolean("Enable Pack Products")
    enable_rounding = fields.Boolean("Enable Rounding")
    rounding_options = fields.Selection([("digits", 'Digits'), ('points', 'Points'), ('3decimal', '3 Decimal'), ('2decimal', '2 Decimal'), ('1decimal', '1 Decimal'), ('50fills', '50 Fills'), ('250fills', '250 Fills')], string='Rounding Options', default='digits')
    rounding_journal_id = fields.Many2one('account.journal', "Rouding Payment Method")

    # pos_return
    enable_pos_return = fields.Boolean("Enable Return from POS")
    scrap_location_id = fields.Many2one("stock.location", "Scrap Stock Locaiton")

class pos_session(models.Model):
    _inherit = 'pos.session'

    @api.model
    def take_money_out(self, name, amount, session_id):
        try:
            cash_out_obj = self.env['cash.box.out']
            total_amount = 0.0
            active_model = 'pos.session'
            active_ids = [session_id]
            if active_model == 'pos.session':
                records = self.env[active_model].browse(active_ids)
                bank_statements = [record.cash_register_id for record in records if record.cash_register_id]
                if not bank_statements:
                    raise Warning(_('There is no cash register for this PoS Session'))
                res = cash_out_obj.create({'name': name, 'amount': amount})
                return res._run(bank_statements)
            else:
                return {}
        except:
           return {'error':'There is no cash register for this PoS Session '}

    @api.model
    def put_money_in(self, name, amount, session_id):
        try:
            cash_out_obj = self.env['cash.box.in']
            total_amount = 0.0
            active_model = 'pos.session'
            active_ids = [session_id]
            if active_model == 'pos.session':
                records = self.env[active_model].browse(active_ids)
                bank_statements = [record.cash_register_id for record in records if record.cash_register_id]
                if not bank_statements:
                    raise Warning(_('There is no cash register for this PoS Session'))
                res = cash_out_obj.create({'name': name, 'amount': amount})
                return res._run(bank_statements)
            else:
                return {}
        except Exception, e:
           return {'error':'There is no cash register for this PoS Session '}

    @api.model
    def get_session_report(self):
        try:
            s_date = date.today().strftime("%Y-%m-%d")
#             sql query for get "In Progress" session
            self._cr.execute("""
                select ps.id,pc.name, ps.name from pos_session ps
                left join pos_config pc on (ps.config_id = pc.id)
                where ps.start_at <= '%s'
                AND ps.start_at >= '%s'
                AND ps.user_id = %d
            """ %(s_date + " 23:59:59",s_date + " 00:00:00", self._uid))
            session_detail = self._cr.fetchall()

            self._cr.execute("""
                SELECT pc.name, ps.name, sum(abs.total_entry_encoding) FROM pos_session ps
                JOIN pos_config pc on (ps.config_id = pc.id)
                JOIN account_bank_statement abs on (ps.id = abs.pos_session_id)
                WHERE ps.start_at <=' %s'
                AND ps.start_at >=' %s'
                AND ps.user_id = %d
                GROUP BY ps.id, pc.name;
            """%(s_date + " 23:59:59",s_date + " 00:00:00",self._uid))
            session_total = self._cr.fetchall()
#             sql query for get payments total of "In Progress" session
            lst = []
            journal_amounts = {}
            bank_detail = []
            for pay_id in session_detail:
                self._cr.execute("""
                    select pc.name, aj.name, abs.total_entry_encoding from account_bank_statement abs
                    join pos_session ps on abs.pos_session_id = ps.id
                    join pos_config pc on ps.config_id = pc.id
                    join account_journal aj on  abs.journal_id = aj.id
                    where pos_session_id=%s
                """ % pay_id[0])
                bank_detail.append(self._cr.dictfetchall()) 
#                     if i[2] != None:
#                         lst.append({'session_name':i[0], 'journals':i[1], 'total':i[2]})

            cate_lst = []
            for cate_id in session_detail:
                self._cr.execute("""
                    select pc.name as categ_name, sum(pol.price_unit), poc.name from pos_category pc
                    join product_template pt on pc.id = pt.pos_categ_id
                    join product_product pp on pt.id = pp.product_tmpl_id
                    join pos_order_line pol on pp.id = pol.product_id
                    join pos_order po on pol.order_id = po.id
                    join pos_session ps on ps.id = po.session_id
                    join pos_config poc ON ps.config_id = poc.id
                    where po.session_id = %s
                    group by pc.name, poc.name
                """ % cate_id[0])
                cate_detail = self._cr.dictfetchall()
                for j in cate_detail:
                    cate_lst.append({'cate_name':j.get('categ_name'), 'cate_total':j.get('sum'), 'session_name':j.get('name')})
            categ_null = []
            for cate_id_null in session_detail:
                self._cr.execute(""" 
                    select sum(pol.price_unit), poc.name from pos_order_line pol
                    join pos_order po on po.id = pol.order_id
                    join product_product pp on pp.id = pol.product_id
                    join product_template pt on pt.id = pp.product_tmpl_id
                    join pos_session ps on ps.id = po.session_id
                    join pos_config poc on ps.config_id = poc.id
                    where po.session_id = %s and pt.pos_categ_id is null
                    group by poc.name
                """ % cate_id_null[0])
                categ_null_detail = self._cr.dictfetchall()
                for k in categ_null_detail:
                    categ_null.append({'cate_name':'Undefined Category', 'cate_total':k.get('sum'), 'session_name':k.get('name')})
            all_cat = []
#             for sess in session_total:
#                 def_cate_lst = []
#                 for j in cate_lst:
#                     if j['session_name'] == sess[0]:
#                         def_cate_lst.append(j)
#                 for k in categ_null:
#                     if k['session_name'] == sess[0]:
#                         def_cate_lst.append(k)
#                 all_cat.append(def_cate_lst)
            all_cat_dict = {}
            for j in cate_lst:
                catename = str(j['cate_name'])
                if not all_cat_dict.has_key(catename):
                    all_cat_dict.update({catename: 0.0})
                all_cat_dict[catename] += float(j['cate_total'])
            for j in categ_null:
                catename = str(j['cate_name'])
                if not all_cat_dict.has_key(catename):
                    all_cat_dict.update({catename: 0.0})
                all_cat_dict[catename] += float(j['cate_total'])
            # 
            for journals in bank_detail:
                for journal in journals:
                    if journal_amounts.has_key(journal.get('name')):
                        val = journal_amounts[journal.get('name')]
                        journal_amounts[journal.get('name')] = val + journal.get('total_entry_encoding')
                    else:
                        journal_amounts[journal.get('name')] = journal.get('total_entry_encoding')

            return {'session_total':session_total, 'payment_lst':journal_amounts, 'all_cat':all_cat_dict}
        except:
           return {'error':'Error Function Working'}

    @api.multi
    def get_ip(self):
        if not self:
            return False
        return {'ip': self.config_id.proxy_ip or False}

    @api.multi
    def get_proxy_ip(self):
        proxy_id = self.env['res.users'].browse([self._uid]).company_id.report_ip_address
        return {'ip': proxy_id or False}

    @api.multi
    def get_user(self):
        if self._uid == SUPERUSER_ID:
            return True
    @api.multi
    def get_gross_total(self):
        gross_total = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    gross_total += line.qty * (line.product_id.lst_price - line.product_id.standard_price)
        return gross_total

    @api.multi
    def get_product_cate_total(self):
        balance_end_real = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    balance_end_real += (line.qty * line.price_unit)
        return balance_end_real

    @api.multi
    def get_net_gross_total(self):
        net_gross_profit = 0.0
        if self:
            net_gross_profit = self.get_gross_total() - self.get_total_tax()
        return net_gross_profit

    @api.multi
    def get_product_name(self, category_id):
        if category_id:
            category_name = self.env['pos.category'].browse([category_id]).name
            return category_name

    @api.multi
    def get_payments(self):
        if self:
            statement_line_obj = self.env["account.bank.statement.line"]
            pos_order_obj = self.env["pos.order"]
            company_id = self.env['res.users'].browse([self._uid]).company_id.id
            pos_ids = pos_order_obj.search([('state', 'in', ['paid', 'invoiced', 'done']),
                                            ('company_id', '=', company_id), ('session_id', '=', self.id)])
            data = {}
            if pos_ids:
                pos_ids = [pos.id for pos in pos_ids]
                st_line_ids = statement_line_obj.search([('pos_statement_id', 'in', pos_ids)])
                if st_line_ids:
                    a_l = []
                    for r in st_line_ids:
                        a_l.append(r['id'])
                    self._cr.execute("select aj.name,sum(amount) from account_bank_statement_line as absl,account_bank_statement as abs,account_journal as aj " \
                                    "where absl.statement_id = abs.id and abs.journal_id = aj.id  and absl.id IN %s " \
                                    "group by aj.name ", (tuple(a_l),))
    
                    data = self._cr.dictfetchall()
                    return data
            else:
                return {}

    @api.multi
    def get_product_category(self):
        product_list = []
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    flag = False
                    product_dict = {}
                    for lst in product_list:
                        if line.product_id.pos_categ_id:
                            if lst.get('pos_categ_id') == line.product_id.pos_categ_id.id:
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                flag = True
                        else:
                            if lst.get('pos_categ_id') == '':
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                flag = True
                    if not flag:
                        product_dict.update({
                                    'pos_categ_id': line.product_id.pos_categ_id and line.product_id.pos_categ_id.id or '',
                                    'price': (line.qty * line.price_unit)
                                })
                        product_list.append(product_dict)
        return product_list

    @api.multi
    def get_journal_amount(self):
        journal_list = []
        if self and self.statement_ids:
            for statement in self.statement_ids:
                journal_dict = {}
                journal_dict.update({'journal_id': statement.journal_id and statement.journal_id.name or '',
                                     'ending_bal': statement.balance_end_real or 0.0})
                journal_list.append(journal_dict)
        return journal_list

    @api.multi
    def get_total_closing(self):
        if self:
            return self.cash_register_balance_end_real

    @api.multi
    def get_total_returns(self):
        pos_order_obj = self.env['pos.order']
        total_return = 0.0
        if self:
            total_return = sum([order.amount_total for order in pos_order_obj.search([('session_id', '=', self.id), '|',
                                               ('parent_return_order', '!=', ''), ('refund_order_id', '!=', False)])])
        return total_return

    @api.multi
    def get_total_sales(self):
        total_price = 0.0
        if self:
            for order in self.order_ids:
                if not order.parent_return_order and not order.refund_order_id:
                    total_price += sum([(line.qty * line.price_unit) for line in order.lines])
        return total_price

    @api.multi
    def get_total_tax(self):
        if self:
            total_tax = 0.0
            pos_order_obj = self.env['pos.order']
            total_tax += sum([order.amount_tax for order in pos_order_obj.search([('session_id', '=', self.id)])])
        return total_tax

    @api.multi
    def get_total_discount(self):
        total_discount = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                total_discount += sum([((line.qty * line.price_unit) * line.discount) / 100 for line in order.lines])
        return total_discount

    @api.multi
    def get_total_redeem(self):
        total_redeem = 0.0
        if self:
            total_redeem += sum([order.redeem_point_amt for order in self.order_ids])
        return total_redeem

    # @api.multi
    # def get_total_coupon(self):
    #     total_coupon_amt = 0.0
    #     if self:
    #         total_coupon_amt += sum([order.gift_coupon_amt for order in self.order_ids])
    #     return total_coupon_amt

    @api.multi
    def get_total_first(self):
        total = 0.0
        if self:
            total = (self.get_total_sales() + self.get_total_tax())\
                - (abs(self.get_total_returns()) + 
                   # self.get_total_coupon() +
                   self.get_total_redeem() + self.get_total_discount())
        return total

    @api.multi
    def get_session_date(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz = timezone(self._context.get('tz'))
            else:
                tz = pytz.utc
#             tz = timezone(tz_name)
            c_time = datetime.now(tz)
            hour_tz = int(str(c_time)[-5:][:2])
            min_tz = int(str(c_time)[-5:][3:])
            sign = str(c_time)[-6][:1]
            if sign == '+':
                date_time = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT) + \
                                                    timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT) - \
                                                    timedelta(hours=hour_tz, minutes=min_tz)
            return date_time.strftime('%d/%m/%Y')

    @api.multi
    def get_session_time(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz = timezone(self._context.get('tz'))
            else:
                tz = pytz.utc
#             tz = timezone(tz_name)
            c_time = datetime.now(tz)
            hour_tz = int(str(c_time)[-5:][:2])
            min_tz = int(str(c_time)[-5:][3:])
            sign = str(c_time)[-6][:1]
            if sign == '+':
                date_time = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT) + \
                                                    timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT) - \
                                                    timedelta(hours=hour_tz, minutes=min_tz)
            return date_time.strftime('%I:%M:%S %p')

    @api.multi
    def get_current_date(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
#             tz = timezone(tz_name)
            c_time = datetime.now(tz)
            return c_time.strftime('%d/%m/%Y')
        else:
            return date.today().strftime('%d/%m/%Y')

    @api.multi
    def get_current_time(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
#             tz = timezone(tz_name)
            c_time = datetime.now(tz)
            return c_time.strftime('%I:%M %p')
        else:
            return datetime.now().strftime('%I:%M:%S %p')

    @api.multi
    def close_session_from_ui(self): 
        session_cash_control = self.browse().cash_control
        if session_cash_control:
            self.signal_workflow('cashbox_control')
        self.signal_workflow('close')

    @api.depends('config_id.cash_control')
    def _compute_cash_all(self):
        cashdrawer = False
        for session in self:
            session.cash_journal_id = session.cash_register_id = session.cash_control = False
            if session.config_id.cash_control:
                for statement in session.statement_ids:
                    if statement.journal_id.type == 'cash':
                        if statement.journal_id.is_cashdrawer:
                            session.cash_control = True
                            session.cash_journal_id = statement.journal_id.id
                            session.cash_register_id = statement.id
                            cashdrawer = True
                if not cashdrawer:
                    raise UserError(_("Please enable cash drawer in cash journal."))
                if not session.cash_control:
                    raise UserError(_("Cash control can only be applied to cash journals."))

    @api.multi
    def get_company_data_x(self):
        return self.user_id.company_id

    @api.multi
    def get_pos_name_x (self):
        return self.config_id.name

    @api.multi
    def get_current_date_x(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
#             tz = timezone(tz_name)
            c_time = datetime.now(tz)
            return c_time.strftime('%d/%m/%Y')
        else:
            return date.today().strftime('%d/%m/%Y')
    
    @api.multi
    def get_session_date_x(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz = self._context['tz']
                tz = timezone(tz)
            else:
                tz = pytz.utc
            if tz:
#                 tz = timezone(tz_name)
                c_time = datetime.now(tz)
                hour_tz = int(str(c_time)[-5:][:2])
                min_tz = int(str(c_time)[-5:][3:])
                sign = str(c_time)[-6][:1]
                if sign == '+':
                    date_time = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT) + \
                                                        timedelta(hours=hour_tz, minutes=min_tz)
                else:
                    date_time = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT) - \
                                                        timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT)
            return date_time.strftime('%d/%m/%Y')

    @api.multi
    def get_current_time_x(self):
        if self._context and self._context.get('tz'):
            tz = self._context['tz']
            tz = timezone(tz)
        else:
            tz = pytz.utc
        if tz:
#             tz = timezone(tz_name)
            c_time = datetime.now(tz)
            return c_time.strftime('%I:%M %p')
        else:
            return datetime.now().strftime('%I:%M:%S %p')
    
    @api.multi
    def get_session_time_x(self, date_time):
        if date_time:
            if self._context and self._context.get('tz'):
                tz = self._context['tz']
                tz = timezone(tz)
            else:
                tz = pytz.utc
            if tz:
#                 tz = timezone(tz_name)
                c_time = datetime.now(tz)
                hour_tz = int(str(c_time)[-5:][:2])
                min_tz = int(str(c_time)[-5:][3:])
                sign = str(c_time)[-6][:1]
                if sign == '+':
                    date_time = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT) + \
                                                        timedelta(hours=hour_tz, minutes=min_tz)
                else:
                    date_time = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT) - \
                                                        timedelta(hours=hour_tz, minutes=min_tz)
            else:
                date_time = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT)
            return date_time.strftime('%I:%M:%S %p')
    
    @api.multi
    def get_total_sales_x(self):
        total_price = 0.0
        if self:
            for order in self.order_ids:
                if order.state != 'draft':
                    for line in order.lines:
                        total_price = total_price + line.price_subtotal
        total_price = total_price + self.get_total_returns_x()+ self.get_total_discount_x()
        return total_price
    
    @api.multi
    def get_total_returns_x(self):
        pos_order_obj = self.env['pos.order']
        total_return = 0.0
        if self:
            for order in pos_order_obj.search([('session_id', '=', self.id)]):
                if order.amount_total < 0:
                    total_return += abs(order.amount_total)
        return total_return

    @api.multi
    def get_total_tax_x(self):
        total_tax = 0.0
        if self:
            pos_order_obj = self.env['pos.order']
            total_tax += sum([order.amount_tax for order in pos_order_obj.search([('session_id', '=', self.id)])])
        return total_tax

    @api.multi
    def get_total_discount_x(self):
        total_discount = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                total_discount += sum([line.item_discount_share + line.item_discount_amount for line in order.lines])
#                 total_discount += sum([((line.qty * line.price_unit) * line.discount) / 100 for line in order.lines])
        return total_discount

    @api.multi
    def get_total_first_x(self):
        global gross_total
        if self:
            gross_total = (self.get_total_sales_x() + self.get_total_tax_x()) \
                 + self.get_total_discount_x()
        return gross_total

    @api.multi
    def get_net_sale_x(self):
        if self:
            net_total = (self.get_total_sales_x() - self.get_total_returns_x()) - self.get_total_discount_x()
        return net_total

    @api.multi
    def get_user_x(self):
        if self._uid == SUPERUSER_ID:
            return True

    @api.multi
    def get_gross_total_x(self):
        total_cost = 0.0
        gross_total = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    total_cost += line.qty * line.product_id.standard_price
        gross_total = self.get_total_sales_x() - \
                    + self.get_total_tax_x() - total_cost
        return gross_total

    @api.multi
    def get_net_gross_total_x(self):
        net_gross_profit = 0.0
        total_cost = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    total_cost += line.qty * line.product_id.standard_price
            net_gross_profit = self.get_total_sales_x() - self.get_total_tax_x() - total_cost
        return net_gross_profit

    @api.multi
    def get_product_cate_total_x(self):
        balance_end_real = 0.0
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    balance_end_real += (line.qty * line.product_mrp)
        return balance_end_real

    @api.multi
    def get_product_name_x(self, category_id):
        if category_id:
            category_name = self.env['pos.category'].browse([category_id]).name
            return category_name

    @api.multi
    def get_product_category_x(self):
        product_list = []
        if self and self.order_ids:
            for order in self.order_ids:
                for line in order.lines:
                    flag = False
                    product_dict = {}
                    for lst in product_list:
                        if line.product_id.pos_categ_id:
                            if lst.get('pos_categ_id') == line.product_id.pos_categ_id.id:
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
#                                 if line.product_id.pos_categ_id.show_in_report:
                                lst['qty'] = lst.get('qty') or 0.0 + line.qty
                                flag = True
                        else:
                            if lst.get('pos_categ_id') == '':
                                lst['price'] = lst['price'] + (line.qty * line.price_unit)
                                lst['qty'] = lst.get('qty') or 0.0 + line.qty
                                flag = True
                    if not flag:
                        if line.product_id.pos_categ_id:
                            product_dict.update({
                                        'pos_categ_id': line.product_id.pos_categ_id and line.product_id.pos_categ_id.id or '',
                                        'price': (line.qty * line.price_unit),
                                        'qty': line.qty
                                    })
                        else:
                            product_dict.update({
                                        'pos_categ_id': line.product_id.pos_categ_id and line.product_id.pos_categ_id.id or '',
                                        'price': (line.qty * line.price_unit),
                                    })
                        product_list.append(product_dict)
        return product_list
    
    @api.multi
    def get_payments_x(self):
        if self:
            statement_line_obj = self.env["account.bank.statement.line"]
            pos_order_obj = self.env["pos.order"]
            company_id = self.env['res.users'].browse([self._uid]).company_id.id
            pos_ids = pos_order_obj.search([('session_id', '=', self.id),
                                            ('state', 'in', ['paid', 'invoiced', 'done']),
                                            ('user_id', '=', self.user_id.id), ('company_id', '=', company_id)])
            data = {}
            if pos_ids:
                pos_ids = [pos.id for pos in pos_ids]
                st_line_ids = statement_line_obj.search([('pos_statement_id', 'in', pos_ids)])
                if st_line_ids:
                    a_l = []
                    for r in st_line_ids:
                        a_l.append(r['id'])
                    self._cr.execute("select aj.name,sum(amount) from account_bank_statement_line as absl,account_bank_statement as abs,account_journal as aj " \
                                    "where absl.statement_id = abs.id and abs.journal_id = aj.id  and absl.id IN %s " \
                                    "group by aj.name ", (tuple(a_l),))

                    data = self._cr.dictfetchall()
                    return data
            else:
                return {}

    def _confirm_orders(self):
        for session in self:
            company_id = session.config_id.journal_id.company_id.id
            orders = session.order_ids.filtered(lambda order: order.state == 'paid')
            journal_id = self.env['ir.config_parameter'].sudo().get_param(
                'pos.closing.journal_id_%s' % company_id, default=session.config_id.journal_id.id)

            move = self.env['pos.order'].with_context(force_company=company_id)._create_account_move(session.start_at, session.name, int(journal_id), company_id)
            orders.with_context(force_company=company_id)._create_account_move_line(session, move)
            for order in session.order_ids.filtered(lambda o: o.state not in ['done', 'invoiced']):
                if order.state not in ('draft'):
                    # raise UserError(_("You cannot confirm all orders of this session, because they have not the 'paid' status"))
                    order.action_pos_order_done()

    @api.multi
    def action_pos_session_open(self):
        pos_order = self.env['pos.order'].search([('state', '=', 'draft')])
        for order in pos_order:
            if order.session_id.state != 'opened':
                order.write({'session_id': self.id})
        return super(pos_session, self).action_pos_session_open()

class quick_cash_payment(models.Model):
    _name = "quick.cash.payment"
 
    name = fields.Float(string='Amount')
    
    _sql_constraints = [
        ('quick_cash_payment', 'unique(name)', 'This amount already selected'),
    ]

class PosCategory(models.Model):
    _inherit = "pos.category"

    return_valid_days = fields.Integer("Return Valid Days")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
