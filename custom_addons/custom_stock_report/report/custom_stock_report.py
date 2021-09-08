from odoo import api, models, _
from datetime import datetime
from collections import defaultdict
from odoo.exceptions import ValidationError
from itertools import groupby
from collections import OrderedDict
from odoo.tools.float_utils import float_round
from odoo.addons import decimal_precision as dp


class custom_stock_report(models.AbstractModel):
    _name = 'report.custom_stock_report.custom_stock_report_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('custom_stock_report.custom_stock_report_template')
        docargs = {
                    'doc_ids': self.env['stock.report'].browse(data['id']),
                    'doc_model': report.model,
                    'docs': self,
                    'summary_query': self._query_summary,
                    'detail_query': self._query_detail,
                    '_get_search_record': self._get_search_record
                }
        stock_rpt_id = self.env['stock.report'].browse(data['id'])
        if stock_rpt_id:
            brand_rpt = ', '.join(map(lambda x: (x.name), stock_rpt_id.brand_ids))
        if not [brand.id for brand in self.env['product.brand'].search([])]:
            raise ValidationError(_('No brand is defined to show.'))
        return report_obj.render('custom_stock_report.custom_stock_report_template', docargs)

    def _get_search_record(self, obj):
        brand_ids = ', '.join(map(lambda x: (x.name), self.env['product.brand'].search([]))) 
        category_ids = ', '.join(map(lambda x: (x.name), self.env['product.category'].search([])))
        
        if obj.internal_location == True:
            location_ids = ', '.join(map(lambda x: (x.name), self.env['stock.location'].search([('usage', '=', 'internal')])))
        else: 
            location_ids = ', '.join(map(lambda x: (x.name), self.env['stock.location'].search([]))) 
        return [brand_ids, category_ids, location_ids]

    def _query_summary(self, obj):
        if not obj.date:
            to_date = datetime.strftime(datetime.today(), '%Y-%m-%d')
            to_date = datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        else:
            to_date = datetime.strptime(obj.date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        if not obj.category_ids:
            new_category_ids = self.env['product.category'].search([])
            category_ids = [prod_cat_id.id for prod_cat_id in self.env['product.category'].search([])]
        else:
            new_category_ids = obj.category_ids
            category_ids = [prod_cat_id.id for prod_cat_id in obj.category_ids]
        if obj.partner_id:
            product_suppliers = self.env['product.supplierinfo'].search([('name','=',obj.partner_id.id)])
            product_ids = []
            for product_supplier in product_suppliers:
                product_ids.append(product_supplier.product_tmpl_id.id)
                new_product_ids = product_ids
                
#            if not obj.product_ids:
#                product_ids = [product.id for product in self.env['product.product'].search([('type', '=', 'product')])]
#                new_product_ids = self.env['product.product'].search([('type', '=', 'product')])
#            else:
#                product_ids = [product.id for product in obj.product_ids]
#                new_product_ids = obj.product_ids
        else:
            if not obj.product_ids:
                product_ids = [product.id for product in self.env['product.product'].search([('type', '=', 'product')])]
                new_product_ids = self.env['product.product'].search([('type', '=', 'product')])
            else:
                product_ids = [product.id for product in obj.product_ids]
                new_product_ids = obj.product_ids            
        if not obj.location_ids and obj.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([('usage', '=', 'internal')])]
            new_location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        elif not obj.location_ids and not obj.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([])]
            new_location_ids = self.env['stock.location'].search([])
        else:
            location_ids = [location.id for location in obj.location_ids]
            new_location_ids = obj.location_ids
        if not obj.brand_ids:
            brand_ids = [brand.id for brand in self.env['product.brand'].search([])]
            new_brand_ids = self.env['product.brand'].search([])
        else:
            brand_ids = [brand.id for brand in obj.brand_ids]
            new_brand_ids = obj.brand_ids
            
        print"product_ids: ",product_ids
        if obj.view_by == 'summary':

            if obj.group_by == 'category':
                group_name = 'pc.name'
                group = 'pc'

            if obj.group_by == 'location':
                group_name = 'sl.complete_name'
                group = 'sl'

            if obj.group_by == 'brand':
                group_name = 'pb.name'
                group = 'pb'
            
            SQL = """ """
            if obj.date_selection == 'upto_date':
               SQL = """
                        SELECT 
                            pc.name as product_category,
                            sl.complete_name as location,
                            pt.name as product,
                            pp.default_code as item_code,
                            pp.barcode as barcode,
                            pp.id as product_id,
                            pt.name as description,
                            pb.name as brand,
                            sum(sq.qty) as qty,
                            sum(sq.cost) as cost
                        FROM 
                            stock_quant sq
                            
                            FULL JOIN product_product pp on sq.product_id= pp.id
                            FULL JOIN product_template pt on pp.product_tmpl_id= pt.id
                            FULL JOIN product_category pc on pt.categ_id= pc.id
                            FULL JOIN stock_location sl on sq.location_id = sl.id
                            FULL JOIN product_brand pb on pt.product_brand_id = pb.id
                        WHERE 
                            sq.in_date <= '%s' AND
                            pt.type = 'product' AND
                        """  % (to_date)
            else:
                SQL = """
                        SELECT 
                            pc.name as product_category,
                            sl.complete_name as location,
                            pt.name as product,
                            pp.default_code as item_code,
                            pp.barcode as barcode,
                            pp.id as product_id,
                            pt.name as description,
                            pb.name as brand,
                            sum(sq.quantity) as qty,
                            sum(sq.price_unit_on_quant) as cost
                        FROM 
                            stock_history sq
                            
                            FULL JOIN product_product pp on sq.product_id= pp.id
                            FULL JOIN product_template pt on sq.product_template_id= pt.id
                            FULL JOIN product_category pc on sq.product_categ_id= pc.id
                            FULL JOIN stock_location sl on sq.location_id = sl.id
                            FULL JOIN product_brand pb on pt.product_brand_id = pb.id
                        WHERE 
                            sq.date <= '%s' AND
                            pt.type = 'product' AND
                        """  % (to_date)
            SQL += """  pc.id in %s AND
                        sl.id in %s AND
                        pp.id in %s AND
                        (pb.id in %s or pb.id is NULL)
                        
                        GROUP BY pp.id, pc.name, sl.complete_name, pt.name, pb.name, pp.default_code
                    """ % (
                            " (%s) " % ','.join(map(str, category_ids)),
                            " (%s) " % ','.join(map(str, location_ids)),
                            " (%s) " % ','.join(map(str, product_ids)),
                            " (%s) " % ','.join(map(str, brand_ids)))
