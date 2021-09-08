from odoo import api, fields, models

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super(AccountInvoice,
                           self).finalize_invoice_move_lines(move_lines)
        print "inside analytic_default_siafa finalize_invoice_move_lines: ",move_lines
        new_move_lines = []
#        sale_order = self.env['sale.order'].search([('name','=',self.origin)])
        location_id = (self.location_id and self.location_id.id) or (self.invoice_line_ids and self.invoice_line_ids[0].sale_line_ids and \
                        self.invoice_line_ids[0].sale_line_ids[0].order_id.warehouse_id.lot_stock_id.id)
        if location_id:
#            location_id = sale_order.warehouse_id.lot_stock_id.id
            for line_tuple in move_lines:
                line_tuple[2]['location_id'] = location_id
                new_move_lines.append(line_tuple)
            print "finalize_invoice_move_lines new_move_lines: ",new_move_lines
            return new_move_lines
        return move_lines