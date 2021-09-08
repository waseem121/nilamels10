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
    
    @api.multi
    def temp_get_move_and_quant_stock_report(self):
        output = StringIO.StringIO()
        output.write('"Internal Ref","Product","Location","Moves stock","Quants stock"')
        output.write("\n")

        product_obj = self.env['product.product']
        all_products = [self.product_id] if self.product_id else False
        if not all_products:
            all_products = product_obj.search([('active','=',True)])

        if self.location_id:
            all_locations = [self.location_id]
        else:
            all_locations = self.env['stock.location'].search([('usage','=','internal')])
#        all_locations = self.env['stock.location'].search([('id','=',31)])
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
#                    if quants_qty>=0:
#                        continue
                    
                    self._cr.execute("select id from stock_move where "\
                        "product_id=%s and state='done' and (location_id=%s or location_dest_id=%s)"\
                        ,(product.id,location.id,location.id))
                    move_res = self._cr.fetchall()
                    in_qty,out_qty = 0.0, 0.0
                    if move_res:
                        move_ids = [r[0] for r in move_res]
                        if len(move_ids):
                            for move in Move.browse(move_ids):
                                qty = move.product_qty
                                if (move.location_id.id != location.id) and (move.location_dest_id.id == location.id):
                                    in_qty+=qty
                                if (move.location_dest_id.id != location.id) and (move.location_id.id == location.id):
                                    out_qty+=qty
                    print"in_qty: ",in_qty
                    print"out_qty: ",out_qty
#                    stop
                    moves_qty = in_qty - out_qty
                    print"moves_qty: ",moves_qty
                    if int(quants_qty) == int(moves_qty):
                        print"equal qty continue"
                        continue

                    output.write('"%s","%s","%s","%s","%s"' % (product.default_code,product.name, location.name, moves_qty, quants_qty))
                    output.write("\n")
                    print "mis/export_location_stock () exported"
            except Exception, e:
                print "mis/export_location_stock() Exception: ",str(e)
                continue
            print "mis/export_location_stock () End product: ",product.id

        today = time.strftime('%Y-%m-%d %H:%M:%S')
        out=base64.encodestring(output.getvalue())
        self.write({'data':out,'state':'get','name':'Export_stock_move_diff_'+today+'.csv'})
        return {
            'name': 'Stock Report',
            'type': 'ir.actions.act_window',
            'res_model': 'temp.script',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }
    
    
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
#        all_products = product_obj.search([('id','=',1395)])
        all_locations = [self.location_id] if self.location_id else False
        if not all_locations:
            all_locations = self.env['stock.location'].search([('usage','=','internal')])
#        internal_locations = self.env['stock.location'].search([('usage','=','internal')])
#        all_locations = self.env['stock.location'].search([('id','=',31)])
        print'all_locations: ',all_locations
        
        vendor_locations = self.env['stock.location'].search([('usage','=','supplier')])
        customer_locations = self.env['stock.location'].search([('usage','=','customer')])
        
        Move = self.env['stock.move']
        stock_quant_sudo = self.env['stock.quant'].sudo()
        count = 0
        for product in all_products:
            count+=1
#            if True:
            try:
                total_in, total_out = 0,0
                for location in all_locations:
                    try:
                        print"location name: ",location.name
                        self._cr.execute("select sum(product_qty) from stock_move where "\
                            "product_id=%s and state='done' and location_id=%s and location_dest_id!=%s"\
                            ,(product.id,location.id, location.id))
                        res = self._cr.fetchone()
                        out_qty = res[0] or 0
                        print"out_qty: ",out_qty
                        total_out += out_qty

                        self._cr.execute("select sum(product_qty) from stock_move where "\
                            "product_id=%s and state='done' and location_id!=%s and location_dest_id=%s"\
                            ,(product.id,location.id, location.id))
                        res = self._cr.fetchone()
                        in_qty = res[0] or 0
                        print"in_qty: ",in_qty
                        total_in += in_qty

                        stock = int(in_qty - out_qty)
                        print"stock: ",stock
                        if stock==0:
                            print"zero stock"
                            continue
