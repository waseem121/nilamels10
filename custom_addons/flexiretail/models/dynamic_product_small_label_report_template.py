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

from openerp import models, api, _
from reportlab.graphics import barcode 
from base64 import b64encode
from openerp.exceptions import Warning


class product_label_report_template(models.AbstractModel):
    _name = 'report.flexiretail.prod_small_lbl_rpt'

    def _get_barcode_string(self, value, type, data):
        barcode_str = ''
        if data['form']['with_barcode'] and value and type:
            try:
                barcode_str = barcode.createBarcodeDrawing(
                                       type, value=value, format='png', width=int(data['form']['barcode_height']),
                                       height=int(data['form']['barcode_width']), humanReadable=data['form']['humanReadable'])
            except Exception:
                return ''
            encoded_string = b64encode(barcode_str.asString('png'))
            barcode_str = "<img style='width:" + str(data['form']['display_width']) + "px;height:" + str(data['form']['display_height']) + "px'src='data:image/png;base64,{0}'>".format(encoded_string)
        return barcode_str or ''

    def _get_barcode_data(self, data):
        product_list = []
        model = ''
        if self._context.get('active_model') == 'sale.order':
            model = 'sale.order.line'
        elif self._context.get('active_model') == 'purchase.order':
            model = 'purchase.order.line'
        elif self._context.get('active_model') == 'stock.picking':
            model = 'stock.move'
        elif self._context.get('active_model') == 'account.invoice':
            model = 'account.invoice.line'
        product_ids = self.env['product.small.label.qty'].search([('id', 'in', data['form']['product_ids'])])
        if data.get('form').get('label_preview'):
            if product_ids.line_id:
                line_brw = self.env[model].browse(product_ids[0].line_id)
                product_list.append(line_brw)
            else:
                product_list.append(product_ids[0].product_id)
            return product_list
        else:
            for product_line in product_ids:
                if product_line.line_id:
                    line_brw = self.env[model].browse(product_line.line_id)
                    for qty in range(product_line.qty):
                        product_list.append(line_brw)
                else:
                    for qty in range(product_line.qty):
                        product_list.append(product_line.product_id)
        return product_list

    def _get_price(self, product, pricelist_id=None):
        price = 0
        if product:
            price = product.list_price
            if pricelist_id:
                price = pricelist_id.price_get(product.id, 1.0)
                if price and isinstance(price, dict):
                    price = price.get(pricelist_id.id)
        return price

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('flexiretail.prod_small_lbl_rpt')
        docargs = {
            'doc_ids': self.env["wizard.product.small.label.report"].browse(data["ids"]),
            'doc_model': report.model,
            'docs': self,
            'get_barcode_data': self._get_barcode_data,
            'get_barcode_string': self._get_barcode_string,
            'get_price': self._get_price,
            'data': data
        }
        return report_obj.render('flexiretail.prod_small_lbl_rpt', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
