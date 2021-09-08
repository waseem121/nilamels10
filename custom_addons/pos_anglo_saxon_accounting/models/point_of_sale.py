# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"
    
    @api.model
    def _anglo_saxon_pos_move_lines(self, po_line):
        """Return the additional move lines for pos orders.

        po_line: A pos.order.line object.
        """
        ResPartner = self.env['res.partner']
        order = po_line.order_id
        location_id = order.location_id.id
        cur = order.pricelist_id.currency_id
        prec = cur.decimal_places
        if po_line.product_id.type == 'product':
            partner_id = ResPartner._find_accounting_partner(order.partner_id).id or False
            
            product_template = po_line.product_id.product_tmpl_id
            product_accounts = product_template.get_product_accounts() ### fiscal_position is optional parameter
            print "product_accounts=============: ",product_accounts
            dacc = product_accounts['stock_output']
            cacc = product_accounts['expense']
            
            if dacc and cacc:
                price_unit = po_line.cost or po_line.product_id.standard_price
                amount = round(price_unit * po_line.qty,prec)
                return [
                    {
#                        'insert_data': 'product',
                        'name': po_line.name[:64],
                        'quantity': po_line.qty,
                        'product_id': po_line.product_id.id,
                        'account_id': dacc.id,
#                        'analytic_account_id': self._prepare_analytic_account(po_line),
                        'credit': 0.0,
                        'debit': amount,
                        'tax_ids': [(6, 0, po_line.tax_ids_after_fiscal_position.ids)],
                        'partner_id': partner_id,
                        'location_id': location_id
                       },
                    
                    {
#                        'insert_data': 'counter_part',
                        'name': po_line.name[:64],
                        'quantity': po_line.qty,
                        'product_id': po_line.product_id.id,
                        'account_id': cacc.id,
                        'credit': amount,
                        'debit': 0.0,
                        'tax_ids': [(6, 0, po_line.tax_ids_after_fiscal_position.ids)],
                        'partner_id': partner_id,
                        'location_id': location_id
                    },
                ]
        return []
    
