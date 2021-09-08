from odoo import api, models, _
from datetime import datetime
from collections import defaultdict
from odoo.exceptions import ValidationError
from itertools import groupby
from operator import itemgetter


class custom_stock_report_lot(models.AbstractModel):
    _name = 'report.custom_stock_report.custom_stock_report_lot_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('custom_stock_report.custom_stock_report_lot_template')
        docargs = {
            'doc_ids': self.env['stock.report.lot'].browse(data['id']),
            'doc_model': report.model,
            'docs': self,
            'detail_query': self._query_detail,
            #             '_get_search_record': self._get_search_record
        }
        stock_rpt_lot_id = self.env['stock.report.lot'].browse(data['id'])
        if not [brand.id for brand in self.env['product.brand'].search([])]:
            raise ValidationError(_('No brand is defined to show.'))
        return report_obj.render('custom_stock_report.custom_stock_report_lot_template', docargs)

    #     def _get_search_record(self, obj):
    #         brand_ids = ', '.join(map(lambda x: (x.name), self.env['product.brand'].search([])))
    #         category_ids = ', '.join(map(lambda x: (x.name), self.env['product.category'].search([])))
    #
    #         if obj.internal_location == True:
    #             location_ids = ', '.join(map(lambda x: (x.name), self.env['stock.location'].search([('usage', '=', 'internal')])))
    #         else:
    #             location_ids = ', '.join(map(lambda x: (x.name), self.env['stock.location'].search([])))
    #         return [brand_ids, category_ids, location_ids]

    def _query_detail(self, obj):
        query1 = ''
        query2 = ''
        if obj.exp_date_from and obj.exp_date_to:
            ex_date_from = datetime.strptime(obj.exp_date_from, '%Y-%m-%d')
            ex_date_to = datetime.strptime(obj.exp_date_to, '%Y-%m-%d')
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
        if not obj.category_ids:
            new_category_ids = self.env['product.category'].search([])
            category_ids = [prod_cat_id.id for prod_cat_id in self.env['product.category'].search([])]
        else:
            new_category_ids = obj.category_ids
            category_ids = [prod_cat_id.id for prod_cat_id in obj.category_ids]
        if not obj.product_ids:
            product_ids = [product.id for product in self.env['product.product'].search([('type', '=', 'product')])]
        else:
            product_ids = [product.id for product in obj.product_ids]
        if not obj.location_ids and obj.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([('usage', '=', 'internal')])]
            new_location_ids = self.env['stock.location'].search([])
        elif not obj.location_ids and not obj.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([('usage', '=', 'internal')])]
            new_location_ids = self.env['stock.location'].search([])
        else:
            location_ids = [location.id for location in obj.location_ids]
            new_location_ids = obj.location_ids
        if not obj.brand_ids:
            # brand_ids = [brand.id for brand in self.env['product.brand'].search([])]
            brand_ids = None
            new_brand_ids = self.env['product.brand'].search([])
            if not new_brand_ids:
                raise ValidationError(_('No brand is defined to show.'))
        else:
            brand_ids = [brand.id for brand in obj.brand_ids]
            new_brand_ids = obj.brand_ids

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
                   " AND pb.id in  (%s) " % ','.join(map(str, brand_ids)) if brand_ids else '')
        SQL += 'GROUP BY pp.id, spl.id, pc.name, sl.complete_name, pt.name, pb.name, pt.default_code, pp.barcode, sq.id, sq.qty, spl.name, spl.life_date, pt.list_price'
        self._cr.execute(SQL)
        res = self._cr.dictfetchall()
        final_dict = {}
        if obj.group_by == 'category':
            team_dict = defaultdict(list)
            for category in new_category_ids:
                product_dict = defaultdict(list)
                for each in res:
                    if category.name == each['product_category']:
                        product_dict[each['product']].append(each)
                if product_dict:
                    team_dict[category.name] = dict(product_dict)
            final_dict = dict(team_dict)
            print "--------", final_dict
        if obj.group_by == 'location':
            team_dict = defaultdict(list)
            for location in new_location_ids:
                product_dict = defaultdict(list)
                for each in res:
                    if location.complete_name == each['location']:
                        product_dict[each['product']].append(each)
                if product_dict:
                    team_dict[location.complete_name] = dict(product_dict)
            final_dict = dict(team_dict)
        if obj.group_by == 'brand':
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