#             SQL += ",spl.name" if obj.date_selection == 'upto_date' else ",sq.serial_number"
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
                final_dict = dict(team_dict)
            fdict = {}
            for key,value in final_dict.items():
                if key not in fdict:
                    fdict.update({key: {}})
                for prod,prodval in value.items():
                    res = []
                    if prod not in fdict[key]:
                        fdict[key].update({prod: []})
                    for k,v in groupby(prodval, key=lambda x:x['product']):
                        d = {'product':k, 'value': 0, 'qty': 0, 'cost': 0}
                        for innerv in v:
                            product = self.env['product.product'].search([('id', '=', innerv['product_id'])])
                            if obj.date_selection == 'on_date':
                                print"on Dateeeeeeeeeeeeeeeeeeeeeeeeeeee"
                                
                                SQL = """SELECT cost from product_price_history 
                                    where product_id = %s AND
                                    datetime <= '%s' order by id desc limit 1
                                """  % (product.id, to_date)
                                
                                SQL_old = """SELECT avg(cost) as cost from product_price_history 
                                    where product_id = %s AND
                                    datetime <= '%s' group by product_id
                                """  % (product.id, to_date)
                                self._cr.execute(SQL)
                                cost_res = self._cr.dictfetchall()
                                cost = cost_res[0].get('cost',0.0) if cost_res and cost_res[0] and cost_res[0].get('cost',0.0) else 0.0
                            else:
                                product_history = self.env['product.price.history'].search([('product_id', '=', product.id)], order='id desc', limit=1)
                                cost = product_history and product_history.cost or 0.0
                            d['qty'] += float(innerv['qty'])
                            d['cost'] = cost #float(innerv['cost'])
                            d['value'] = product.lst_price
                            d['product_category'] = innerv['product_category']
                        res.append(d)
                    fdict[key][prod] += res
            return fdict

    def _query_detail(self, obj):
        location_obj = self.env['stock.location']
        product_obj = self.env['product.product']
        Move = self.env['stock.move']
        if obj.date_selection == 'upto_date':
            if obj.stock_lot in ['with_lot']:
                where_lot_id = 'sq.lot_id is not null AND'
            elif obj.stock_lot in ['without_lot']:
                where_lot_id = 'sq.lot_id is null AND'
            else:
                where_lot_id = ''
        else:
            if obj.stock_lot in ['with_lot']:
                where_lot_id = 'sq.serial_number is not null AND'
            elif obj.stock_lot in ['without_lot']:
                where_lot_id = 'sq.serial_number is null AND'
            else:
                where_lot_id = ''
        if not obj.date:
            to_date = datetime.strftime(datetime.today(), '%Y-%m-%d')
            to_date = datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        else:
            to_date = datetime.strptime(obj.date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        if not obj.category_ids:
            new_category_ids = self.env['product.category'].search([])
            category_ids = [prod_cat_id.id for prod_cat_id in self.env['product.category'].search([])]
        else:
            new_category_ids = obj.category_ids
            category_ids = [prod_cat_id.id for prod_cat_id in obj.category_ids]
            category_ids = []
            for categ in obj.category_ids:
                category_ids += self.env['product.category'].search([('id', 'child_of', categ.id)]).ids
            category_ids = list(set(category_ids))
            new_category_ids = self.env['product.category'].browse(category_ids)
            
        partner_product_ids = []
        if obj.partner_id:
            product_suppliers = self.env['product.supplierinfo'].search([('name','=',obj.partner_id.id)])
            product_ids = []
            for product_supplier in product_suppliers:
                products = self.env['product.product'].search([('product_tmpl_id', '=', product_supplier.product_tmpl_id.id)])
                for product in products:
                    product_ids.append(product.id)
            new_product_ids = product_ids
            partner_product_ids = product_ids
        else:
            if not obj.product_ids:
                product_ids = [product.id for product in self.env['product.product'].search([('type', '=', 'product')])]
                new_product_ids = self.env['product.product'].search([('type', '=', 'product')])
            else:
                product_ids = [product.id for product in obj.product_ids]
                new_product_ids = obj.product_ids
#         if not obj.location_ids:
#             location_ids = [location.id for location in self.env['stock.location'].search([])]
#             new_location_ids = self.env['stock.location'].search([])
#         else:
#             location_ids = [location.id for location in obj.location_ids]
#             new_location_ids = obj.location_ids

        if not obj.location_ids and obj.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([('usage', '=', 'internal')])]
            new_location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        elif not obj.location_ids and not obj.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([])]
            new_location_ids = self.env['stock.location'].search([])
        else:
            location_ids = [location.id for location in obj.location_ids]
            new_location_ids = obj.location_ids

        if not obj.brand_ids:
            brand_ids = [brand.id for brand in self.env['product.brand'].search([])]
            new_brand_ids = self.env['product.brand'].search([])
        else:
            brand_ids = [brand.id for brand in obj.brand_ids]
            new_brand_ids = obj.brand_ids
        include_zero = obj.include_zero
        print"c include_zero: ",include_zero
