# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
from odoo.exceptions import Warning, ValidationError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    commission = fields.Float(string='Commission', digits=dp.get_precision('Discount'))
    commission_account_id = fields.Many2one('account.account', string="Commission Account")
    discount_account_id = fields.Many2one('account.account', string="Discount Account")
    
    @api.onchange('commission','amount_untaxed')
    def _onchange_commission(self):
        prec_discount = self.env['decimal.precision'].precision_get('Discount')
        if self.commission:
            item_commission = 0.0
            invoice_lines = self.invoice_line_ids_two or self.invoice_line_ids
            if len(invoice_lines):
                for line in invoice_lines:
                    commission_percentage = self.commission /self.amount_untaxed
                    commission_share = float_round(commission_percentage * line.price_subtotal, precision_digits=prec_discount)
                    line.write({'commission_share':commission_share})
                    line.commission_share = commission_share
                    item_commission += commission_share
                

            commission = float_round(self.commission, precision_digits=prec_discount)

            ### if any fills diff, adding it to first line
            #get the latest item discount for comparing
            item_commission_prev = item_commission
            item_commission = 0.0
            invoice_lines = self.invoice_line_ids_two or self.invoice_line_ids
            if len(invoice_lines):
                for line in invoice_lines:
                    item_commission += float_round(line.commission_share, precision_digits=prec_discount)


            if commission != item_commission:
                diff = commission - item_commission
                invoice_lines = self.invoice_line_ids_two or self.invoice_line_ids
                if len(invoice_lines):
                    updated=False
                    commission_share=0.0
                    for line in invoice_lines:
                        if (line.price_subtotal<=0) or updated:
                            continue
                        commission_share = line.commission_share + diff
                        item_commission_prev = item_commission_prev + diff

                        commission_share = float_round(commission_share, precision_digits=prec_discount)
                        line.write({'commission_share':commission_share})
                        line.commission_share=commission_share
                        updated=True

                    
    # to create the commission Credit entry
    @api.multi
    def action_move_create(self):
        discount_enabled=False
        for invoice in self:
            if invoice.type in ('out_invoice', 'out_refund'):
                settings = self.env['account.config.settings'].search([],order='id DESC')
                if settings:
                    discount_enabled = settings[0].group_enable_separate_discount_entry or False
                    if discount_enabled and invoice.total_discount and not settings[0].discount_account_id:
                        raise UserError(_('Please configure Discount account.'))
                    invoice.write({'discount_account_id':settings[0].discount_account_id.id})

                    commission_enabled = settings[0].group_enable_commission or False
                    if commission_enabled and invoice.commission and not self.commission_account_id:
                        raise UserError(_('Please select Commission account.'))
                
        result = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if inv.type not in ('out_invoice', 'out_refund'):
                continue
            commission_account_id = False
            if inv.commission and inv.move_id:
                commission_account_id = inv.commission_account_id.id
                move = inv.move_id
                move.button_cancel()
                
                credit_line_ids = move.line_ids.filtered(lambda l:l.credit)
                name = credit_line_ids[0].name
                partner_id = credit_line_ids[0].partner_id and credit_line_ids[0].partner_id.id or False
                
                credit = sum(credit_line_ids.mapped('credit'))
                credit_line_ids.with_context({'check_move_validity':False}).write(
                                {'credit':credit - inv.commission,
                                'debit':0
                                })
                print"credit line updated with commission"
                                
                commission_line = {
                    'name': 'Commission',
                    'product_id': False,
                    'quantity': 0.0,
                    'product_uom_id': False,
                    'ref': name,
                    'partner_id': partner_id,
                    'account_id': inv.commission_account_id.id,
                    'move_id': move.id,
                    'credit':self.commission
                }

                line_id = self.env['account.move.line'].with_context({
                        'check_move_validity':False}).create(commission_line)
                print"commission_line created "
                move.post()
                
            # seprate entry for discount
            total_discount = inv.total_discount or 0.0
            if discount_enabled and total_discount and inv.move_id:
                move = inv.move_id
                move.button_cancel()
                
                credit_line_ids = move.line_ids.filtered(lambda l:l.credit)
                name = credit_line_ids[0].name
                partner_id = credit_line_ids[0].partner_id and credit_line_ids[0].partner_id.id or False
                
                if commission_account_id:
                    credit_line_ids = move.line_ids.filtered(lambda l:l.account_id.id != commission_account_id and l.credit)
                    
                credit = sum(credit_line_ids.mapped('credit'))
                credit_line_ids.with_context({'check_move_validity':False}).write(
                                {'credit':credit + total_discount,
                                'debit':0
                                })
                print"credit line updated with discount"
                                
                discount_line = {
                    'name': 'Discount',
                    'product_id': False,
                    'quantity': 0.0,
                    'product_uom_id': False,
                    'ref': name,
                    'partner_id': partner_id,
                    'account_id': inv.discount_account_id.id,
                    'move_id': move.id,
                    'debit':total_discount
                }

                line_id = self.env['account.move.line'].with_context({
                        'check_move_validity':False}).create(discount_line)
                print"discount_line created "
                move.post()
                                                            
        return True
    
    # to raise the warning messages at first only
    @api.multi
    def action_invoice_open(self):
        if self.number:
            pickings = self.env['stock.picking'].search([('origin','=',self.number)])
            if len(pickings):
                for picking in pickings:
                    if picking.state not in ['done', 'cancel']:
                        raise Warning(_("The Delivery for this order is not validated yet, Please validate it first...!!!!"))
                    
        if self.type in ('out_invoice', 'out_refund'):
            settings = self.env['account.config.settings'].search([],order='id DESC')
            if settings:
                discount_enabled = settings[0].group_enable_separate_discount_entry or False
                if discount_enabled and self.total_discount and not settings[0].discount_account_id:
                    raise UserError(_('Please configure Discount account.'))
                self.write({'discount_account_id':settings[0].discount_account_id.id})
                print"invoice updatednew"

                commission_enabled = settings[0].group_enable_commission or False
                if commission_enabled and self.commission and not self.commission_account_id:
                    raise UserError(_('Please select Commission account.'))

        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))

        if self.is_direct_invoice or self.refund_without_invoice:
            if not self.refund_without_invoice:
                product_lst = self.invoice_line_ids.mapped('product_id')
                for product_id in product_lst:
                    product_sum_qty = sum(
                        self.invoice_line_ids.filtered(lambda l: l.product_id.id == product_id.id).mapped('quantity'))
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
                    if invoice_line.quantity > available_qty:
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

        #update the cost in invoice line
        self.update_invoice_line_cost()

        to_open_invoices.action_date_assign()
        company_id = self.env.user.company_id.id
        ir_values = self.env['ir.values']
        is_discount_posting_setting = ir_values.get_default('account.config.settings', 'is_discount_posting_setting',
                                                            company_id=company_id) or False
        ctx = dict(self._context or {})
        ctx['is_discount_posting_setting'] = is_discount_posting_setting
        to_open_invoices.with_context(ctx).action_move_create()
        return to_open_invoices.invoice_validate()

    # updates the cost in invoicelines
    def update_invoice_line_cost(self):
        for l in self.invoice_line_ids:
            standard_price = l.product_id.standard_price
            l.write({'cost_price':standard_price})
        for l in self.invoice_line_ids_two:
            standard_price = l.product_id.standard_price or 0.0
            l.write({'cost_price':standard_price})
        return True
    
    
class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    
    commission_share = fields.Float(string='Commission Share', digits=dp.get_precision('Discount'))
