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


class ChangeCustomer(models.TransientModel):
    _name = 'change.customer'

    partner_id = fields.Many2one('res.partner', 
        string='Customer', required=True)
    user_id = fields.Many2one('res.users', 
        string='Salesman')
        
        
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            user_id = self.partner_id.user_id and self.partner_id.user_id.id or False
            if user_id:
                self.user_id = user_id

    @api.multi
    def do_change_customer(self):
        new_partner = self.partner_id or False
        new_account = new_partner.property_account_receivable_id
        
        new_salesman = self.user_id or False
        if not new_salesman:
            new_salesman = new_partner.user_id or False
        if not new_salesman:
            raise Warning(_('Please choose salesman.'))
        
        context = self._context
        invoice = self.env['account.invoice'].browse(context.get('active_id'))
        if new_partner.id == invoice.partner_id.id:
            raise Warning(_('Please choose different partner, This one is already in the invoice.'))
        if not invoice.refund_without_invoice:
            raise Warning(_('This feature is only available for Refund Without Invoices.'))
        old_account = invoice.account_id
        
        move = invoice.move_id
        aml = move.line_ids.filtered(lambda x: x.account_id.reconcile or x.account_id.internal_type == 'liquidity')
        aml.remove_move_reconcile()
        
        move.button_cancel()
        aml = move.line_ids.filtered(lambda x: x.account_id.id==old_account.id)
        aml.write({'account_id':new_account.id})
        
        # change the partner and lable in move line
        vals = {'partner_id':new_partner.id}
        addr = new_partner.address_get(['delivery'])
        partner_shipping_id = addr and addr.get('delivery')
        name = new_partner.street or new_partner.name or False
        if not partner_shipping_id:
            partner_shipping_id = new_partner.id
        if partner_shipping_id:
            partner_shipping = self.env['res.partner'].browse(partner_shipping_id)
            name = partner_shipping.street or partner_shipping.name or False
        if name:
            vals['name'] = name
        move.line_ids.write(vals)
        # change the partner and lable in move line
        move.write({'salesman_id':new_salesman.id})
        
        invoice.write({'partner_id':new_partner.id,
            'partner_shipping_id':partner_shipping_id,
            'account_id':new_account.id,
            'user_id':new_salesman.id})
            
            
        if invoice.invoice_picking_id:
            picking = invoice.invoice_picking_id
            picking.write({'partner_id':new_partner.id})
            picking_move = picking.account_move_id or False
            if picking_move:
                picking_move.line_ids.write({'partner_id':new_partner.id})
                
        move.post()
        
        
        # auto-reconcile start
        if invoice.type == 'out_refund' and invoice.state!='draft':
            account = new_account
            if account.auto_reconcile:
                credit_aml = invoice.move_id.line_ids.filtered(lambda r: r.account_id.id == account.id)
                credit = credit_aml.credit
                print"credit: ",credit

                debit_aml_all = self.env['account.move.line'].search([('account_id','=',account.id),('debit','>',0.0),('reconciled','=',False)])
                print"debit_aml_all: ",debit_aml_all
                debit_aml_ids = []
                debit = 0.0
                skip = False
                for l in debit_aml_all:
                    debit += l.debit
                    if skip:
                        continue
                    debit_aml_ids.append(l.id)
                    if credit <=debit:
                        skip=True
                print"debit: ",debit

                debit_aml = self.env['account.move.line'].browse(debit_aml_ids)
                print"debit_aml: ",debit_aml

                res = (credit_aml + debit_aml).reconcile()
                print"after reconcile res: ",res
        # auto-reconcile end
            
        return True
    


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
