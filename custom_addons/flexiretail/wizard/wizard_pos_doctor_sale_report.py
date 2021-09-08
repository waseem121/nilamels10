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

from odoo import models, fields, api , _
from odoo.exceptions import Warning
from datetime import datetime, date
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')

from itertools import groupby


class wizard_pos_doctor_sale_report(models.TransientModel):
    _name = 'wizard.pos.doctor.sale.report'

    start_date = fields.Date(String="Start Date", default=date.today())
    end_date = fields.Date(String="End Date", default=date.today())
    config_ids = fields.Many2many('pos.config', string="Store")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char('filename', readonly=True)
    data = fields.Binary('file', readonly=True)

    @api.onchange('config_ids')
    def onchange_config_ids(self):
        if self.env.user.default_pos:
            return {'domain': {'config_ids': [('id', '=', self.env.user.default_pos.id)]}}

    @api.multi
    def print_pdf_report(self):
        data = self.read()[0]
        datas = {
            'model': 'wizard.pos.doctor.sale.report',
            'docids':self.id,
            'form': data
        }
        return self.env['report'].get_action(self, 'flexiretail.report_doctor_sale_template', data=datas)

    @api.multi
    def print_excel_report(self):
        stylePC = xlwt.XFStyle()
        stylePC.num_format_str = '@'
        fontP = xlwt.Font()
        fontP.bold = True
        stylePC.font = fontP
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet("Sale Report")
        worksheet.write(0, 0, 'Name', style=stylePC)
        worksheet.write(0, 1, 'Date', style=stylePC)
        worksheet.write(0, 2, 'Doctor' , style=stylePC)
        worksheet.write(0, 3, 'invoice' , style=stylePC)
        worksheet.write(0, 4, 'Barcode ', style=stylePC)
        worksheet.write(0, 5, 'Brand ', style=stylePC)
        worksheet.write(0, 6, 'Product', style=stylePC)
        worksheet.write(0, 7, 'Qty', style=stylePC)
        worksheet.write(0, 8, 'Rate', style=stylePC)

        worksheet.col(0).width = 4500
        worksheet.col(2).width = 4500
        worksheet.col(3).width = 4500
        worksheet.col(4).width = 4500
        worksheet.col(6).width = 6800

        rows = 1
        column = 0
        doctor_group_record = self.env['report.flexiretail.report_doctor_sale_template'].get_doctor_record(self)
        lst = []
        for key in doctor_group_record.keys():
            lst.append(key)
        lst = sorted(lst, reverse=True)
        for each in lst:
            for key, value in doctor_group_record.items():
                if key == each:
                    for line in value:
                        worksheet.write(rows, column, line.get('pos_name') or '')
                        worksheet.write(rows, column + 1, line.get('date') or '')
                        worksheet.write(rows, column + 2, line.get('doctor'))
                        worksheet.write(rows, column + 3, line.get('invoice'))
                        worksheet.write(rows, column + 4, line.get('barcode'))
                        worksheet.write(rows, column + 5, line.get('brand'))
                        worksheet.write(rows, column + 6, line.get('name'))
                        worksheet.write(rows, column + 7, line.get('qty'))
                        worksheet.write(rows, column + 8, "%.3f" % line.get('rate'))
                        rows += 1
                    rows += 1

        file_data = cStringIO.StringIO()
        workbook.save(file_data)
        self.write({
            'state': 'get',
            'data': base64.encodestring(file_data.getvalue()),
            'name': 'doctor_sale_report.xls'
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Doctor Sale Report',
            'res_model': 'wizard.pos.doctor.sale.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }


class report_flexiretail_report_doctor_sale_template(models.AbstractModel):
    _name = 'report.flexiretail.report_doctor_sale_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('flexiretail.report_doctor_sale_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
            'get_doctor_record':self.get_doctor_record,
        }
        return report_obj.render('flexiretail.report_doctor_sale_template', docargs)

    def get_doctor_record(self, obj):
        doctor_group_by = {}
        pos_order_obj = self.env['pos.order']
        start_date = obj.start_date if obj.start_date else str(date.today())
        end_date = obj.end_date if obj.end_date else str(date.today())

        config_obj = self.env['pos.config']
        if obj.config_ids:
            config_obj = obj.config_ids.ids
        if not obj.config_ids and self.env.user.default_pos:
            config_obj = self.env.user.default_pos.ids
        config_ids = config_obj if config_obj else config_obj.search([]).ids
        session_ids = self.env['pos.session'].search([('config_id', 'in', [x for x in config_ids])])
        for each_session in session_ids:
            pos_order_obj |= pos_order_obj.search([('session_id', '=', each_session.id),
                                  ('date_order', '>=', start_date),
                                  ('date_order', '<=', end_date)])

        for order in pos_order_obj.sorted(lambda l:l.date_order):
            for order_line in order.lines:
                if not order.instructor_id in doctor_group_by:
                    doctor_group_by.update({order.instructor_id:[]})
                doctor_group_by[order.instructor_id].append({'date':datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y'),
                                                             'pos_name':order.session_id.config_id.name,
                                                             'doctor':order.instructor_id.name or '',
                                                             'invoice':order.pos_reference,
                                                             'barcode':order_line.product_id.barcode or '',
                                                             'brand':order_line.product_id.categ_id.name,
                                                             'name':order_line.product_id.name,
                                                             'qty':order_line.qty,
                                                             'rate':order_line.price_subtotal_incl
                                                          })
        return doctor_group_by