#    def _create_account_move_line(self, session=None, move=None): Moved to pos_siafa
#        # Tricky, via the workflow, we only have one id in the ids variable
#        ### Customize: adde pos_anglo_saxon_accounting lines
#        """Create a account move line of order grouped by products or not."""
#        IrProperty = self.env['ir.property']
#        ResPartner = self.env['res.partner']
#
#        if session and not all(session.id == order.session_id.id for order in self):
#            raise UserError(_('Selected orders do not have the same session!'))
#
#        grouped_data = {}
#        have_to_group_by = session and session.config_id.group_by or False
#        rounding_method = session and session.config_id.company_id.tax_calculation_rounding_method
##        print'_create_account_move_line',self.filtered(lambda o: not o.account_move or order.state == 'paid')
#        for order in self.filtered(lambda o: not o.account_move or order.state == 'paid'):
#            current_company = order.sale_journal.company_id
#            account_def = IrProperty.get(
#                'property_account_receivable_id', 'res.partner')
#            order_account = order.partner_id.property_account_receivable_id.id or account_def and account_def.id
#            partner_id = ResPartner._find_accounting_partner(order.partner_id).id or False
#            if move is None:
#                # Create an entry for the sale
#                journal_id = self.env['ir.config_parameter'].sudo().get_param(
#                    'pos.closing.journal_id_%s' % current_company.id, default=order.sale_journal.id)
#                move = self._create_account_move(
#                    order.session_id.start_at, order.name, int(journal_id), order.company_id.id)
#
#            def insert_data(data_type, values):
#                # if have_to_group_by:
#                values.update({
#                    'partner_id': partner_id,
#                    'move_id': move.id,
#                })
#
#                if data_type == 'product':
#                    key = ('product', values['partner_id'], (values['product_id'], tuple(values['tax_ids'][0][2]), values['name']), values['analytic_account_id'], values['debit'] > 0)
#                elif data_type == 'tax':
#                    key = ('tax', values['partner_id'], values['tax_line_id'], values['debit'] > 0)
#                elif data_type == 'counter_part':
#                    key = ('counter_part', values['partner_id'], values['account_id'], values['debit'] > 0)
#                else:
#                    return
#
#                grouped_data.setdefault(key, [])
#
#                if have_to_group_by:
#                    if not grouped_data[key]:
#                        grouped_data[key].append(values)
#                    else:
#                        current_value = grouped_data[key][0]
#                        current_value['quantity'] = current_value.get('quantity', 0.0) + values.get('quantity', 0.0)
#                        current_value['credit'] = current_value.get('credit', 0.0) + values.get('credit', 0.0)
#                        current_value['debit'] = current_value.get('debit', 0.0) + values.get('debit', 0.0)
#                else:
#                    grouped_data[key].append(values)
#
#            # because of the weird way the pos order is written, we need to make sure there is at least one line,
#            # because just after the 'for' loop there are references to 'line' and 'income_account' variables (that
#            # are set inside the for loop)
#            # TOFIX: a deep refactoring of this method (and class!) is needed
#            # in order to get rid of this stupid hack
#            assert order.lines, _('The POS order must have lines when calling this method')
#            # Create an move for each order line
#            cur = order.pricelist_id.currency_id
#            for line in order.lines:
#                amount = line.price_subtotal
#
#                # Search for the income account
#                if line.product_id.property_account_income_id.id:
#                    income_account = line.product_id.property_account_income_id.id
#                elif line.product_id.categ_id.property_account_income_categ_id.id:
#                    income_account = line.product_id.categ_id.property_account_income_categ_id.id
#                else:
#                    raise UserError(_('Please define income '
#                                      'account for this product: "%s" (id:%d).')
#                                    % (line.product_id.name, line.product_id.id))
#
#                name = line.product_id.name
#                if line.notice:
#                    # add discount reason in move
#                    name = name + ' (' + line.notice + ')'
#
#                # Create a move for the line for the order line
#                insert_data('product', {
#                    'name': name,
#                    'quantity': line.qty,
#                    'product_id': line.product_id.id,
#                    'account_id': income_account,
#                    'analytic_account_id': self._prepare_analytic_account(line),
#                    'credit': ((amount > 0) and amount) or 0.0,
#                    'debit': ((amount < 0) and -amount) or 0.0,
#                    'tax_ids': [(6, 0, line.tax_ids_after_fiscal_position.ids)],
#                    'partner_id': partner_id
#                })
#                # Customize jayesh: create anglo saxon accounting
#                anglo_saxon_accounting = self._anglo_saxon_pos_move_lines(line)
#                print'anglo_saxon_accounting---',anglo_saxon_accounting
#                if len(anglo_saxon_accounting):
#                    insert_data('counter_part',anglo_saxon_accounting[0])
#                    insert_data('counter_part',anglo_saxon_accounting[1])
#                ####
#                # Create the tax lines
#                taxes = line.tax_ids_after_fiscal_position.filtered(lambda t: t.company_id.id == current_company.id)
#                print'taxes====',taxes
#                if not taxes:
#                    continue
#                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#                for tax in taxes.compute_all(price, cur, line.qty)['taxes']:
#                    insert_data('tax', {
#                        'name': _('Tax') + ' ' + tax['name'],
#                        'product_id': line.product_id.id,
#                        'quantity': line.qty,
#                        'account_id': tax['account_id'] or income_account,
#                        'credit': ((tax['amount'] > 0) and tax['amount']) or 0.0,
#                        'debit': ((tax['amount'] < 0) and -tax['amount']) or 0.0,
#                        'tax_line_id': tax['id'],
#                        'partner_id': partner_id
#                    })
#                    
#            # round tax lines per order
#            if rounding_method == 'round_globally':
#                for group_key, group_value in grouped_data.iteritems():
#                    if group_key[0] == 'tax':
#                        for line in group_value:
#                            line['credit'] = cur.round(line['credit'])
#                            line['debit'] = cur.round(line['debit'])
#
#            # counterpart
#            insert_data('counter_part', {
#                'name': _("Trade Receivables"),  # order.name,
#                'account_id': order_account,
#                'credit': ((order.amount_total < 0) and -order.amount_total) or 0.0,
#                'debit': ((order.amount_total > 0) and order.amount_total) or 0.0,
#                'partner_id': partner_id
#            })
#
#            order.write({'state': 'done', 'account_move': move.id})
#
#        all_lines = []
#        for group_key, group_data in grouped_data.iteritems():
#            for value in group_data:
#                all_lines.append((0, 0, value),)
#        if move:  # In case no order was changed
#            move.sudo().write({'line_ids': all_lines})
#            move.sudo().post()
#
#        return True

class PosOrderLine(models.Model):
    _inherit = "pos.order.line" 
    
    cost = fields.Float('Cost Price', copy=False)
    
    @api.model
    def create(self, values):
        if values.get('product_id',False):
            product = self.env['product.product'].browse(values['product_id'])
            values['cost'] = product.standard_price
        return super(PosOrderLine, self).create(values)
    