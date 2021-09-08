from odoo import _
from odoo import api
from odoo import fields
from odoo import models
import odoo.addons.decimal_precision as dp
from odoo.addons.sale_stock.models.sale_order import SaleOrderLine
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        for order in self:
            order.state = 'sale'
            order.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                self.force_quotation_send()

            if order.pricelist_id.update_transaction_value and order.pricelist_id.transaction_on == 'validate':
                for lines in order.order_line.filtered(lambda l:l.price_unit > 0.00):
                    pricelist_item = order.pricelist_id.item_ids.filtered(lambda l:l.compute_price == 'fixed' and l.applied_on == '1_product' and l.uom_id.id == lines.product_uom.id)
                    if pricelist_item:
                        each_price = order.pricelist_id.item_ids.search([('product_tmpl_id', '=', lines.product_id.product_tmpl_id.id),
                                                                        ('compute_price', '=', 'fixed'), ('applied_on', '=', '1_product'),
                                                                        ('pricelist_id', '=', order.pricelist_id.id), ('uom_id', '=', lines.product_uom.id)])
                        if not each_price:
                            order.pricelist_id.write({'item_ids':[(0, 0, {'applied_on':'1_product',
                                                     'product_tmpl_id':lines.product_id.product_tmpl_id.id,
                                                     'uom_id': lines.product_uom.id,
                                                     'fixed_price':lines.price_unit})]})

                        # order_lines = order.order_line.filtered(lambda l:l.product_id.id in [x.product_id.id for x in each_price] and l.price_unit > 0.00).sorted(lambda l:l.price_unit)
                        # if order_lines:
                        # 	for each_pricelist in each_price:
                        else:
                            each_price.fixed_price = lines.price_unit
                    else:
                        order.pricelist_id.write({'item_ids':[(0, 0, {'applied_on':'1_product',
                                                 'product_tmpl_id':lines.product_id.product_tmpl_id.id,
                                                 'uom_id': lines.product_uom.id,
                                                 'fixed_price':lines.price_unit
                                                 })]})

            if order.is_this_direct_sale:
                order.invoice_status = 'invoiced'
                order.action_invoice_create()
                order.action_done()
            else:
                # do not create picking if sales order created from invoice
                no_picking = self._context.get('no_picking', False)
                if not no_picking:
                    order.order_line._action_procurement_create()
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting') and not self.is_this_direct_sale:
            self.action_done()
        return True



class SaleOrderLineInherit(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_so_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_so_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
                                               lang=self.order_id.partner_id.lang,
                                               partner=self.order_id.partner_id.id,
                                               quantity=vals.get('product_uom_qty') or self.product_uom_qty,
                                               date=self.order_id.date_order,
                                               pricelist=self.order_id.pricelist_id.id,
                                               uom=self.product_uom.id
                                               )

        result = {'domain': domain}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
	self.update(vals)

        return result
