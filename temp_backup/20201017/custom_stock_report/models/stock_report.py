import base64
import xlwt
import cStringIO
from odoo import fields, models, api, _
from collections import defaultdict
from datetime import datetime, date
from odoo.exceptions import ValidationError

import time
from base64 import b64decode
import csv
import base64
import cStringIO
import StringIO

class stock_location(models.Model):
    _inherit = 'stock.location'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('physical_loc'):
            loc_ids = self.search([('usage', '=', 'internal')])
            if name:
                loc_ids = self.search([('usage', '=', 'internal'), ('name', operator, name)] + args)
            return loc_ids.name_get()
        return super(stock_location, self).name_search(name, args)


class StockReport(models.TransientModel):
    _name = 'stock.report'

    product_ids = fields.Many2many('product.product', string="Product")
    category_ids = fields.Many2many('product.category', string="Category")
    date = fields.Date(string="Date")
    internal_location = fields.Boolean(string="Physical Location", default=True)
    date_selection = fields.Selection([('on_date', 'On Date'), ('upto_date', 'Upto Date')],
                                      string="Based on")
    group_by = fields.Selection(
        [('category', 'Category'), ('location', 'Location'), ('brand', 'Brand')],
        string="Group By")
    location_ids = fields.Many2many('stock.location', string="Location")
    view_by = fields.Selection([('detail', 'Detail'), ('summary', 'Summary')],
                               string="View By")
    data = fields.Binary(string="Data")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char(string='File Name', readonly=True)
    brand_ids = fields.Many2many('product.brand', string="Brand")
    price_selection = fields.Selection(
        [('show_price', 'Show Price'), ('show_cost', 'Show Cost'), ('both', 'Show Price and Cost')],
        string="Price Selection", default="both", required=False)
    stock_lot = fields.Selection([('all_lot', 'All'), ('with_lot', 'With Lot'),
                                  ('without_lot', 'Without Lot')], string="Stock Lot", default="all_lot", required=True)
    partner_id = fields.Many2one('res.partner', string='Vendor')
    include_zero = fields.Boolean(string="Include Zero",help='shows the products having zero or negative qty as well.')
    
    @api.multi
    def temp_get_move_and_quant_stock_report(self):
        output = StringIO.StringIO()
        output.write('"Product","Location","Quants stock","Moves stock"')
        output.write("\n")

        product_obj = self.env['product.product']
        all_products = product_obj.search([('active','=',True)])
#        all_products = product_obj.search([('id','=',1097)])
#        all_products = product_obj.search([('id','=',1816)])
        all_locations = self.env['stock.location'].search([('usage','=','internal')])
        all_locations = self.env['stock.location'].search([('id','=',15)])
        print'all_locations: ',all_locations
        
        Move = self.env['stock.move']
        for product in all_products:
            try:
                for location in all_locations:
                    print"location: ",location
                    product = product.with_context({'location': location.id,
                        'compute_child': False})
                    quants_qty = product.qty_available
                    print"quants_qty: ",quants_qty
                    
                    
                    self._cr.execute("select id from stock_move where "\
                        "product_id=%s and state='done' and (location_id=%s or location_dest_id=%s)"\
                        ,(product.id,location.id,location.id))
                    move_res = self._cr.fetchall()
                    in_qty,out_qty = 0.0, 0.0
                    if move_res:
                        move_ids = [r[0] for r in move_res]
                        if len(move_ids):
                            for move in Move.browse(move_ids):
#                                if not move.picking_id:
#                                    continue
#                                picking_type_id = move.picking_id and move.picking_id.picking_type_id or False
#                                if not picking_type_id:
#                                    continue
#                                if picking_type_id and picking_type_id.code != 'internal':
#                                    continue

                                qty = move.product_uom_qty

                                if move.product_uom.uom_type == 'bigger':
                                    qty = qty * move.product_uom.factor_inv
                                if move.product_uom.uom_type == 'smaller':
                                    qty = qty / move.product_uom.factor_inv

                                if (move.location_id.id != location.id) and (move.location_dest_id.id == location.id):
                                    in_qty+=qty
                                if (move.location_dest_id.id != location.id) and (move.location_id.id == location.id):
                                    out_qty+=qty
                    print"in_qty: ",in_qty
                    print"out_qty: ",out_qty