#                        quant_created = stock_quant_sudo.create({
#                                'product_id':product.id,
#                                'location_id':location.id,
#                                'qty':stock,
#                                'in_date':'2021-03-30',
#                                'cost':product.product_tmpl_id.standard_price or 0.0
#                            })
#                        print"quant_created: ",quant_created
                        
                        quant_created_ids = stock_quant_sudo.search([('product_id','=',product.id),
                                    ('location_id','=',location.id),
#                                    ('qty','=',stock),
                                    ('in_date','=','2021-03-30'),
                                ])
                        if not quant_created_ids:
                            continue
                        quant_created = quant_created_ids[0]
                        
                        move_ids = []
                        move_ids = self.env['stock.move'].search([('product_id','=',product.id),
                                ('state','=','done'),
                                ('location_id','=',vendor_locations[0].id),
                                ('location_dest_id','=',location.id),
                                ])
                        if not len(move_ids):
                            move_ids = self.env['stock.move'].search([('product_id','=',product.id),
                                    ('state','=','done'),
                                    ('location_dest_id','=',location.id),
                                    ])

                        if len(move_ids):
                            self._cr.execute("""INSERT INTO stock_quant_move_rel 
                                (move_id, quant_id) 
                                VALUES(%s,%s)
                                """, (move_ids[0].id,quant_created.id))
                        
                    except Exception, e:
                        print "mis/temp_create_single_quant_entry() IN Exception: ",str(e)
                        continue
                        
                # make entry in vendor location
                move_ids = []
                quant_created = stock_quant_sudo.create({
                        'product_id':product.id,
                        'location_id':vendor_locations[0].id,
                        'qty':total_in,
                        'in_date':'2021-03-30',
                        'cost':product.product_tmpl_id.standard_price or 0.0
                    })
                print"quant_created: ",quant_created
                move_ids = self.env['stock.move'].search([('product_id','=',product.id),
                        ('state','=','done'),
                        ('location_id','=',vendor_locations[0].id),
                        ])
                if len(move_ids):
                    self._cr.execute("""INSERT INTO stock_quant_move_rel 
                        (move_id, quant_id) 
                        VALUES(%s,%s)
                        """, (move_ids[0].id,quant_created.id))
                
                # make entry in customer location
                quant_created = stock_quant_sudo.create({
                        'product_id':product.id,
                        'location_id':customer_locations[0].id,
                        'qty':total_out,
                        'in_date':'2021-03-30',
                        'cost':product.product_tmpl_id.standard_price or 0.0
                    })
                print"quant_created: ",quant_created
                move_ids = self.env['stock.move'].search([('product_id','=',product.id),
                        ('state','=','done'),
                        ('location_dest_id','=',customer_locations[0].id),
                        ])
                if len(move_ids):
                    self._cr.execute("""INSERT INTO stock_quant_move_rel 
                        (move_id, quant_id) 
                        VALUES(%s,%s)
                        """, (move_ids[0].id,quant_created.id))
                print"Total In: ",total_in
                print"Total Out: ",total_out
                print"Stock: ",total_in - total_out
                
                
                    
            except Exception, e:
                print "mis/temp_create_single_quant_entry() Exception: ",str(e)
                continue
            print "mis/temp_create_single_quant_entry () Remaining: ",len(all_products) - count
        
        print "mis/temp_create_single_quant_entry () Exit "
        return True
        return {'type':'ir.actions.act_window_close' }
    
    
    @api.multi
    def script_create_customer_location_quants(self):
        product_obj = self.env['product.product']
        all_products = product_obj.search([('active','=',True)])
