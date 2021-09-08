# -*- coding: utf-8 -*-

from openerp import models, api, fields, exceptions
import odoo.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    discount_type = fields.Selection(
        [('per','Percentage'), ('amount','Amount'),
        ], 'Discount Type',)
    
    @api.multi
    def update_old_invoice(self):
        search_ids = self.search([('discount_type', '=', False)])
        if not search_ids:
            return False
        search_ids.write({'discount_type': 'per'})
        return True
    
    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.invoice_line_ids:
            ## Commented
            #price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            ## End
            ## ADDED
            if line.invoice_id.discount_type == 'per':
                price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            else:
                price_unit = line.price_unit - line.discount
            ## END
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped


AccountInvoice()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice', 'invoice_id.discount_type')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        ## Commented
        #price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        ## END
        if self.invoice_id.discount_type == 'per':
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        else:
            price = self.price_unit - self.discount or 0.0
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(date=self.invoice_id.date_invoice).compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign
        
    ## Overriding fields
    discount = fields.Float(string='Discount', digits=dp.get_precision('Discount'),
        default=0.0)
        

AccountInvoiceLine()
       
#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
