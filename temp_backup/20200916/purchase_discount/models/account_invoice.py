# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        """
        update discount on invoice line.
        """
        data = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(
            line)
        if line.discount_item:
            data.update({
                'discount': line.discount_item
            })
        return data
    
    
    # substract the discount share from the subtotal
    @api.model
    def _anglo_saxon_purchase_move_lines(self, i_line, res):
        """Return the additional move lines for purchase invoices and refunds.

        i_line: An account.invoice.line object.
        res: The move line entries produced so far by the parent move_line_get.
        """
        inv = i_line.invoice_id
        company_currency = inv.company_id.currency_id
        if i_line.product_id and i_line.product_id.valuation == 'real_time' and i_line.product_id.type == 'product':
            # get the fiscal position
            fpos = i_line.invoice_id.fiscal_position_id
            # get the price difference account at the product
            acc = i_line.product_id.property_account_creditor_price_difference
            if not acc:
                # if not found on the product get the price difference account at the category
                acc = i_line.product_id.categ_id.property_account_creditor_price_difference_categ
            acc = fpos.map_account(acc).id
            # reference_account_id is the stock input account
            reference_account_id = i_line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)['stock_input'].id
            diff_res = []
            account_prec = inv.company_id.currency_id.decimal_places
            # calculate and write down the possible price difference between invoice price and product price
            for line in res:
                if line.get('invl_id', 0) == i_line.id and reference_account_id == line['account_id']:
                    valuation_price_unit = i_line.product_id.uom_id._compute_price(i_line.product_id.standard_price, i_line.uom_id)
                    if i_line.product_id.cost_method != 'standard' and i_line.purchase_line_id:
                        #for average/fifo/lifo costing method, fetch real cost price from incomming moves
#                        valuation_price_unit = i_line.purchase_line_id.product_uom._compute_price(i_line.purchase_line_id.price_unit, i_line.uom_id)
                        valuation_price_unit = (i_line.purchase_line_id.price_subtotal - i_line.purchase_line_id.discount_share) / (i_line.purchase_line_id.product_qty + i_line.purchase_line_id.free_qty)
                        if inv.currency_id.id != company_currency.id:
                            valuation_price_unit = valuation_price_unit / inv.exchange_rate
#                        stock_move_obj = self.env['stock.move']
#                        valuation_stock_move = stock_move_obj.search([('purchase_line_id', '=', i_line.purchase_line_id.id), ('state', '=', 'done')])
#                        if valuation_stock_move:
#                            valuation_price_unit_total = 0
#                            valuation_total_qty = 0
#                            for val_stock_move in valuation_stock_move:
#                                valuation_price_unit_total += val_stock_move.price_unit * val_stock_move.product_qty
#                                valuation_total_qty += val_stock_move.product_qty
#                            valuation_price_unit = valuation_price_unit_total / valuation_total_qty
#                            valuation_price_unit = i_line.product_id.uom_id._compute_price(valuation_price_unit, i_line.uom_id)
#                    if inv.currency_id.id != company_currency.id:
#                        print"different currency"
#                        if inv.exchange_rate:
#                            valuation_price_unit = company_currency.with_context(date=inv.date_invoice).compute_custom(valuation_price_unit, inv.currency_id, inv.exchange_rate, round=False)
#                            print"valuation_price_unit in iff: ",valuation_price_unit
#                        else:
#                            valuation_price_unit = company_currency.with_context(date=inv.date_invoice).compute(valuation_price_unit, inv.currency_id, round=False)
#                            print"valuation_price_unit in else: ",valuation_price_unit
                            
                    new_price_unit = (i_line.price_subtotal - i_line.discount_share) / (i_line.quantity + i_line.free_qty)
                    if inv.currency_id.id != company_currency.id:
                        new_price_unit = new_price_unit / inv.exchange_rate
                    
                    if round(valuation_price_unit, 3) != round(new_price_unit,3):
                        # calculate from the purchase order line, as
                        # stockmove priceunit gets changed when there is expenses in shipment
                        purchase_line = i_line.purchase_line_id
                        valuation_price_unit = (purchase_line.price_subtotal - purchase_line.discount_share) / ((purchase_line.product_qty + purchase_line.free_qty) * (purchase_line.product_uom.factor_inv))
                        if purchase_line.product_uom.id != purchase_line.product_id.uom_id.id:
                            valuation_price_unit = (purchase_line.price_subtotal - purchase_line.discount_share) / ((purchase_line.product_qty + purchase_line.free_qty) * (purchase_line.product_uom.factor_inv))
                        if inv.currency_id.id != company_currency.id:
                            if inv.exchange_rate:
                                valuation_price_unit = inv.currency_id.compute_custom(valuation_price_unit, inv.company_id.currency_id, inv.exchange_rate, round=False)
                            else:
                                valuation_price_unit = inv.currency_id.compute(valuation_price_unit, inv.company_id.currency_id, round=False)
                                
                    if round(valuation_price_unit, 3) != round(new_price_unit,3):                                
                        if valuation_price_unit != i_line.price_unit and line['price_unit'] == i_line.price_unit and acc:
                            # price with discount and without tax included
                            price_unit = i_line.price_unit * (1 - (i_line.discount or 0.0) / 100.0)
                            tax_ids = []
                            if line['tax_ids']:
                                #line['tax_ids'] is like [(4, tax_id, None), (4, tax_id2, None)...]
                                taxes = self.env['account.tax'].browse([x[1] for x in line['tax_ids']])
                                price_unit = taxes.compute_all(price_unit, currency=inv.currency_id, quantity=1.0)['total_excluded']
                                for tax in taxes:
                                    tax_ids.append((4, tax.id, None))
                                    for child in tax.children_tax_ids:
                                        if child.type_tax_use != 'none':
                                            tax_ids.append((4, child.id, None))
                            price_before = line.get('price', 0.0)
                            line.update({'price': round(valuation_price_unit * line['quantity'], account_prec)})
                            diff_res.append({
                                'type': 'src',
                                'name': i_line.name[:64],
                                'price_unit': round(price_unit - valuation_price_unit, account_prec),
                                'quantity': line['quantity'],
                                'price': round(price_before - line.get('price', 0.0), account_prec),
                                'account_id': acc,
                                'product_id': line['product_id'],
                                'uom_id': line['uom_id'],
                                'account_analytic_id': line['account_analytic_id'],
                                'tax_ids': tax_ids,
                                })
            return diff_res
        return []
