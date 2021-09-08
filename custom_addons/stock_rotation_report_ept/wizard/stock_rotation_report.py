# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import models, fields, api
from datetime import datetime,timedelta
from odoo.tools.float_utils import float_round as round
from odoo.exceptions import Warning,ValidationError,UserError
from io import StringIO, BytesIO
from itertools import chain
import itertools
import time
import base64
import collections
try:
    import xlwt
    from xlwt import Borders
except ImportError:
    xlwt = None


class Stock_Rotation_Report(models.TransientModel):
    _name = "stock.rotation.report"
    
    datas=fields.Binary('File')
    filtaration = fields.Selection([
        ('location', 'Location'), ('warehouse', 'Warehouse')], default='location', 
        string='Filteration Based on')
    include_all_warehouse = fields.Boolean('Include All Warehouse?',default=True)
    warehouse_ids = fields.Many2many('stock.warehouse',string='Warehouses')
    include_all_location = fields.Boolean('Include All Locations?',default=True)
    location_ids = fields.Many2many('stock.location',string='Locations')
    from_date = fields.Date(string='From Date',required=True)
    to_date = fields.Date(string='To Date',required=True)
    
    
    @api.multi
    def print_stock_rotation_report(self):
        """
            This method is called when from wizard Download report button is clicked.
            the method first check for some of validations like
            from date and to date is not same or  to date is not privious then from date
            and also take all products of type product(Stockable Product) and active.
            and then call method get_stock_rotation_report for generate report based on selected period.
        """
        warehouses = False
        locations = False
        from_date = False
        to_date = False
        active_id = self.ids[0]
        today=datetime.now().strftime("%Y-%m-%d")
        f_name = 'Stock Rotation Report' + ' ' + today
        stock_warehouse_obj = self.env['stock.warehouse']
        stock_locations_obj = self.env['stock.location']
        product_obj = self.env['product.product']
        
        if self.filtaration == 'warehouse':
            if not self.include_all_warehouse:
                if not self.warehouse_ids:
                    raise ValidationError("please select the Warehouse.")
                warehouses = self.warehouse_ids
            else:
                warehouses = stock_warehouse_obj.search([])
        else:
            if not self.include_all_location:
                if not self.location_ids:
                    raise ValidationError("please select the Locations.")
                locations = self.location_ids
            else:
                locations = stock_locations_obj.search([('usage','=','internal')])


        if not self.from_date:
            raise ValidationError("please select the From Date.")
        
        if not self.to_date:
            raise ValidationError("please select the To Date.")

        all_products = product_obj.with_context(active_test=True).search([('type','=','product')])
        from_date = self.from_date
        to_date = self.to_date
        
        date_1 = time.strptime(from_date, "%Y-%m-%d")
        date_2 = time.strptime(to_date, "%Y-%m-%d")
        if not (date_1 <= date_2):
            raise ValidationError("Fromdate is not previous then Todate")
        self.get_stock_rotation_report(from_date,to_date,warehouses,locations,all_products)
        if self.datas:
            return {
                    'type' : 'ir.actions.act_url',
                    'url':'web/content/?model=stock.rotation.report&download=true&field=datas&id=%s&filename=%s.xls'%(active_id,f_name),
                    'target': 'new',
                }
    @api.multi
    def create_sheet(self):
        """
            this is general method for create work sheet and also create some of 
            style which is used for give different effects on sheets.
        """
        workbook = xlwt.Workbook()
        borders = Borders()
        header_border = Borders()
        header_border.left,header_border.right,header_border.top,header_border.bottom = Borders.THIN,Borders.THIN,Borders.THIN,Borders.THICK
        borders.left,borders.right,borders.top,borders.bottom = Borders.THIN,Borders.THIN,Borders.THIN,Borders.THIN
        header_bold = xlwt.easyxf("font: bold on, height 200; pattern: pattern solid, fore_colour gray25;alignment: horizontal center ,vertical center")
        header_bold.borders=header_border
        body_style = xlwt.easyxf("font: height 200; alignment: horizontal left")
        body_style.borders=borders
        
        ## style for different colors in columns
        xlwt.add_palette_colour("light_blue_21", 0x21)
        workbook.set_colour_RGB(0x21, 153, 255, 255)  
        qty_cell_style = xlwt.easyxf("font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour light_blue_21;  borders: top thin,right thin,bottom thin,left thin")
        
        xlwt.add_palette_colour("custom_orange", 0x22)
        workbook.set_colour_RGB(0x22, 255, 204, 153)
        value_style = xlwt.easyxf("font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour custom_orange;  borders: top thin,right thin,bottom thin,left thin")
        
        xlwt.add_palette_colour("custom_mandys_pink", 0x20)
        workbook.set_colour_RGB(0x20, 246, 228, 204)
        value_style2 = xlwt.easyxf("font: height 200,bold on, name Arial; align: horiz right, vert center;  pattern: pattern solid, fore_colour custom_mandys_pink;  borders: top thin,right thin,bottom thin,left thin")
        
        
        xlwt.add_palette_colour("custom_yellow", 0x25)
        workbook.set_colour_RGB(0x25, 255, 255, 179)
        blank_cell_style = xlwt.easyxf("font: height 200,bold on, name Arial; align: horiz center, vert center;  pattern: pattern solid, fore_colour custom_yellow;  borders: top thin,right thin,bottom thin,left thin")
        return workbook,header_bold,body_style,qty_cell_style,value_style,blank_cell_style,value_style2
    
    
    @api.multi
    def add_headings(self,from_date,to_date,warehouses,locations,workbook,header_bold,body_style,qty_cell_style,value_style,blank_cell_style):
        """
            this is genral method which is called when add the new sheets headings.
            work of these method is set height and width of cell and also
            add headings for given workbook.
        """
        sheet_data={}
        row_data={}
        if warehouses:
            for warehouse in warehouses:
                warehouse.name_worksheet = workbook.add_sheet(warehouse.name,cell_overwrite_ok=True)
                warehouse.name_worksheet.row(0).height = 400
                warehouse.name_worksheet.row(1).height = 400
                warehouse.name_worksheet.row(3).height = 400
                warehouse.name_worksheet.col(0).width = 8000
                warehouse.name_worksheet.col(1).width = 10000
                warehouse.name_worksheet.col(2).width = 3000
                warehouse.name_worksheet.col(3).width = 3000
                warehouse.name_worksheet.col(4).width = 1200
                warehouse.name_worksheet.col(5).width = 5000
                warehouse.name_worksheet.col(6).width = 5000
                warehouse.name_worksheet.col(7).width = 5000
                warehouse.name_worksheet.col(8).width = 7000
                warehouse.name_worksheet.col(9).width = 7000
                warehouse.name_worksheet.col(10).width = 5000
                warehouse.name_worksheet.col(11).width = 1200
                warehouse.name_worksheet.col(12).width = 7000
                warehouse.name_worksheet.col(13).width = 7000
                warehouse.name_worksheet.col(14).width = 1200
                warehouse.name_worksheet.col(15).width = 6000
                warehouse.name_worksheet.col(16).width = 6000
                warehouse.name_worksheet.write(0,0,'From Date',header_bold)
                warehouse.name_worksheet.write(0,1,from_date,body_style)
                warehouse.name_worksheet.write(1,0,'To Date',header_bold)
                warehouse.name_worksheet.write(1,1,to_date,body_style)
                warehouse.name_worksheet.write(3,0,'Internal Reference ',header_bold)
                warehouse.name_worksheet.write(3,1,'Name',header_bold)
                warehouse.name_worksheet.write(3,2,'Cost',header_bold)
                warehouse.name_worksheet.write(3,3,'Sales Price',header_bold)
                warehouse.name_worksheet.write(3,4,None,blank_cell_style)
                warehouse.name_worksheet.write(3,5,'Opening Stock',header_bold)
                warehouse.name_worksheet.write(3,6,'Purchase in period',header_bold)
                warehouse.name_worksheet.write(3,7,'Sales in Period',header_bold)
                warehouse.name_worksheet.write(3,8,'Discarded in Period(OUT)',header_bold)
                warehouse.name_worksheet.write(3,9,'Adjusted in Period(IN)',header_bold)
                warehouse.name_worksheet.write(3,10,'Closing Stock',header_bold)
                warehouse.name_worksheet.write(3,11,None,blank_cell_style)
                warehouse.name_worksheet.write(3,12,'Warehouse Transfer(IN)',header_bold)
                warehouse.name_worksheet.write(3,13,'Warehouse Transfer(OUT)',header_bold)
                warehouse.name_worksheet.write(3,14,None,blank_cell_style)
                warehouse.name_worksheet.write(3,15,'Last purchase',header_bold)
                warehouse.name_worksheet.write(3,16,'Last sale',header_bold)
                warehouse.name_worksheet.set_panes_frozen(True)
                warehouse.name_worksheet.set_horz_split_pos(4) 
                warehouse.name_worksheet.set_vert_split_pos(2)
                sheet_data.update({warehouse.id: warehouse.name_worksheet})
                row_data.update({warehouse.name_worksheet: 4})
        if locations:
            for location in locations:
                location.name_worksheet = workbook.add_sheet(location.name,cell_overwrite_ok=True)
                location.name_worksheet.row(0).height = 400
                location.name_worksheet.row(1).height = 400
                location.name_worksheet.row(3).height = 400
                location.name_worksheet.col(0).width = 8000
                location.name_worksheet.col(1).width = 10000
                location.name_worksheet.col(2).width = 3000
                location.name_worksheet.col(3).width = 3000
                location.name_worksheet.col(4).width = 1200
                location.name_worksheet.col(5).width = 5000
                location.name_worksheet.col(6).width = 5000
                location.name_worksheet.col(7).width = 5000
                location.name_worksheet.col(8).width = 7000
                location.name_worksheet.col(9).width = 7000
                location.name_worksheet.col(10).width = 5000
                location.name_worksheet.col(11).width = 1200
                location.name_worksheet.col(12).width = 7000
                location.name_worksheet.col(13).width = 7000
                location.name_worksheet.col(14).width = 1200
                location.name_worksheet.col(15).width = 6000
                location.name_worksheet.col(16).width = 6000
                location.name_worksheet.write(0,0,'From Date',header_bold)
                location.name_worksheet.write(1,0,'To Date',header_bold)
                location.name_worksheet.write(0,1,from_date,body_style)
                location.name_worksheet.write(1,1,to_date,body_style)
                location.name_worksheet.write(3,0,'Internal Reference ',header_bold)
                location.name_worksheet.write(3,1,'Name',header_bold)
                location.name_worksheet.write(3,2,'Cost',header_bold)
                location.name_worksheet.write(3,3,'Sales Price',header_bold)
                location.name_worksheet.write(3,4,None,blank_cell_style)
                location.name_worksheet.write(3,5,'Opening Stock',header_bold)
                location.name_worksheet.write(3,6,'Purchase in period',header_bold)
                location.name_worksheet.write(3,7,'Sales in Period',header_bold)
                location.name_worksheet.write(3,8,'Discarded in Period(OUT)',header_bold)
                location.name_worksheet.write(3,9,'Adjusted in Period(IN)',header_bold)
                location.name_worksheet.write(3,10,'Closing Stock',header_bold)
                location.name_worksheet.write(3,11,None,blank_cell_style)
                location.name_worksheet.write(3,12,'Warehouse Transfer(IN)',header_bold)
                location.name_worksheet.write(3,13,'Warehouse Transfer(OUT)',header_bold)
                location.name_worksheet.write(3,14,None,blank_cell_style)
                location.name_worksheet.write(3,15,'Last purchase',header_bold)
                location.name_worksheet.write(3,16,'Last sale',header_bold)
                location.name_worksheet.set_panes_frozen(True)
                location.name_worksheet.set_horz_split_pos(4) 
                location.name_worksheet.set_vert_split_pos(2)
                sheet_data.update({location.id: location.name_worksheet})
                row_data.update({location.name_worksheet: 4})
        return workbook,sheet_data,row_data

    @api.multi
    def get_child_locations(self,location):
        """
            this method is used for get all the chield location
            for given location in argument.
            returns the list of chield locations.
        """
        child_list=[]
        child_list.append(location.id)
        child_locations = self.env['stock.location'].search([('usage','=','internal'),('location_id','=',location.id)])
        if child_locations:
            for child_location in child_locations:
                child_list.append(child_location.id)
                ## recursive calling to find child of child lcoations
                children_loc = self.get_child_locations(child_location)
                ## adding child into one list
                for child in children_loc:
                    child_list.append(child)
        return child_list
    
    @api.multi
    def get_all_locations(self,warehouse=False,location=False):
        """
            This method is used for  get the location
            for specific warehouse.it intenally called 
            get child location method. and return the chield locations
            of given warehouse.
        """
        ## finding all location along with it's child locations for given warehouse
        all_locations=[]
        if warehouse:
            locations= self.env['stock.location'].search([('usage','=','internal'),('id','in',warehouse.view_location_id.child_ids.ids)])
        else:
            locations = location

        for location in locations:
            child_locations_list = self.get_child_locations(location)
            if child_locations_list:
                child_locations_list = set(child_locations_list)
                ## adding all child in to one list 
                for child in child_locations_list:
                    all_locations.append(child) 
        return all_locations
    
    @api.multi
    def get_other_wahouse_locations(self,warehouse):
        """
            this method is use for get other warehouses location
            which is used when inter warehouse transfer transection
            if find.
        """
        stock_warehouse_obj = self.env['stock.warehouse']
        warehouses = stock_warehouse_obj.search([('id','not in',warehouse.ids)])
        dest_wahouse_lst = []
        for wh in warehouses:
            dest_wahouse_lst.append(self.get_all_locations(wh))
        
        dest_wahouse_lst=list(itertools.chain(*dest_wahouse_lst))
        return dest_wahouse_lst  
        
    @api.multi
    def get_product_qty(self,location,date):
        """
            This method is use to get the opening stock of product for specific location
            at specific date. query is modification of get inventory at date of base v10.
        """
        query = """
                SELECT tmp.product_id,SUM(quantity) as quantity FROM( 
                    SELECT  location_id,
                        product_id,
                        SUM(quantity) as quantity,
                        date,
                        COALESCE(SUM(price_unit_on_quant * quantity) / NULLIF(SUM(quantity), 0), 0) as price_unit_on_quant
                        FROM
                        ((SELECT
                            stock_move.id AS id,
                            stock_move.id AS move_id,
                            dest_location.id AS location_id,
                            dest_location.company_id AS company_id,
                            stock_move.product_id AS product_id,
                            product_template.id AS product_template_id,
                            product_template.categ_id AS product_categ_id,
                            quant.qty AS quantity,
                            stock_move.date AS date,
                            quant.cost as price_unit_on_quant,
                            stock_move.origin AS source,
                            stock_production_lot.name AS serial_number
                        FROM
                            stock_quant as quant
                        JOIN
                            stock_quant_move_rel ON stock_quant_move_rel.quant_id = quant.id
                        JOIN
                            stock_move ON stock_move.id = stock_quant_move_rel.move_id
                        LEFT JOIN
                            stock_production_lot ON stock_production_lot.id = quant.lot_id
                        JOIN
                            stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                        JOIN
                            stock_location source_location ON stock_move.location_id = source_location.id
                        JOIN
                            product_product ON product_product.id = stock_move.product_id
                        JOIN
                            product_template ON product_template.id = product_product.product_tmpl_id
                        WHERE quant.qty>0 AND stock_move.state = 'done' AND dest_location.usage in ('internal', 'transit')
                        AND (
                            not (source_location.company_id is null and dest_location.company_id is null) or
                            source_location.company_id != dest_location.company_id or
                            source_location.usage not in ('internal', 'transit'))
                        ) UNION ALL
                        (SELECT
                            (-1) * stock_move.id AS id,
                            stock_move.id AS move_id,
                            source_location.id AS location_id,
                            source_location.company_id AS company_id,
                            stock_move.product_id AS product_id,
                            product_template.id AS product_template_id,
                            product_template.categ_id AS product_categ_id,
                            - quant.qty AS quantity,
                            stock_move.date AS date,
                            quant.cost as price_unit_on_quant,
                            stock_move.origin AS source,
                            stock_production_lot.name AS serial_number
                        FROM
                            stock_quant as quant
                        JOIN
                            stock_quant_move_rel ON stock_quant_move_rel.quant_id = quant.id
                        JOIN
                            stock_move ON stock_move.id = stock_quant_move_rel.move_id
                        LEFT JOIN
                            stock_production_lot ON stock_production_lot.id = quant.lot_id
                        JOIN
                            stock_location source_location ON stock_move.location_id = source_location.id
                        JOIN
                            stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                        JOIN
                            product_product ON product_product.id = stock_move.product_id
                        JOIN
                            product_template ON product_template.id = product_product.product_tmpl_id
                        WHERE quant.qty>0 AND stock_move.state = 'done' AND source_location.usage in ('internal', 'transit')
                        AND (
                            not (dest_location.company_id is null and source_location.company_id is null) or
                            dest_location.company_id != source_location.company_id or
                            dest_location.usage not in ('internal', 'transit'))
                        ))
                        AS foo
                        GROUP BY move_id, location_id, company_id, product_id, date) AS tmp
                        WHERE tmp.location_id in (%s)  AND tmp.date < '%s 00:00:00'
                        GROUP BY tmp.product_id 
                    """%(','.join(str(x) for x in location),date)
        self._cr.execute(query)
        result = self._cr.fetchall()
        return result 
    
    @api.multi
    def find_last_sales_qty(self,from_date,to_date,warehouse,location,product_id):
        """
            this method is used for finding the last quantity sale for specific product
            in given duration.
        """
        if warehouse:
            query="""
                    select date from stock_move mv 
                    Inner join stock_location sl on sl.id = mv.location_dest_id and sl.usage='customer' and mv.location_id in (%s)
                    where state='done' and product_id = %s and warehouse_id= %s and date between '%s 00:00:00' and '%s 23:59:59'
                    order by date desc
                    limit 1
                  """%(','.join(str(x) for x in location),product_id.id,warehouse.id,from_date,to_date)
        else:
            query="""
                    select date from stock_move mv 
                    Inner join stock_location sl on sl.id = mv.location_dest_id and sl.usage='customer' and mv.location_id in (%s)
                    where state='done' and product_id = %s and date between '%s 00:00:00' and '%s 23:59:59'
                    order by date desc
                    limit 1
                  """%(','.join(str(x) for x in location),product_id.id,from_date,to_date)
        self._cr.execute(query)
        result = self._cr.fetchall()
        return result

    @api.multi
    def find_last_purchase_date(self,from_date,to_date,location,product_id):
        """
            this method is used for finding the last date of purchase for specific product
            in given duration. for specific location of warehouse.
        """
        query="""select date from stock_move mv 
                Inner join stock_location sl on sl.id = mv.location_id and sl.usage='supplier' 
                and mv.location_dest_id in (%s) where state='done' and product_id = %s and date between '%s 00:00:00' and '%s 23:59:59'
                order by date desc
                limit 1"""%(','.join(str(x) for x in location),product_id.id,from_date,to_date)
        self._cr.execute(query)
        result = self._cr.fetchall()
        return result
    
    @api.multi
    def find_purchase_qty_in_duration(self,from_date,to_date,location,product_id):
        """
            this method is used for finding the last purchase qty for specific product
            in given duration. for specific location of warehouse.
        """
        # query="""
        #     select sum(product_uom_qty) from stock_move mv 
        #     Inner join stock_location sl on sl.id = mv.location_id and sl.usage='supplier'
        #     and mv.location_dest_id in (%s) where state='done' and product_id = %s and date between '%s 00:00:00' and '%s 23:59:59'
        #     """
        query = """select sum(product_uom_qty) as total,product_uom from stock_move mv 
        Inner join stock_location sl on sl.id = mv.location_id and sl.usage='supplier' 
        and mv.location_dest_id in (%s) where state='done' and product_id = %s and 
        date between '%s 00:00:00' and '%s 23:59:59' group by product_uom"""%(
            ','.join(str(x) for x in location), product_id.id,from_date,to_date)
        self._cr.execute(query)
        result = self._cr.fetchall()
        uom_rec = self.env['product.uom']
        purchase_qty = 0
        for r in result:
            factor_inv = uom_rec.browse(r[1]).factor_inv
            purchase_qty += r[0] * factor_inv
        # Return Qty
        return_query = """select sum(product_uom_qty) as total,product_uom 
        from stock_move mv Inner join stock_location sl on sl.id = 
        mv.location_dest_id and sl.usage='supplier' and mv.location_id in (
        %s) where state='done' and product_id = %s and date between '%s 
        00:00:00' and '%s 23:59:59' group by product_uom""" % (
            ','.join(str(x) for x in location), product_id.id, from_date,
            to_date)
        self._cr.execute(return_query)
        return_result = self._cr.fetchall()
        purchase_return_qty = 0
        for re in return_result:
            factor_inv = uom_rec.browse(re[1]).factor_inv
            purchase_return_qty += re[0] * factor_inv
        purchase_qty -= purchase_return_qty
        return purchase_qty
    
    @api.multi
    def find_sale_qty_in_duration(self,from_date,to_date,warehouse,location,product_id):
        """
            this method is used for finding the last sale qty for specific product
            in given duration. for specific location of warehouse.
        """
        if warehouse:
            query="""select sum(product_uom_qty) as total, product_uom from stock_move mv 
                    Inner join stock_location sl on sl.id = mv.location_dest_id and sl.usage='customer'
                    where state='done' and mv.location_id in (%s) and product_id = %s and 
                    warehouse_id= %s and date between '%s 00:00:00' and '%s 23:59:59' group by product_uom
                    """%(','.join(str(x) for x in location),product_id.id,warehouse.id,from_date,to_date)
            return_query="""select sum(product_uom_qty) as total, product_uom from stock_move mv 
                    Inner join stock_location sl on sl.id = mv.location_id and sl.usage='customer'
                    where state='done' and mv.location_dest_id in (%s) and product_id = %s and 
                    warehouse_id= %s and date between '%s 00:00:00' and '%s 23:59:59' group by product_uom
                    """%(','.join(str(x) for x in location),product_id.id,warehouse.id,from_date,to_date)
        else:
            query="""select sum(product_uom_qty) as total,product_uom from stock_move mv 
                    Inner join stock_location sl on sl.id = mv.location_dest_id and sl.usage='customer'
                    where state='done' and mv.location_id in (%s) and product_id = %s and 
                    date between '%s 00:00:00' and '%s 23:59:59' group by product_uom
                    """%(','.join(str(x) for x in location),product_id.id,from_date,to_date)
            return_query="""select sum(product_uom_qty) as total,product_uom from stock_move mv 
                    Inner join stock_location sl on sl.id = mv.location_id and sl.usage='customer'
                    where state='done' and mv.location_dest_id in (%s) and product_id = %s and 
                    date between '%s 00:00:00' and '%s 23:59:59' group by product_uom
                    """%(','.join(str(x) for x in location),product_id.id,from_date,to_date)
        self._cr.execute(query)
        result = self._cr.fetchall()
        uom_rec = self.env['product.uom']
        sale_qty = 0
        for r in result:
            factor_inv = uom_rec.browse(r[1]).factor_inv
            sale_qty += r[0] * factor_inv
        # Return Qty
        self._cr.execute(return_query)
        return_result = self._cr.fetchall()
        sale_return_qty = 0
        for re in return_result:
            factor_inv = uom_rec.browse(re[1]).factor_inv
            sale_return_qty += re[0] * factor_inv
        sale_qty -= sale_return_qty
        return sale_qty
    
    @api.multi
    def find_scap_location_qty(self,from_date,to_date,product_id,location_id):
        """
            this method is used for finding the scrap qty for specific product
            in given duration. for specific location of warehouse.
        """
        query = """
                select sum(product_uom_qty) from stock_move mv 
                Inner join stock_location sl on sl.id = mv.location_dest_id and sl.usage='inventory'
                where state='done' and product_id = %s and mv.location_id in (%s)  and date between '%s 00:00:00' and '%s 23:59:59'
                """ %(product_id.id,','.join(str(x) for x in location_id),from_date,to_date)
        self._cr.execute(query)
        result = self._cr.fetchall()
        return result
    
    @api.multi
    def find_adjusted_qty_in_duration(self,from_date,to_date,product_id,location_id):
        """
            this method is used for finding the adjusted qty for specific product
            in given duration. for specific location of warehouse.
        """
        query = """
                select sum(product_uom_qty) from stock_move mv 
                Inner join stock_location sl on sl.id = mv.location_id and sl.usage='inventory' 
                and mv.location_dest_id in (%s) where state='done' and product_id =%s and date between '%s 00:00:00' and '%s 23:59:59'
                """ %(','.join(str(x) for x in location_id),product_id.id,from_date,to_date)
        self._cr.execute(query)
        result = self._cr.fetchall()
        return result
    
    
    @api.multi
    def find_warehouse_transer_out_qty(self,product_id,source_location_lst,dest_location_lst,from_date,to_date):
        """
            this method is used for finding the qty tranfer from warehouse for specific product
            in given duration.
        """
        query = """
                select sum(product_uom_qty) from stock_move mv 
                Inner join stock_location sl on sl.id = mv.location_id and sl.usage='internal' 
                where state='done' and product_id =%s  and mv.location_id in (%s) and mv.location_dest_id in (%s) and date between '%s 00:00:00' and '%s 23:59:59'
                """%(product_id.id,','.join(str(x) for x in source_location_lst),','.join(str(x) for x in dest_location_lst),from_date,to_date)
        self._cr.execute(query)
        result = self._cr.fetchall()
        return result
    @api.multi
    def find_warehouse_transer_in_qty(self,product_id,source_location_lst,dest_location_lst,from_date,to_date):
        """
            this method is used for finding the qty tranfer to warehouse for specific product
            in given duration.
        """
        query = """
                select sum(product_uom_qty) from stock_move mv 
                Inner join stock_location sl on sl.id = mv.location_dest_id and sl.usage='internal' 
                where state='done' and product_id = %s  and mv.location_id in (%s) and mv.location_dest_id in (%s) and date between '%s 00:00:00' and '%s 23:59:59'
                """%(product_id.id,','.join(str(x) for x in dest_location_lst),','.join(str(x) for x in source_location_lst),from_date,to_date)
        self._cr.execute(query)
        result = self._cr.fetchall()
        return result

    # Prepered data with Location
    @api.multi
    def prepare_data_with_location(self,from_date,to_date,locations,all_products):
        """
            This method is used for prepare data based on warehouse. 
        """
        data_dict = {}
        stock_quant_obj=self.env['stock.quant']
        for loc in locations:
            all_locations =  self.get_all_locations(warehouse=False, location=loc)
            if not all_locations:
                continue
            #here we are finding the opening stock for these we are using base query
            #of inventory at date v10
            result = self.get_product_qty(all_locations,from_date)
            qty_dict = dict((x,y) for x, y in result)
            
            for product in all_products:
                last_sales = ''
                qty_purchase_in_duration = 0
                qty_sales_in_duration = 0
                last_purchase_date = ''
                scrap_location_qty = 0
                adjusted_qty_in_duration = 0
                warehouse_out_qty = 0
                warehouse_in_qty = 0
