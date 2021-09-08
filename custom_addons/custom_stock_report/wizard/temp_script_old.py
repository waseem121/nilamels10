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
from collections import OrderedDict


class TempScript(models.TransientModel):
    _name = 'temp.script'

    product_id = fields.Many2one('product.product', string="Product")
    date = fields.Date(string="Date")
    location_id = fields.Many2one('stock.location', string="Location", 
            domain=[('usage', '=', 'internal')])

    data = fields.Binary(string="Data")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char(string='File Name', readonly=True)
    ref = fields.Char(string='Ref')
    
    
    ########
    ## Temp script code start
    ####
    # temperary script
    # for one product only
    @api.multi
    def script_invoice_and_picking_qty_diff(self):
        output = StringIO.StringIO()
        output.write('"InvoiceNo","Product","Invoice Qty","Picking Qty"')
        output.write("\n")
        
        Invoice = self.env['account.invoice']
        InvoiceLine = self.env['account.invoice.line']
        Pick = self.env['stock.picking']
        
        if self.product_id:
            domain = [('product_id','=',self.product_id.id),('invoice_id.state','!=','cancel')]
            if self.date:
                domain.append(('invoice_id.date_invoice','>=',self.date))
            if self.location_id:
                domain.append(('invoice_id.location_id','=',self.location_id.id))
            line_ids = InvoiceLine.search(domain)
            invoice_ids = line_ids.mapped('invoice_id')
#            print"invoice_ids: ",invoice_ids
        else:
            domain = [('state','!=','cancel')]
            if self.date:
                domain.append(('date_invoice','>=',self.date))
            if self.location_id:
                domain.append(('location_id','=',self.location_id.id))
            invoice_ids = Invoice.search(domain)
#            print"invoice_ids e: ",invoice_ids
            