#        all_products = product_obj.search([('id','=',1395)])
        all_locations = [self.location_id] if self.location_id else False
        if not all_locations:
            all_locations = self.env['stock.location'].search([('usage','=','internal')])
            
        vendor_locations = self.env['stock.location'].search([('usage','=','supplier')])
        customer_locations = self.env['stock.location'].search([('usage','=','customer')])
        
        Move = self.env['stock.move']
        stock_quant_sudo = self.env['stock.quant'].sudo()
        count = 0
        for product in all_products:
            print"script_create_customer_location_quants start: ",product.id
            try:
                for location in all_locations:
                    print"location: ",location
                    store_quants = stock_quant_sudo.search([('product_id','=',product.id),
                                ('location_id','=',location.id)])
                    print"store_quants: ",store_quants
                    if not len(store_quants):
                        print"no quant Continue"
                        continue
                    store_move_ids = []
                    self._cr.execute("""SELECT move_id FROM stock_quant_move_rel WHERE quant_id = %s""", (store_quants[0].id,))
                    res = self._cr.fetchall()
                    if len(res):
                        store_move_ids = [x[0] for x in res]
                        print"store move_ids: ",store_move_ids

                    move_ids = Move.search([('product_id','=',product.id),
                            ('state','=','done'),
                            ('location_id','=',location.id),
                            ('location_dest_id','=',customer_locations[0].id),
                            ])
                    print"len moves: ",len(move_ids)
                    out_qty = sum(move_ids.mapped('product_qty'))
                    print"out_qty: ",out_qty
                    if int(out_qty)==0:
                        continue

                    quant_created = stock_quant_sudo.create({
                            'product_id':product.id,
                            'location_id':customer_locations[0].id,
                            'qty':out_qty,
                            'in_date':'2021-03-30',
                            'cost':product.product_tmpl_id.standard_price or 0.0
                        })
                    print"quant_created: ",quant_created
            except Exception, e:
                print "mis/script_create_customer_location_quants() Exception: ",str(e)
                continue
            print"script_create_customer_location_quants End: ",product.id
                
        print"Exit"
        return True
    
    
    @api.multi
    def script_create_difference_quant_entry(self):
        product_obj = self.env['product.product']
        all_products = [self.product_id] if self.product_id else False
        if not all_products:
            all_products = product_obj.search([('active','=',True)])
#        all_products = product_obj.search([('id','=',1387)])
        all_locations = [self.location_id] if self.location_id else False
        if not all_locations:
            all_locations = self.env['stock.location'].search([('usage','=','internal')])
#        all_locations = self.env['stock.location'].search([('id','=',31)])
        print'all_locations: ',all_locations
        
        stock_quant_sudo = self.env['stock.quant'].sudo()
        count = 0
        for location in all_locations:
            count+=1
#            if True:
            try:
                for product in all_products:
                    product = product.with_context({'location': location.id,
                        'compute_child': False})
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
                        
#                        quants_qty = product.qty_available
#                        print"quants_qty From Page: ",quants_qty
                        
                        self._cr.execute("select sum(qty) from stock_quant where "\
                            "product_id=%s and location_id=%s"\
                            ,(product.id,location.id))
                        res = self._cr.fetchone()
                        quants_qty = res[0] or 0
                        print"quants_qty: ",quants_qty

                        
                        if int(quants_qty) == int(stock):
                            print"equal qty continue"
                            continue
                            
                        diff = stock - quants_qty
                        if diff == 0:
                            continue
                        quant_created = stock_quant_sudo.create({
                                'product_id':product.id,
                                'location_id':location.id,
                                'qty':diff,
                                'in_date':'2021-06-06',
                                'cost':product.product_tmpl_id.standard_price or 0.0
                            })
                        print"quant_created: ",quant_created
                    except Exception, e:
                        print "mis/temp_create_single_quant_entry() IN Exception: ",str(e)
                        continue
                        
            except Exception, e:
                print "mis/temp_create_single_quant_entry() Exception: ",str(e)
                continue
            print "mis/temp_create_single_quant_entry () Remaining: ",len(all_products) - count
        
        print "mis/temp_create_single_quant_entry () Exit "
        return {'type':'ir.actions.act_window_close' }
    
    def script_update_account_level(self):
        Account = self.env['account.account']
        account_ids = Account.search([('parent_id','!=',False)])