#        print"product_ids1: ",product_ids
        if obj.view_by == 'detail':
            SQL = """ """
            if obj.date_selection == 'upto_date':
               SQL = """
                        SELECT 
                            pc.name as product_category,
                            sl.complete_name as location,
                            pt.name as product,
                            pp.default_code as item_code,
                            pp.barcode as barcode,
                            pp.id as product_id,
                            pt.name as description,
                            pb.name as brand,
                            sum(sq.qty) as qty,
                            sum(sq.cost) as cost,
                            spl.name as serial_number
                        FROM 
                            stock_quant sq
                            
                            FULL JOIN product_product pp on sq.product_id= pp.id
                            FULL JOIN product_template pt on pp.product_tmpl_id= pt.id
                            FULL JOIN product_category pc on pt.categ_id= pc.id
                            FULL JOIN stock_location sl on sq.location_id = sl.id
                            FULL JOIN product_brand pb on pt.product_brand_id = pb.id
                            FULL JOIN stock_production_lot spl on sq.lot_id = spl.id
                        WHERE 
                            pt.type = 'product' AND
                            %s
                        """  % (where_lot_id,)
            else:
                print"before On date query"
                SQL = """
                    select 
                        distinct(product_id) 
                    from 
                        stock_move
                    where
                        date<= '%s' AND
                        state !='cancel' AND
                        
                """
                
                SQL = """
                    SELECT 
                        pc.name as product_category,
                        sl.complete_name as location,
                        pt.name as product,
                        pp.default_code as item_code,
                        pp.barcode as barcode,
                        pp.id as product_id,
                        pt.name as description,
                        pb.name as brand,
                        sum(m.product_qty) as qty,
                        sum(m.price_unit) as cost,
                        '' as serial_number
                    FROM
                        stock_move m
                        FULL JOIN product_product pp on m.product_id= pp.id
                        FULL JOIN product_template pt on pp.product_tmpl_id= pt.id
                        FULL JOIN product_category pc on pt.categ_id= pc.id
                        FULL JOIN stock_location sl on (m.location_id = sl.id or m.location_dest_id=sl.id)
                        FULL JOIN product_brand pb on pt.product_brand_id = pb.id
                    WHERE 
                        m.date <= '%s' AND
                        pt.type = 'product' AND
                    """  % (to_date)
