# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
import tempfile
import binascii
import xlrd
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from openerp.exceptions import Warning
from openerp import models, fields, exceptions, api, _
import io

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
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

class gen_product(models.TransientModel):
    _name = "gen.product"

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')

    @api.multi
    def create_product(self, values):
        product_obj = self.env['product.product']
        product_categ_obj = self.env['product.category']
        product_uom_obj = self.env['product.uom']
        product_brand = self.env['product.brand']
        vedor_obj = self.env['res.partner'].search([('supplier','=',True)])
        if values.get('categ_id')=='':
            raise Warning('CATEGORY field can not be empty')
        else:
            categ_id = product_categ_obj.search([('name','=',values.get('categ_id'))])
        
        if values.get('type') == 'Consumable':
            type ='consu'
        elif values.get('type') == 'Service':
            type ='service'
        elif values.get('type') == 'Stockable Product':
            type ='product'
        
        if values.get('categ_id')=='':
            uom_id = 1
        else:
            uom_search_id  = product_uom_obj.search([('name','=',values.get('uom'))])
            uom_id = uom_search_id.id
        
        if values.get('uom_po_id')=='':
            uom_po_id = 1
        else:
            uom_po_search_id  = product_uom_obj.search([('name','=',values.get('po_uom'))])
            uom_po_id = uom_po_search_id.id
        if values.get('barcode') == '':
            barcode = False
        else:
            barcode = values.get('barcode')

        if values.get('product_brand_id')=='':
            pass
        else:
            brand_search_id  = product_brand.search([('name','=',values.get('product_brand_id'))])
            if not brand_search_id:
                raise Warning('Product brand field can not be empty')
            else:
                brand_id = brand_search_id.id

        if values.get('vendor_id')=='':
            vendor_id = 1
        else:
            vendor_search_id  = vedor_obj.search([('name','=',values.get('vendor_id'))])
            vendor_id = vendor_search_id.id

        if values.get('uom_so_id')=='':
            uom_so_id = 1
        else:
            uom_search_so_id  = product_uom_obj.search([('name','=',values.get('uom_so_id'))])
            uom_so_id = uom_search_so_id.id                
            
        vals = {
                                  'name':values.get('name'),
                                  'default_code':values.get('default_code'),
                                  'categ_id':categ_id.id,
                                  'type':type,
                                  'barcode': barcode,
                                  'uom_id':uom_id,
                                  'uom_po_id':uom_po_id,
                                  'lst_price':values.get('sale_price'),
                                  'standard_price':values.get('cost_price'),
                                  'weight':values.get('weight'),
                                  'volume':values.get('volume'),
                                  'uom_so_id' : uom_so_id,
                                  'product_brand_id' : brand_id,
                                  }
        res = product_obj.create(vals)
        self.env['product.supplierinfo'].create({'name':vendor_id,
                                                'product_tmpl_id':res.product_tmpl_id.id
                                                })
        return res

    @api.multi
    def import_product(self):
 
        if self.import_option == 'csv':      
            keys = ['name','default_code','categ_id','type','barcode','uom','po_uom','sale_price','cost_price','weight','volume','uom_so_id','product_brand_id','vendor_id']
            csv_data = base64.b64decode(self.file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')
            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))
            values = {}
            for i in range(len(file_reader)):
#                val = {}
                field = list(map(str, file_reader[i]))
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        values.update({'option':self.import_option})
                        res = self.create_product(values)
        else:                        
            fp = tempfile.NamedTemporaryFile(delete = False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = (map(lambda row:isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    values.update( {'name':line[0],
                                    'default_code': line[1],
                                    'categ_id': line[2],
                                    'type': line[3],
                                    'barcode': line[4],
                                    'uom': line[5],
                                    'po_uom': line[6],
                                    'sale_price': line[7],
                                    'cost_price': line[8],
                                    'weight': line[9],
                                    'volume': line[10],
                                    'uom_so_id':line[11],
                                    'product_brand_id' : line[12],
                                    'vendor_id' : line[13]
                                    })
                    res = self.create_product(values)
        
                        
        return res

