from odoo import api, fields, models, _
import base64
from io import  StringIO, BytesIO
from dateutil import parser
import datetime 
from datetime import datetime, timedelta
from datetime import timedelta
from odoo.exceptions import ValidationError
import cStringIO

try:
    import xlwt
    from xlwt import Borders
except ImportError:
       xlwt = None
       
class NonMovingProductWizard(models.TransientModel):
    
    _name = 'non.moving.product.wizard.ept'
    
    datas = fields.Binary('File')
    from_date = fields.Datetime(string="From Date", default=datetime.today() - timedelta(days=30), required=True)
    to_date = fields.Datetime(string="To Date", default=datetime.today(), required=True)
    
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses', required=True)

    @api.constrains('from_date', 'to_date')
    def _check_value(self):
        if any(self.filtered(lambda value: value.from_date > str(datetime.today()) or value.to_date > str(datetime.today()))):
            raise ValidationError(_("Please select Dates which are not in Future"))
        if any(self.filtered(lambda value: value.from_date > value.to_date)):
            raise ValidationError(_("Enter the To Date Less than From Date"))
        
        
    
    @api.multi
    def print_non_moving_product(self):
        active_id = self.ids[0]
        from_date = self.from_date
        to_date = self.to_date
        
        today = datetime.now().strftime("%Y-%m-%d")
        f_name = 'Non Moving Product' + ' ' + today
        
       
        warehouse_ids = self.warehouse_ids.ids
        
        self.get_non_moving_report(today, warehouse_ids, from_date, to_date)
        if self.datas:
            return {
            'type' : 'ir.actions.act_url',
            'url':   'web/content/?model=non.moving.product.wizard.ept&download=true&field=datas&id=%s&filename=%s.xls' % (active_id, f_name),
            'target': 'self',
             }
            
    @api.multi
    def get_non_moving_report(self, today, warehouse_ids, from_date, to_date):
        
        warehouse_obj = self.env['stock.warehouse']
        warehouse_id_ls = warehouse_obj.search([('id', 'in', warehouse_ids)])
        workbook, header_bold, body_style, qty_cell_style, value_style, days_style = self.create_sheet()
        workbook, sheet_data, row_data = self.add_headings(warehouse_id_ls, workbook, header_bold, from_date, to_date)
        data_dict = self.prepare_data(warehouse_ids, from_date, to_date)
        self.write_warehouse_wise_data(data_dict, sheet_data, row_data, body_style, qty_cell_style, value_style, days_style)
        