#                 here from result of inventory at date we are seaching for specific product.
                opening_product_qty = qty_dict.get(product.id)

                #finding last sales qty
                last_sales = self.find_last_sales_qty(from_date,to_date,False,all_locations,product)
                #finding last purchase date of product
                last_purchase_date = self.find_last_purchase_date(from_date,to_date,all_locations,product)
                #fiding date purchase qty in duration for specific product
                qty_purchase_in_duration = self.find_purchase_qty_in_duration(from_date,to_date,all_locations,product)
                #fiding scrap qty of precific product
                scrap_location_qty = self.find_scap_location_qty(from_date,to_date,product,all_locations)
                #finding sales qty in duration
                qty_sales_in_duration = self.find_sale_qty_in_duration(from_date,to_date,False,all_locations,product)
                #fidning adjusted qty in duration
                adjusted_qty_in_duration = self.find_adjusted_qty_in_duration(from_date, to_date, product, all_locations)

                # dest_location_lst = self.get_other_wahouse_locations(warehouse)
                
                # if any(all_locations) and any(dest_location_lst):
                #     #fidning warehouse in qty 
                #     warehouse_in_qty = self.find_warehouse_transer_in_qty(product, all_locations, dest_location_lst,from_date,to_date)
                #     #fidning warehouse out qty for specific product.
                #     warehouse_out_qty = self.find_warehouse_transer_out_qty(product, all_locations, dest_location_lst,from_date,to_date)
                
                #     if warehouse_out_qty:
                #         warehouse_out_qty = warehouse_out_qty and warehouse_out_qty[0][0] or ''
                #     if warehouse_in_qty:
                #         warehouse_in_qty = warehouse_in_qty and warehouse_in_qty[0][0] or ''
                    
                if adjusted_qty_in_duration:
                    adjusted_qty_in_duration = adjusted_qty_in_duration and adjusted_qty_in_duration[0][0] or '' 
                if scrap_location_qty:
                    scrap_location_qty = scrap_location_qty and scrap_location_qty[0][0] or ''
                    
                # if qty_sales_in_duration:
                #     qty_sales_in_duration = qty_sales_in_duration and qty_sales_in_duration[0][0] or ''
                # if qty_purchase_in_duration:
                #     qty_purchase_in_duration = qty_purchase_in_duration or ''
                if last_sales:
                    last_sales = datetime.strptime(last_sales and last_sales[0][0], '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') or ''
                
                if last_purchase_date:
                    last_purchase_date = datetime.strptime(last_purchase_date and last_purchase_date[0][0], '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') or ''
                   
                if data_dict.has_key(loc.id):
                    data_lst=data_dict.get(loc.id)
                    data_lst.append({'product':product,'sku':product.default_code or '','name':product.name,
                                     'Cost':product.standard_price or '','sales_price':product.lst_price or '',
                                     'opening_qty':opening_product_qty or 0,'last_sales':last_sales or '',
                                     'last_purchase_date':last_purchase_date or '','qty_purchase_in_duration':qty_purchase_in_duration or 0,
                                     'qty_sales_in_duration': qty_sales_in_duration or 0,'scrap_location_qty':scrap_location_qty or 0,
                                     'adjusted_qty_in_duration':adjusted_qty_in_duration or 0
                                     ,'warehouse_in_qty':warehouse_in_qty or 0,
                                     'warehouse_out_qty':warehouse_out_qty or 0 
                                     })
                    data_dict.update({loc.id:data_lst})
                    continue
                data_dict.update({loc.id:[{'product':product,'sku':product.default_code or '','name':product.name,
                                                 'Cost':product.standard_price or '','sales_price':product.lst_price or '',
                                                 'opening_qty':opening_product_qty or 0,
                                                 'last_sales':last_sales or '','last_purchase_date':last_purchase_date or '',
                                                 'qty_purchase_in_duration':qty_purchase_in_duration or 0,
                                                 'qty_sales_in_duration': qty_sales_in_duration or 0,
                                                 'scrap_location_qty':scrap_location_qty or 0,
                                                 'adjusted_qty_in_duration':adjusted_qty_in_duration or 0,
                                                 'warehouse_in_qty':warehouse_in_qty or 0,
                                                 'warehouse_out_qty':warehouse_out_qty or 0
                                                 }]})
        return data_dict

    # prepare data with warehouse
    @api.multi
    def prepare_data_with_warehouse(self,from_date,to_date,warehouses,all_products):
        """
            This method is used for prepare data based on warehouse. 
        """
        data_dict = {}
        stock_quant_obj=self.env['stock.quant']
        for warehouse in warehouses:
            all_locations =  self.get_all_locations(warehouse)
            if not all_locations:
                continue
            
            #here we are finding the opening stock for these we are using base query
            #of inventory at date v10
            result = self.get_product_qty(all_locations,from_date)
            qty_dict = dict((x,y) for x, y in result)
            
            for product in all_products:
                last_sales = ''
                qty_purchase_in_duration = 0
                qty_sales_in_duration = 0
                last_purchase_date = ''
                scrap_location_qty = 0
                adjusted_qty_in_duration = 0
                warehouse_out_qty = 0
                warehouse_in_qty = 0