#                print"SQL 00: ",SQL
                SQL_old = """
                        SELECT 
                            pc.name as product_category,
                            sl.complete_name as location,
                            pt.name as product,
                            pp.default_code as item_code,
                            pp.barcode as barcode,
                            pp.id as product_id,
                            pt.name as description,
                            pb.name as brand,
                            sum(sq.quantity) as qty,
                            sum(sq.price_unit_on_quant) as cost,
                            sq.serial_number as serial_number
                        FROM 
                            stock_history sq
                            
                            FULL JOIN product_product pp on sq.product_id= pp.id
                            FULL JOIN product_template pt on sq.product_template_id= pt.id
                            FULL JOIN product_category pc on sq.product_categ_id= pc.id
                            FULL JOIN stock_location sl on sq.location_id = sl.id
                            FULL JOIN product_brand pb on pt.product_brand_id = pb.id
                        WHERE 
                            sq.date <= '%s' AND
                            pt.type = 'product' AND
                            %s
                        """  % (to_date,where_lot_id)
            SQL += """  pc.id in %s AND
                        sl.id in %s AND
                        pp.id in %s AND
                        (pb.id in %s or pb.id is NULL)
                        
                        GROUP BY pp.id, pc.name, sl.complete_name, pt.name, pb.name, pp.default_code
                    """ % (
                            " (%s) " % ','.join(map(str, category_ids)),
                            " (%s) " % ','.join(map(str, location_ids)),
                            " (%s) " % ','.join(map(str, product_ids)),
                            " (%s) " % ','.join(map(str, brand_ids)))
            if obj.date_selection == 'upto_date':
                SQL += ",spl.name" if obj.date_selection == 'upto_date' else ",sq.serial_number"
            SQL += " ORDER BY pt.name ASC"
#            print"SQL: ",SQL
            self._cr.execute(SQL)
            res = self._cr.dictfetchall()
#            print"ressssssssssssssssssssssss: ",res
            if res:
                used_product_ids = []
                for each in res:
                    used_product_ids.append(each['product_id'])
                used_product_ids = list(set(used_product_ids))