#        account_ids = Account.search([('id','=',5643)])
        for account in account_ids:
            if not account.parent_id:
                continue
            account.write({'parent_id': account.parent_id.id})
        
        return {'type':'ir.actions.act_window_close' }
    
    
    @api.multi
    def script_update_cost_invoice_line(self):
        self._cr.execute("""SELECT l.id FROM account_invoice i, account_invoice_line l 
            WHERE i.id=l.invoice_id AND i.state='draft'""")
        query_res = self._cr.fetchall()
        if len(query_res):
            line_ids = [x[0] for x in query_res]
            if len(line_ids):
                lines = self.env['account.invoice.line'].browse(line_ids)
                for line in lines:
                    product = line.product_id or False
                    if not product:
                        continue
                    line.write({'cost_price':product.standard_price})
        
        return {'type':'ir.actions.act_window_close' }
    
    @api.multi
    def script_update_inventory_adjustment(self):
        inventory = self.env['stock.inventory'].browse(4)
        product_ids = inventory.move_ids.mapped('product_id').ids
        Move = self.env['stock.move']
        missing_ids = []
        for line in inventory.line_ids:
            if line.product_qty == 0:
                continue
            if line.product_id.id in product_ids:
                continue
            missing_ids.append(line.product_id.id)
#            if line.product_id.id != 1633:
#                continue
            vals = {
                'product_id':line.product_id.id,
                'product_uom':line.product_uom_id.id,
                'name': 'INV:'+str(inventory.name),
                'date': inventory.date,
                'create_date': inventory.date,
                'location_id': 5,   #inv adjustment
                'location_dest_id': 15,   # FOODEX STORE
                'company_id': 1,
                'product_uom_qty': line.product_qty,
                'ordered_qty':line.product_qty,
                'inventory_id': inventory.id,
                'procure_method':'make_to_stock',
                'state': 'draft',
                'scrapped':False,
                'price_unit':line.product_id.standard_price,
            }
#            print"vals: ",vals
            move = Move.create(vals)
            print"move created"
            move.action_done()
            print"move Doneeeeeeee"
#            break;
        
        return {'type':'ir.actions.act_window_close' }
    
    @api.multi
    def script_update_avg_cost(self):
        Location = self.env['stock.location']
        Move = self.env['stock.move']
        PriceHistory = self.env['product.price.history']
        InvoiceLine = self.env['account.invoice.line']
        Picking = self.env['stock.picking']
        Scrap = self.env['stock.scrap']
        
        adjustment_location_ids = Location.search([('name','=','Inventory adjustment')])
        vendor_location_ids = Location.search([('name','=','Vendors')])
        
        #LC-PB-CB-60/90
#        product_ids = self.env['product.product'].search([('default_code','=','fddr0001')])
#        product_ids = self.env['product.product'].search([('default_code','=','LC-PB-GB-002')])
#        product_ids = self.env['product.product'].search([('id','=',1643)])
        if self.product_id:
            product_ids = [self.product_id]
        else:
            product_ids = self.env['product.product'].search([])
        for product in product_ids:
            print"default code: ",product.default_code
            product_cost = float(round(product.standard_price,6))
            total_amount, total_qty = 0.0, 0.0
            adjustment_moves = Move.search([
                    ('product_id','=',product.id),
                    ('state','=','done'),
                    ('location_id','=',adjustment_location_ids[0].id),
                ])
            for move in adjustment_moves:
                SQL = """SELECT cost from product_price_history 
                    where product_id = %s AND
                    datetime >= '%s' order by id asc limit 1
                """  % (product.id, '2021-01-01')
                self._cr.execute(SQL)
                cost_res = self._cr.dictfetchall()
                print"cost_res: ",cost_res
                if not cost_res:
                    SQL = """SELECT id, cost from product_price_history 
                        where product_id = %s
                        order by id asc limit 1
                    """  % (product.id)
                    self._cr.execute(SQL)
                    cost_res = self._cr.dictfetchall()
                    print"cost resss new: ",cost_res
                    
                cost = cost_res[0].get('cost') if cost_res and cost_res[0] and cost_res[0].get(
                    'cost') else 0.0
                this_cost = move.product_qty * cost
                total_amount += this_cost
                total_qty += move.product_qty
            print"total_amount: ",total_amount
                
            purchase_moves = Move.search([
                    ('product_id','=',product.id),
                    ('state','=','done'),
                    ('location_id','=',vendor_location_ids[0].id),
                ])
            print"Len purchase_moves: ",len(purchase_moves)
            for move in purchase_moves:
                print"move.price_unit: ",move.price_unit
                this_cost = move.product_qty * move.price_unit
