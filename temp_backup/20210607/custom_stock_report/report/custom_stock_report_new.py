from odoo import api, models, _
from datetime import datetime
from collections import defaultdict
from odoo.exceptions import ValidationError
from itertools import groupby


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
                                SQL = """SELECT avg(cost) as cost from product_price_history 
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
#             if obj.date_selection == 'upto_date':
#                 SQL = """
#                     SELECT 
#                         %s as product_category,
#                         sum(sq.qty) as qty,
#                         avg(sq.cost) as cost,
#                         sum(sq.qty * sq.cost) as value
#                     FROM 
#                         stock_quant sq
#                         
#                         FULL JOIN product_product pp on sq.product_id= pp.id
#                         FULL JOIN product_template pt on pp.product_tmpl_id= pt.id
#                         FULL JOIN product_category pc on pt.categ_id= pc.id
#                         FULL JOIN stock_location sl on sq.location_id = sl.id
#                         FULL JOIN product_brand pb on pt.product_brand_id = pb.id
#                     WHERE 
#                         sq.in_date <= '%s' AND
#                         pt.type = 'product' AND
#                     """  % (group_name,
#                            to_date)
#             else:
#                 SQL = """
#                     SELECT 
#                         %s as product_category,
#                         sum(sq.quantity) as qty,
#                         avg(sq.price_unit_on_quant) as cost,
#                         sum(sq.quantity) * sum(sq.price_unit_on_quant) as value
#                     FROM 
#                         stock_history sq
#                         
#                         FULL JOIN product_product pp on sq.product_id= pp.id
#                         FULL JOIN product_template pt on sq.product_template_id= pt.id
#                         FULL JOIN product_category pc on sq.product_categ_id= pc.id
#                         FULL JOIN stock_location sl on sq.location_id = sl.id
#                         FULL JOIN product_brand pb on pt.product_brand_id = pb.id
#                     WHERE 
#                         sq.date <= '%s' AND
#                         pt.type = 'product' AND
#                     """  % (group_name,
#                            to_date) 
#             SQL +=    """   
#                     pc.id in %s AND
#                     sl.id in %s AND
#                     pp.id in %s AND
#                     (pb.id in %s or pb.id is NULL)
#                 """ % (
#                        " (%s) " % ','.join(map(str, category_ids)),
#                        " (%s) " % ','.join(map(str, location_ids)),
#                        " (%s) " % ','.join(map(str, product_ids)),
#                        " (%s) " % ','.join(map(str, brand_ids)))
#             SQL += ' GROUP BY %s.id' %(group)
#             self._cr.execute(SQL)
#             res = self._cr.dictfetchall()
#             return res

    def _query_detail(self, obj):
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
        print"to_date: ",to_date
        if not obj.category_ids:
            new_category_ids = self.env['product.category'].search([])
            category_ids = [prod_cat_id.id for prod_cat_id in self.env['product.category'].search([])]
        else:
            new_category_ids = obj.category_ids
            category_ids = [prod_cat_id.id for prod_cat_id in obj.category_ids]
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
        print"include_zero: ",include_zero
#        print"product_ids1: ",product_ids
        if obj.view_by == 'detail':
            SQL = """ """
            if obj.date_selection == 'upto_date':
                ## upto date query
#                            JOIN
#                                stock_quant_move_rel ON stock_quant_move_rel.quant_id = sq.id
#                            JOIN
#                                stock_move ON stock_move.id = stock_quant_move_rel.move_id                
               SQL_new = """
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
                            
                            JOIN
                                stock_quant_move_rel ON stock_quant_move_rel.quant_id = sq.id
                            JOIN
                                stock_move ON stock_move.id = stock_quant_move_rel.move_id
                            JOIN
                                stock_location source_location ON stock_move.location_id = source_location.id
                            
                    
                        WHERE 
                            stock_move.date <= '%s' AND
                            stock_move.state='done' AND
                            sq.qty>0 AND
                            pt.type = 'product' AND
                            %s
                        """  % (to_date,where_lot_id)
                        
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
                            sq.in_date <= '%s' AND
                            pt.type = 'product' AND
                            %s
                        """  % (to_date,where_lot_id)                        
            else:
                print"as on date query called"
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
            SQL += ",spl.name" if obj.date_selection == 'upto_date' else ",sq.serial_number"
            SQL += " ORDER BY pt.name ASC"
#            print"sqll: ",SQL
#            SQL += " ORDER BY pp.name ASC"
#             SQL = """SELECT pc.name as product_category, 
#                     sl.complete_name as location,
#                     pt.name as product,
#                     sq.price_unit_on_quant as cost,
#                     rp.name as partner,
#                     pb.name as brand,
#                     sq.quantity as qty,
#                     sq.quantity * sq.price_unit_on_quant as value,
#                     pp.default_code as item_code,
#                     pt.name as description
#                     FROM stock_history sq
#                     LEFT JOIN product_category pc on sq.product_categ_id= pc.id
#                     LEFT JOIN product_product pp on sq.product_id= pp.id
#                     LEFT JOIN product_template pt on pp.product_tmpl_id= pt.id
#                     LEFT JOIN stock_location sl on sq.location_id = sl.id
#                     LEFT JOIN stock_move sm on sq.move_id = sm.id
#                     LEFT JOIN stock_picking sp on sm.picking_id = sp.id
#                     LEFT JOIN res_partner rp on sp.partner_id= rp.id
#                     LEFT JOIN product_brand pb on pt.product_brand_id = pb.id
#                     WHERE sm.date <= '%s' AND
#                     pc.id in %s AND
#                     sl.id in %s AND
#                     pp.id in %s AND
#                     (pb.id in %s or pb.id is NULL)
#                     """ % (
#                 to_date, " (%s) " % ','.join(map(str, category_ids)),
#                 " (%s) " % ','.join(map(str, location_ids)),
#                 " (%s) " % ','.join(map(str, product_ids)),
#                 " (%s) " % ','.join(map(str, brand_ids)))
            self._cr.execute(SQL)
            res = self._cr.dictfetchall()
            print"query res: ",res
            
            used_product_ids = []
            for each in res:
                used_product_ids.append(each['product_id'])

            
