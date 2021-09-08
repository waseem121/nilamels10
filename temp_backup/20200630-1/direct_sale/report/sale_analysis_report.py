
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

from odoo import tools
from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class sale_analysis_report(models.Model):
    _name = "sale.analysis.report"
    _description = "Sales Orders Statistics"
    _auto = False
    _order = 'date desc'

    name = fields.Char('Invoice Number', readonly=True)
    date = fields.Date('Date Order', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    product_uom_qty = fields.Float('Product Quantity', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    price_subtotal = fields.Float('Total Price', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', readonly=True)
    categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    nbr = fields.Integer('# of Lines', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)
    account_type = fields.Selection([('out_invoice', 'Sale'), ('out_refund', 'Return')], string="Account Type")
    cost_price = fields.Float('Cost Price', readonly=True, digits=(16, 3))
    profit = fields.Float('Profit', readonly=True, digits=dp.get_precision('Discount'))
    discount = fields.Float('Discount', readonly=True, digits=dp.get_precision('Discount'))

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    SUM(CASE WHEN s.type = 'out_invoice' THEN l.quantity ELSE l.quantity * -1 END) as product_uom_qty,
                    SUM(CASE WHEN s.type = 'out_invoice' THEN l.price_subtotal_signed ELSE (l.price_subtotal_signed*-1) * -1 END) as price_subtotal,

                    SUM(CASE WHEN s.type = 'out_invoice' THEN l.discount_amount ELSE l.discount_amount * -1 END) as discount,

                    SUM(CASE WHEN s.type = 'out_invoice' THEN (l.quantity * l.cost_price) ELSE (l.quantity * l.cost_price) * -1 END) as cost_price,

                    SUM(CASE WHEN s.type = 'out_invoice' THEN (l.price_subtotal_signed - (l.quantity * l.cost_price)) ELSE ((l.price_subtotal_signed * -1) - (l.quantity * l.cost_price)) * -1 END) as profit,

                    count(*) as nbr,
                    s.number as name,
                    s.date_invoice as date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_invoice)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.type as account_type,
                    p.product_tmpl_id
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _from(self):
        from_str = """
                account_invoice_line l
                      join account_invoice s on (l.invoice_id=s.id)
                      join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
                    left join currency_rate cr on (cr.currency_id = s.currency_id AND
                        cr.company_id = s.company_id AND
                        cr.date_start <= COALESCE(s.date_invoice, NOW()) AND
                        cr.date_end IS NULL OR cr.date_end > COALESCE(s.date_invoice, NOW()))
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    l.invoice_id,
                    t.categ_id,
                    s.number,
                    s.date_invoice,
                    s.partner_id,
                    s.user_id,
                    s.state,
                    s.company_id,
                    s.pricelist_id,
                    p.product_tmpl_id,
                    s.type
                    having s.type in ('out_invoice','out_refund') and s.state != 'cancel'
        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))
