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
from openerp import models, fields, api


class ImportInvoiceLineSelection(models.TransientModel):
    _name = "import.invoice.line.selection"
    
    invoice_line = fields.Many2one(
        comodel_name='account.invoice.line', string="Invoice line",
        required=True, domain="[('invoice_id', '=', import_invoice_line.invoice)]")
    expense_type = fields.Many2one(
        comodel_name='purchase.expense.type', string='Expense type',
        required=True)
    import_invoice_line = fields.Many2one(
        comodel_name='import.invoice.line.wizard', string='Cost distribution',
        ondelete='cascade')
    
class ImportInvoiceLine(models.TransientModel):
    _name = "import.invoice.line.wizard"
    _description = "Import supplier invoice line"

    supplier = fields.Many2one(
        comodel_name='res.partner', string='Supplier', required=True,
        domain="[('supplier',  '=', True)]")
    invoice = fields.Many2one(
        comodel_name='account.invoice', string="Invoice", required=True,
        domain="[('partner_id', '=', supplier), ('type', '=', 'in_invoice'),"
               "('state', 'in', ['open', 'paid'])]")
#    invoice_line = fields.Many2one(
#        comodel_name='account.invoice.line', string="Invoice line",
#        required=True, domain="[('invoice_id', '=', invoice)]")
#    expense_type = fields.Many2one(
#        comodel_name='purchase.expense.type', string='Expense type',
#        required=True)
    invoice_lines = fields.Many2many(
        comodel_name='account.invoice.line', 
        relation='import_invoice_wizard_line_rel', column1='wizard_id',
        column2='invoice_line_id', string='Invoice Lines',
        domain="[('invoice_id', '=', invoice)]")


    @api.multi
    def action_import_invoice_line(self):
        self.ensure_one()
        invoice_line_ids = [x.id for x in self.invoice_lines]
        for invoice_line in self.env['account.invoice.line'].browse(invoice_line_ids):
            expense_types = self.env['purchase.expense.type'].search([('product_id','=',invoice_line.product_id.id)])
            type = False
            if expense_types:
                type = [x.id for x in expense_types]
                type = type[0]

            self.env['purchase.cost.distribution.expense'].create({
                'distribution': self.env.context['active_id'],
                'invoice_line': invoice_line.id,
                'ref': invoice_line.name,
                'expense_amount': invoice_line.price_subtotal,
                'type': type
            })
