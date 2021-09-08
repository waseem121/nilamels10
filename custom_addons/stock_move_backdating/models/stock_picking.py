# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
from odoo.exceptions import Warning, ValidationError

class Picking(models.Model):
    _name = "stock.picking"
    _inherit = _name
    
    date_done = fields.Datetime('Date of Transfer', copy=False, readonly=False, help="Completion Date of Transfer")
    
    @api.multi
    def do_new_transfer(self):
        for pick in self:
            user = self.env['res.users'].browse(self.env.uid)
            allow_negative = user.has_group('direct_sale.group_allow_negative_qty')
	    if pick.picking_type_id.code !='incoming' and allow_negative:
                if pick.state in ('waiting','partially_available','confirmed'):
                    pick.action_confirm()
                if pick.state=='draft' and pick.picking_type_id.code == 'internal':
                    pick.action_confirm()
                    pick.action_assign()
                pick.action_done()
                return True
            
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
                        
            pack_operations_delete = self.env['stock.pack.operation']
            if not pick.move_lines and not pick.pack_operation_ids:
                raise UserError(_('Please create some Initial Demand or Mark as Todo and create some Operations. '))
            # In draft or with no pack operations edited yet, ask if we can just do everything
            if pick.state == 'draft' or all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
                # If no lots when needed, raise error
                picking_type = pick.picking_type_id
                if (picking_type.use_create_lots or picking_type.use_existing_lots):
                    for pack in pick.pack_operation_ids:
                        if pack.product_id and pack.product_id.tracking != 'none':
                            raise UserError(_('Some products require lots/serial numbers, so you need to specify those first!'))
                view = self.env.ref('stock.view_immediate_transfer')
#                wiz = self.env['stock.immediate.transfer'].create({'pick_id': pick.id,'date_backdating':pick.date_done or fields.Datetime.now()}) ## Added
                wiz = self.env['stock.immediate.transfer'].create({'pick_id': pick.id,'date_backdating':pick.min_date or fields.Datetime.now()}) ## Added
                # TDE FIXME: a return in a loop, what a good idea. Really.
                return {
                    'name': _('Immediate Transfer?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.immediate.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }

            # Check backorder should check for other barcodes
            if pick.check_backorder():
                view = self.env.ref('stock.view_backorder_confirmation')
                wiz = self.env['stock.backorder.confirmation'].create({
                    'pick_id': pick.id,
                    'date_backdating':pick.min_date or fields.Datetime.now()})## Added
                # TDE FIXME: same reamrk as above actually
                return {
                    'name': _('Create Backorder?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.backorder.confirmation',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }
            for operation in pick.pack_operation_ids:
                if operation.qty_done < 0:
                    raise UserError(_('No negative quantities allowed'))
                if operation.qty_done > 0:
#                    operation.write({'product_qty': operation.qty_done,'date':pick.date_done or fields.Datetime.now()}) ## Added
                    operation.write({'product_qty': operation.qty_done,
                        'date':pick.min_date or fields.Datetime.now()}) ## Added
                else:
                    pack_operations_delete |= operation
            if pack_operations_delete:
                pack_operations_delete.unlink()
#        force_period_date=pick.date_done or time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        force_period_date=pick.min_date or time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.with_context(force_period_date=force_period_date).do_transfer()
        return