#                    stop
                    moves_qty = in_qty - out_qty
                    print"moves_qty: ",moves_qty
                    if quants_qty == moves_qty:
                        print"equal qty continue"
                        continue

                    output.write('"%s","%s","%s","%s"' % (product.name, location.name, quants_qty, moves_qty))
                    output.write("\n")
                    print "mis/export_location_stock () exported"
            except Exception, e:
                print "mis/export_location_stock() Exception: ",str(e)
                continue
            print "mis/export_location_stock () End product: ",product.id

        today = time.strftime('%Y-%m-%d %H:%M:%S')
        out=base64.encodestring(output.getvalue())
        self.write({'data':out,'state':'get','name':'Export_'+today+'.csv'})
        return {
            'name': 'Stock Report',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }
    
    @api.multi
    def temp_delete_extra_quants(self):
        print"temp_delete_extra_quants called"
        
#        update the date for IN quants made from inventory adjustment
#        inventory = self.env['stock.inventory'].search([('name','=','OP-31-12-2019')])
        inventory = self.env['stock.inventory'].search([('name','=','Test6 product')])
        for i in inventory:
            i_date = i.date
            i_location_id = i.location_id.id
            for move in i.move_ids:
                quants = move.quant_ids
                print"quants: ",quants
                for quant in quants:
                    location_id = quant.location_id and quant.location_id.id or False
                    print"location_id: ",location_id
                    if location_id:
                        if location_id == i_location_id:
                            quant.write({'in_date':i_date})
                            print"quant date udpated: ",quant.id
        