#        invoice_ids = Invoice.browse(44646)
        for inv in invoice_ids:
            print"inv: ",inv
            product_ids = inv.invoice_line_ids.mapped('product_id')
            print"product_ids: ",product_ids
            
            for product in product_ids:
                inv_qty = 0
                for l in inv.invoice_line_ids:
                    if l.product_id.id == product.id:
                        qty = l.quantity+l.free_qty
                        if l.uom_id.uom_type == 'bigger':
                            qty = qty * l.uom_id.factor_inv
                        if l.uom_id.uom_type == 'smaller':
                            qty = qty / l.uom_id.factor_inv
                        inv_qty += qty

                if inv_qty<=0:
                    continue
                print"inv.idd: ",inv.id
                print"inv_qty: ",inv_qty

                picking_ids = []
                if inv.invoice_picking_id:
                    picking_ids = [inv.invoice_picking_id.id]

                pick_domain = [('origin','=',inv.number),('state','=','done')]
                if inv.type=='out_refund':
                    pick_domain.append(('location_dest_id','=',inv.location_id.id))
                if inv.type=='out_invoice':
                    pick_domain.append(('location_id','=',inv.location_id.id))
                
                
                pickings = Pick.search(pick_domain)
                if len(pickings):
                    for p in pickings:
                        picking_ids.append(p.id)
                if len(picking_ids):
                    picking_ids = list(set(picking_ids))
                    print"len(picking_ids): ",len(picking_ids)
                    if len(pickings)>0:
                        pickings = Pick.browse(picking_ids)
                        picking_qty = 0
                        for p in pickings:
                            for m in p.move_lines:
                                if m.state!='done':
                                    continue
                                if inv.type=='out_refund' and m.location_dest_id.id != inv.location_id.id:
                                    continue
                                if inv.type=='out_invoice' and m.location_id.id != inv.location_id.id:
                                    continue
                                if m.product_id.id == product.id:
                                    picking_qty += m.product_qty
                        print"picking_qty: ",picking_qty
                        if int(inv_qty) != int(picking_qty):
                            print"exporting inv: ",inv
                            output.write('"%s","%s","%s","%s"' % (inv.number,str(product.default_code),inv_qty,picking_qty))
                            output.write("\n")
                            print "mis/export_location_stock () exported"
                        
        today = time.strftime('%Y-%m-%d %H:%M:%S')
        out=base64.encodestring(output.getvalue())
        self.write({'data':out,'state':'get','name':'Export_invoice_DupPicking'+today+'.csv'})
        return {
            'name': 'Faulty Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'temp.script',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }
        
        
    @api.multi
    def script_inventory_adjustment_report(self):
        output = StringIO.StringIO()
        output.write('"Code","Product","Real Qty","In-Out stock"')
        output.write("\n")
        
        Inventory = self.env['stock.inventory']
        if not self.ref:
            raise ValidationError(_('Please enter Inventory adjustment name in Ref field!'))
        
        inventory_ids = Inventory.search([('name','=',self.ref)])
        if not inventory_ids:
            raise ValidationError(_('No inventory adjustment found!'))
        inventory = inventory_ids[0]
        location = inventory.location_id
        
#        date = str(inventory.date).split(" ")[0]
        date = inventory.date
        print"date: ",date
        for line in inventory.line_ids:
            product = line.product_id
            real_qty = line.product_qty
            
            self._cr.execute("select sum(product_qty) from stock_move where "\
                "product_id=%s and state='done' and location_id=%s and location_dest_id!=%s and date>%s"\
                ,(product.id,location.id, location.id, date))
            res = self._cr.fetchone()
            out_qty = res[0] or 0
#            print"out_qty: ",out_qty

            self._cr.execute("select sum(product_qty) from stock_move where "\
                "product_id=%s and state='done' and location_id!=%s and location_dest_id=%s  and date>%s"\
                ,(product.id,location.id, location.id, date))
            res = self._cr.fetchone()
            in_qty = res[0] or 0
#            print"in_qty: ",in_qty

            stock = int(in_qty - out_qty)
#            print"stock: ",stock
            
            output.write('"%s","%s","%s","%s"' % (str(product.default_code),product.name,real_qty,stock))
            output.write("\n")
#            print "mis/script_inventory_adjustment_report () exported"
                        
        today = time.strftime('%Y-%m-%d %H:%M:%S')
        out=base64.encodestring(output.getvalue())
        self.write({'data':out,'state':'get','name':'Export_inventory_adjustment'+today+'.csv'})
        return {
            'name': 'Inventory Adjustment Export',
            'type': 'ir.actions.act_window',
            'res_model': 'temp.script',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }        
        
    @api.multi
    def script_create_single_quant_entry(self):
        product_obj = self.env['product.product']
        all_products = product_obj.search([('active','=',True)])
        all_products = product_obj.search([('id','=',1395)])
        all_locations = [self.location_id] if self.location_id else False
        if not all_locations:
            all_locations = self.env['stock.location'].search([('usage','=','internal')])
#        internal_locations = self.env['stock.location'].search([('usage','=','internal')])
#        all_locations = self.env['stock.location'].search([('id','=',31)])
        print'all_locations: ',all_locations
        
        Move = self.env['stock.move']
        stock_quant_sudo = self.env['stock.quant'].sudo()
        count = 0
        for product in all_products:
            count+=1
#            if True:
            try:
                match = 0
                for location in all_locations:
#                    internal_locations = self.env['stock.location'].search([('usage','=','internal'),
#                                                    ('id','!=',location.id)])
                    try:
                        print"location name: ",location.name
                        self._cr.execute("select sum(product_qty) from stock_move where "\
                            "product_id=%s and state='done' and location_id=%s and location_dest_id!=%s"\
                            ,(product.id,location.id, location.id))
                        res = self._cr.fetchone()
                        out_qty = res[0] or 0
                        print"out_qty: ",out_qty

                        self._cr.execute("select sum(product_qty) from stock_move where "\
                            "product_id=%s and state='done' and location_id!=%s and location_dest_id=%s"\
                            ,(product.id,location.id, location.id))
                        res = self._cr.fetchone()
                        in_qty = res[0] or 0
                        print"in_qty: ",in_qty

                        stock = int(in_qty - out_qty)
                        print"stock: ",stock
                        if stock==0:
                            match += in_qty
                            print"zero stock"
                            continue
                        quant_created = stock_quant_sudo.create({
                                'product_id':product.id,
                                'location_id':location.id,
                                'qty':stock,
                                'in_date':'2021-03-30',
                                'cost':product.product_tmpl_id.standard_price or 0.0
                            })
                        print"quant_created: ",quant_created
                        
                        move_ids = []
                        move_ids = self.env['stock.move'].search([('product_id','=',product.id),
                                ('state','=','done'),
                                ('location_dest_id','=',location.id),
                                ('location_id.usage','not in',('internal', 'transit'))
                                ], order='id desc')
#                        if not len(move_ids):
#                            move_ids = self.env['stock.move'].search([('product_id','=',product.id),
#                                    ('state','=','done'),
#                                    ('location_dest_id','=',location.id),
#                                    ], order='id desc')
                            
                        
#                        if stock>0:
#                            move_ids = self.env['stock.move'].search([('product_id','=',product.id),
#                                    ('state','=','done'),
#                                    ('location_id','=',location.id),
#                                    ('location_dest_id.usage','not in',('internal', 'transit'))
#                                    ])
#                        else:
#                            move_ids = self.env['stock.move'].search([('product_id','=',product.id),
#                                    ('state','=','done'),
#                                    ('location_dest_id','=',location.id),
#                                    ('location_id.usage','not in',('internal', 'transit'))
#                                    ])
                        if len(move_ids):
                            print"moveids0000:Usage ",move_ids[0].location_dest_id.usage
                            self._cr.execute("""INSERT INTO stock_quant_move_rel 
                                (move_id, quant_id) 
                                VALUES(%s,%s)
                                """, (move_ids[0].id,quant_created.id))
                            print"relation created"
                        
                    except Exception, e:
                        print "mis/temp_create_single_quant_entry() IN Exception: ",str(e)
                        continue
                print"match: ",match
            except Exception, e:
                print "mis/temp_create_single_quant_entry() Exception: ",str(e)
                continue
            print "mis/temp_create_single_quant_entry () Remaining: ",len(all_products) - count
        
        print "mis/temp_create_single_quant_entry () Exit "
        return True
        return {'type':'ir.actions.act_window_close' }