#                print"used_product_ids: ",used_product_ids
                
                # new stock chagnes
                
                if obj.date_selection == 'on_date':
                    domain = [('product_id', 'in', tuple(used_product_ids)),
                            ('state', '=', 'done'),
                            ('date', '<=', obj.date),
                        ]
                    domain_move_in = domain + [
                        ('location_dest_id', 'in', tuple(location_ids))
                        ]
                    domain_move_out = domain + [
                        ('location_id', 'in', tuple(location_ids))
                        ]
#                    print"domain_move_in: ",domain_move_in
                    
                    moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
                    moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
#                    print"moves_in_res len: ",len(moves_in_res)
#                    print"moves_out_res len: ",len(moves_out_res)

                    if not obj.group_by =='location':
                        ## Forecast qty
                        f_domain = [('product_id', 'in', tuple(used_product_ids)),
                                ('state', '=', 'done'),
                                ('date', '<=', obj.date)]
                        domain_move_in = domain + [
                            ('location_dest_id', 'in', tuple(location_ids))]
                        domain_move_out = domain + [
                            ('location_id', 'in', tuple(location_ids))]
                        f_moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
                        f_moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
                

                final_dict = {}
                if obj.group_by == 'category':
                    team_dict = defaultdict(list)
                    categ_ids_to_use = []
                    for category in new_category_ids:
                        product_dict = defaultdict(list)
                        for each in res:
                            if category.name == each['product_category']:
                                product_dict[each['product']].append(each)
                                categ_ids_to_use.append(category.id)

                        # add the zero qty product here in product_dict
                        if include_zero and (category.id in categ_ids_to_use):
    #                        templates = self.env['product.template'].search([('categ_id','=',category.id)])
                            templates = self.env['product.template'].search([('categ_id','=',category.id)])
                            for template in templates:
                                this_prods = product_obj.search([('product_tmpl_id','=',template.id),
                                        ('id','not in',used_product_ids)])
                                if len(this_prods):
                                    if len(partner_product_ids):
                                        if this_prods[0].id not in partner_product_ids:
                                            continue
                                    this_prod = this_prods[0].with_context({'location': location_ids, 'compute_child': False})
                                    this_prod_qty_available = this_prod.qty_available or 0.0
                                    if float(this_prod_qty_available) != 0.0:
                                        continue
                                    t_dict = {'brand':template.product_brand_id and template.product_brand_id.name or '',
                                            'barcode':this_prod.barcode,
                                            'item_code':this_prod.default_code,
                                            'qty':this_prod_qty_available,
                                            'cost':this_prod.standard_price,
            #                                'location':'Physical Location/Synergy/STORE',
                                            'location':location_ids,
                                            'serial_number':'',
                                            'product_category':category.name,
                                            'description':template.name,
                                            'product':template.name,
                                            'product_id':this_prod.id}                                
            #                        print"t_dict: ",t_dict
                                    product_dict[template.name].append(t_dict)


                        if product_dict:
                            team_dict[category.name] = dict(product_dict)
                    final_dict = dict(team_dict)
                if obj.group_by == 'location':
                    team_dict = defaultdict(list)
                    location_ids_to_use = []
                    for location in new_location_ids:
                        product_dict = defaultdict(list)
                        for each in res:
                            if location.complete_name == each['location']:
                                product_dict[each['product']].append(each)
                                location_ids_to_use.append(location.id)

                        # add the zero qty product here in product_dict
                        if include_zero and (location.id in location_ids_to_use):
                            all_products = product_obj.search(
                                    [('id','not in',used_product_ids)])
                            for a_product in all_products:
                                if len(partner_product_ids):
                                    if a_product.id not in partner_product_ids:
                                        continue
                                template = a_product.product_tmpl_id
                                if template.categ_id.id not in category_ids:
                                    continue
                                this_prod = a_product.with_context({'location': location.id, 'compute_child': False})
                                this_prod_qty_available = this_prod.qty_available or 0.0
                                if float(this_prod_qty_available) != 0.0:
                                    continue


                                t_dict = {'brand':template.product_brand_id and template.product_brand_id.name or '',
                                        'barcode':this_prod.barcode,
                                        'item_code':this_prod.default_code,
                                        'qty':this_prod_qty_available,
                                        'cost':this_prod.standard_price,
                                        'location':location.name,
                                        'serial_number':'',
                                        'product_category':template.categ_id.name,
                                        'description':template.name,
                                        'product':template.name,
                                        'product_id':this_prod.id}                                
                                product_dict[template.name].append(t_dict)

                        if product_dict:
                            team_dict[location.complete_name] = dict(product_dict)
                    final_dict = dict(team_dict)
                if obj.group_by == 'brand':
                    team_dict = defaultdict(list)
                    brand_ids_to_use = []
                    for brand in new_brand_ids:
                        product_dict = defaultdict(list)
                        for each in res:
                            if brand.name == each['brand']:
                                product_dict[each['product']].append(each)
                                brand_ids_to_use.append(brand.id)

                        # add the zero qty product here in product_dict
                        if include_zero and (brand.id in brand_ids_to_use):
                            templates = self.env['product.template'].search([
                                ('product_brand_id','=',brand.id),
                                ('categ_id','in',category_ids)])
                            if not len(templates):
                                continue
                            for template in templates:
                                this_prods = product_obj.search([
                                        ('product_tmpl_id','=',template.id),
                                        ('id','not in',used_product_ids)])
                                if not len(this_prods):
                                    continue
                                if len(this_prods):
                                    if len(partner_product_ids):
                                        if this_prods[0].id not in partner_product_ids:
                                            continue
                                    this_prod = this_prods
                                    this_prod = this_prods[0].with_context({'location': location_ids, 'compute_child': False})
                                    this_prod_qty_available = this_prod.qty_available or 0.0
                                    if float(this_prod_qty_available) != 0.0:
                                        continue
                                    t_dict = {'brand':template.product_brand_id and template.product_brand_id.name or '',
                                            'barcode':this_prod.barcode,
                                            'item_code':this_prod.default_code,
                                            'qty':this_prod_qty_available,
                                            'cost':this_prod.standard_price,
                                            'location':location_ids,
                                            'serial_number':'',
                                            'product_category':template.categ_id.name,
                                            'description':template.name,
                                            'product':template.name,
                                            'product_id':this_prod.id}                                
                                    product_dict[template.name].append(t_dict)

                        if product_dict:
                            team_dict[brand.name] = dict(product_dict)
                    final_dict = dict(team_dict)
            else:
                print"No purchase moves part"
                product_ids = [product.id for product in self.env['product.product'].search([
                        ('type', '=', 'product'),
                        ('product_tmpl_id.categ_id','in',tuple(new_category_ids.ids))
                
                    ])]