#        fp = StringIO()            
        fp = cStringIO.StringIO()
        workbook.save(fp)
        fp.seek(0)
        sale_file = base64.encodestring(fp.read())
        fp.close()
        self.write({'datas':sale_file})
        
        return True
    @api.multi
    def create_sheet(self):
        workbook = xlwt.Workbook()
        borders = Borders()
        header_border = Borders()
        header_border.left, header_border.right, header_border.top, header_border.bottom = Borders.THIN, Borders.THIN, Borders.THIN, Borders.THICK
        borders.left, borders.right, borders.top, borders.bottom = Borders.THIN, Borders.THIN, Borders.THIN, Borders.THIN
        header_bold = xlwt.easyxf("font: bold on, height 200; pattern: pattern solid, fore_colour gray25;alignment: horizontal center ,vertical center")
        header_bold.borders = header_border
        body_style = xlwt.easyxf("font: height 200; alignment: horizontal left")
        body_style.borders = borders
        
        # # style for different colors in columns
        xlwt.add_palette_colour("light_blue_21", 0x21)
        workbook.set_colour_RGB(0x21, 176, 216, 230)  
        qty_cell_style = xlwt.easyxf("font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour light_blue_21;  borders: top thin,right thin,bottom thin,left thin")
        
        xlwt.add_palette_colour("custom_orange", 0x22)
        workbook.set_colour_RGB(0x22, 255, 204, 153)
        value_style = xlwt.easyxf("font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour custom_orange;  borders: top thin,right thin,bottom thin,left thin")
        
        xlwt.add_palette_colour("custom_pink", 0x23)
        workbook.set_colour_RGB(0x23, 255, 204, 204)
        days_style = xlwt.easyxf("font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour custom_pink;  borders: top thin,right thin,bottom thin,left thin")
        
        return workbook, header_bold, body_style, qty_cell_style, value_style, days_style

    
    
    @api.multi
    def add_headings(self, warehouse_id_ls, workbook, header_bold, from_date, to_date):
        sheet_data = {}
        row_data = {}
        for warehouse in warehouse_id_ls:
            warehouse.name_worksheet = workbook.add_sheet(warehouse.display_name, cell_overwrite_ok=True)
            warehouse.name_worksheet.row(7).height = 600
            warehouse.name_worksheet.col(0).width = 4000
            warehouse.name_worksheet.col(1).width = 5000
            warehouse.name_worksheet.col(2).width = 6000
            warehouse.name_worksheet.col(3).width = 4000
            warehouse.name_worksheet.col(4).width = 5000
            warehouse.name_worksheet.col(5).width = 6500
            
            warehouse.name_worksheet.write(7, 0, 'Product ID', header_bold)
            warehouse.name_worksheet.write(7, 1, 'Product Code', header_bold)
            warehouse.name_worksheet.write(7, 2, 'Product Name', header_bold)
            warehouse.name_worksheet.write(7, 3, 'Available Qty', header_bold)
            warehouse.name_worksheet.write(7, 4, 'Last Sale Date', header_bold)
            warehouse.name_worksheet.write(7, 5, 'Duration from Last sale\n(In days)', header_bold)
            
            
            # Title
            title = "Non Moving Products Report"
            warehouse.name_worksheet.write_merge(0, 0, 0, 5, title, header_bold)
            
            # Date
            string_datefrom = "Date From:"
            string_dateto = "Date To:"
           
            warehouse.name_worksheet.row(2).height = 300
            warehouse.name_worksheet.write(2, 0, string_datefrom, header_bold)
            warehouse.name_worksheet.write(2, 4, string_dateto, header_bold)
            warehouse.name_worksheet.write(2, 1, from_date)
            warehouse.name_worksheet.col(5).width = 6500
            warehouse.name_worksheet.write(2, 5, to_date)
            
            
            # # freezing columns
            warehouse.name_worksheet.set_panes_frozen(True)
            warehouse.name_worksheet.set_horz_split_pos(8) 
            
            # #Get warehouse wise worksheet
            sheet_data.update({warehouse.id: warehouse.name_worksheet})
            
            # #initialize  worksheet wise row value
            row_data.update({warehouse.name_worksheet: 9})
        
        return workbook, sheet_data, row_data
    
    @api.multi
    def prepare_data(self, warehouse_ids, from_date, to_date):
        data_dict = {}
        location_obj = self.env['stock.location']
        warehouse_obj = self.env['stock.warehouse']
        product_obj = self.env['product.product']
        stock_move_obj = self.env['stock.move']
        warehouse_ids = warehouse_obj.search([('id', 'in', warehouse_ids)])
        for warehouse in warehouse_ids:
            product_list = []
            # new change
            location_id = warehouse.lot_stock_id.location_id or False
            if location_id:
                child_locations = self.get_child_locations(location_id)
                if child_locations:
                    child_locations = list(set(child_locations))
            else:
                child_locations = self.get_child_locations(warehouse.lot_stock_id)
