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


class InventoryWizard(models.TransientModel):
    _name = 'wizard.inventory.adjustment.print'

    type = fields.Selection([('with_only_qty', 'With Quantity Only'), ('with_qty_cost', 'With Cost'), ('with_qty_price', 'With Price')], default='with_only_qty', required=True)

    @api.multi
    def print_report1(self):
        active_ids = self.env.context.get('active_ids', [])
        if self.type == 'with_qty_cost':
            datas = {
                'ids': active_ids,
                'model': 'stock.inventory',
                'form': self.env['stock.inventory'].browse(self._context.get('active_id')).read()[0],
                'with_qty_cost': True,
            }
            return self.env['report'].get_action(self.env['stock.inventory'].browse(self._context.get('active_id')),
                                                 'custom_stock_report.report_with_qty_cost', data=datas)
        elif self.type == 'with_qty_price':
            datas = {
                'ids': active_ids,
                'model': 'stock.inventory',
                'form': self.env['stock.inventory'].browse(self._context.get('active_id')).read()[0],
                'with_qty_price': True,
            }
            return self.env['report'].get_action(self.env['stock.inventory'].browse(self._context.get('active_id')),
                                                 'custom_stock_report.report_with_qty_price', data=datas)
        else:
            datas = {
                'ids': active_ids,
                'model': 'stock.inventory',
                'form': self.env['stock.inventory'].browse(self._context.get('active_id')).read()[0],
            }
            return self.env['report'].get_action(self.env['stock.inventory'].browse(self._context.get('active_id')),
                                                 'custom_stock_report.report_with_only_qty', data=datas)



class ReportPrintWithPrice(models.AbstractModel):
    _name = 'report.custom_stock_report.report_with_qty_price'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('custom_stock_report.report_with_qty_price')
        docargs = {
            'doc_ids': data['ids'],
            'doc_model': report.model,
            'docs': self.env['stock.inventory'].browse(data['ids']),
        }
        return report_obj.render('custom_stock_report.report_with_qty_price', docargs)


class ReportPrintWithCost(models.AbstractModel):
    _name = 'report.custom_stock_report.report_with_qty_cost'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('custom_stock_report.report_with_qty_cost')
        docargs = {
            'doc_ids': data['ids'],
            'doc_model': report.model,
            'docs': self.env['stock.inventory'].browse(data['ids']),
        }
        return report_obj.render('custom_stock_report.report_with_qty_cost', docargs)


class ReportPrintWithQtyOnly(models.AbstractModel):
    _name = 'report.custom_stock_report.report_with_only_qty'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('custom_stock_report.report_with_only_qty')
        docargs = {
            'doc_ids': data['ids'],
            'doc_model': report.model,
            'docs': self.env['stock.inventory'].browse(data['ids']),
        }
        return report_obj.render('custom_stock_report.report_with_only_qty', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