#            print"res: ",res
            final_dict = {}
            if obj.group_by == 'category':
                team_dict = defaultdict(list)
                categ_ids_to_use = []
                for category in new_category_ids:
                    product_dict = defaultdict(list)
                    for each in res:
                        print"each: ",each
                        if category.name == each['product_category']:
                            product_dict[each['product']].append(each)
                            categ_ids_to_use.append(category.id)
                    
                    # add the zero qty product here in product_dict
                    if include_zero and (category.id in categ_ids_to_use):
#                        templates = self.env['product.template'].search([('categ_id','=',category.id)])
                        templates = self.env['product.template'].search([('categ_id','=',category.id)])
                        for template in templates:
                            this_prods = self.env['product.product'].search([('product_tmpl_id','=',template.id),
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
                        all_products = self.env['product.product'].search(
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
                            this_prods = self.env['product.product'].search([
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
#            print"final_dict: ",final_dict
            fdict = {}
            for key,value in final_dict.items():
                if key not in fdict:
                    fdict.update({key: {}})
                print"fdict[key]: ",fdict[key]
                for prod,prodval in value.items():
                    print"prod: ",prod
                    res = []
                    if prod not in fdict[key]:
                        fdict[key].update({prod: []})
                    for k,v in groupby(prodval, key=lambda x:x['product']):
                        d = {'product':k, 'value': 0, 'qty': 0, 'cost': 0}
                        for innerv in v:
                            product = self.env['product.product'].search([('id', '=', innerv['product_id'])])
                            if obj.date_selection == 'on_date':
                                print"yesssssssssssssss! "
                                SQL = """SELECT avg(cost) as cost from product_price_history 
                                    where product_id = %s AND
                                    datetime <= '%s' group by product_id
                                """  % (product.id, to_date)
#                                print"yes SQL: ",SQL
                                self._cr.execute(SQL)
                                cost_res = self._cr.dictfetchall()
                                print"cost_res: ",cost_res
                                cost = cost_res[0].get('cost',0.0) if cost_res and cost_res[0] and cost_res[0].get('cost',0.0) else 0.0
                                
                                
                                SQL_updated = """SELECT cost from product_price_history 
                                    where product_id = %s AND
                                    datetime <= '%s' order by id desc limit 1
                                """  % (product.id, to_date)
                                
                            else:
                                product_history = self.env['product.price.history'].search([('product_id', '=', product.id)], order='id desc', limit=1)
#                                product_history = self.env['product.price.history'].search([('product_id', '=', product.id)], order='datetime desc, id desc', limit=1)
                                cost = product_history and product_history.cost or 0.0
                                print"cost: ",cost
                                if product.id == 4457:
                                    print"dddd: ",d
                                    print("yesssssssssssssssssssssssssssssssssssssssssssss")
                                
                            product_virtual_available = product.with_context({'location': location_ids, 'compute_child': False})
                            virtual_available  = float(product_virtual_available.virtual_available_inv)
#                            virtual_available  = float(product_virtual_available.virtual_available)
#                            carton = float(innerv['qty'])
#                            if product.uom_po_id.uom_type == 'bigger':
#                                carton = virtual_available / product.uom_po_id.factor_inv
#                            if product.uom_po_id.uom_type == 'smaller':
#                                carton = virtual_available * product.uom_po_id.factor_inv
#                                
                            d['qty'] += float(innerv['qty'])
                            d['virtual_available'] = virtual_available
#                            d['carton'] = carton
                            d['cost'] = cost #float(innerv['cost'])
                            d['value'] = product.lst_price
                            d['description'] = innerv['description']
                            d['product_category'] = innerv['product_category']
                            d['item_code'] = innerv['item_code']
                            d['barcode'] = innerv['barcode']
                            d['serial_number'] = innerv['serial_number']
                        res.append(d)
                        print"append : ",res
#                    print"res: ",res
                    fdict[key][prod] += res
#            print"fdict: ",fdict
            return fdict
