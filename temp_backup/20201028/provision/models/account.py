# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    x_picking_id = fields.Many2one('stock.picking', 'Picking')
    
    @api.onchange('x_picking_id')
    def _onchange_picking_id_auto_complete(self):
        
        if not self.x_picking_id:
            return
        
        if self.invoice_line_ids:
#            for l in self.invoice_line_ids:
#                l.unlink()
#            self.invoice_line_ids.unlink()
#            self.invoice_line_ids_two.unlink()
            self.amount_untaxed = 0.0
            self.amount_total = 0.0
            
#        self.partner_id = self.picking_id.partner_id
#        self.fiscal_position_id = False
#        self.invoice_payment_term_id = False
#        self.currency_id = self.picking_id.company_id and self.picking_id.company_id.currency_id

        moves = self.x_picking_id.move_lines
#        new_lines = self.env['account.invoice.line']
        Line = self.env['account.invoice.line']
        new_lines = []
        value = {}
        sequence = 1
        arr = []
        for move in moves:
            currency = self.currency_id
            line = {
                'sequence2':sequence,
                'name': move.name,
                'invoice_id': self.id,
                'currency_id': currency and currency.id or False,
                'date_maturity': move.date,
                'uom_id': move.product_uom.id,
                'product_id': move.product_id.id,
                'price_unit': move.price_unit or move.product_id.standard_price,
                'quantity': move.product_uom_qty,
                'partner_id': self.partner_id.id,
                'account_id':move.product_id.categ_id.property_account_income_categ_id.id
                }
#            Line.create(line)
            
            new_lines.append((0,0,line))
            arr.append(line)
            sequence+=1
        value.update(invoice_line_ids=new_lines)
