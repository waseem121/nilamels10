import base64
import cStringIO
import xlwt
from collections import defaultdict
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from itertools import groupby
from operator import itemgetter


class StockReportLot(models.TransientModel):
    _name = 'stock.report.lot'

    # partner_ids = fields.Many2many('res.partner', string="Vendor", domain=[('supplier', '=', True)])
    product_ids = fields.Many2many('product.product', string="Product")
    category_ids = fields.Many2many('product.category', string="Category")
    brand_ids = fields.Many2many('product.brand', string="Brand")
    location_ids = fields.Many2many('stock.location', string="Location")
    internal_location = fields.Boolean(string="Physical Location", default=True)
    group_by = fields.Selection(
        [('category', 'Category'), ('location', 'Location'), ('brand', 'Brand')],
        string="Group By")
    with_price = fields.Boolean(string="With Price/Cost")
    based_on = fields.Selection([('on_date', 'On Date'), ('upto_date', 'Upto Date')],
                                string="Based On", required=True, default="upto_date")
    based_on_date = fields.Date(string="Date")
    exp_date_from = fields.Date(string="Expiry Date From")
    exp_date_to = fields.Date(string="Expiry Date To")
    data = fields.Binary(string="Data")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char(string='File Name', readonly=True)

    @api.multi
    def generate_stock_report_lot(self):
        datas = {
            'id': self.id,
        }
        return self.env['report'].get_action([], 'custom_stock_report.custom_stock_report_lot_template', data=datas)

    @api.multi
    def generate_stock_report_lot_xlsx(self):
        company_id = self.env['res.users'].browse([self._uid]).company_id
        styleP = xlwt.XFStyle()
        stylePC = xlwt.XFStyle()
        styleBorder = xlwt.XFStyle()
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        font = xlwt.Font()
        fontP = xlwt.Font()
        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.THIN
        font.bold = True
        font.height = 240
        fontP.bold = True
        styleP.font = fontP
        stylePC.font = fontP
        stylePC.alignment = alignment
        styleBorder.font = fontP
        styleBorder.alignment = alignment
        styleBorder.borders = borders
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet("Stock Report With Expiry")
        name = str(company_id.name) if company_id.name else ''
        worksheet.write_merge(0, 4, 0, 9, name, style=stylePC)
        worksheet.write_merge(6, 6, 0, 9, "Stock Report Expiry", style=stylePC)
        worksheet.write_merge(7, 7, 0, 9, "Detail View", style=stylePC)
        expire_type = 'Upto Date'
        worksheet.write_merge(9, 9, 0, 1, 'Based on : ' + expire_type, style=stylePC)
        date_on = datetime.strptime(self.based_on_date, "%Y-%m-%d").strftime(
            '%d-%m-%Y') if self.based_on == 'on_date' else datetime.strftime(datetime.today(), '%d-%m-%Y')
        #         date_on = self.based_on_date if self.based_on == 'on_date' else datetime.strftime(datetime.today(), '%d-%m-%Y')
        worksheet.write_merge(9, 9, 2, 3, 'Date : ' + date_on, style=stylePC)
        if self.exp_date_from and self.exp_date_to:
            exp_from = datetime.strptime(self.exp_date_from, "%Y-%m-%d").strftime('%d-%m-%Y')
            exp_to = datetime.strptime(self.exp_date_to, "%Y-%m-%d").strftime('%d-%m-%Y')
            worksheet.write_merge(10, 10, 1, 1, 'Expiry Date From: ' + exp_from, style=stylePC)
            worksheet.write_merge(10, 10, 4, 5, 'Expiry Date To: ' + exp_to, style=stylePC)
        grp_by = ('Category') if self.group_by == 'category' \
            else ('Location') if self.group_by == 'location' \
            else ('Brand') if self.group_by == 'brand' else '-'
        worksheet.write_merge(11, 11, 0, 9, 'Group by : ' + grp_by, style=stylePC)

        if not self.brand_ids:
            b_ids = 'All Brands'
        else:
            b_ids = ', '.join(map(lambda x: (x.name), self.brand_ids))
        worksheet.write_merge(12, 12, 0, 9, 'Brand : ' + b_ids, style=stylePC)

        if not self.category_ids:
            categ_ids = 'All Categories'
        else:
            categ_ids = ', '.join(map(lambda x: (x.name), self.category_ids))
        worksheet.write_merge(13, 13, 0, 9, 'Category : ' + categ_ids, style=stylePC)
        if not self.location_ids:
            if self.internal_location == True:
                loc_ids = 'All Physical Location'
            else:
                loc_ids = 'All Location'
        else:
            loc_ids = ', '.join(map(lambda x: (x.name), self.location_ids))
        worksheet.write_merge(14, 14, 0, 9, 'Location : ' + loc_ids, style=stylePC)

        rows = 16
        final_qty_total = 0
        final_cost_total = 0
        final_value_total = 0
        final_net_value_total = 0
        data = self._query_detail()
        worksheet.col(2).width = 10000
        worksheet.col(3).width = 5000
        worksheet.col(9).width = 4000
        categ_row = rows + 1
        for key, value in data.items():
            qty_total = 0
            cost_total = 0
            value_total = 0
            net_value_total = 0
            worksheet.write_merge(categ_row, categ_row, 0, 5, grp_by + ': ' + key, style=stylePC)
            categ_row += 1

            worksheet.write_merge(categ_row, categ_row, 0, 0, 'Item Code', style=stylePC)
            worksheet.write_merge(categ_row, categ_row, 1, 1, 'Barcode', style=stylePC)
            worksheet.write_merge(categ_row, categ_row, 2, 2, 'Description', style=stylePC)
            #             worksheet.write_merge(categ_row, categ_row, 2, 2, 'Category', style=stylePC)
            worksheet.write_merge(categ_row, categ_row, 3, 3, 'Batch No.', style=stylePC)
            worksheet.write_merge(categ_row, categ_row, 4, 4, 'Exp. Date', style=stylePC)
            worksheet.write_merge(categ_row, categ_row, 5, 5, 'Qty.', style=stylePC)
            worksheet.write_merge(categ_row, categ_row, 6, 6, 'Cost', style=stylePC)
            worksheet.write_merge(categ_row, categ_row, 7, 7, 'Public Price', style=stylePC)
            worksheet.write_merge(categ_row, categ_row, 8, 8, 'Total Cost', style=stylePC)
            worksheet.write_merge(categ_row, categ_row, 9, 9, 'Total Net Value', style=stylePC)
            categ_row += 1
            for k, v in value.items():
                for each_value in v:
                    product_dict = {}
                    product_dict = {'product': k,
                                    'description': each_value['description'],
                                    'product_category': each_value['product_category'],
                                    'item_code': each_value['item_code'],
                                    'barcode': each_value['barcode'],
                                    'batch_no': each_value['batch_no'],
                                    #                                     'ex_date': fields.Datetime.from_string(each_value['ex_date']).strftime('%d-%m-%Y %H:%M:%S'),
                                    'ex_date': fields.Datetime.from_string(each_value['ex_date']).strftime('%d-%m-%Y'),
                                    'qty': each_value['qty'],  # sum(q['qty'] for q in v),
                                    'cost': each_value['cost'],
                                    'sale_price': each_value['sale_price'],
                                    'value': each_value['value'],  # cost total
                                    'net_value': each_value['net_value']  # sale total
                                    #                                     'cost': sum(c['cost'] for c in v),
                                    #                                     'value': sum(v['value'] for v in v)
                                    }
                    worksheet.write_merge(categ_row, categ_row, 0, 0, product_dict['item_code'])
                    worksheet.write_merge(categ_row, categ_row, 1, 1, product_dict['barcode'])
                    worksheet.write_merge(categ_row, categ_row, 2, 2, product_dict['product'])
                    #                     worksheet.write_merge(categ_row, categ_row, 2, 2, product_dict['product_category'])
                    worksheet.write_merge(categ_row, categ_row, 3, 3, product_dict['batch_no'])
                    worksheet.write_merge(categ_row, categ_row, 4, 4, product_dict['ex_date'])
                    worksheet.write_merge(categ_row, categ_row, 5, 5, product_dict['qty'])
                    worksheet.write_merge(categ_row, categ_row, 6, 6, '%.3f' % product_dict['cost'])
                    worksheet.write_merge(categ_row, categ_row, 7, 7, '%.3f' % product_dict['sale_price'])
                    worksheet.write_merge(categ_row, categ_row, 8, 8, '%.3f' % product_dict['value'])  # cost total
                    worksheet.write_merge(categ_row, categ_row, 9, 9, '%.3f' % product_dict['net_value'])  # sale total
                    qty_total += product_dict['qty']
                    #                     cost_total += product_dict['cost']
                    value_total += product_dict['value']
                    net_value_total += product_dict['net_value']
                    categ_row += 1

            #                 if each_value['product'] == k:
            #                     worksheet.write_merge(categ_row, categ_row, 0, 0, product_dict['product'])
            #                     worksheet.write_merge(categ_row, categ_row, 1, 1, product_dict['item_code'])
            #                     worksheet.write_merge(categ_row, categ_row, 2, 2, product_dict['product_category'])
            #                     worksheet.write_merge(categ_row, categ_row, 3, 3, product_dict['batch_no'])
            #                     worksheet.write_merge(categ_row, categ_row, 4, 4, product_dict['ex_date'])
            #                     worksheet.write_merge(categ_row, categ_row, 5, 5, product_dict['qty'])
            #                     worksheet.write_merge(categ_row, categ_row, 6, 6, '%.3f' %product_dict['cost'])
            #                     worksheet.write_merge(categ_row, categ_row, 7, 7, '%.3f' %product_dict['value'])
            #                     qty_total += product_dict['qty']
            #                     cost_total += product_dict['cost']
            #                     value_total += product_dict['value']
            #             final_cost_total +=  cost_total
            final_value_total += value_total
            final_net_value_total += net_value_total
            final_qty_total += qty_total
            worksheet.write(categ_row, 4, 'Total', style=stylePC)
            worksheet.write(categ_row, 5, qty_total, style=styleBorder)
            #             worksheet.write(categ_row, 6, '%.3f' %cost_total, style=styleBorder)
            worksheet.write(categ_row, 8, '%.3f' % value_total, style=styleBorder)
            worksheet.write(categ_row, 9, '%.3f' % net_value_total, style=styleBorder)
            categ_row += 2
        worksheet.write(categ_row + 1, 4, 'Grand Total', style=stylePC)
        worksheet.write(categ_row + 1, 5, final_qty_total, style=styleBorder)
        #         worksheet.write(categ_row + 1, 6, '%.3f' %final_cost_total, style=styleBorder)
        worksheet.write(categ_row + 1, 8, '%.3f' % final_value_total, style=styleBorder)
        worksheet.write(categ_row + 1, 9, '%.3f' % final_net_value_total, style=styleBorder)
        file_data = cStringIO.StringIO()
        workbook.save(file_data)
        self.write({
            'state': 'get',
            'data': base64.encodestring(file_data.getvalue()),
            'name': 'stock_report_lot.xls'
        })
        return {
            'name': 'Stock Report Lot',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.report.lot',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def _query_detail(self):
        query1 = ''
        query2 = ''
        if self.exp_date_from and self.exp_date_to:
            ex_date_from = datetime.strptime(self.exp_date_from, '%Y-%m-%d')
            ex_date_to = datetime.strptime(self.exp_date_to, '%Y-%m-%d')
            query1 = """spl.life_date >= '%s' AND
                        spl.life_date <= '%s' AND""" % (
            ex_date_from.replace(hour=00, minute=00, second=00), ex_date_to.replace(hour=23, minute=59, second=59))
        #         if self.based_on:
        #             if self.based_on == 'on_date':
        #                 b_date = datetime.strptime(self.based_on_date, '%Y-%m-%d')
        #                 query2 = """sm.date <= '%s' AND""" % (b_date.replace(hour=23, minute=59, second=59))
        #             else:
        #                 b_date = datetime.strftime(datetime.today(), '%Y-%m-%d 23:59:59')
        #                 query2 = """sm.date <= '%s' AND""" % (b_date)
        if not self.category_ids:
            new_category_ids = self.env['product.category'].search([])
            category_ids = [prod_cat_id.id for prod_cat_id in self.env['product.category'].search([])]
        else:
            new_category_ids = self.category_ids
            category_ids = [prod_cat_id.id for prod_cat_id in self.category_ids]
        if not self.product_ids:
            product_ids = [product.id for product in self.env['product.product'].search([('type', '=', 'product')])]
        else:
            product_ids = [product.id for product in self.product_ids]
        if not self.location_ids and self.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([('usage', '=', 'internal')])]
            new_location_ids = self.env['stock.location'].search([])
        elif not self.location_ids and not self.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([('usage', '=', 'internal')])]
            new_location_ids = self.env['stock.location'].search([])
        else:
            location_ids = [location.id for location in self.location_ids]
            new_location_ids = self.location_ids
        if not self.brand_ids:
            # brand_ids = [brand.id for brand in self.env['product.brand'].search([])]
            brand_ids = None
            new_brand_ids = self.env['product.brand'].search([])
            if not new_brand_ids:
                raise ValidationError(_('No brand is defined to show.'))
        else:
            brand_ids = [brand.id for brand in self.brand_ids]
            new_brand_ids = self.brand_ids

        SQL = """SELECT 
                    pc.name as product_category,
                    sl.complete_name as location,
                    pt.name as product,
                    pb.name as brand,
                    pt.default_code as item_code,
                    pp.barcode as barcode,
                    pt.name as description,
                    sq.id as sq_id,
                    sq.qty as qty,
                    pt.list_price as sale_price,
                    spl.name as batch_no,
                    spl.life_date as ex_date,
                    sq.qty * pt.list_price as net_value,
                    spl.id,
                    pp.id as product_id
                FROM stock_production_lot spl
                    LEFT JOIN product_product pp on spl.product_id= pp.id
                    LEFT JOIN product_template pt on pp.product_tmpl_id= pt.id
                    LEFT JOIN product_brand pb on pt.product_brand_id = pb.id
                    LEFT JOIN product_category pc on pt.categ_id = pc.id
                    LEFT JOIN stock_quant sq on spl.id = sq.lot_id
                    LEFT JOIN stock_location sl on sq.location_id = sl.id
                    
                WHERE
                    pt.type = 'product' AND
                    %s
                    %s
                    pc.id in %s AND
                    sl.id in %s AND
                    pp.id in %s 
                    %s
            """ % (query1,
                   query2,
                   " (%s) " % ','.join(map(str, category_ids)),
                   " (%s) " % ','.join(map(str, location_ids)),
                   " (%s) " % ','.join(map(str, product_ids)),
                   " AND pb.id in (%s) " % ','.join(map(str, brand_ids)) if brand_ids else '')
        SQL += 'GROUP BY pp.id, spl.id, pc.name, sl.complete_name, pt.name, pb.name, pt.default_code, pp.barcode, sq.id, sq.qty, spl.name, spl.life_date, pt.list_price'
        self._cr.execute(SQL)
        res = self._cr.dictfetchall()
        final_dict = {}
        if self.group_by == 'category':
            team_dict = defaultdict(list)
            for category in new_category_ids:
                product_dict = defaultdict(list)
                for each in res:
                    if category.name == each['product_category']:
                        product_dict[each['product']].append(each)
                if product_dict:
                    team_dict[category.name] = dict(product_dict)
            final_dict = dict(team_dict)
        if self.group_by == 'location':
            team_dict = defaultdict(list)
            for location in new_location_ids:
                product_dict = defaultdict(list)
                for each in res:
                    if location.complete_name == each['location']:
                        product_dict[each['product']].append(each)
                if product_dict:
                    team_dict[location.complete_name] = dict(product_dict)
            final_dict = dict(team_dict)
        if self.group_by == 'brand':
            team_dict = defaultdict(list)
            for brand in new_brand_ids:
                product_dict = defaultdict(list)
                for each in res:
                    if brand.name == each['brand']:
                        product_dict[each['product']].append(each)
                if product_dict:
                    team_dict[brand.name] = dict(product_dict)
            undefine = defaultdict(list)
            for each in res:
                if not each.get('brand'):
                    undefine[each['product']].append(each)
            team_dict['Undefine'] = dict(undefine)
            final_dict = dict(team_dict)
        fdict = {}
        for key_main, value in final_dict.items():
            if key_main not in fdict:
                fdict.update({key_main: {}})
            for prod, prodval in value.items():
                if prod not in fdict[key_main]:
                    fdict[key_main].update({prod: []})
                grouper = itemgetter('product', 'batch_no', 'ex_date', 'id', 'description', 'barcode', 'brand',
                                     'item_code', 'product_category')
                result = []
                for key, grp in groupby(sorted(prodval, key=grouper), grouper):
                    temp_dict = dict(zip(
                        ['product', 'batch_no', 'ex_date', 'id', 'description', 'barcode', 'brand', 'item_code',
                         'product_category'], key))
                    temp_dict["cost"] = temp_dict["sale_price"] = temp_dict["value"] = temp_dict["net_value"] = 0.0
                    temp_dict["qty"] = 0
                    for each in grp:
                        if each.get('product_id', False):
                            product_price_history_id = self.env['product.price.history'].search(
                                [('product_id', '=', each.get('product_id'))], limit=1)
                            each[
                                'cost'] = product_price_history_id.cost if product_price_history_id and product_price_history_id.cost else 0.0
                            each["value"] = each['qty'] * each['cost']
                        temp_dict["qty"] += each["qty"]
                        if not temp_dict["cost"]:
                            temp_dict["cost"] += each["cost"] or 0.0
                        else:
                            temp_dict["cost"] = (temp_dict["cost"] + each["cost"] or 0.0) / 2 if temp_dict["cost"] != \
                                                                                                 each[
                                                                                                     "cost"] or 0.0 else \
                            temp_dict["cost"]
                        if not temp_dict["sale_price"]:
                            temp_dict["sale_price"] += each["sale_price"]
                        else:
                            temp_dict["sale_price"] = (temp_dict["sale_price"] + each["sale_price"]) / 2 if temp_dict[
                                                                                                                "sale_price"] != \
                                                                                                            each[
                                                                                                                "sale_price"] else \
                            temp_dict["sale_price"]
                        #                         temp_dict["cost"] += each["cost"]
                        #                         temp_dict["sale_price"] += each["sale_price"]
                        temp_dict["value"] += each["value"]
                        temp_dict["net_value"] += each["net_value"]
                    result.append(temp_dict)
                fdict[key_main][prod] = result
        return fdict