#                print"This cost: ",this_cost
                
                total_amount += this_cost
                total_qty += move.product_qty
                
            print"total_amount: ",total_amount
            print"total_qty: ",total_qty
            
            new_cost = total_amount
            if total_qty>0:
                new_cost = total_amount / total_qty
                
#            new_cost = 0.750
            new_cost = float(round(new_cost,6))
            print"Newcost: ",new_cost
            
            ## Delete and create history
            if product_cost != new_cost:
                print"Not same"
                price_history_ids = PriceHistory.search([('product_id','=',product.id)])
                if len(price_history_ids):
                    price_history_ids.unlink()
                    
#            history = PriceHistory.create({'product_id':product.id,
#                    'company_id':1,
#                    'cost':new_cost,
#                    'datetime':'2021-05-19'
#                })
            
            ## update invoice cost
            self._cr.execute("""SELECT l.id FROM account_invoice i, account_invoice_line l 
                WHERE i.id=l.invoice_id AND i.state!='cancel' AND i.type in ('out_invoice','out_refund') AND 
                l.product_id = %s """, 
                (product.id,))
            query_res = self._cr.fetchall()
            if not len(query_res):
                product.write({'standard_price':new_cost,'volume':1})
                print"cost updated in product1"
                continue
            line_ids = [x[0] for x in query_res]
            if not len(line_ids):
                product.write({'standard_price':new_cost,'volume':1})
                print"cost updated in product2"
                continue
            invoice_lines = InvoiceLine.browse(line_ids)
            invoice_lines.write({'cost_price':new_cost})
            
            ## update picking cost
            invoice_ids = invoice_lines.mapped('invoice_id')
            for invoice in invoice_ids:
                
                picking_ids = []
                if invoice.invoice_picking_id and invoice.invoice_picking_id.id:
                    picking_ids = [invoice.invoice_picking_id.id]

                origin = invoice.number or False
                if origin:
                    pickings = Picking.search([('origin','=',origin)])
                    for picking in pickings:
                        picking_ids.append(picking.id)
                picking_ids = list(set(picking_ids))
                
                for picking_id in picking_ids:
                    picking = Picking.browse(picking_id)
                    
#                    if picking.id != 820:
#                        continue
                    if picking.state == 'cancel':
                        continue
                    print"Picking costOld: ",picking.picking_cost
                    for move in picking.move_lines:
                        if move.product_id.id != product.id:
                            continue
                        move.write({'price_unit':new_cost})
                        print"move price unit after update: ",move.price_unit
                        for quant in move.quant_ids:
#                            if quant.location_id.usage!='customer':
#                                continue
                            quant.write({'cost':new_cost,'inventory_value':new_cost*quant.qty})
                    
                    
                    # get new picking cost
                    picking_cost = 0.0
                    scrap_ids = Scrap.search([('picking_id', '=', picking.id)])
                    if scrap_ids:
                        for scrap in scrap_ids:
                            m = scrap.move_id
                            picking_cost += (m.price_unit * m.product_qty)
                    else:
                        for m in picking.move_lines:
                            picking_cost += (m.price_unit * m.product_qty)
                    print"picking_cost last: ",picking_cost
                    picking_cost = float(round(picking_cost,6))
                    picking.write({'picking_cost': picking_cost})
                    
                    
                    
                    AccountMove = picking.account_move_id or False
                    if not AccountMove:
                        continue
                    if picking_cost == float(round(AccountMove.amount,6)):
                        print"Same cost in picking and stock journal continue"
                        continue
                        
                    AccountMove.button_cancel()
                    
                    credit_line_ids = AccountMove.line_ids.filtered(lambda l:l.credit)
                    credit = sum(credit_line_ids.mapped('credit'))
                    print"Credit: ",credit
                    credit_line_ids.with_context(
                            {'check_move_validity':False}).write({'credit':picking_cost,
                                                                })
                    
                    debit_line_ids = AccountMove.line_ids.filtered(lambda l:l.debit)
                    debit = sum(debit_line_ids.mapped('debit'))
                    print"Debit: ",debit
                    debit_line_ids.with_context(
                            {'check_move_validity':False}).write({'debit':picking_cost,
                                                                })
                    print"cost updated in voucher lines"
                    AccountMove.post()
                    print"voucher posted"
            ## update stock journal cost
            product.write({'standard_price':new_cost,'volume':1})
            print"cost updated in product master"
        
        return {'type':'ir.actions.act_window_close' }
    
    
    @api.multi
    def script_update_cost_in_inventory_adjustment(self):
        Location = self.env['stock.location']
        Move = self.env['stock.move']
        PriceHistory = self.env['product.price.history']
        InvoiceLine = self.env['account.invoice.line']
        Picking = self.env['stock.picking']
        Scrap = self.env['stock.scrap']
        
        adjustment_location_ids = Location.search([('name','=','Inventory adjustment')])
        vendor_location_ids = Location.search([('name','=','Vendors')])
        
        #LC-PB-CB-60/90
