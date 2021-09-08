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

class import_product_vendor(models.TransientModel):
    _name = "import.product.vendor"

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')

    @api.multi
    def import_vendor(self, values):
        product_obj = self.env['product.product']
        
        default_code = values.get('default_code',False)
        if not default_code:
            raise Warning('Item Code can not be empty.')
        
        default_code = str(default_code)
        if default_code.find(".") != -1:    # in Excel sometims its coming as 443.0
            default_code = default_code.split('.')[0]
        default_code = default_code.zfill(6)
        
        product_ids = product_obj.search([('default_code','=',default_code)])
        print"product_ids: ",product_ids
        message = ''
        if not len(product_ids):
            message = str(default_code)
            
            
        if len(product_ids):
            
            vendor_name = values.get('vendor_name',False)
            print"vendor_name: ",vendor_name
            if not vendor_name:
                raise Warning('Vendor can not be empty.')

            vendor_id = False
            vedor_obj = self.env['res.partner'].search([('supplier','=',True)])
            vendor_search_id  = vedor_obj.search([('name','=',vendor_name)])
            if vendor_search_id:
                vendor_id = vendor_search_id.id
                
            if vendor_id:
                existing_vendor = self.env['product.supplierinfo'].search([
                    ('name','=',vendor_id),
                    ('product_tmpl_id','=',product_ids[0].product_tmpl_id.id)])
                if not len(existing_vendor):
                    self.env['product.supplierinfo'].create({
                            'name':vendor_id,
                            'product_tmpl_id':product_ids[0].product_tmpl_id.id
                        })
                    print"vendor added successfully"
        if message:
            return message
        

    @api.multi
    def import_product_vendor(self):
 
        message = ''
        if self.import_option == 'csv':      
#            keys = ['Item Code', 'Vendor Name']
            keys = ['default_code', 'vendor_name']
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
                        res = self.import_vendor(values)
                        if res:
                            message += str(res)+', '
                            
        else:                        
            fp = tempfile.NamedTemporaryFile(delete = False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            for row_no in range(sheet.nrows):
                if row_no <= 0:
                    fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = (map(lambda row:isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    values.update({
                        'default_code':line[0],
                        'vendor_name':line[1],
                    })
                    res = self.import_vendor(values)
                    if res:
                        message += str(res)+', '
                        
        if message:
            raise Warning(message)
#        
        return res