#                 here from result of inventory at date we are seaching for specific product.
                opening_product_qty = qty_dict.get(product.id)

                #finding last sales qty
                last_sales = self.find_last_sales_qty(from_date,to_date,warehouse,all_locations,product)
                #finding last purchase date of product
                last_purchase_date = self.find_last_purchase_date(from_date,to_date,all_locations,product)
                #fiding date purchase qty in duration for specific product
                qty_purchase_in_duration = self.find_purchase_qty_in_duration(from_date,to_date,all_locations,product)
                #fiding scrap qty of precific product
                scrap_location_qty = self.find_scap_location_qty(from_date,to_date,product,all_locations)
                #finding sales qty in duration
                qty_sales_in_duration = self.find_sale_qty_in_duration(from_date,to_date,warehouse,all_locations,product)
                #fidning adjusted qty in duration
                adjusted_qty_in_duration = self.find_adjusted_qty_in_duration(from_date, to_date, product, all_locations)
                
                dest_location_lst = self.get_other_wahouse_locations(warehouse)
                
                if any(all_locations) and any(dest_location_lst):
                    #fidning warehouse in qty 
                    warehouse_in_qty = self.find_warehouse_transer_in_qty(product, all_locations, dest_location_lst,from_date,to_date)
                    #fidning warehouse out qty for specific product.
                    warehouse_out_qty = self.find_warehouse_transer_out_qty(product, all_locations, dest_location_lst,from_date,to_date)
                
                    if warehouse_out_qty:
                        warehouse_out_qty = warehouse_out_qty and warehouse_out_qty[0][0] or ''
                    if warehouse_in_qty:
                        warehouse_in_qty = warehouse_in_qty and warehouse_in_qty[0][0] or ''
                    
                if adjusted_qty_in_duration:
                    adjusted_qty_in_duration = adjusted_qty_in_duration and adjusted_qty_in_duration[0][0] or '' 
                if scrap_location_qty:
                    scrap_location_qty = scrap_location_qty and scrap_location_qty[0][0] or ''
                    
                # if qty_sales_in_duration:
                #     qty_sales_in_duration = qty_sales_in_duration and qty_sales_in_duration[0][0] or ''
                # if qty_purchase_in_duration:
                #     qty_purchase_in_duration = qty_purchase_in_duration[0][0] or ''
                if last_sales:
                    last_sales = datetime.strptime(last_sales and last_sales[0][0], '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') or ''
                
                if last_purchase_date:
                    last_purchase_date = datetime.strptime(last_purchase_date and last_purchase_date[0][0], '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') or ''
                   
                if data_dict.has_key(warehouse.id):
                    data_lst=data_dict.get(warehouse.id)
                    data_lst.append({'product':product,'sku':product.default_code or '','name':product.name,
                                     'Cost':product.standard_price or '','sales_price':product.lst_price or '',
                                     'opening_qty':opening_product_qty or 0,'last_sales':last_sales or '',
                                     'last_purchase_date':last_purchase_date or '','qty_purchase_in_duration':qty_purchase_in_duration or 0,
                                     'qty_sales_in_duration': qty_sales_in_duration or 0,'scrap_location_qty':scrap_location_qty or 0,
                                     'adjusted_qty_in_duration':adjusted_qty_in_duration or 0
                                     ,'warehouse_in_qty':warehouse_in_qty or 0,
                                     'warehouse_out_qty':warehouse_out_qty or 0 
                                     })
                    data_dict.update({warehouse.id:data_lst})
                    continue
                data_dict.update({warehouse.id:[{'product':product,'sku':product.default_code or '','name':product.name,
                                                 'Cost':product.standard_price or '','sales_price':product.lst_price or '',
                                                 'opening_qty':opening_product_qty or 0,
                                                 'last_sales':last_sales or '','last_purchase_date':last_purchase_date or '',
                                                 'qty_purchase_in_duration':qty_purchase_in_duration or 0,
                                                 'qty_sales_in_duration': qty_sales_in_duration or 0,
                                                 'scrap_location_qty':scrap_location_qty or 0,
                                                 'adjusted_qty_in_duration':adjusted_qty_in_duration or 0,
                                                 'warehouse_in_qty':warehouse_in_qty or 0,
                                                 'warehouse_out_qty':warehouse_out_qty or 0
                                                 }]})
        return data_dict
    
    @api.multi
    def print_date_in_sheet(self,data_dict,workbook,sheet_data,row_data,body_style,qty_cell_style,value_style,blank_cell_style,value_style2):
        """
            this method is used for just printing data
            in sheet based on given data dict. and apply 
            styles for cells. 
        """
        product_data_dict = collections.OrderedDict()
        row=4
        column=0
        for warehouse_id,data_details in data_dict.iteritems():
            for product_data in data_details:
                row=row_data[sheet_data[warehouse_id]]
                sheet_data[warehouse_id].row(row).height = 350
                opening_stock = product_data.get('opening_qty') or 0
                qty_purchase = product_data.get('qty_purchase_in_duration') or 0
                qty_sale = product_data.get('qty_sales_in_duration') or 0
                scap_qty = product_data.get('scrap_location_qty') or 0
                adj_qty = product_data.get('adjusted_qty_in_duration') or 0
                last_sales = product_data.get('last_sales') or ''
                last_purchase_date = product_data.get('last_purchase_date') or ''
                warehouse_in_qty = product_data.get('warehouse_in_qty') or 0
                warehouse_out_qty = product_data.get('warehouse_out_qty') or 0
                closing_qty = (opening_stock+qty_purchase+warehouse_in_qty)-(qty_sale+scap_qty+warehouse_out_qty)
                sheet_data[warehouse_id].write(row,column,product_data.get('sku'),body_style)
                sheet_data[warehouse_id].write(row,column+1,product_data.get('name') or '-',body_style)
                sheet_data[warehouse_id].write(row,column+2,product_data.get('Cost') or 0,qty_cell_style)
                sheet_data[warehouse_id].write(row,column+3,product_data.get('sales_price') or 0,qty_cell_style)
                sheet_data[warehouse_id].write(row,column+4,None,blank_cell_style)
                sheet_data[warehouse_id].write(row,column+5,opening_stock,value_style2)
                sheet_data[warehouse_id].write(row,column+6,qty_purchase,value_style2)
                sheet_data[warehouse_id].write(row,column+7,qty_sale,value_style2)
                sheet_data[warehouse_id].write(row,column+8,scap_qty,value_style2)
                sheet_data[warehouse_id].write(row,column+9,adj_qty,value_style2)
                sheet_data[warehouse_id].write(row,column+10,closing_qty,value_style2)
                sheet_data[warehouse_id].write(row,column+11,None,blank_cell_style)
                sheet_data[warehouse_id].write(row,column+12,warehouse_in_qty,value_style)
                sheet_data[warehouse_id].write(row,column+13,warehouse_out_qty,value_style)
                sheet_data[warehouse_id].write(row,column+14,None,blank_cell_style)
                sheet_data[warehouse_id].write(row,column+15,last_purchase_date,body_style)
                sheet_data[warehouse_id].write(row,column+16,last_sales,body_style)
                row+=1
                row_data.update({sheet_data[warehouse_id]: row})
                product_data_dict = self.prepare_date_for_all_warehouses_sheets(product_data.get('product'),product_data_dict,opening_stock,last_sales,last_purchase_date,qty_purchase,qty_sale,scap_qty,adj_qty,warehouse_in_qty,warehouse_out_qty)
        return product_data_dict
    
    
    @api.multi
    def prepare_date_for_all_warehouses_sheets(self,product,product_data_dict,opening_qty,last_sales,last_purchase_date,qty_purchase_in_duration,qty_sales_in_duration,scrap_location_qty,adjusted_qty_in_duration,warehouse_in_qty,warehouse_out_qty):
        """
            this method is use for prepare the data for print all inventory 
            sheet the method is prepare the dict and key is product id.
            if already there then make qty addition and update in dict.
            return product_data_dict
        """
        if last_purchase_date: 
            last_purchase_date = datetime.strptime(last_purchase_date, '%d-%m-%Y')
        if last_sales:
            last_sales = datetime.strptime(last_sales, '%d-%m-%Y')
        if product_data_dict.has_key(product):
            product_data = product_data_dict.get(product)
            old_opening_qty = product_data.get('opening_qty')
            new_opening_qty = product_data.get('opening_qty') + opening_qty 
            
            new_last_sales = product_data.get('last_sales')
            new_last_sales.append(last_sales) 
            
            new_last_purchase_date_lst = product_data.get('last_purchase_date')
            new_last_purchase_date_lst.append(last_purchase_date)
            
            old_qty_purchase_in_duration = product_data.get('qty_purchase_in_duration')
            new_qty_purchase_in_duration = old_qty_purchase_in_duration + qty_purchase_in_duration
             
            old_qty_sales_in_duration = product_data.get('qty_sales_in_duration')
            new_qty_sales_in_duration = old_qty_sales_in_duration + qty_sales_in_duration
            
            old_scrap_location_qty = product_data.get('scrap_location_qty')
            new_scrap_location_qty = old_scrap_location_qty + scrap_location_qty
            
            old_adjusted_qty_in_duration = product_data.get('adjusted_qty_in_duration')
            new_adjusted_qty_in_duration = old_adjusted_qty_in_duration + adjusted_qty_in_duration
            
            old_warehouse_in_qty = int(product_data.get('warehouse_in_qty') or 0)
            new_warehouse_in_qty = old_warehouse_in_qty +  warehouse_in_qty or 0
            
            old_warehouse_out_qty = int(product_data.get('warehouse_out_qty') or 0)
            new_warehouse_out_qty = old_warehouse_out_qty +  warehouse_out_qty or 0
            
            product_data.update({'opening_qty':new_opening_qty,'last_sales':new_last_sales,
                                  'last_purchase_date':new_last_purchase_date_lst,'qty_purchase_in_duration':new_qty_purchase_in_duration,
                                  'qty_sales_in_duration': new_qty_sales_in_duration,'scrap_location_qty':new_scrap_location_qty,
                                  'adjusted_qty_in_duration':new_adjusted_qty_in_duration,
                                  'warehouse_in_qty':new_warehouse_in_qty,'warehouse_out_qty':new_warehouse_out_qty
                                  })
            
            product_data_dict.update({product:product_data})
            return product_data_dict
            
        product_data_dict.update({product:{
                                          'opening_qty':opening_qty or 0,'last_sales':[last_sales or ''],
                                          'last_purchase_date':[last_purchase_date],'qty_purchase_in_duration':qty_purchase_in_duration or 0,
                                          'qty_sales_in_duration': qty_sales_in_duration or 0,'scrap_location_qty':scrap_location_qty or 0,
                                          'adjusted_qty_in_duration':adjusted_qty_in_duration or 0,
                                          'warehouse_in_qty':warehouse_in_qty or 0,'warehouse_out_qty':warehouse_out_qty or 0
                                          }})
        return product_data_dict
    
    @api.multi
    def create_all_inventory_sheet(self,from_date,to_date,workbook,sheet_data,row_data,body_style,qty_cell_style,value_style,blank_cell_style,header_bold):
        """
            this method is used for just add the one sheet (i.e All Stock Rotation)
            and add heading of it.
        """
        worksheet_all_stock_rotation = workbook.add_sheet('All Stock Rotation',cell_overwrite_ok=True)
        worksheet_all_stock_rotation.row(0).height = 400
        worksheet_all_stock_rotation.row(1).height = 400
        worksheet_all_stock_rotation.row(3).height = 400
        worksheet_all_stock_rotation.col(0).width = 8000
        worksheet_all_stock_rotation.col(1).width = 10000
        worksheet_all_stock_rotation.col(2).width = 3000
        worksheet_all_stock_rotation.col(3).width = 3000
        worksheet_all_stock_rotation.col(4).width = 1200
        worksheet_all_stock_rotation.col(5).width = 5000
        worksheet_all_stock_rotation.col(6).width = 5000
        worksheet_all_stock_rotation.col(7).width = 5000
        worksheet_all_stock_rotation.col(8).width = 7000
        worksheet_all_stock_rotation.col(9).width = 7000
        worksheet_all_stock_rotation.col(10).width = 5000
        worksheet_all_stock_rotation.col(11).width = 1200
        worksheet_all_stock_rotation.col(12).width = 7000
        worksheet_all_stock_rotation.col(13).width = 7000
        worksheet_all_stock_rotation.col(14).width = 1200
        worksheet_all_stock_rotation.col(15).width = 6000
        worksheet_all_stock_rotation.col(16).width = 6000
        worksheet_all_stock_rotation.write(0,0,'From Date',header_bold)
        worksheet_all_stock_rotation.write(0,1,from_date,body_style)
        worksheet_all_stock_rotation.write(1,0,'To Date',header_bold)
        worksheet_all_stock_rotation.write(1,1,to_date,body_style)
        worksheet_all_stock_rotation.write(3,0,'Internal Reference ',header_bold)
        worksheet_all_stock_rotation.write(3,1,'Name',header_bold)
        worksheet_all_stock_rotation.write(3,2,'Cost',header_bold)
        worksheet_all_stock_rotation.write(3,3,'Sales Price',header_bold)
        worksheet_all_stock_rotation.write(3,4,None,blank_cell_style)
        worksheet_all_stock_rotation.write(3,5,'Opening Stock',header_bold)
        worksheet_all_stock_rotation.write(3,6,'Purchase in period',header_bold)
        worksheet_all_stock_rotation.write(3,7,'Sales in Period',header_bold)
        worksheet_all_stock_rotation.write(3,8,'Discarded in Period(OUT)',header_bold)
        worksheet_all_stock_rotation.write(3,9,'Adjusted in Period(IN)',header_bold)
        worksheet_all_stock_rotation.write(3,10,'Closing Stock',header_bold)
        worksheet_all_stock_rotation.write(3,11,None,blank_cell_style)
        worksheet_all_stock_rotation.write(3,12,'Warehouse Transfer(IN)',header_bold)
        worksheet_all_stock_rotation.write(3,13,'Warehouse Transfer(OUT)',header_bold)
        worksheet_all_stock_rotation.write(3,14,None,blank_cell_style)
        worksheet_all_stock_rotation.write(3,15,'Last purchase',header_bold)
        worksheet_all_stock_rotation.write(3,16,'Last sale',header_bold)
        worksheet_all_stock_rotation.set_panes_frozen(True)
        worksheet_all_stock_rotation.set_horz_split_pos(4) 
        worksheet_all_stock_rotation.set_vert_split_pos(2)
        return workbook,worksheet_all_stock_rotation
    
    
    @api.multi
    def print_all_rotation_sheet_data(self,product_data_dict,workbook,worksheet_all_stock_rotation,body_style,qty_cell_style,value_style,blank_cell_style,value_style2):
        """
            This methdo is use for just 
            the print the data of only one sheet(all rotationsheet).
            based on product data dict.
        """
        row=4
        column=0
        for product_id,product_data in product_data_dict.iteritems():
            worksheet_all_stock_rotation.row(row).height = 350
            opening_stock = product_data.get('opening_qty') or 0
            qty_purchase = product_data.get('qty_purchase_in_duration') or 0
            qty_sale = product_data.get('qty_sales_in_duration') or 0
            scap_qty = product_data.get('scrap_location_qty') or 0
            warehouse_in_qty = product_data.get('warehouse_in_qty') or 0
            warehouse_out_qty = product_data.get('warehouse_out_qty') or 0
            
            closing_qty = (opening_stock+qty_purchase+warehouse_in_qty)-(qty_sale+scap_qty+warehouse_out_qty)
            last_purchase_date = ''
            last_sales = ''
            last_purchase_date_lst = filter(None, product_data.get('last_purchase_date'))
            if any(last_purchase_date_lst):
                last_purchase_date = max(last_purchase_date_lst)
                last_purchase_date = last_purchase_date.strftime('%d-%m-%Y') or ''
            last_sales_lst = filter(None, product_data.get('last_sales'))
            if any(last_sales_lst):
                last_sales = max(last_sales_lst)
                last_sales = last_sales.strftime('%d-%m-%Y') or ''
                
            worksheet_all_stock_rotation.write(row,column,product_id.default_code,body_style)
            worksheet_all_stock_rotation.write(row,column+1,product_id.name or '',body_style)
            worksheet_all_stock_rotation.write(row,column+2,product_id.standard_price or 0,qty_cell_style)
            worksheet_all_stock_rotation.write(row,column+3,product_id.lst_price or 0,qty_cell_style)
            worksheet_all_stock_rotation.write(row,column+4,None,blank_cell_style)
            worksheet_all_stock_rotation.write(row,column+5,opening_stock,value_style2)
            worksheet_all_stock_rotation.write(row,column+6,qty_purchase,value_style2)
            worksheet_all_stock_rotation.write(row,column+7,qty_sale,value_style2)
            worksheet_all_stock_rotation.write(row,column+8,scap_qty,value_style2)
            worksheet_all_stock_rotation.write(row,column+9,product_data.get('adjusted_qty_in_duration') or 0,value_style2)
            worksheet_all_stock_rotation.write(row,column+10,closing_qty,value_style2)
            worksheet_all_stock_rotation.write(row,column+11,None,blank_cell_style)
            worksheet_all_stock_rotation.write(row,column+12,warehouse_in_qty,value_style)
            worksheet_all_stock_rotation.write(row,column+13,warehouse_out_qty,value_style)
            worksheet_all_stock_rotation.write(row,column+14,None,blank_cell_style)
            worksheet_all_stock_rotation.write(row,column+15,last_purchase_date,body_style)
            worksheet_all_stock_rotation.write(row,column+16,last_sales,body_style)
            row+=1
        return True

    @api.multi
    def get_stock_rotation_report(self,from_date,to_date,warehouses,locations,all_products):
        """
            This method is handling all the other methods
            and when all the process is done 
            at that time write data in datas field after encode in base64.
        """
        workbook,header_bold,body_style,qty_cell_style,value_style,blank_cell_style,value_style2=self.create_sheet()
        workbook,sheet_data,row_data = self.add_headings(from_date,to_date,warehouses,locations,workbook,header_bold,body_style,qty_cell_style,value_style,blank_cell_style)
        if locations:
            data_dict = self.prepare_data_with_location(from_date, to_date, locations, all_products)
        else:
            data_dict = self.prepare_data_with_warehouse(from_date, to_date, warehouses, all_products)
        product_data_dict = self.print_date_in_sheet(data_dict,workbook,sheet_data,row_data,body_style,qty_cell_style,value_style,blank_cell_style,value_style2)
        workbook,worksheet_all_stock_rotation = self.create_all_inventory_sheet(from_date,to_date,workbook,sheet_data,row_data,body_style,qty_cell_style,value_style,blank_cell_style,header_bold)
        self.print_all_rotation_sheet_data(product_data_dict,workbook,worksheet_all_stock_rotation,body_style,qty_cell_style,value_style,blank_cell_style,value_style2)
        fp = BytesIO()            
        workbook.save(fp)
        fp.seek(0)
        report_date = base64.encodestring(fp.read())
        fp.close()
        self.write({'datas':report_date})
        return True