#        product_ids = self.env['product.product'].search([('default_code','=','fddr0001')])
#        product_ids = self.env['product.product'].search([('default_code','=','LC-PB-GB-002')])
#        product_ids = self.env['product.product'].search([('id','=',1643)])
        product_ids = self.env['product.product'].search([])
        move_ids = Move.search([('inventory_id','=',4)])
        product_ids = move_ids.mapped('product_id')
        print"len Product ids: ",len(product_ids)
        for product in product_ids:
            print"default code: ",product.default_code
            product_cost = float(round(product.standard_price,6))
            total_amount, total_qty = 0.0, 0.0
            adjustment_moves = Move.search([
                    ('product_id','=',product.id),
                    ('state','=','done'),
                    ('location_id','=',adjustment_location_ids[0].id),
                ])
            for move in adjustment_moves:
                if move.price_unit:
                    continue
                print"Move cost: ",move.price_unit
                SQL = """SELECT cost from product_price_history 
                    where product_id = %s AND
                    datetime >= '%s' order by id asc limit 1
                """  % (product.id, '2021-01-01')
                self._cr.execute(SQL)
                cost_res = self._cr.dictfetchall()
                print"cost_res: ",cost_res
                if not cost_res:
                    SQL = """SELECT id, cost from product_price_history 
                        where product_id = %s
                        order by id asc limit 1
                    """  % (product.id)
                    self._cr.execute(SQL)
                    cost_res = self._cr.dictfetchall()
                    print"cost resss new: ",cost_res
                    
                cost = cost_res[0].get('cost') if cost_res and cost_res[0] and cost_res[0].get(
                    'cost') else 0.0
                print"costtt: ",cost
                move.write({'price_unit':cost})
                    
        return {'type':'ir.actions.act_window_close' }
    
    def script_check_picking_and_journal_cost_old(self):
        AccountMove = self.env['account.move']
        Picking = self.env['stock.picking']
        picking_ids = Picking.search([('location_dest_id','=',9),('state','!=','done')])
        for picking in picking_ids:
            print"picking ",picking
            picking_cost = picking.picking_cost
            voucher_amount = picking.account_move_id.amount
            
            if picking.account_move_id:
                stop
            if float(round(picking_cost,3))!= float(round(voucher_amount,3)) and picking.account_move_id:
                print"picking.id: ",picking.id
                print"picking_cost: ",picking_cost
                print"voucher_amount: ",voucher_amount
                print"picking.account_move_id: ",picking.account_move_id
                
                AccountMove = picking.account_move_id or False
                if not AccountMove:
                    continue
                if picking_cost == float(round(AccountMove.amount,6)):
                    print"Same cost in picking and stock journal continue"
                    continue
                    
                stop
                AccountMove.button_cancel()

                credit_line_ids = AccountMove.line_ids.filtered(lambda l:l.credit)
                credit = sum(credit_line_ids.mapped('credit'))
                print"Credit: ",credit
                credit_line_ids.with_context(
                        {'check_move_validity':False}).write({'credit':picking_cost,
                                                            })

                debit_line_ids = AccountMove.line_ids.filtered(lambda l:l.debit)
                debit = sum(debit_line_ids.mapped('debit'))
                print"Debit: ",debit
                debit_line_ids.with_context(
                        {'check_move_validity':False}).write({'debit':picking_cost,
                                                            })
                print"cost updated in voucher lines"
                AccountMove.post()
                print"voucher posted"
            
        
        return {'type':'ir.actions.act_window_close' }
    
    def script_check_picking_and_journal_cost(self):
        AccountMove = self.env['account.move']
        Picking = self.env['stock.picking']
        account_moves = AccountMove.search([('journal_id','=',5)])
        total = 0.0
        for move in account_moves:
            picking_ids = Picking.search([('account_move_id','=',move.id)])
            if not len(picking_ids):
                print"Faluty Move:   ",move
                print"Faluty Move ref:   ",move.ref
                if move.id!=139:
                    total += move.amount
        print"Total amount: ",total
        return {'type':'ir.actions.act_window_close' }

    @api.multi
    def get_invoice_with_duplicate_pickings(self):
        output = StringIO.StringIO()
        output.write('"InvoiceID","InvoiceNumber","Number of pickings"')
        output.write("\n")
        
        Invoice = self.env['account.invoice']
        Pick = self.env['stock.picking']
        if self.location_id:
            location_id = self.location_id.id
            if self.product_id:
                product_ids = [self.product_id.id]
            else:
                self._cr.execute("select l.product_id from account_invoice a, account_invoice_line l where a.id=l.invoice_id and a.location_id=%s"\
                    "and a.state!='cancel'"\
                    ,(location_id,))
                res = self._cr.fetchall()
                if res:
                    product_ids = [r[0] for r in res]

            exported_inv_ids = []
            count = 0
            for product_id in product_ids:
                count += 1
                print"Remaining: ",len(product_ids) - count
                invoice_ids = []
                self._cr.execute("select l.invoice_id from account_invoice a, account_invoice_line l where a.id=l.invoice_id and a.location_id=%s"\
                    "and a.state!='cancel' and l.product_id=%s"\
                    ,(location_id,product_id))
                inv_res = self._cr.fetchall()
                if inv_res:
                    invoice_ids = [r[0] for r in inv_res]

                if not len(invoice_ids):
                    continue
                for inv in Invoice.browse(invoice_ids):
                    print"Remaining: ",len(product_ids) - count
                    if inv.id in exported_inv_ids:
                        continue
                    inv_qty = 0
                    for l in inv.invoice_line_ids:
                        if l.product_id.id == product_id:
                            qty = l.quantity+l.free_qty
                            if l.uom_id.uom_type == 'bigger':
                                qty = qty * l.uom_id.factor_inv
                            if l.uom_id.uom_type == 'smaller':
                                qty = qty / l.uom_id.factor_inv
                            inv_qty += qty

                    if inv_qty<=0:
                        continue
                    print"inv_qty: ",inv_qty

                    picking_ids = []
                    if inv.invoice_picking_id:
                        picking_ids = [inv.invoice_picking_id.id]

                    pickings = Pick.search([('origin','=',inv.number),
                        ('picking_type_id.default_location_src_id','=',inv.location_id.id),
                        ('state','=','done')])
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
                                    if m.product_id.id == product_id:
                                        picking_qty += m.product_qty
                            print"picking_qty: ",picking_qty
                            if int(inv_qty) != int(picking_qty) and inv.id not in exported_inv_ids:
                                print"exporting inv: ",inv
                                output.write('"%s","%s","%s"' % (inv.id,inv.number,len(picking_ids)))
                                output.write("\n")
                                exported_inv_ids.append(inv.id)
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
        
        
        
                
            
            
                
    
    
    