#                print"product_ids: ",product_ids

                if obj.date_selection == 'on_date':
                    domain = [('product_id', 'in', tuple(product_ids)),
                            ('state', '=', 'done'),
                            ('date', '<=', obj.date),
                        ]
                    domain_move_in = domain + [
                        ('location_dest_id', 'in', tuple(location_ids))
                        ]
                    domain_move_out = domain + [
                        ('location_id', 'in', tuple(location_ids))
                        ]
#                    print"domain_move_in: ",domain_move_in
                    
                    moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
                    moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out, ['product_id', 'product_qty'], ['product_id'], orderby='id'))

                used_product_ids = []
                final_dict = {}
                if obj.group_by == 'category':
                    team_dict = defaultdict(list)
                    categ_ids_to_use = []
                    for category in new_category_ids:
                        product_dict = defaultdict(list)

                        templates = self.env['product.template'].search([('categ_id','=',category.id)])
                        for template in templates:
                            this_prods = product_obj.search([('product_tmpl_id','=',template.id)])
                            if len(this_prods):
                                this_prod = this_prods[0].with_context({'location': location_ids, 'compute_child': False})
                                this_prod_qty_available = this_prod.qty_available or 0.0
                                if float(this_prod_qty_available) != 0.0:
                                    continue
                                t_dict = {'brand':template.product_brand_id and template.product_brand_id.name or '',
                                        'barcode':this_prod.barcode,
                                        'item_code':this_prod.default_code,
                                        'qty':this_prod_qty_available,
                                        'cost':this_prod.standard_price,
        #                                'location':'Physical Location/Synergy/STORE',
                                        'location':location_ids,
                                        'serial_number':'',
                                        'product_category':category.name,
                                        'description':template.name,
                                        'product':template.name,
                                        'product_id':this_prod.id}                                
        #                        print"t_dict: ",t_dict
                                product_dict[template.name].append(t_dict)                                



                        if product_dict:
                            team_dict[category.name] = dict(product_dict)

                    final_dict = dict(team_dict)
                if obj.group_by == 'location':
                    team_dict = defaultdict(list)
                    location_ids_to_use = []
                    for location in new_location_ids:
                        product_dict = defaultdict(list)
                        
                        for a_product in product_ids:
                            a_product = product_obj.browse(a_product)
                            template = a_product.product_tmpl_id

                            t_dict = {'brand':template.product_brand_id and template.product_brand_id.name or '',
                                    'barcode':a_product.barcode,
                                    'item_code':a_product.default_code,
                                    'qty':0,
                                    'cost':a_product.standard_price,
                                    'location':location.name,
                                    'serial_number':'',
                                    'product_category':template.categ_id.name,
                                    'description':template.name,
                                    'product':template.name,
                                    'product_id':a_product.id}                                
                            product_dict[template.name].append(t_dict)

                        if product_dict:
                            team_dict[location.complete_name] = dict(product_dict)
                    final_dict = dict(team_dict)
                if obj.group_by == 'brand':
                    team_dict = defaultdict(list)
                    brand_ids_to_use = []
                    for brand in new_brand_ids:
                        product_dict = defaultdict(list)

                        # add the zero qty product here in product_dict
                        templates = self.env['product.template'].search([
                            ('product_brand_id','=',brand.id)])
                        if not len(templates):
                            continue
                        for template in templates:
                            this_prods = product_obj.search([
                                    ('product_tmpl_id','=',template.id)])
                            if not len(this_prods):
                                continue
                            if len(this_prods):
                                this_prod = this_prods
                                t_dict = {'brand':template.product_brand_id and template.product_brand_id.name or '',
                                        'barcode':this_prod.barcode,
                                        'item_code':this_prod.default_code,
                                        'qty':0,
                                        'cost':this_prod.standard_price,
                                        'location':location_ids,
                                        'serial_number':'',
                                        'product_category':template.categ_id.name,
                                        'description':template.name,
                                        'product':template.name,
                                        'product_id':this_prod.id}                                
                                product_dict[template.name].append(t_dict)

                        if product_dict:
                            team_dict[brand.name] = dict(product_dict)
                    final_dict = dict(team_dict)
                            
