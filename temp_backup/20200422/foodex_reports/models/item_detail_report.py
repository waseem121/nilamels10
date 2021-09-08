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
from datetime import date


class ItemDetailReport(models.TransientModel):
    _name = "item.details.report"

    product_ids = fields.Many2many('product.product', string="Product")
    category_ids = fields.Many2many('product.category', string="Category")
    group_by = fields.Selection(
        [('category', 'Category'), ('brand', 'Brand')],
        string="Group By")
    brand_ids = fields.Many2many('product.brand', string="Brand")
    price_selection = fields.Selection(
        [('show_price', 'Show Price'), ('show_cost', 'Show Cost'), ('both', 'Show Price and Cost')],
        string="Price Selection", default="both", required=False)
    partner_id = fields.Many2one('res.partner', string='Vendor')

    @api.multi
    def action_print_item_details(self):
        self.clear_caches()
        datas = {
            'model': self._name,
            'docids':self.id,
            'product_ids':self.product_ids.ids if self.product_ids else False,
            'category_ids':self.category_ids.ids if self.category_ids else False,
            'brand_ids': self.brand_ids.ids if self.brand_ids else False,
            'price_selection':self.price_selection,
            'partner_id':self.partner_id.id if self.partner_id else False,
            'groupby':self.group_by
        }
        return self.env['report'].get_action(self, 'foodex_reports.item_details_report_template', data=datas)


class ReportItemDetails(models.AbstractModel):
    _name = 'report.foodex_reports.item_details_report_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        domain = []
        if data.get('product_ids'):
            domain.append(('id','in',data.get('product_ids')))
        if data.get('category_ids'):
            domain.append(('categ_id','in',data.get('category_ids')))
        if data.get('brand_ids'):
            domain.append(('product_brand_id','in',data.get('brand_ids')))
        product_ids = self.env['product.product'].sudo().search(domain)
        product_lst = []
        if data.get('partner_id') and product_ids:
            for each in product_ids:
                if each.seller_ids and data.get('partner_id') in [each_supplier.name.id for each_supplier in each.seller_ids]:
                    product_lst.append(each.id)
        else:
            product_lst = [each.id for each in product_ids]
        prod_ids = False
        if product_lst:
            if data.get('groupby') == 'category':
                prod_ids = self.env['product.product'].search([('id','in',product_lst)], order="categ_id")
            if data.get('groupby') == 'brand':
                prod_ids = self.env['product.product'].search([('id', 'in', product_lst)], order="product_brand_id")
            if not data.get('groupby'):
                prod_ids = self.env['product.product'].search([('id', 'in', product_lst)])
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex_reports.item_details_report_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'data':prod_ids,
            'price_selection':data.get('price_selection'),
            'groupby':data.get('groupby')
        }
        return report_obj.render('foodex_reports.item_details_report_template', docargs)