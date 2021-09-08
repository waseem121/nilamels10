from odoo import _
from odoo import api
from odoo import fields
from odoo import models
import odoo.addons.decimal_precision as dp
from odoo.addons.sale_stock.models.sale_order import SaleOrderLine
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning



class AccountInvoiceInherit(models.Model):
    _inherit = "account.invoice"

    @api.one
    def product_price_update(self):
        for lines in self.invoice_line_ids.filtered(lambda l: l.product_id and l.price_unit > 0.00):
            pricelist_item = self.pricelist_id.item_ids.filtered(
                                                                 lambda l: l.compute_price == 'fixed' and l.applied_on == '1_product' and l.uom_id.id == lines.uom_id.id)
            if pricelist_item:
                each_price = self.pricelist_id.item_ids.search([('product_tmpl_id', '=', lines.product_id.product_tmpl_id.id),
                                                               ('compute_price', '=', 'fixed'),
                                                               ('applied_on', '=', '1_product'),
                                                               ('pricelist_id', '=', self.pricelist_id.id),
                                                               ('uom_id', '=', lines.uom_id.id)])
                if not each_price:
                    self.pricelist_id.write({'item_ids': [(0, 0, {'applied_on': '1_product',
                                            'product_tmpl_id': lines.product_id.product_tmpl_id.id,
                                            'uom_id': lines.uom_id.id,
                                            'fixed_price': lines.price_unit})]})

                # order_lines = self.invoice_line_ids.filtered(
                # 	lambda l: l.product_id.id in [x.product_id.id for x in each_price] and l.price_unit > 0.00).sorted(
                # 	lambda l: l.price_unit)
                # print("------------------------------------------------------",order_lines)
                else:
                    # if order_lines:
                    # for each_pricelist in each_price:
                        # print("product_price_update.......................3",order_lines[0].price_unit)
                        each_price.fixed_price = lines.price_unit
						
            else:
                self.pricelist_id.write({'item_ids': [(0, 0, {'applied_on': '1_product',
                                        #'product_id': lines.product_id.product_tmpl_id.id,
					'product_tmpl_id': lines.product_id.product_tmpl_id.id,
                                        'uom_id': lines.uom_id.id,
                                        'fixed_price': lines.price_unit
                                        })]})




class AccountInvoiceLineInherit(models.Model):
    _inherit = 'account.invoice.line'


    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        if not self.invoice_id:
            return

        part = self.invoice_id.partner_id
        fpos = self.invoice_id.fiscal_position_id
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        type = self.invoice_id.type
                
        location_id = self.invoice_id.location_id.id
        if self.invoice_id.refund_without_invoice:
            location_id = self.invoice_id.partner_id.property_stock_customer.id
        product_qty_available = self.product_id.with_context({'location': location_id, 'compute_child': False})
        if product_qty_available:
            self.update({'available_qty': product_qty_available.qty_available,
                        'forecast_qty': product_qty_available.virtual_available_inv})   # forecasted qty to shows based on invoice lines

        if not part:
            warning = {
                'title': _('Warning!'),
                'message': _('You must first select a partner!'),
            }
            return {'warning': warning}

        if not self.product_id:
            if type not in ('in_invoice', 'in_refund'):
                self.price_unit = 0.0
            domain['uom_id'] = []
        else:
            if part.lang:
                product = self.product_id.with_context(lang=part.lang)
            else:
                product = self.product_id

            self.name = product.partner_ref
            account = self.get_invoice_line_account(type, product, fpos, company)
            if account:
                self.account_id = account.id
            self._set_taxes()

            if type in ('in_invoice', 'in_refund'):
                if product.description_purchase:
                    self.name += '\n' + product.description_purchase
            else:
                if product.description_sale:
                    self.name += '\n' + product.description_sale

            if not self.uom_id or product.uom_so_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_so_id.id
            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

            if company and currency:

                if self.uom_id and self.uom_id.id != product.uom_so_id.id:
                    self.price_unit = product.uom_so_id._compute_price(self.price_unit, self.uom_id)
        return {'domain': domain}

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        warning = {}
        result = {}
        date = uom_id = False
        if not self.uom_id:
            self.price_unit = 0.0
        if self.product_id and self.uom_id:
            if self.product_id.uom_so_id.category_id.id != self.uom_id.category_id.id:
                warning = {
                    'title': _('Warning!'),
                    'message': _('The selected unit of measure is not compatible with the unit of measure of the product.'),
                }

                self.uom_id = self.product_id.uom_so_id.id
            if self.uom_id:
                price = dict((product_id, res_tuple[0]) for product_id, res_tuple in self.invoice_id.pricelist_id._compute_price_rule([(self.product_id, self.quantity, self.partner_id)], date=False, uom_id=self.uom_id.id).iteritems())
                self.price_unit = price.get(self.product_id.id, 0.0)
                if warning:
                    result['warning'] = warning
                                        
                # changes for showing available stock based on UoM selected
                location_id = self.invoice_id.location_id.id
                if self.invoice_id.refund_without_invoice:
                    location_id = self.invoice_id.partner_id.property_stock_customer.id
                product_qty_available = self.product_id.with_context({'location': location_id, 'compute_child': False})
                if product_qty_available:
                    qty_available = product_qty_available.qty_available
                    virtual_available_inv = product_qty_available.virtual_available_inv
                    if self.uom_id.uom_type == 'bigger':
                        qty_available = (qty_available) / (self.uom_id.factor_inv)
                    if self.uom_id.uom_type == 'smaller':
                        qty_available = (qty_available) * (self.uom_id.factor_inv)
                        
                    if self.uom_id.uom_type == 'bigger':
                        virtual_available_inv = (virtual_available_inv) / (self.uom_id.factor_inv)
                    if self.uom_id.uom_type == 'smaller':
                        virtual_available_inv = (virtual_available_inv) * (self.uom_id.factor_inv)
                    self.update({'available_qty': qty_available,
                            'forecast_qty': virtual_available_inv})
                                
        return result
