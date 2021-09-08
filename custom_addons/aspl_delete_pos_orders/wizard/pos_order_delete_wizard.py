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
from odoo import fields, models, api, _
from odoo.exceptions import Warning

class PosDeleteOrder(models.TransientModel):
    _name = "pos.order.delete"

    security_pin = fields.Char("Enter PIN")

    @api.one
    def delete_pos_order(self):
        user_id = self.env['res.users'].browse([self._uid])
        order_obj = self.env['pos.order']

        session_lst = set([each.session_id for each in order_obj.browse(self._context.get('active_ids'))])
        if len(session_lst) > 1:
            raise Warning(_('Please select orders from same sessions'))
        if not user_id.allow_delete:
            raise Warning(_('Sorry!\n'
                            'You are not allowed to perform this operation !'))
        if user_id.pos_security_pin != self.security_pin:
            raise Warning(_('Incorrect PIN!\n'
                            'Please Enter correct PIN!'))
        if self._context.get('active_ids'):
            self._cr.execute(''' select id from account_bank_statement_line
                WHERE pos_statement_id in %s''' % (" (%s) " % ','.join(map(str, self._context.get('active_ids')))))
            result = self._cr.dictfetchall()
            #remove lines for payment
            for statement_line in result:
                line_brw_id = self.env['account.bank.statement.line'].browse([statement_line.get('id')])
                if line_brw_id.journal_entry_ids:
                    move_lines = [line.id for move_id in line_brw_id.journal_entry_ids for line in move_id.line_ids]
                    if move_lines:
                        del_rec_line = ''' delete from account_partial_reconcile
                                    WHERE credit_move_id in %s or debit_move_id in %s''' % (" (%s) " % ','.join(map(str, move_lines))," (%s) " % ','.join(map(str, move_lines)))
                        self._cr.execute(del_rec_line)
                    if line_brw_id.journal_entry_ids:
                        del_move = ''' delete from account_move
                                    WHERE id in %s''' % (" (%s) " % ','.join(map(str, line_brw_id.journal_entry_ids.ids)))
                        self._cr.execute(del_move)
                        self._cr.commit()
            once = False
            total_amount = sum(order_obj.browse(self._context.get('active_ids')).filtered(lambda x: x.state == 'done').mapped('amount_total'))
            #remove move lines for sales
            for order_id in order_obj.browse(self._context.get('active_ids')):
                move_line_sale = self.env['account.move.line'].search([('tr','=', False), ('pos_order_id','=', order_id.id)], limit=1)
                if move_line_sale:
                    move_line_tr = self.env['account.move.line'].search([('tr','=', True), ('move_id','=', move_line_sale.move_id.id)], limit=1)
                    if not once and move_line_tr:
                        update_move_line = ''' UPDATE account_move_line set debit=%s
                                    WHERE id = %s''' % (move_line_tr.debit - total_amount, move_line_tr.id)
                        self._cr.execute(update_move_line)
                        del_move_line = ''' delete from account_move_line
                                WHERE pos_order_id =  %s and tr=False''' % (order_id.id)
                        self._cr.execute(del_move_line)
                        self._cr.commit()
                        once=True
            #Update statements
            orders = order_obj.browse(self._context.get('active_ids'))
            session_ids = list(set([order.session_id for order in orders]))
            picking_ids = [order.picking_id.id for order in orders if order.picking_id]
            statements = list(set([statement_id for session_id in session_ids for statement_id in session_id.statement_ids]))
            del_rec_line = ''' delete from pos_order
                            WHERE id in %s''' % (" (%s) " % ','.join(map(str, self._context.get('active_ids'))))
            self._cr.execute(del_rec_line)
            #remove delivery orders
            if picking_ids:
                del_pack_line = ''' delete from stock_pack_operation
                                WHERE picking_id in %s''' % (" (%s) " % ','.join(map(str, picking_ids)))
                self._cr.execute(del_pack_line)
                del_move_line = ''' delete from stock_move
                                WHERE picking_id in %s''' % (" (%s) " % ','.join(map(str, picking_ids)))
                self._cr.execute(del_move_line)
                del_picking_line = ''' delete from stock_picking
                                WHERE id in %s''' % (" (%s) " % ','.join(map(str, picking_ids)))
                self._cr.execute(del_picking_line)
            for each_stat in statements:
                each_stat._end_balance()
                if each_stat.state == 'confirm':
                    each_stat.write({'balance_end_real' : each_stat.balance_end_real - total_amount})
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