#            child_locations = self.get_child_locations(warehouse.lot_stock_id)
            customer_location_ids = self.env['stock.location'].search([('usage', '=', 'customer')]).ids
            if len(child_locations) == 1:
                tuple_child_locations = tuple(child_locations)
                str_child_locations = str(tuple_child_locations).replace(',', '')
                
            else:
                str_child_locations = tuple(child_locations)
            if len(customer_location_ids) == 1:
                tuple_customer_location_ids = tuple(customer_location_ids)
                str_customer_location_ids = str(tuple_customer_location_ids).replace(',', '')
            else:
                str_customer_location_ids = tuple(customer_location_ids)
            if not child_locations or not customer_location_ids:
                return True
            
            product_list_qry = """select * from stock_move where (location_id in %s and location_dest_id in %s) and state='done' and date >= '%s' and date <='%s'""" % (str_child_locations, str_customer_location_ids, from_date, to_date)
            
            self._cr.execute(product_list_qry)
            move_ids = self._cr.dictfetchall()
            for move in move_ids:
                product = move.get('product_id')
                product_list.append(product)
                
            all_internal_product_ids = product_obj.with_context(active_test=True).search([])
            non_moving_product_ids = []
            
            for product in all_internal_product_ids:
                move_ids = stock_move_obj.search([('location_dest_id', 'in', child_locations), ('product_id', '=', product.id)])
                if move_ids:
                    oldest_date_str = min(move_ids.mapped('date'))
                    oldest_date = str(parser.parse(oldest_date_str).date())
                    if to_date < oldest_date :
                        continue  
                if product.id not in product_list:
                    non_moving_product_ids.append(product.id)
            non_moving_product_ids = product_obj.search([('id', 'in', non_moving_product_ids), ('type', '=', 'product')])
            output_location_ids = location_obj.search([('usage', '=', 'customer')])
            
            
            for product in non_moving_product_ids:
                last_sale_date = stock_move_obj.search([('location_id', 'in', child_locations), ('location_dest_id', 'in', output_location_ids.ids), ('product_id', '=', product.id)], limit=1, order="date desc")
                qty = product.with_context(warehouse=warehouse.id).qty_available
                if qty > 0:
                    last_day_oldest = self.days_oldest(last_sale_date.date)
                    if data_dict.get(warehouse.id):
                        data_dict.get(warehouse.id).append({'product_id':product.id,
                                                    'default_code':product.default_code,
                                                    'name':product.name,
                                                    'qty_available':product.with_context(warehouse=warehouse.id).qty_available,
                                                    'last_sale_date':last_sale_date.date or "",
                                                    'last_day_oldest':last_day_oldest or ""})
                    else:
                        data_dict.update({warehouse.id:[{'product_id':product.id,
                                                    'default_code':product.default_code,
                                                    'name':product.name,
                                                    'qty_available':product.with_context(warehouse=warehouse.id).qty_available,
                                                    'last_sale_date':last_sale_date.date or "",
                                                    'last_day_oldest':last_day_oldest or ""}]})                                   
                                                           
        return data_dict
   
   
    @api.multi
    def days_oldest(self, last_sale_date):
        if not last_sale_date:
            return 0
        today = datetime.strptime(str(datetime.now().date()), '%Y-%m-%d').strftime('%m-%d-%Y')
        current_date = datetime.strptime(str(today), '%m-%d-%Y').date()
        someday = last_sale_date
        time = someday[:4] + '-' + someday[5:7] + '-' + someday[8:10]
        time_validation = datetime.strptime(str(time), '%Y-%m-%d').strftime('%m-%d-%Y')
        final_date = datetime.strptime(str(time_validation), '%m-%d-%Y').date()
        diff = current_date - final_date 
        return diff.days
   
    @api.multi
    def get_child_locations(self, location):
      
        child_list = []
        child_list.append(location.id)
        child_locations_obj = self.env['stock.location'].search([('usage', '=', 'internal'), ('location_id', '=', location.id)])
        if child_locations_obj:
            for child_location in child_locations_obj:
                child_list.append(child_location.id)
                children_loc = self.get_child_locations(child_location)
                for child in children_loc:
                    child_list.append(child)
        return child_list
    
    
    @api.multi
    def write_warehouse_wise_data(self, data_dict, sheet_data, row_data, body_style, qty_cell_style, value_style, days_style):
        column = 0
        if data_dict:
            for warehouse_id, data_details in data_dict.items():
                for product_data in data_details:
                    row = row_data[sheet_data[warehouse_id]]
                    sheet_data[warehouse_id].row(row).height = 350
                    sheet_data[warehouse_id].write(row, column, product_data.get('product_id'), body_style)
                    sheet_data[warehouse_id].write(row, column + 1, product_data.get('default_code') or '-', body_style)
                    sheet_data[warehouse_id].write(row, column + 2, product_data.get('name'), body_style)
                    sheet_data[warehouse_id].write(row, column + 3, product_data.get('qty_available'), qty_cell_style)
                    sheet_data[warehouse_id].write(row, column + 4, product_data.get('last_sale_date'), value_style)
                    sheet_data[warehouse_id].write(row, column + 5, product_data.get('last_day_oldest'), days_style)
                    row += 1
                    # Increse row
                    row_data.update({sheet_data[warehouse_id]: row})
        
        else:
            return False