#            print"final_dict: ",final_dict
            ###### custom changes
            g_location = obj.location_ids.ids or []
            if len(g_location):
                location_ids = g_location
            ##### custom changes 
            fdict = {}
            for key,value in final_dict.items():
                if key not in fdict:
                    fdict.update({key: {}})
                for prod,prodval in value.items():
                    res = []
                    if prod not in fdict[key]:
                        fdict[key].update({prod: []})
#                    print"prodval: ",prodval
                    for k,v in groupby(prodval, key=lambda x:x['product']):
                        d = {'product':k, 'value': 0, 'qty': 0, 'cost': 0}
                        for innerv in v:
                            
                            product = product_obj.search([('id', '=', innerv['product_id'])])
                            if obj.date_selection == 'on_date':
                                
                                SQL = """SELECT cost from product_price_history 
                                    where product_id = %s AND
                                    datetime <= '%s' order by id desc limit 1
                                """  % (product.id, to_date)
                                
                                SQL_old = """SELECT avg(cost) as cost from product_price_history 
                                    where product_id = %s AND
                                    datetime <= '%s' group by product_id
                                """  % (product.id, to_date)
                                self._cr.execute(SQL)
                                cost_res = self._cr.dictfetchall()
                                cost = cost_res[0].get('cost',0.0) if cost_res and cost_res[0] and cost_res[0].get('cost',0.0) else 0.0
                            else:
                                product_history = self.env['product.price.history'].search([('product_id', '=', product.id)], order='id desc', limit=1)
                                cost = product_history and product_history.cost or 0.0
                                
                            if obj.date_selection == 'upto_date':
                                
                                stock = float(innerv['qty'])
                                if obj.group_by == 'location':
                                    this_locations = location_obj.search([('complete_name','=',key)])
                                    if this_locations:
                                        product_virtual_available = product.with_context({'location': this_locations.ids, 'compute_child': False})
                                    else:
                                        product_virtual_available = product.with_context({'location': location_ids, 'compute_child': False})
                                else:
                                    product_virtual_available = product.with_context({'location': location_ids, 'compute_child': False})
                                virtual_available  = float(product_virtual_available.virtual_available_inv)
                                carton = float(innerv['qty'])
                                if product.uom_po_id.uom_type == 'bigger':
                                    carton = virtual_available / product.uom_po_id.factor_inv
                                if product.uom_po_id.uom_type == 'smaller':
                                    carton = virtual_available * product.uom_po_id.factor_inv
                                    
                                d['qty'] += float(innerv['qty'])
                            else: # On date report
                                # taking qty for each location seperately
                                if obj.group_by == 'location':
                                    this_locations = location_obj.search([('complete_name','=',key)])
                                    if this_locations:
                                        domain = [('product_id', 'in', tuple([product.id])),
                                                ('state', '=', 'done'),
                                                ('date', '<=', obj.date)
                                            ]
                                        domain_move_in = domain + [
                                            ('location_dest_id', 'in', tuple(this_locations.ids))
                                            ]
                                        domain_move_out = domain + [
                                            ('location_id', 'in', tuple(this_locations.ids))
                                            ]
                                        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
                                        moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
                                        
                                        ## Forecast qty
                                        f_domain = [('product_id', 'in', tuple([product.id])),
                                                ('state', '!=', 'cancel'),
                                                ('date', '<=', obj.date)
                                            ]
                                        domain_move_in = f_domain + [
                                            ('location_dest_id', 'in', tuple(this_locations.ids))
                                            ]
                                        domain_move_out = domain + [
                                            ('location_id', 'in', tuple(this_locations.ids))
                                            ]
                                        f_moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
                                        f_moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
                                    
                                    
                                in_qty = float_round(moves_in_res.get(product.id, 0.0), precision_rounding=product.uom_id.rounding)
                                out_qty = float_round(moves_out_res.get(product.id, 0.0), precision_rounding=product.uom_id.rounding)
                                stock = round((in_qty - out_qty))
                                
                                f_in_qty = float_round(f_moves_in_res.get(product.id, 0.0), precision_rounding=product.uom_id.rounding)
                                f_out_qty = float_round(f_moves_out_res.get(product.id, 0.0), precision_rounding=product.uom_id.rounding)
                                virtual_available = round((f_in_qty - f_out_qty))
                                
                                carton = virtual_available
                                if product.uom_po_id.uom_type == 'bigger':
                                    carton = virtual_available / product.uom_po_id.factor_inv
                                if product.uom_po_id.uom_type == 'smaller':
                                    carton = virtual_available * product.uom_po_id.factor_inv
                                d['qty'] = stock
                                
                                
#                            d['qty'] += float(innerv['qty'])
                            d['virtual_available'] = virtual_available
                            d['carton'] = carton
                            d['cost'] = cost #float(innerv['cost'])
                            d['value'] = product.lst_price
                            d['description'] = innerv['description']
                            d['product_category'] = innerv['product_category']
                            d['item_code'] = innerv['item_code']
                            d['barcode'] = innerv['barcode']
                            d['serial_number'] = innerv['serial_number']
                        res.append(d)
#                    print"res: ",res
                    fdict[key][prod] += res
                    
                    
            ## sorting it by product
            keys = fdict.keys()
            final_dict = {}
            for key in fdict.keys():
                res = fdict.get(key)
                t = OrderedDict(sorted(res.items()))
                final_dict[key]=t
                
#            fdict
#            return fdict
#            print"final_dict: ",final_dict
            return final_dict
