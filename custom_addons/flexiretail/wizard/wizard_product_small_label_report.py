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

from openerp import fields, models, api, _
import base64
from openerp.exceptions import Warning
from wand.image import Image
import os, glob
import os.path


class product_small_label_design(models.Model):
    _name = 'product.small.label.design'

    @api.model
    def default_get(self, fields_list):
        res = super(product_small_label_design, self).default_get(fields_list)
        if self._context.get('wiz_id') and self._context.get('from_wizard'):
            for wiz in self.env['wizard.product.small.label.report'].browse(self._context.get('wiz_id')):
                res.update({
                    'template_label_design': wiz.report_design,
                    'report_model': wiz.report_model,
                    'label_width': wiz.label_width,
                    'label_height': wiz.label_height,
                    'dpi': wiz.dpi,
                    'margin_top': wiz.margin_top,
                    'margin_left': wiz.margin_left,
                    'margin_bottom': wiz.margin_bottom,
                    'margin_right': wiz.margin_right,
                    'humanReadable': wiz.humanReadable,
                    'barcode_height': wiz.barcode_height,
                    'barcode_width': wiz.barcode_width,
                    'display_height': wiz.display_height,
                    'display_width': wiz.display_width,
                    'with_barcode': wiz.with_barcode,
                    'label_logo': wiz.label_logo
                })
        return res

    name = fields.Char(string="Design Name")
    report_model = fields.Char(string='Model')
    template_label_design = fields.Text(string="Template Design")
    # label
    label_width = fields.Integer(string='Label Width (mm)', default=43, required=True)
    label_height = fields.Integer(string='Label Height (mm)', default=30, required=True)
    dpi = fields.Integer(string='DPI', default=80, help="The number of individual dots\
                                that can be placed in a line within the span of 1 inch (2.54 cm)")
    margin_top = fields.Integer(string='Margin Top (mm)', default=4)
    margin_left = fields.Integer(string='Margin Left (mm)', default=1)
    margin_bottom = fields.Integer(string='Margin Bottom (mm)', default=1)
    margin_right = fields.Integer(string='Margin Right (mm)', default=1)
    # barcode
    humanReadable = fields.Boolean(string="HumanReadable", help="User wants to print barcode number\
                                    with barcode label.")
    barcode_height = fields.Integer(string="Height", default=300, required=True, help="This height will\
                                    required for the clearity of the barcode.")
    barcode_width = fields.Integer(string="Width", default=1500, required=True, help="This width will \
                                    required for the clearity of the barcode.")
    display_height = fields.Integer(string="Display Height (px)", required=True, default=30,
                                    help="This height will required for display barcode in label.")
    display_width = fields.Integer(string="Display Width (px)", required=True, default=120,
                                   help="This width will required for display barcode in label.")
    with_barcode = fields.Boolean(string='Barcode', help="Click this check box if user want to print\
                                    barcode for Product Label.", default=True)
    active = fields.Boolean(string="Active", default=True)
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    label_logo = fields.Binary(string="Label Logo")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('from_wizard') and self._context.get('report_model'):
            args.append(('report_model', '=', self._context.get('report_model')))
        elif self._context.get('from_wizard') and not self._context.get('report_model'):
            args.append(('report_model', '=', False))
        return super(product_small_label_design,self).name_search(name, args=args, operator=operator, limit=limit)

    @api.multi
    def close_wizard(self):
        self.write({'active': False})
        return {
            'name': _('Print Product Label'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'wizard.product.small.label.report',
            'target': 'new',
            'res_id': self._context.get('wiz_id') ,
            'context': self.env.context
        }

    @api.multi
    def go_to_label_wizard(self):
        if not self.name:
            raise Warning(_('Label Design Name is required.'))
        return {
            'name': _('Product Label'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'wizard.product.small.label.report',
            'target': 'new',
            'res_id': self._context.get('wiz_id'),
            'context': self.env.context
        }

class wizard_product_small_label_report(models.TransientModel):
    _name = "wizard.product.small.label.report"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(wizard_product_small_label_report, self).fields_view_get(view_id=view_id, view_type=view_type,
                                           toolbar=toolbar, submenu=False)
        if view_type in ['form']:
            if self._context.get('active_model'):
                if self._context.get('active_model') != 'wizard.product.small.label.report':
                    for elm in result.get('fields').get('product_ids').get('views').get('tree'):
                        if elm == 'arch':
                            result['fields']['product_ids']['views']['tree']['arch'] = """<tree string="Products" editable="top">
                                                                                            <field name="product_id" modifiers="{&quot;required&quot;: true, &quot;readonly&quot;: true}"/>
                                                                                            <field name="qty" modifiers="{}"/>
                                                                                            <field name="line_id" invisible="1" modifiers="{&quot;tree_invisible&quot;: true}"/>
                                                                                            </tree>"""
        return result

    @api.model
    def default_get(self, fields_list):
        prod_list = []
        product_list_dict = []
        res = super(wizard_product_small_label_report, self).default_get(fields_list)
        if self._context.get('active_ids') and self._context.get('active_model') == 'purchase.order':
            for line in self.env['purchase.order.line'].search([('order_id', 'in', self._context.get('active_ids'))]):
                if line.product_id and line.product_qty:
                   product_list_dict.append({'product_id': line.product_id.id, 'qty': line.product_qty, 'line_id':line.id})
        elif self._context.get('active_ids') and self._context.get('active_model') == 'sale.order':
            for line in self.env['sale.order.line'].search([('order_id', 'in', self._context.get('active_ids'))]):
                if line.product_id and line.product_uom_qty:
                   product_list_dict.append({'product_id': line.product_id.id, 'qty': line.product_uom_qty, 'line_id':line.id})
        elif self._context.get('active_ids') and self._context.get('active_model') == 'stock.picking':
            for line in self.env['stock.move'].search([('picking_id', 'in', self._context.get('active_ids'))]):
                if line.product_id and line.product_qty:
                    product_list_dict.append({'product_id': line.product_id.id, 'qty': line.product_qty, 'line_id':line.id})
        elif self._context.get('active_ids') and self._context.get('active_model') == 'account.invoice':
            for line in self.env['account.invoice.line'].search([('invoice_id', 'in', self._context.get('active_ids'))]):
                if line.product_id and line.quantity:
                    product_list_dict.append({'product_id': line.product_id.id, 'qty': line.quantity, 'line_id':line.id})
        elif self._context.get('active_ids') and self._context.get('active_model') == 'product.product':
            for each_product in self.env['product.product'].browse(self._context.get('active_ids')):
                product_list_dict.append({'product_id': each_product.id, 'qty': 1})
        for each_dict in product_list_dict:
            prod_list.append((0, 0, {'product_id': each_dict.get('product_id'),
                                     'qty': each_dict.get('qty'),
                                     'line_id': each_dict.get('line_id')}))
        if self._context.get('active_model'):
            res['report_model'] = self._context.get('active_model')
            design_id = self.env['product.small.label.design'].search([('report_model', '=', self._context.get('active_model'))], limit=1)
            if design_id:
                res['design_id'] = design_id.id
        else:
            res['report_model'] = 'wizard.product.small.label.report'
            design_id = self.env['product.small.label.design'].search([('report_model', '=', 'wizard.product.small.label.report')], limit=1)
            if design_id:
                res['design_id'] = design_id.id
        res['product_ids'] = prod_list
        return res

    @api.model
    def _get_report_design(self):
        view_id = self.env['ir.ui.view'].search([('name', '=', 'prod_small_lbl_rpt')])
        if view_id.arch:
            return view_id.arch

    @api.model
    def _get_report_id(self):
        view_id = self.env['ir.ui.view'].search([('name', '=', 'prod_small_lbl_rpt')])
        if not view_id:
            raise Warning('Someone has deleted the reference view of report.\
                Please Update the module!')
        return view_id.id

    @api.model
    def _get_report_paperformat_id(self):
        xml_id = self.env['ir.actions.report.xml'].search([('report_name', '=',
                                                        'flexiretail.prod_small_lbl_rpt')])
        if not xml_id or not xml_id.paperformat_id:
            raise Warning('Someone has deleted the reference paperformat of report.Please Update the module!')
        return xml_id.paperformat_id.id


    report_model = fields.Char(string='Model')
    design_id = fields.Many2one('product.small.label.design', string="Template")
    product_ids = fields.One2many('product.small.label.qty', 'prod_small_wiz_id', string='Product List')
    label_width = fields.Integer(string='Label Width (mm)', default=43, required=True)
    label_height = fields.Integer(string='Label Height (mm)', default=30, required=True)
    dpi = fields.Integer(string='DPI', default=80, help="The number of individual dots \
                        that can be placed in a line within the span of 1 inch (2.54 cm)")
    margin_top = fields.Integer(string='Margin Top (mm)', default=4)
    margin_left = fields.Integer(string='Margin Left (mm)', default=1)
    margin_bottom = fields.Integer(string='Margin Bottom (mm)', default=1)
    margin_right = fields.Integer(string='Margin Right (mm)', default=1)
    # barcode input
    humanReadable = fields.Boolean(string="HumanReadable", help="User wants to print barcode number \
                                    with barcode label.")
    barcode_height = fields.Integer(string="Height", default=300, required=True,
                                    help="This height will required for the clearity of the barcode.")
    barcode_width = fields.Integer(string="Width", default=1500, required=True,
                                   help="This width will required for the clearity of the barcode.")
    display_height = fields.Integer(string="Display Height (px)", required=True, default=30,
                                    help="This height will required for display barcode in label.")
    display_width = fields.Integer(string="Display Width (px)", required=True, default=120,
                                   help="This width will required for display barcode in label.")
    # report design
    report_design = fields.Text(string="Report Design", default=_get_report_design, required=True)
    view_id = fields.Many2one('ir.ui.view', string='Report View', default=_get_report_id)
    paper_format_id = fields.Many2one('report.paperformat', string="Paper Format", default=_get_report_paperformat_id)
    with_barcode = fields.Boolean(string='Barcode', help="Click this check box if user want to\
                        print barcode for Product Label.", default=True)
    label_preview = fields.Binary(string="Label Preview")
    view_preview = fields.Boolean(string="View Preview")
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist")
    make_update_existing = fields.Boolean(string="Update Existing Template")
    label_logo = fields.Binary(string="Label Logo")

    @api.onchange('design_id')
    def on_change_design_id(self):
        if self.design_id:
            self.report_design = self.design_id.template_label_design
            self.report_model = self.design_id.report_model
            # label format args
            self.label_width = self.design_id.label_width
            self.label_height = self.design_id.label_height
            self.dpi = self.design_id.dpi
            self.margin_top = self.design_id.margin_top
            self.margin_left = self.design_id.margin_left
            self.margin_bottom = self.design_id.margin_bottom
            self.margin_right = self.design_id.margin_right
            # barcode args
            self.with_barcode = self.design_id.with_barcode
            self.barcode_height = self.design_id.barcode_height
            self.barcode_width = self.design_id.barcode_width
            self.humanReadable = self.design_id.humanReadable
            self.display_height = self.design_id.display_height
            self.display_width = self.design_id.display_width
            self.label_logo = self.design_id.label_logo

    @api.multi
    def save_design(self):
        if not self.make_update_existing:
            view_id = self.env['ir.model.data'].get_object_reference('flexiretail',
                                                    'wizard_product_small_label_design_form_view')[1]
            ctx = dict(self.env.context)
            ctx.update({'wiz_id' : self.id})
            return {
                'name': _('Product Small Label Design'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'product.small.label.design',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'view_id': view_id,
                'context': ctx,
                'nodestroy': True
            }
        else:
            if self.design_id:
                self.design_id.write({
                                'template_label_design': self.report_design,
                                'report_model': self.report_model,
                                'label_width': self.label_width,
                                'label_height': self.label_height,
                                'dpi': self.dpi,
                                'margin_top': self.margin_top,
                                'margin_left': self.margin_left,
                                'margin_bottom': self.margin_bottom,
                                'margin_right': self.margin_right,
                                'humanReadable': self.humanReadable,
                                'barcode_height': self.barcode_height,
                                'barcode_width': self.barcode_width,
                                'display_height': self.display_height,
                                'display_width': self.display_width,
                                'with_barcode': self.with_barcode,
                                'label_logo': self.label_logo
                                })
                return {
                        'name': _('Product Label'),
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'wizard.product.small.label.report',
                        'target': 'new',
                        'res_id': self.id,
                        'context': self.env.context
                        }

    @api.multi
    @api.onchange('dpi')
    def onchange_dpi(self):
        if self.dpi < 80:
            self.dpi = 80

    @api.multi
    def action_preview(self):
        encoded_string = ''
        if len(self.product_ids) <= 0:
            raise Warning(_('Define product with at least 1 quantity for pdf preview.'))
        data = self.read()[0]
        if self.view_id:
            self.view_id.sudo().write({'arch': self.report_design})
        self._set_paper_format_id()
        if data.get('product_ids'):
            data['product_ids'] = [data.get('product_ids')[0]]
        data.update({'label_preview': True})
        datas = {
            'ids': self._ids,
            'model': 'wizard.product.small.label.report',
            'form': data
        }
        ctx = {
            'dynamic_size': True,
            'data': data
        }
        pdf_data = self.env['report'].get_html(self, 'flexiretail.prod_small_lbl_rpt', data=datas)
        body = [(self.id, pdf_data)]
        pdf_image = self.env['report']._run_wkhtmltopdf([], [], body, None, self.paper_format_id,
                                                {}, {'loaded_documents': {}, 'model': u'product.product'})
        with Image(blob=pdf_image) as img:
            filelist = glob.glob("/tmp/*.jpg")
            for f in filelist:
                os.remove(f)
            img.save(filename="/tmp/temp.jpg")
        if os.path.exists("/tmp/temp-0.jpg"):
               with open(("/tmp/temp-0.jpg"), "rb") as image_file:
                   encoded_string = base64.b64encode(image_file.read())
        elif os.path.exists("/tmp/temp.jpg"):
            with open(("/tmp/temp.jpg"), "rb") as image_file:
                   encoded_string = base64.b64encode(image_file.read())
        self.write({'view_preview': True, 'label_preview': encoded_string})
        return {
            'name': _('Product Label'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'wizard.product.small.label.report',
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context
        }

    @api.multi
    def action_print(self):
        if not self.product_ids:
            raise Warning('Select any product first.!')
        for product in self.product_ids:
            if product.qty <= 0:
                raise Warning('%s product label qty should be greater then 0.!'
                           % (product.product_id.name))
        if (self.label_height <= 0) or (self.label_width <= 0):
            raise Warning(_('You can not give label width and label height to less then zero(0).'))
        if (self.margin_top < 0) or (self.margin_left < 0) or \
            (self.margin_bottom < 0) or (self.margin_right < 0):
            raise Warning('Margin Value(s) for report can not be negative!')
        if self.with_barcode and (self.barcode_height <= 0 or self.barcode_width <=0 or
                                  self.display_height <= 0 or self.display_width <= 0):
            raise Warning('Give proper barcode height and width value(s) for display')
        data = self.read()[0]
        data.update({'label_preview': False})
        datas = {
            'ids': self._ids,
            'model': 'wizard.product.small.label.report',
            'form': data
        }
        ctx = {
            'dynamic_size': True,
            'data': data
        }
        if self.view_id and self.report_design:
            self.view_id.sudo().write({'arch': self.report_design})
        self._set_paper_format_id()
        return self.env['report'].get_action(self,
                        'flexiretail.prod_small_lbl_rpt', data=datas)

    @api.multi
    def _set_paper_format_id(self):
        if self.paper_format_id:
            result = self.paper_format_id.sudo().write({
                        'format': 'custom',
                        'page_width': self.label_width,
                        'page_height': self.label_height,
                        'margin_top': self.margin_top,
                        'margin_left': self.margin_left,
                        'margin_bottom': self.margin_bottom,
                        'margin_right': self.margin_right,
                        'dpi': self.dpi
                    })

class product_label_qty(models.TransientModel):
    _name = 'product.small.label.qty'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Integer(string='Quantity', default=1)
    prod_small_wiz_id = fields.Many2one('wizard.product.small.label.report', string='Product Label Wizard ID')
    line_id = fields.Integer(string='Line ID')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
