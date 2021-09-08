# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, exceptions, api, _
import openerp.addons.decimal_precision as dp
from datetime import datetime


class PurchaseCostDistribution(models.Model):
    _name = "purchase.cost.distribution"
    _description = "Purchase landed costs distribution"
    _order = 'name desc'

    @api.one
    @api.depends('total_expense', 'total_purchase')
    def _compute_amount_total(self):
        self.amount_total = round(self.total_purchase + self.total_expense, 2)
#         self.amount_total = round(self.total_purchase, 2)

    @api.one
    @api.depends('cost_lines.product_qty', 'cost_lines.standard_price_new')
    def _compute_calculated_amount_total(self):
        calculated_amount_total = 0.0
        for x in self.cost_lines:
            calculated_amount_total += (x.product_qty * x.standard_price_new)
        self.calculated_amount_total = round(calculated_amount_total, 2)

    @api.one
    @api.depends('calculated_amount_total', 'amount_total')
    def _compute_difference_amount_total(self):
        self.difference_amount = self.amount_total - self.calculated_amount_total

    @api.one
    @api.depends('cost_lines', 'cost_lines.total_amount')
    def _compute_total_purchase(self):
        # ## Due to rounding problem, we cannot rely on x.total_amount. Correct value is PO amount total

#         self.total_purchase = sum([(x.standard_price_new * x.product_qty) for x in self.cost_lines])
        self.total_purchase = sum([(x.total_amount) for x in self.cost_lines])

        total = 0.0
        for each_lines in self.expense_lines:
            if each_lines.currency_id != self.currency_id:
                if self.exchange_rate:
                    total += each_lines.currency_id.compute_custom(each_lines.expense_amount, self.currency_id, self.exchange_rate, round=False)
                else:
                    total += each_lines.currency_id.compute(each_lines.expense_amount, self.currency_id, round=False)
            else:
                total += each_lines.expense_amount
        self.total_expense = total

    @api.one
    @api.depends('cost_lines', 'cost_lines.product_price_unit')
    def _compute_total_price_unit(self):
        self.total_price_unit = sum([x.product_price_unit for x in
                                     self.cost_lines])

    @api.one
    @api.depends('cost_lines', 'cost_lines.product_qty')
    def _compute_total_uom_qty(self):
        self.total_uom_qty = sum([x.product_qty for x in self.cost_lines])

    @api.one
    @api.depends('cost_lines')
    def _compute_total_line_qty(self):
        self.total_line_qty = sum([x.purchase_line_id.product_qty for x in self.cost_lines])

    @api.one
    @api.depends('cost_lines', 'cost_lines.total_weight')
    def _compute_total_weight(self):
        self.total_weight = sum([x.total_weight for x in self.cost_lines])

    @api.one
    @api.depends('cost_lines', 'cost_lines.total_weight_net')
    def _compute_total_weight_net(self):
        self.total_weight_net = sum([x.total_weight_net for x in
                                     self.cost_lines])

    @api.one
    @api.depends('cost_lines', 'cost_lines.total_volume')
    def _compute_total_volume(self):
        self.total_volume = sum([x.total_volume for x in self.cost_lines])

    @api.one
    @api.depends('expense_lines', 'expense_lines.expense_amount')
    def _compute_total_expense(self):
        self.total_expense = sum([x.expense_amount for x in
                                  self.expense_lines])

    def _expense_lines_default(self):
        expenses = self.env['purchase.expense.type'].search(
            [('default_expense', '=', True)])
        return [{'type': x, 'expense_amount':x.default_amount , 'currency_id':x.currency_id.id, 'account_id':x.account_id.id}
                for x in expenses]

    name = fields.Char(string='Distribution number', required=True,
                       index=True, default='/')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=(lambda self: self.env['res.company']._company_default_get(
            'purchase.cost.distribution')))
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency',
        related="company_id.currency_id")
    state = fields.Selection(
        [('draft', 'Draft'),
         ('calculated', 'Calculated'),
         ('done', 'Done'),
         ('error', 'Error'),
         ('cancel', 'Cancel')], string='Status', readonly=True,
        default='draft')
    cost_update_type = fields.Selection(
        [('direct', 'Direct Update')], string='Cost Update Type',
        default='direct', required=True)
    date = fields.Date(
        string='Date', required=True, readonly=True, index=True,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today)
    total_uom_qty = fields.Float(
        compute=_compute_total_uom_qty, readonly=True,
        digits=dp.get_precision('Product UoS'),
        string='Total quantity')
    total_line_qty = fields.Float(
        compute=_compute_total_line_qty, readonly=True,
        digits=dp.get_precision('Product UoS'),
        string='Total line quantity')
    total_weight = fields.Float(
        compute=_compute_total_weight, string='Total gross weight',
        readonly=True,
        digits=dp.get_precision('Stock Weight'))
    total_weight_net = fields.Float(
        compute=_compute_total_weight_net,
        digits=dp.get_precision('Stock Weight'),
        string='Total net weight', readonly=True)
    total_volume = fields.Float(
        compute=_compute_total_volume, string='Total volume', readonly=True)
    total_purchase = fields.Float(
        compute=_compute_total_purchase,
        digits=(12, 4), string='Total purchase')
    total_price_unit = fields.Float(
        compute=_compute_total_price_unit, string='Total price unit',
        digits=dp.get_precision('Product Price'))
    amount_total = fields.Float(
        compute=_compute_amount_total,
        digits=(12, 3), string='Total')
        
    calculated_amount_total = fields.Float(
        compute=_compute_calculated_amount_total,
        digits=(12, 3), string='Calculated Total')
        
    difference_amount = fields.Float(
        compute=_compute_difference_amount_total,
        digits=(12, 3), string='Difference')
        
    total_expense = fields.Float(
        compute=_compute_total_expense,
        digits=(12, 4), string='Total expenses')
    note = fields.Text(string='Documentation for this order')
    cost_lines = fields.One2many(
        comodel_name='purchase.cost.distribution.line', ondelete="cascade",
        inverse_name='distribution', string='Distribution lines')
    expense_lines = fields.One2many(
        comodel_name='purchase.cost.distribution.expense', ondelete="cascade",
        inverse_name='distribution', string='Expenses',
        default=_expense_lines_default)
    exchange_rate = fields.Float(string='Exchange Rate', 
        digits=dp.get_precision('Discount'), default=0.0)

    @api.multi
    def unlink(self):
        for c in self:
            if c.state not in ('draft', 'calculated'):
                raise exceptions.Warning(
                    _("You can't delete a confirmed cost distribution"))
        return super(PurchaseCostDistribution, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'purchase.cost.distribution')
        return super(PurchaseCostDistribution, self).create(vals)

    @api.multi
    def action_calculate(self):
        for distribution in self:
            # Check expense lines for amount 0
            if any([not x.expense_amount for x in distribution.expense_lines]):
                raise exceptions.Warning(
                    _('Please enter an amount for all the expenses'))
            # Check if exist lines in distribution
            if not distribution.cost_lines:
                raise exceptions.Warning(
                    _('There is no picking lines in the distribution'))
            # Calculating expense line
            for line in distribution.cost_lines:
                line.expense_lines.unlink()
                for expense in distribution.expense_lines:
                    if (expense.affected_lines and
                            line.id not in expense.affected_lines.ids):
                        continue
                    if expense.type.calculation_method == 'amount':
                        multiplier = line.total_amount
                        if expense.affected_lines:
                            divisor = sum([x.total_amount for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_purchase
                    elif expense.type.calculation_method == 'price':
                        multiplier = line.product_price_unit
                        if expense.affected_lines:
                            divisor = sum([x.product_price_unit for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_price_unit
                    elif expense.type.calculation_method == 'qty':
                        multiplier = line.product_qty
                        if expense.affected_lines:
                            divisor = sum([x.product_qty for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_uom_qty
                    elif expense.type.calculation_method == 'line_qty':
                        multiplier = line.purchase_line_id.product_qty
                        if expense.affected_lines:
                            divisor = sum([x.purchase_line_id.product_qty for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_line_qty
                    elif expense.type.calculation_method == 'weight':
                        multiplier = line.total_weight
                        if expense.affected_lines:
                            divisor = sum([x.total_weight for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_weight
                    elif expense.type.calculation_method == 'weight_net':
                        multiplier = line.total_weight_net
                        if expense.affected_lines:
                            divisor = sum([x.total_weight_net for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_weight_net
                    elif expense.type.calculation_method == 'volume':
                        multiplier = line.total_volume
                        if expense.affected_lines:
                            divisor = sum([x.total_volume for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_volume
                    elif expense.type.calculation_method == 'equal':
                        multiplier = 1
                        divisor = (len(expense.affected_lines) or
                                   len(distribution.cost_lines))
                    else:
                        raise exceptions.Warning(
                            _('No valid distribution type.'))
                    expense_amount = (expense.expense_amount * multiplier / 
                                      divisor)

                    expense_line = {
                        'distribution_expense': expense.id,
                        'expense_amount': expense_amount,
                        'cost_ratio': expense_amount / line.product_qty,
                        'distribution_line': line.id,
                        'currency_id':expense.currency_id.id,
                    }
                    self.env['purchase.cost.distribution.line.expense'].create(expense_line)
#                    line.expense_lines = [(0, 0, expense_line)]
            distribution.state = 'calculated'
        return True

    @api.one
    def _product_price_update(self, move, new_price):
        """Method that mimicks stock.move's product_price_update_before_done
        method behaviour, but taking into account that calculations are made
        on an already done move, and prices sources are given as parameters.
        """
        if (move.location_id.usage == 'supplier' and
                move.product_id.cost_method == 'average'):
            product = move.product_id
            qty_available = product.product_tmpl_id.qty_available
            product_avail = move.state == 'done' and (qty_available - move.product_qty) or qty_available
            new_std_price = 0.00
            if move.state == 'done':
                # Get the standard price
                if product_avail <= 0:
                    new_std_price = new_price
                else:
                    domain_quant = [
                        ('product_id', 'in',
                         product.product_tmpl_id.product_variant_ids.ids),
                        ('id', 'not in', move.quant_ids.ids)]
                    quants = self.env['stock.quant'].read_group(
                    domain_quant, ['product_id', 'qty', 'cost'], [])[0]
                    if quants.get('cost') and quants.get('qty'):
                        new_std_price = ((quants.get('cost') * quants.get('qty') + 
                                      new_price * move.product_qty) / 
                                     qty_available)
#                     new_std_price = new_price
                # Write the standard price, as SUPERUSER_ID, because a
                # warehouse manager may not have the right to write on products
                product.sudo().write({'standard_price': new_std_price})
            else:
#                new_std_price = ((move.product_qty * new_price) + (product.product_tmpl_id.standard_price * qty_available)) / (move.product_qty + qty_available)
#                obj_precision = self.env['stock.quant']
#                precision = obj_precision.precision_get('Product Price')
#                new_std_price = round(new_std_price, precision)
                move.write({'price_unit': new_price})

    @api.one
    def action_done(self):
        for line in self.cost_lines:
            if self.cost_update_type == 'direct':
                line.move_id.quant_ids._price_update(line.standard_price_new)
                self._product_price_update(
                    line.move_id, line.standard_price_new)
                line.move_id.product_price_update_after_done()
        self.state = 'done'

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.one
    def action_cancel(self):
        for line in self.cost_lines:
            if line.picking_id.state == 'assigned':
                self.state = 'draft'
                return True
            if self.cost_update_type == 'direct':
                x = self.currency_id.compare_amounts(
                        line.move_id.quant_ids[0].cost,
                        line.standard_price_new)
#                 if line.cost_difference == 0 and line.standard_price_new != 0:
#                     if self.currency_id.compare_amounts(
#                             line.move_id.quant_ids[0].cost,
#                             line.standard_price_new) != 0:
#                         raise exceptions.Warning(
#                             _('Cost update cannot be undone because there has '
#                               'been a later update. Restore correct price and try '
#                               'again.'))
                line.move_id.quant_ids._price_update(line.standard_price_old)
                self._product_price_update(
                    line.move_id, line.standard_price_old)
                line.move_id.product_price_update_after_done()
        self.state = 'draft'


class PurchaseCostDistributionLine(models.Model):
    _name = "purchase.cost.distribution.line"
    _description = "Purchase cost distribution Line"
    _rec_name = 'picking_id'

    @api.one
    @api.depends('product_price_unit', 'product_qty')
    def _compute_total_amount(self):
        # ## check currency difference not required as standard_price_old already in right currency
        self.total_amount = self.standard_price_old * self.product_qty

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_weight(self):
        self.total_weight = self.product_weight * self.product_qty

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_weight_net(self):
        self.total_weight_net = self.product_weight_net * self.product_qty

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_volume(self):
        self.total_volume = self.product_volume * self.product_qty

    @api.one
    @api.depends('expense_lines', 'expense_lines.cost_ratio')
    def _compute_cost_ratio(self):
        total = 0.0
        for each_lines in self.expense_lines:
            if each_lines.currency_id != self.distribution.currency_id:
                total += each_lines.currency_id.compute(each_lines.expense_amount, self.distribution.currency_id, round=False)
            else:
                total += each_lines.expense_amount
        self.cost_ratio = total / self.product_qty

    @api.one
    @api.depends('expense_lines', 'expense_lines.expense_amount')
    def _compute_expense_amount(self):
        total = 0.0
        for each_lines in self.expense_lines:
            if each_lines.currency_id != self.distribution.currency_id:
                if self.distribution.exchange_rate:
                    total += each_lines.currency_id.compute_custom(each_lines.expense_amount, self.distribution.currency_id, self.distribution.exchange_rate, round=False)
                else:
                    total += each_lines.currency_id.compute(each_lines.expense_amount, self.distribution.currency_id, round=False)
            else:
                total += each_lines.expense_amount
        self.expense_amount = total

    @api.one
    @api.depends('standard_price_old', 'cost_ratio')
    def _compute_standard_price_new(self):
#         self.standard_price_new = self.standard_price_old + self.cost_ratio + self.cost_difference
        self.standard_price_new = self.standard_price_old + self.cost_ratio 

    @api.one
    @api.depends('move_id', 'move_id.picking_id', 'move_id.product_id',
                 'move_id.product_qty')
    def _compute_display_name(self):
        self.name = '%s / %s / %s' % (
            self.move_id.picking_id.name, self.move_id.product_id.display_name,
            self.move_id.product_qty)

    @api.one
    @api.depends('move_id', 'move_id.product_id')
    def _get_product_id(self):
        # Cannot be done via related field due to strange bug in update chain
        self.product_id = self.move_id.product_id.id

    @api.one
    @api.depends('move_id', 'move_id.product_qty')
    def _get_product_qty(self):
        # Cannot be done via related field due to strange bug in update chain
        self.product_qty = self.move_id.product_qty

    @api.one
    @api.depends('move_id')
    def _get_standard_price_old(self):
#        self.standard_price_old = (
#            self.move_id and self.move_id.get_price_unit(self.move_id) or 0.0)
        uom_obj = self.env['product.uom']
        qty_default_uom = 0.0
        if self.purchase_line_id.product_qty > 0.0:
            qty_default_uom = self.purchase_line_id.product_uom._compute_quantity(self.purchase_line_id.product_qty, self.purchase_line_id.product_id.uom_id)
        if qty_default_uom > 0:
            self.standard_price_old = self.purchase_line_id.price_subtotal / qty_default_uom
#            self.standard_price_old =  self.move_id.price_unit
        else:
            self.standard_price_old = self.purchase_line_id.price_subtotal
        # ## check currency difference
        if self.purchase_id.currency_id != self.distribution.currency_id:
#            self.standard_price_old = self.purchase_id.currency_id.compute(self.standard_price_old, self.distribution.currency_id, round=False)
            exchange_rate = self.purchase_line_id and self.purchase_line_id.order_id.exchange_rate or 0.0
            if exchange_rate:
                self.standard_price_old = self.purchase_id.currency_id.compute_custom(self.standard_price_old, self.distribution.currency_id, exchange_rate, round=False)
            else:
                self.standard_price_old = self.purchase_id.currency_id.compute(self.standard_price_old, self.distribution.currency_id, round=False)

    name = fields.Char(
        string='Name', compute='_compute_display_name')
    distribution = fields.Many2one(
        comodel_name='purchase.cost.distribution', string='Cost distribution',
        ondelete='cascade')
    move_id = fields.Many2one(
        comodel_name='stock.move', string='Picking line', ondelete="restrict")
    purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line', string='Purchase order line',
        related='move_id.purchase_line_id')
    purchase_id = fields.Many2one(
        comodel_name='purchase.order', string='Purchase order', readonly=True,
        related='move_id.purchase_line_id.order_id', store=True)
    partner = fields.Many2one(
        comodel_name='res.partner', string='Supplier', readonly=True,
        related='move_id.purchase_line_id.order_id.partner_id')
    picking_id = fields.Many2one(
        'stock.picking', string='Picking', related='move_id.picking_id',
        store=True)
    product_id = fields.Many2one(
        comodel_name='product.product', string='Product', store=True,
        compute='_get_product_id')
    product_qty = fields.Float(
        string='Quantity', compute='_get_product_qty', store=True)
    product_uom = fields.Many2one(
        comodel_name='product.uom', string='Unit of measure',
        related='move_id.product_uom')
    product_uos_qty = fields.Float(
        string='Quantity (UoS)', related='move_id.product_uom_qty')
    product_uos = fields.Many2one(
        comodel_name='product.uom', string='Product UoS',
        related='move_id.product_uom')
    product_price_unit = fields.Float(
        string='Unit price', related='move_id.price_unit', digits=(12, 4))
    expense_lines = fields.One2many(
        comodel_name='purchase.cost.distribution.line.expense',
        inverse_name='distribution_line', string='Expenses distribution lines',
        ondelete='cascade')
    product_volume = fields.Float(
        string='Volume', help="The volume in m3.",
        related='product_id.product_tmpl_id.volume')
    product_weight = fields.Float(
        string='Gross weight', related='product_id.product_tmpl_id.weight',
        help="The gross weight in Kg.")
    product_weight_net = fields.Float(
        string='Net weight', related='product_id.product_tmpl_id.weight',
        help="The net weight in Kg.")
    standard_price_old = fields.Float(
        string='Unit Cost', compute="_get_standard_price_old", store=True,
        digits=(12, 4))
    cost_difference = fields.Float(
        string='Difference Cost',
        digits=(12, 4))
    expense_amount = fields.Float(
        string='Expense Amount', digits=(12, 4),
        compute='_compute_expense_amount')
    cost_ratio = fields.Float(
        string='Unit Expense Amount', digits=(12, 4),
        compute='_compute_cost_ratio')
    standard_price_new = fields.Float(
        string='Landed Cost', digits=(12, 4),
        compute='_compute_standard_price_new')
    total_amount = fields.Float(
        compute=_compute_total_amount, string='Amount line',
        digits=(12, 4))
    total_weight = fields.Float(
        compute=_compute_total_weight, string="Line weight", store=True,
        digits=dp.get_precision('Stock Weight'),
        help="The line gross weight in Kg.")
    total_weight_net = fields.Float(
        compute=_compute_total_weight_net, string='Line net weight',
        digits=dp.get_precision('Stock Weight'), store=True,
        help="The line net weight in Kg.")
    total_volume = fields.Float(
        compute=_compute_total_volume, string='Line volume', store=True,
        help="The line volume in m3.")
    purchase_unit_price = fields.Float(related='purchase_line_id.price_unit', string="Unit Price(F)")


class PurchaseCostDistributionLineExpense(models.Model):
    _name = "purchase.cost.distribution.line.expense"
    _description = "Purchase cost distribution line expense"

    distribution_line = fields.Many2one(
        comodel_name='purchase.cost.distribution.line',
        string='Cost distribution line', ondelete="cascade")
    distribution_expense = fields.Many2one(
        comodel_name='purchase.cost.distribution.expense',
        string='Distribution expense', ondelete="cascade")
    type = fields.Many2one(
        'purchase.expense.type', string='Expense type',
        related='distribution_expense.type')
    expense_amount = fields.Float(
        string='Expense amount', default=0.0,
        digits=(12, 4))
    cost_ratio = fields.Float(
        'Unit cost', default=0.0,
        digits=(12, 4))
    currency_id = fields.Many2one('res.currency', string="Currency")


class PurchaseCostDistributionExpense(models.Model):
    _name = "purchase.cost.distribution.expense"
    _description = "Purchase cost distribution expense"
    _rec_name = "type"

    @api.one
    @api.depends('distribution', 'distribution.cost_lines')
    def _get_imported_lines(self):
        self.imported_lines = self.env['purchase.cost.distribution.line']
        self.imported_lines |= self.distribution.cost_lines

    def _compute_expense_amount_currency(self):
        for line in self:
            if line.distribution.exchange_rate:
                line.expense_amount_currency = line.currency_id.compute_custom(line.expense_amount, line.distribution.company_id.currency_id,line.distribution.exchange_rate)
            else:
                line.expense_amount_currency = line.currency_id.compute(line.expense_amount, line.distribution.company_id.currency_id)

    distribution = fields.Many2one(
        comodel_name='purchase.cost.distribution', string='Cost distribution',
        index=True, ondelete="cascade", required=True)
    ref = fields.Char(string="Reference")
    type = fields.Many2one(
        comodel_name='purchase.expense.type', string='Expense type',
        index=True, ondelete="restrict")
    calculation_method = fields.Selection(
        string='Calculation method', related='type.calculation_method',
        readonly=True)
    imported_lines = fields.Many2many(
        comodel_name='purchase.cost.distribution.line',
        string='Imported lines', compute='_get_imported_lines')
    affected_lines = fields.Many2many(
        comodel_name='purchase.cost.distribution.line', column1="expense_id",
        relation="distribution_expense_aff_rel", column2="line_id",
        string='Affected lines',
        help="Put here specific lines that this expense is going to be "
             "distributed across. Leave it blank to use all imported lines.",
        domain="[('id', 'in', imported_lines[0][2])]")
    expense_amount = fields.Float(
        string='Expense amount', digits=(12, 3),
        required=True)
    invoice_line = fields.Many2one(
        comodel_name='account.invoice.line', string="Supplier invoice line",
        domain="[('invoice_id.type', '=', 'in_invoice'),"
               "('invoice_id.state', 'in', ('open', 'paid'))]")
    account_id = fields.Many2one('account.account', string="Account")
    currency_id = fields.Many2one('res.currency', string="Currency")
    expense_amount_currency = fields.Float(
        string='Expense amount (Base Currency)', digits=(12, 3),
        compute='_compute_expense_amount_currency')

    @api.onchange('type')
    def onchange_type(self):
        if self.type and self.type.default_amount:
            self.expense_amount = self.type.default_amount


class report_purchase_landed_cost_landed_cost_report_template(models.AbstractModel):
    _name = 'report.purchase_landed_cost.landed_cost_report_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('purchase_landed_cost.landed_cost_report_template')
        record_id = self.env['purchase.cost.distribution'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': record_id,
            '_get_purchase_data':self._get_purchase_data,
            '_get_lot_values':self._get_lot_values,
        }
        return report_obj.render('purchase_landed_cost.landed_cost_report_template', docargs)

    def _get_lot_values(self, cost_line_id):
        lot_id = cost_line_id.move_id.quant_ids.mapped('lot_id')
        return lot_id if lot_id else False

    def _get_purchase_data(self, cost_distribution_id):
        get_data = {}
        cost_line_id = cost_distribution_id.cost_lines[0] if cost_distribution_id.cost_lines else False
        if cost_line_id:
            receipt_date = datetime.strptime(cost_line_id.picking_id.min_date, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') if cost_line_id.picking_id.min_date else False
            get_data.update({'receipt_no':cost_line_id.picking_id.name,
                             'receipt_date':receipt_date,
                             'purchase_order':cost_line_id.purchase_id.name,
                             'warehouse':cost_line_id.picking_id.location_dest_id.name,
                             'supplier':cost_line_id.purchase_id.partner_id.name,
                             'credit_account':cost_line_id.purchase_id.partner_id.property_account_payable_id.name,
                             'received_by':self.env.user.name,
                             'currency':cost_line_id.purchase_id.currency_id.name,
                             'exch_rate':cost_line_id.purchase_id.currency_id.rate,
                             })
        return get_data