#        move_ids = []
#        moves = self.env['stock.move'].search([])
#        for move in moves:
#            move_ids.append(move.id)
#        self._cr.execute("select move_id,quant_id from stock_quant_move_rel")
#        res = self._cr.dictfetchall()
##        print"res: ",res
#        delete_quant_ids =  []
#        for d in res:
#            move_id = d.get('move_id')
#            quant_id = d.get('quant_id')
##            print"move_id: ",move_id
##            print"quant_id: ",quant_id
#            if move_id not in move_ids:
#                delete_quant_ids.appen(quant_id)
#                
#        print"delete_quant_ids: ",delete_quant_ids
#        
#        delete_quant_ids = []
#        
#        all_operations = self.env['stock.move.operation.link'].search([])
#        for o in all_operations:
#            if o.move_id.id not in move_ids:
#                delete_quant_ids.append(o.reserved_quant_id.id)
#        print"delete_quant_ids: ",delete_quant_ids
        
        print"temp_delete_extra_quants exit"
        return True

    @api.multi
    def temp_update_cost_in_lines(self):
        print"temp_update_cost_in_lines called"
        
        self._cr.execute("""SELECT l.id FROM account_invoice i, account_invoice_line l 
            WHERE i.id=l.invoice_id AND i.state!='cancel'""")
        query_res = self._cr.fetchall()
        if len(query_res):
            line_ids = [x[0] for x in query_res]
            line_ids = list(set(line_ids))
            print"line_ids: ",line_ids
            lines = self.env['account.invoice.line'].browse(line_ids)
            for line in lines:
                line.write({'cost_price':line.product_id.standard_price})
                
                invoice = line.invoice_id
                total_cost = sum((l.cost_price * (l.quantity+l.free_qty)) for l in invoice.invoice_line_ids)
                invoice.write({'total_cost':total_cost})
                print"cost updated"
            
        print"temp_update_cost_in_lines exit"
        return True

    @api.multi
    def generate_stock_report(self):
        datas = {
            'id': self.id,
        }
        
        if self.partner_id:
            product_suppliers = self.env['product.supplierinfo'].search([('name','=',self.partner_id.id)])
            if not product_suppliers:
                raise ValidationError(_('No product found for this supplier!'))        
            
        return self.env['report'].get_action([], 'custom_stock_report.custom_stock_report_template', data=datas)

    @api.multi
    def generate_stock_report_xlsx(self):
        company_id = self.env['res.users'].browse([self._uid]).company_id
        '''
        based on the sql query write data in Xls file
        '''
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
        stylePC.font = fontP
        stylePC.alignment = alignment
        styleBorder.font = fontP
        styleBorder.alignment = alignment
        styleBorder.borders = borders
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet("Stock Report")
        name = company_id.name if company_id.name else ''
        worksheet.write_merge(0, 4, 0, 5, name, style=stylePC)
        worksheet.write_merge(6, 6, 0, 5, "Stock Report", style=stylePC)
        worksheet.write_merge(7, 7, 0, 5, self.view_by.title() + " View", style=stylePC)
        date_sel = 'On Date' if self.date_selection == 'on_date' else 'Upto Date'
        worksheet.write_merge(9, 9, 0, 1, 'Based on : ' + date_sel, style=stylePC)
        if self.date:
            new_date = datetime.strptime(self.date, "%Y-%m-%d").strftime('%d-%m-%Y')

            worksheet.write_merge(9, 9, 2, 3, 'Date : ' + new_date, style=stylePC)
        else:
            worksheet.write_merge(9, 9, 2, 3, 'Date : ' + str(datetime.strftime(datetime.today(), '%d-%m-%Y')),
                                  style=stylePC)
        if self.view_by == 'detail':
            if self.stock_lot == 'without_lot':
                stock_lot = 'Without Lot'
            elif self.stock_lot == 'with_lot':
                stock_lot = 'With Lot'
            else:
                stock_lot = 'All'
            worksheet.write_merge(9, 9, 4, 6, 'Stock Lot : ' + stock_lot, style=stylePC)
        grp_by = ('Category') if self.group_by == 'category' \
            else ('Location') if self.group_by == 'location' \
            else ('Brand') if self.group_by == 'brand' else '-'
        worksheet.write_merge(10, 10, 0, 4, 'Group by : ' + grp_by, style=stylePC)

        if not self.brand_ids:
            b_ids = 'All Brands'
        else:
            b_ids = ', '.join(map(lambda x: (x.name), self.brand_ids))
        worksheet.write_merge(11, 11, 0, 4, 'Brand : ' + b_ids, style=stylePC)

        if not self.category_ids:
            categ_ids = 'All Categories'
        else:
            categ_ids = ', '.join(map(lambda x: (x.name), self.category_ids))
        worksheet.write_merge(12, 12, 0, 5, 'Category : ' + categ_ids, style=stylePC)

        if not self.location_ids:
            if self.internal_location == True:
                loc_ids = 'All Physical Locations'
            else:
                loc_ids = "All Locations"
        else:
            loc_ids = ', '.join(map(lambda x: (x.name), self.location_ids))
        worksheet.write_merge(13, 13, 0, 5, 'Location : ' + loc_ids, style=stylePC)

        if self.view_by == 'detail':
            rows = 15
            final_qty_total = 0
            final_cost_total = 0
            final_value_total = 0
            final_total_value = 0
            final_total_cost = 0
            data = self._query_detail()
            worksheet.col(1).width = 5000
            categ_row = rows + 1
            i = 0
            if self.stock_lot != "without_lot":
                i = 1
            for key, value in data.items():
                qty_total = 0
                cost_total = 0
                value_total = 0
                total_cost_total = 0
                total_value_total = 0
                worksheet.write_merge(categ_row, categ_row, 0, 5, grp_by + ': ' + key, style=stylePC)
                categ_row += 1
                worksheet.write_merge(categ_row, categ_row, 0, 0, 'Item Code', style=stylePC)
                worksheet.write_merge(categ_row, categ_row, 1, 1, 'Barcode', style=stylePC)
                worksheet.write_merge(categ_row, categ_row, 2, 2, 'Description', style=stylePC)
                worksheet.write_merge(categ_row, categ_row, 3, 3, 'Category', style=stylePC)
                if self.stock_lot != "without_lot":
                    worksheet.write_merge(categ_row, categ_row, 4, 4, 'Serial No.', style=stylePC)
                worksheet.write_merge(categ_row, categ_row, 4 + i, 4 + i, 'Qty.', style=stylePC)
                if self.price_selection == 'both':
                    worksheet.write_merge(categ_row, categ_row, 5 + i, 5 + i, 'Cost', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 6 + i, 6 + i, 'Total Cost', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 7 + i, 7 + i, 'Public Price', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 8 + i, 8 + i, 'Total Value', style=stylePC)
                elif self.price_selection == 'show_price':
                    worksheet.write_merge(categ_row, categ_row, 5 + i, 5 + i, 'Public Price', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 6 + i, 6 + i, 'Total Value', style=stylePC)
                elif self.price_selection == 'show_cost':
                    worksheet.write_merge(categ_row, categ_row, 5 + i, 5 + i, 'Cost', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 6 + i, 6 + i, 'Total Cost', style=stylePC)
                for k, v in value.items():
                    categ_row += 1
                    for each_value in v:
                        product_dict = {}
                        product = self.env['product.product'].search([('id', '=', each_value['product_id'])])
                        qty_sum = sum(q['qty'] for q in v)
                        if self.date and self.date_selection == 'on_date':
                            to_date = datetime.strptime(self.date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                            SQL = """SELECT avg(cost) as cost from product_price_history 
                                where product_id = %s AND
                                datetime <= '%s' group by product_id
                            """ % (product.id, to_date)
                            self._cr.execute(SQL)
                            cost_res = self._cr.dictfetchall()
                            cost_sum = cost_res[0].get('cost') if cost_res and cost_res[0] and cost_res[0].get(
                                'cost') else 0.0
                        else:
                            product_history = self.env['product.price.history'].search(
                                [('product_id', '=', product.id)], order='id desc', limit=1)
                            cost_sum = product_history and product_history.cost or 0.0

                        value_sum = float(product.lst_price)  # sum(val['value'] for val in v)
                        product_dict = {'product': k,
                                        'description': each_value['description'],
                                        'product_category': each_value['product_category'],
                                        'item_code': each_value['item_code'],
                                        'barcode': each_value['barcode'],
                                        'qty': qty_sum,
                                        'cost': cost_sum,
                                        'cost_total': cost_sum * qty_sum,
                                        'value': value_sum,
                                        'value_total': value_sum * qty_sum,
                                        'serial_number': each_value['serial_number']
                                        }
                    if each_value['product'] == k:

                        worksheet.write_merge(categ_row, categ_row, 0, 0, product_dict['item_code'])
                        worksheet.write_merge(categ_row, categ_row, 1, 1, product_dict['barcode'])
                        worksheet.write_merge(categ_row, categ_row, 2, 2, product_dict['product'])
                        worksheet.write_merge(categ_row, categ_row, 3, 3, product_dict['product_category'])
                        if self.stock_lot != "without_lot":
                            worksheet.write_merge(categ_row, categ_row, 4, 4, product_dict['serial_number'])
                        worksheet.write_merge(categ_row, categ_row, 4 + i, 4 + i, product_dict['qty'])
                        if self.price_selection == 'both':
                            worksheet.write_merge(categ_row, categ_row, 5 + i, 5 + i, '%.3f' % product_dict['cost'])
                            worksheet.write_merge(categ_row, categ_row, 6 + i, 6 + i,
                                                  '%.3f' % product_dict['cost_total'])
                            worksheet.write_merge(categ_row, categ_row, 7 + i, 7 + i, '%.3f' % product_dict['value'])
                            worksheet.write_merge(categ_row, categ_row, 8 + i, 8 + i,
                                                  '%.3f' % product_dict['value_total'])
                        elif self.price_selection == 'show_price':
                            worksheet.write_merge(categ_row, categ_row, 5 + i, 5 + i, '%.3f' % product_dict['value'])
                            worksheet.write_merge(categ_row, categ_row, 6 + i, 6 + i,
                                                  '%.3f' % product_dict['value_total'])
                        elif self.price_selection == 'show_cost':
                            worksheet.write_merge(categ_row, categ_row, 5 + i, 5 + i, '%.3f' % product_dict['cost'])
                            worksheet.write_merge(categ_row, categ_row, 6 + i, 6 + i,
                                                  '%.3f' % product_dict['cost_total'])
                        qty_total += product_dict['qty']
                        cost_total += product_dict['cost']
                        total_cost_total += product_dict['cost_total']
                        value_total += product_dict['value']
                        total_value_total += product_dict['value_total']
                final_cost_total += cost_total
                final_value_total += value_total
                final_qty_total += qty_total
                final_total_cost += total_cost_total
                final_total_value += total_value_total
                worksheet.write(categ_row + 1, 3 + i, 'Total', style=stylePC)
                worksheet.write(categ_row + 1, 4 + i, qty_total, style=styleBorder)
                if self.price_selection == 'show_cost':
                    #                     worksheet.write(categ_row + 1, 5+i, '%.3f' %cost_total, style=styleBorder)
                    worksheet.write(categ_row + 1, 6 + i, '%.3f' % total_cost_total, style=styleBorder)
                if self.price_selection == 'both':
                    #                     worksheet.write(categ_row + 1, 5+i, '%.3f' %cost_total, style=styleBorder)
                    worksheet.write(categ_row + 1, 6 + i, '%.3f' % total_cost_total, style=styleBorder)
                    #                     worksheet.write(categ_row + 1, 7+i, '%.3f' %value_total, style=styleBorder)
                    worksheet.write(categ_row + 1, 8 + i, '%.3f' % total_value_total, style=styleBorder)
                if self.price_selection == 'show_price':
                    #                     worksheet.write(categ_row + 1, 5+i, '%.3f' %value_total, style=styleBorder)
                    worksheet.write(categ_row + 1, 6 + i, '%.3f' % total_value_total, style=styleBorder)
                categ_row += 2
            worksheet.write(categ_row + 1, 3 + i, 'Grand Total', style=stylePC)
            worksheet.write(categ_row + 1, 4 + i, final_qty_total, style=styleBorder)
            if self.price_selection == 'show_cost':
                #                 worksheet.write(categ_row + 1, 5+i, '%.3f' %final_cost_total, style=styleBorder)
                worksheet.write(categ_row + 1, 6 + i, '%.3f' % final_total_cost, style=styleBorder)
            if self.price_selection == 'both':
                #                 worksheet.write(categ_row + 1, 5+i, '%.3f' %final_cost_total, style=styleBorder)
                worksheet.write(categ_row + 1, 6 + i, '%.3f' % final_total_cost, style=styleBorder)
                #                 worksheet.write(categ_row + 1, 7+i, '%.3f' %final_value_total, style=styleBorder)
                worksheet.write(categ_row + 1, 8 + i, '%.3f' % final_total_value, style=styleBorder)
            if self.price_selection == 'show_price':
                worksheet.write(categ_row + 1, 4 + i, '%.3f' % final_value_total, style=styleBorder)
        #                 worksheet.write(categ_row + 1, 5+i, '%.3f' %final_total_value, style=styleBorder)
        if self.view_by == 'summary':
            i = 0
            worksheet.write(15, 0, grp_by, style=stylePC)
            worksheet.write(15, 1, 'Qty', style=stylePC)
            #             worksheet.write(15, 2, 'Cost', style=stylePC)
            worksheet.write(15, 2, 'Value', style=stylePC)
            rows = 17
            qty_total = 0
            cost_total = 0
            value_total = 0
            worksheet.col(0).width = 4500
            if self.group_by == 'location':
                worksheet.col(0).width = 10000
            data = self._query_summary()
            categ_row = 14
            total_cost_total = 0.0
            final_total_cost, final_qty_total, final_cost_total = 0.0, 0.0, 0.0
            final_qty_total = 0
            final_cost_total = 0
            final_value_total = 0
            final_total_value = 0
            final_total_cost = 0
            categ_d = {}
            for key, value in data.items():
                qty_total = 0
                cost_total = 0
                value_total = 0
                total_cost_total = 0
                total_value_total = 0
                categ_row += 1
                for k, v in value.items():
                    #                     categ_row += 1
                    for each_value in v:
                        product_dict = {}
                        product = self.env['product.product'].search([('id', '=', each_value['product_id'])])
                        qty_sum = sum(q['qty'] for q in v)
                        if self.date and self.date_selection == 'on_date':
                            to_date = datetime.strptime(self.date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                            SQL = """SELECT avg(cost) as cost from product_price_history 
                                where product_id = %s AND
                                datetime <= '%s' group by product_id
                            """ % (product.id, to_date)
                            self._cr.execute(SQL)
                            cost_res = self._cr.dictfetchall()
                            cost_sum = cost_res[0].get('cost') if cost_res and cost_res[0] and cost_res[0].get(
                                'cost') else 0.0
                        else:
                            product_history = self.env['product.price.history'].search(
                                [('product_id', '=', product.id)], order='id desc', limit=1)
                            cost_sum = product_history and product_history.cost or 0.0

                        value_sum = float(product.lst_price)  # sum(val['value'] for val in v)
                        product_dict = {'product': k,
                                        'description': each_value['description'],
                                        'product_category': each_value['product_category'],
                                        'item_code': each_value['item_code'],
                                        'barcode': each_value['barcode'],
                                        'qty': qty_sum,
                                        'cost': cost_sum,
                                        'cost_total': cost_sum * qty_sum,
                                        'value': value_sum,
                                        'value_total': value_sum * qty_sum,
                                        }
                    if each_value['product'] == k:
                        qty_total += product_dict['qty']
                        cost_total += product_dict['cost']
                        total_cost_total += product_dict['cost_total']
                        value_total += product_dict['value']
                        total_value_total += product_dict['value_total']
                final_cost_total += cost_total
                final_value_total += value_total
                final_qty_total += qty_total
                final_total_cost += total_cost_total
                final_total_value += total_value_total
                worksheet.write(categ_row + 1, 0 + i, key)
                worksheet.write(categ_row + 1, 1 + i, qty_total)
                worksheet.write(categ_row + 1, 2 + i, '%.3f' % total_cost_total)
            categ_row += 1
            worksheet.write(categ_row + 1, 0 + i, 'Total', style=stylePC)
            worksheet.write(categ_row + 1, 1 + i, final_qty_total, style=styleBorder)
            worksheet.write(categ_row + 1, 2 + i, '%.3f' % final_total_cost, style=styleBorder)
        file_data = cStringIO.StringIO()
        workbook.save(file_data)
        self.write({
            'state': 'get',
            'data': base64.encodestring(file_data.getvalue()),
            'name': 'stock_report.xls'
        })
        return {
            'name': 'Stock Report',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def _query_summary(self):
        if not self.date:
            to_date = datetime.strftime(datetime.today(), '%Y-%m-%d')
            to_date = datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        else:
            to_date = datetime.strptime(self.date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
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
            new_location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        elif not self.location_ids and not self.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([])]
            new_location_ids = self.env['stock.location'].search([])
        else:
            location_ids = [location.id for location in self.location_ids]
            new_location_ids = self.location_ids
        if not self.brand_ids:
            brand_ids = [brand.id for brand in self.env['product.brand'].search([])]
            if not brand_ids:
                raise ValidationError(_('No brand is defined to show.'))
            new_brand_ids = self.env['product.brand'].search([])
        else:
            brand_ids = [brand.id for brand in self.brand_ids]
            new_brand_ids = self.brand_ids

        if self.view_by == 'summary':
            if self.group_by == 'category' and category_ids:
                group_name = 'pc.name'
                group = 'pc'
            if self.group_by == 'location' and location_ids:
                group_name = 'sl.complete_name'
                group = 'sl'
            if self.group_by == 'brand':
                if brand_ids:
                    group_name = 'pb.name'
                    group = 'pb'
                else:
                    raise ValidationError(_('No brand is defined to show.'))
            SQL = """ """
            if self.date_selection == 'upto_date':
                SQL = """
                    SELECT 
                        pc.name as product_category,
                        sl.complete_name as location,
                        pt.name as product,
                        pp.default_code as item_code,
                        pp.id as product_id,
                        pp.barcode as barcode,
                        pt.name as description,
                        pb.name as brand,
                        sum(sq.qty) as qty,
                        sum(sq.cost) as cost,
                        sum(sq.qty * sq.cost) as value
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
                    """ % (to_date)
            else:
                SQL = """
                    SELECT 
                        pc.name as product_category,
                        sl.complete_name as location,
                        pt.name as product,
                        pp.default_code as item_code,
                        pp.id as product_id,
                        pp.barcode as barcode,
                        pt.name as description,
                        pb.name as brand,
                        sum(sq.quantity) as qty,
                        sum(sq.price_unit_on_quant) as cost,
                        sum(sq.quantity * sq.price_unit_on_quant) as value
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
                    """ % (to_date)
            SQL += """  pc.id in %s AND
                        sl.id in %s AND
                        pp.id in %s AND
                        (pb.id in %s or pb.id is NULL)
                        
                    GROUP BY %s.id, pp.id, pc.name, sl.complete_name, pt.name, pb.name, pp.default_code
                """ % (
                " (%s) " % ','.join(map(str, category_ids)),
                " (%s) " % ','.join(map(str, location_ids)),
                " (%s) " % ','.join(map(str, product_ids)),
                " (%s) " % ','.join(map(str, brand_ids)), group)
            #             SQL += ",spl.name" if self.date_selection == 'upto_date' else ",sq.serial_number"
            #                 SQL = """
            #                     SELECT
            #                         %s as product_category,
            #                         sum(sq.quantity) as qty,
            #                         avg(sq.price_unit_on_quant) as cost,
            #                         sum(sq.quantity * sq.price_unit_on_quant) as value,
            #                         sq.id as history_id
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
            #             SQL +="""
            #                     pc.id in %s AND
            #                     sl.id in %s AND
            #                     pp.id in %s AND
            #                     (pb.id in %s or pb.id is NULL)
            #                 """ % (
            #                        " (%s) " % ','.join(map(str, category_ids)),
            #                        " (%s) " % ','.join(map(str, location_ids)),
            #                        " (%s) " % ','.join(map(str, product_ids)),
            #                        " (%s) " % ','.join(map(str, brand_ids)))
            #             SQL += ' GROUP BY %s.id, sq.id' %(group)
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
            return final_dict

    #             return res

    def _query_detail(self):
        self.ensure_one()
        if self.date_selection == 'upto_date':
            if self.stock_lot in ['with_lot']:
                where_lot_id = 'sq.lot_id is not null AND'
            elif self.stock_lot in ['without_lot']:
                where_lot_id = 'sq.lot_id is null AND'
            else:
                where_lot_id = ''
        else:
            if self.stock_lot in ['with_lot']:
                where_lot_id = 'sq.serial_number is not null AND'
            elif self.stock_lot in ['without_lot']:
                where_lot_id = 'sq.serial_number is null AND'
            else:
                where_lot_id = ''
        if not self.date:
            to_date = datetime.strftime(datetime.today(), '%Y-%m-%d')
            to_date = datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        else:
            to_date = datetime.strptime(self.date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

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

        #         if not self.location_ids and self.internal_location:
        #             location_ids = [location.id for location in self.env['stock.location'].search([('usage', '=', 'internal')])]
        #         elif not self.location_ids and not self.internal_location:
        #             location_ids = [location.id for location in self.env['stock.location'].search([])]
        #         else:
        #             location_ids = [location.id for location in self.location_ids]

        if not self.location_ids and self.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([('usage', '=', 'internal')])]
            new_location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        elif not self.location_ids and not self.internal_location:
            location_ids = [location.id for location in self.env['stock.location'].search([])]
            new_location_ids = self.env['stock.location'].search([])
        else:
            location_ids = [location.id for location in self.location_ids]
            new_location_ids = self.location_ids

        if not self.brand_ids:
            brand_ids = [brand.id for brand in self.env['product.brand'].search([])]
            if not brand_ids:
                raise ValidationError(_('No brand is defined to show.'))
            new_brand_ids = self.env['product.brand'].search([])
        else:
            brand_ids = [brand.id for brand in self.brand_ids]
            new_brand_ids = self.brand_ids

        if self.view_by == 'detail':
            SQL = """ """
            if self.date_selection == 'upto_date':
                SQL = """
                    SELECT 
                        pc.name as product_category,
                        sl.complete_name as location,
                        pt.name as product,
                        pp.default_code as item_code,
                        pp.id as product_id,
                        pp.barcode as barcode,
                        pt.name as description,
                        pb.name as brand,
                        sum(sq.qty) as qty,
                        sum(sq.cost) as cost,
                        sum(sq.qty * sq.cost) as value,
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
                    """ % (to_date, where_lot_id)
            else:
                SQL = """
                    SELECT 
                        pc.name as product_category,
                        sl.complete_name as location,
                        pt.name as product,
                        pp.default_code as item_code,
                        pp.id as product_id,
                        pp.barcode as barcode,
                        pt.name as description,
                        pb.name as brand,
                        sum(sq.quantity) as qty,
                        sum(sq.price_unit_on_quant) as cost,
                        sum(sq.quantity * sq.price_unit_on_quant) as value,
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
                    """ % (to_date, where_lot_id)

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
            SQL += ",spl.name" if self.date_selection == 'upto_date' else ",sq.serial_number"
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
            return final_dict