#        self.invoice_line_ids = [x for x in new_lines]
        return {'value':value}
    
    @api.multi
    def action_invoice_open(self):
        print"provision/account action_invoice_open called"

        # invoice_ids
        if self.number:
            pickings = self.env['stock.picking'].search([('origin','=',self.number)])
            if len(pickings):
                for picking in pickings:
                    if picking.state not in ['done', 'cancel']:
                        raise Warning(_("The Delivery for this order is not validated yet, Please validate it first...!!!!"))

        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))
        
        if self.x_picking_id:
            self.x_picking_id.write({'origin':self.number})
        if not self.x_picking_id:
            if self.is_direct_invoice or self.refund_without_invoice:
                if not self.refund_without_invoice:
                    product_lst = self.invoice_line_ids.mapped('product_id')
                    for product_id in product_lst:
                        product_sum_qty = sum(
                            self.invoice_line_ids.filtered(lambda l: l.product_id.id == product_id.id).mapped('quantity'))
                        product_sum_free_qty = sum(
                            self.invoice_line_ids.filtered(lambda l: l.product_id.id == product_id.id).mapped('free_qty'))
                        product_sum_qty += product_sum_qty +product_sum_free_qty

                        prod_qty_available = product_id.with_context(
                            {'location': self.location_id.id, 'compute_child': False}).qty_available
    #                        {'location': self.location_id.id, 'compute_child': False}).virtual_available_inv
                        if prod_qty_available < product_sum_qty:
                            raise Warning(_('%s has not enough quantity into %s location.') % (
                                product_id.name, self.location_id.name))

                    for invoice_line in self.invoice_line_ids.filtered(
                            lambda l: l.product_id.tracking != 'none' and not l.lot_ids):
                        if self.env['stock.config.settings'].search([], order='id desc',
                                                                    limit=1).group_stock_production_lot:
                            raise Warning(
                                _('For product %s serial number must be required.') % invoice_line.product_id.name)
                            zero_lot = invoice_line.lot_ids.filtered(lambda l: l.remaining_qty <= 0)
                            if zero_lot:
                                raise Warning(_('Define Lot/Serial number %s for product %s is now not available.' %
                                                ([str(lot.name) for lot in zero_lot], invoice_line.product_id.name)))

                    for invoice_line in self.invoice_line_ids.filtered(
                            lambda l: l.product_id.tracking == 'serial' and l.lot_ids):
                        if len(invoice_line.lot_ids) != invoice_line.quantity:
                            raise Warning(
                                _('Please check serial number and quantity on product %s, those must be in same number.') %
                                ("'" + invoice_line.product_id.name + "'"))

                    for invoice_line in self.invoice_line_ids.filtered(lambda l: l.product_id):
                        available_qty = 0.00
                        if invoice_line.product_id.tracking != 'none':
                            for each_lot in invoice_line.lot_ids:
                                available_qty += invoice_line.product_id.with_context(
                                    {'location': self.location_id.id, 'compute_child': False,
                                     'lot_id': each_lot.id}).qty_available
                        else:
                            available_qty = invoice_line.product_id.with_context(
                                {'location': self.location_id.id, 'compute_child': False}).qty_available
                        if (invoice_line.quantity + invoice_line.free_qty) > available_qty:
                            raise Warning(_('Not enough quantity for %s .') % (invoice_line.product_id.name))
                else:
                    for invoice_line in self.invoice_line_ids.filtered(
                            lambda l: l.product_id.tracking != 'none' and not l.lot_ids):
                        if self.env['stock.config.settings'].search([], order='id desc',
                                                                    limit=1).group_stock_production_lot:
                            raise Warning(
                                _('For product %s serial number must be required.') % invoice_line.product_id.name)

                if self.refund_invoice_id:
                    self.do_return_picking()
                else:
                    self.action_create_sales_order()    #creates only sales order no picking created here
                    self.action_stock_transfer()
                    self.check_date()
        to_open_invoices.action_date_assign()
        company_id = self.env.user.company_id.id
        ir_values = self.env['ir.values']
        is_discount_posting_setting = ir_values.get_default('account.config.settings', 'is_discount_posting_setting',
                                                            company_id=company_id) or False
        ctx = dict(self._context or {})
        ctx['is_discount_posting_setting'] = is_discount_posting_setting
        # sequence_code = self.env['ir.sequence'].next_by_code('account.invoice')
        # self.number = sequence_code
        # ctx['sequence_number'] = sequence_code
        # ctx['name'] = sequence_code
        # ctx['number'] = sequence_code
        to_open_invoices.with_context(ctx).action_move_create()
        # sequence number
        # self.number = sequence_code
        # self.name = sequence_code
        return to_open_invoices.invoice_validate()    
    
    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if res.is_direct_invoice or res.refund_without_invoice or res.type in ['in_invoice', 'in_refund'] or self._context.get('sale_order_location',False):
            new_name = False
            journal = res.journal_id
            location = res.location_id
            if location.sequence_id:
                sequence = location.sequence_id
                if res.refund_without_invoice or res.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                    sequence = journal.refund_sequence_id
                new_name = sequence.with_context(ir_sequence_date=res.date_invoice).next_by_id()
            else:
                raise UserError(_('Please define a sequence on the Location.'))                
            if new_name:
                res.number = new_name

        if res.pricelist_id and res.pricelist_id.update_transaction_value:
            res.product_price_update()
        return res    
    
#    @api.model
#    def create(self, vals):
#        res = super(AccountInvoice, self).create(vals)
#        number = res.number
#        location_id = vals.get('location_id', False)
#        if location_id:
#            location = self.env['stock.location'].browse(location_id)
#            res.number = location.name[:2] + '-'+number
#            
#        return res
    
#    @api.multi
#    def write(self, vals):
#        if vals.get('location_id',False):
#            for inv in self:
#                if inv.location_id.id != vals.get('location_id',False):
#                    location = self.env['stock.location'].browse(vals.get('location_id',False))
#                    number = inv.number
#                    print"number.find('-'): ",number.find('-')
#                    if number.find('-') != -1:
#                        vals['number'] = location.name[:2]+ '-' + number.split("-")[1]
#
#        res = super(AccountInvoice, self).write(vals)
#        return res    