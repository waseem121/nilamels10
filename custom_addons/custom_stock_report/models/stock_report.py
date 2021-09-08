import base64
import xlwt
import cStringIO
from odoo import fields, models, api, _
from collections import defaultdict
from datetime import datetime, date
from odoo.exceptions import ValidationError
from itertools import groupby
from odoo.tools.float_utils import float_round
from odoo.addons import decimal_precision as dp

import time
from base64 import b64decode
import csv
import base64
import cStringIO
import StringIO
from collections import OrderedDict


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
    
    
    ########
    ## Temp script code start
    ####
    # temperary script
    # for one product only
    @api.multi
    def get_invoice_with_duplicate_pickings_one_product(self):
        output = StringIO.StringIO()
        output.write('"InvoiceID","InvoiceNumber","Inv Qty","Picking Qty"')
        output.write("\n")
        
        Invoice = self.env['account.invoice']
        Pick = self.env['stock.picking']
        
        all_locations = self.location_ids
        if len(all_locations):
            invoice_ids = Invoice.search([('state','not in',('cancel',)),
                ('location_id','=',all_locations.ids[0]),
#                ('id','=',43332)
                ])
        else:
            invoice_ids = Invoice.search([('state','not in',('cancel',))])
        
        product_id = 1387
        product_id = 1365
        for inv in invoice_ids:
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
            print"inv.idd: ",inv.id
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
                    if int(inv_qty) != int(picking_qty):
                        print"exporting inv: ",inv
                        output.write('"%s","%s","%s","%s"' % (inv.id,inv.number,inv_qty,picking_qty))
                        output.write("\n")
                        print "mis/export_location_stock () exported"
                        
        today = time.strftime('%Y-%m-%d %H:%M:%S')
        out=base64.encodestring(output.getvalue())
        self.write({'data':out,'state':'get','name':'Export_invoice_DupPicking'+today+'.csv'})
        return {
            'name': 'Faulty Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }    
        
    # for all products
    @api.multi
    def get_invoice_with_duplicate_pickings(self):
        output = StringIO.StringIO()
        output.write('"InvoiceID","InvoiceNumber","Number of pickings"')
        output.write("\n")
        
        Invoice = self.env['account.invoice']
        Pick = self.env['stock.picking']
        all_locations = self.location_ids

        if len(all_locations):
            location_id = all_locations.ids[0]
            self._cr.execute("select l.product_id from account_invoice a, account_invoice_line l where a.id=l.invoice_id and a.location_id=%s"\
                "and a.state!='cancel'"\
                ,(location_id,))
            res = self._cr.fetchall()
            if res:
                product_ids = [r[0] for r in res]
            
#            invoice_ids = Invoice.search([('state','not in',('cancel',)),
#                ('location_id','=',location_id),
##                ('id','=',43332)
#                ])
        else:
#            invoice_ids = Invoice.search([('state','not in',('cancel',))])
            product_ids = self.env['product.product'].search([])
            product_ids = product_ids.ids
        print"len( product_ids: ",len(product_ids)
#        product_ids = [1365]
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
            'res_model': 'stock.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }            
        
    
    @api.multi
    def get_faulty_moves(self):
        output = StringIO.StringIO()
        output.write('"Picking ID"')
        output.write("\n")
        
        Invoice = self.env['account.invoice']
        Pick = self.env['stock.picking']
        Move = self.env['stock.move']
        Line = self.env['account.invoice.line']
        
        self._cr.execute("select l.id from account_invoice_line l, account_invoice a where l.invoice_id=a.id "\
            "and a.state != 'cancel' and a.type in ('out_invoice', 'out_refund') and "\
            "a.location_id = %s and a.date_invoice>=%s and a.date_invoice<=%s and "\
            "l.product_id=%s and a.refund_without_invoice!=True",(31,'2020-01-01','2020-12-31',1044))
        line_res = self._cr.fetchall()
        van_line_ids = []
        if line_res:
            van_line_ids = [r[0] for r in line_res]
#        van_line_ids = [143190, 126472, 126473, 126476, 126477, 126478, 126479, 126483, 126484, 126486, 126487, 126488, 126489, 141743, 127516, 141744, 130594, 130595, 127524, 127525, 127526, 127528, 127529, 130603, 130604, 123442, 128053, 130615, 130616, 127547, 123452, 123454, 123455, 130625, 130626, 123468, 123469, 130653, 130654, 145769, 135800, 139901, 139902, 136981, 139906, 139907, 139908, 131862, 139913, 143127, 143128, 146584, 146585, 146592, 146593, 139909, 143134, 139124, 146635, 146633, 146634, 135799, 127522, 138962, 138963, 138964, 138974, 138976, 134887, 134888, 123119, 123120, 148213, 148214, 123127, 123128, 125741, 139024, 139025, 139026, 139027, 131860, 131861, 136982, 131863, 139032, 131865, 131866, 143131, 143132, 143133, 131870, 131871, 131872, 131873, 143138, 143139, 136996, 136997, 136998, 143144, 143145, 125740, 127538, 144686, 144687, 131383, 131384, 131385, 131386, 125755, 125756, 131392, 140621, 140622, 140623, 131409, 131410, 131414, 131415, 131416, 131422, 131423, 131424, 123451, 145764, 145765, 145768, 127548, 145772, 145773, 124275, 124276, 139125, 142829, 132501, 132502, 132513, 132514, 141733, 141734, 141735, 132520, 132521, 141738, 141740, 142834, 132527, 132528, 132530, 142775, 142776, 142777, 129979, 129980, 129992, 129993, 148215, 147916, 145357, 145358, 145362, 145363, 145367, 145369, 145370, 130014, 126431, 126432, 130018, 126444, 126445, 142830, 126447, 126448, 126450, 142835, 142836, 126454, 126455]
            
        van_line_ids = list(set(van_line_ids))
#        print"van_line_ids: ",van_line_ids
        
#        self._cr.execute("select picking_id from stock_move where state='done' and date>='2001-01-01' and date<='2020-12-31' and product_id=1044 and location_id=31 and location_dest_id=9")
        self._cr.execute("select picking_id from stock_move where state='done' and date>='2001-01-01' and date<='2020-12-31' and product_id=1044 and location_id=31")
        res = self._cr.fetchall()
        if res:
            picking_ids = [r[0] for r in res]
        total_move_qty = 0.0
        total_inv_qty = 0.0
        picking_ids = list(set(picking_ids))
        stock_line_ids = []
        extra_ids = []
        for picking in Pick.browse(picking_ids):
            if picking.state=='cancel':
                print"cancelled picking............................. ",picking.id
                continue
#            invoice_ids = Invoice.search([('invoice_picking_id','=',picking.id)])
            invoice_ids = Invoice.search([('number','=',picking.origin)])
            print"invoice_ids: ",invoice_ids
            move_qty = 0.0
            for m in picking.move_lines:
                if m.product_id.id==1031:
                    move_qty += m.product_qty
            inv_qty = 0.0
            
            for invoice in invoice_ids:
                if invoice.state=='cancel':
                    print"cancelled invoice: =====",invoice.id
                    continue
#                if invoice.date_invoice>'2020-01-01' or invoice.date_invoice<'2020-12-31':
#                    print"this is faulty invoice********************: ",invoice.id
#                    continue
                for l in invoice.invoice_line_ids:
                    if l.product_id.id==1031:
                        if l.id in stock_line_ids:
                            extra_ids.append(l.id)
                        stock_line_ids.append(l.id)
                        if l.id not in van_line_ids:
                            print"thissssssssssssssssss is not in van: ",l.id
                        qty = l.quantity+l.free_qty
                        if l.uom_id.uom_type == 'bigger':
                            qty = qty * l.uom_id.factor_inv
                        if l.uom_id.uom_type == 'smaller':
                            qty = qty / l.uom_id.factor_inv
                        
                        inv_qty += (qty)
                        
            print"extra_ids: ",extra_ids
            print"move_qty: ",move_qty
            print"inv_qty: ",inv_qty
            total_move_qty += move_qty
            total_inv_qty += inv_qty
            if float(move_qty) != float(inv_qty):
                print"exporting move: ",picking
                output.write('"%s"' % (picking.id))
                output.write("\n")
                print "mis/export_location_stock () exported"

        def Diff(li1, li2): 
            li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2] 
            return li_dif 
        
        print"total_move_qty: ",total_move_qty
        print"total_inv_qty: ",total_inv_qty
        today = time.strftime('%Y-%m-%d %H:%M:%S')
        out=base64.encodestring(output.getvalue())
        self.write({'data':out,'state':'get','name':'Export_'+today+'.csv'})
        return {
            'name': 'Faulty Moves',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }
    
    @api.multi
    def temp_get_move_and_quant_stock_report(self):
        output = StringIO.StringIO()
        output.write('"Internal Ref","Product","Location","Moves stock","Quants stock"')
        output.write("\n")

        product_obj = self.env['product.product']
        all_products = product_obj.search([('active','=',True)])
        all_products = product_obj.search([('id','=',1387)])
#        all_products = product_obj.search([('id','=',1118)])
#        all_locations = self.env['stock.location'].search([('usage','=','internal')])
        all_locations = self.env['stock.location'].search([('id','=',31)])
        print'all_locations: ',all_locations
        
        all_locations = self.location_ids
        
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
    def temp_create_difference_quant_entry(self):
        product_obj = self.env['product.product']
        all_products = product_obj.search([('active','=',True)])
#        all_products = product_obj.search([('id','=',1387)])
#        all_products = product_obj.search([('id','=',2000)])
        all_locations = self.location_ids
        if not all_locations:
            all_locations = self.env['stock.location'].search([('usage','=','internal')])
#        all_locations = self.env['stock.location'].search([('id','=',31)])
        print'all_locations: ',all_locations
        
        Move = self.env['stock.move']
        stock_quant_sudo = self.env['stock.quant'].sudo()
        count = 0

        for location in all_locations:
            count+=1
#            if True:
            try:
                all_products = all_products.with_context({'location': location.id,
                    'compute_child': False})
                for product in all_products:
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
                        
                        quants_qty = product.qty_available
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
                                'in_date':'2021-03-20',
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
    
        
    @api.multi
    def temp_create_single_quant_entry(self):
        product_obj = self.env['product.product']
        all_products = product_obj.search([('active','=',True)])
#        all_products = product_obj.search([('id','=',1387)])
        all_locations = self.location_ids
        if not all_locations:
            all_locations = self.env['stock.location'].search([('usage','=','internal')])
#        all_locations = self.env['stock.location'].search([('id','=',31)])
        print'all_locations: ',all_locations
        
        Move = self.env['stock.move']
        stock_quant_sudo = self.env['stock.quant'].sudo()
        count = 0
        for product in all_products:
            count+=1
#            if True:
            try:
                for location in all_locations:
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
                            print"zero stock"
                            continue
                        quant_created = stock_quant_sudo.create({
                                'product_id':product.id,
                                'location_id':location.id,
                                'qty':stock,
                                'in_date':'2021-03-17',
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
                    
                    
        return True
                    
        
    @api.multi
    def temp_correct_move_quant_stock(self):
        product_obj = self.env['product.product']
        all_products = product_obj.search([('active','=',True)])
#        all_products = product_obj.search([('id','=',1387)])
        all_locations = self.location_ids
        if not all_locations:
            all_locations = self.env['stock.location'].search([('usage','=','internal')])
#        all_locations = self.env['stock.location'].search([('id','=',31)])
        print'all_locations: ',all_locations
        
        Move = self.env['stock.move']
        stock_quant_sudo = self.env['stock.quant'].sudo()
        for product in all_products:
            try:
                for location in all_locations:
                    print"location: ",location
                    product = product.with_context({'location': location.id,
                        'compute_child': False})
                    quants_qty = int(product.qty_available)
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
                    moves_qty = int(moves_qty)
                    print"moves_qty: ",moves_qty
                    if quants_qty == moves_qty:
                        print"equal qty continue"
                        continue
                    
                    diff = moves_qty - quants_qty
                    if (diff > 0 and moves_qty>0 and quants_qty>0):
                        print"111"
                        self._cr.execute("""SELECT id FROM stock_quant WHERE 
                            product_id = %s and location_id=%s ORDER BY id ASC""", 
                            (product.id, location.id))
                        res = self._cr.fetchall()
                        if len(res):
                            add_qty_quant_ids = [x[0] for x in res]
                            if len(add_qty_quant_ids):
                                add_qty_quant = stock_quant_sudo.browse(add_qty_quant_ids[0])
                                add_qty_quant.write({'qty':float(add_qty_quant.qty+diff)})
                                print"qty added in old quant qty"
                                
                    if (diff < 0 and moves_qty<0 and quants_qty<0):
                        print"444"
                        self._cr.execute("""SELECT id FROM stock_quant WHERE 
                            product_id = %s and location_id=%s ORDER BY id ASC""", 
                            (product.id, location.id))
                        res = self._cr.fetchall()
                        if len(res):
                            add_qty_quant_ids = [x[0] for x in res]
                            if len(add_qty_quant_ids):
                                add_qty_quant = stock_quant_sudo.browse(add_qty_quant_ids[0])
                                add_qty_quant.write({'qty':float(add_qty_quant.qty-diff)})
                                print"qty added in old quant qty44"
                                
                    if diff <0:
                        print"222"
                        self._cr.execute("""SELECT id FROM stock_quant WHERE 
                            product_id = %s and location_id=%s ORDER BY id ASC""", 
                            (product.id, location.id))
                        res = self._cr.fetchall()
                        if len(res):
                            sub_qty_quant_ids = [x[0] for x in res]
                            if len(sub_qty_quant_ids):
                                qty_updated=False
                                for q in stock_quant_sudo.browse(sub_qty_quant_ids):
                                    if qty_updated:
                                        continue
                                    if (q.qty>0) and q.qty > diff:
                                        q.write({'qty':float(q.qty+diff)})
                                        qty_updated=True
                                        print"qty sub in old quant"
                                if not qty_updated:
                                    for q in stock_quant_sudo.browse(sub_qty_quant_ids):
                                        if qty_updated:
                                            continue
                                        if (q.qty<=0):
                                            q.write({'qty':float(q.qty+diff)})
                                            qty_updated=True
                        else:
                            quant_created = stock_quant_sudo.create({'product_id':product.id,
                                            'location_id':location.id,
                                            'qty':diff, 'in_date':'2020-12-29'})
                            print"quant_created yesssss else22: ",quant_created
                                            
                    if diff >0 and (moves_qty<0 and quants_qty<0):
                        print"333"
                        self._cr.execute("""SELECT id FROM stock_quant WHERE 
                            product_id = %s and location_id=%s ORDER BY id ASC""", 
                            (product.id, location.id))
                        res = self._cr.fetchall()
                        if len(res):
                            sub_qty_quant_ids = [x[0] for x in res]
                            if len(sub_qty_quant_ids):
                                qty_updated=False
                                for q in stock_quant_sudo.browse(sub_qty_quant_ids):
                                    if qty_updated:
                                        continue
                                    if (q.qty>0) and q.qty > diff:
                                        print"1"
                                        q.write({'qty':float(q.qty-diff)})
                                        qty_updated=True
                                if not qty_updated:
                                    for q in stock_quant_sudo.browse(sub_qty_quant_ids):
                                        if qty_updated:
                                            continue
                                        if (q.qty<0):
                                            print"2"
                                            q.write({'qty':float(q.qty+diff)})
                                            qty_updated=True
                                            
                    if diff > 0 and moves_qty>0 and quants_qty<=0:
                        print"55"
                        self._cr.execute("""SELECT id FROM stock_quant WHERE 
                            product_id = %s and location_id=%s ORDER BY id ASC""", 
                            (product.id, location.id))
                        res = self._cr.fetchall()
                        print"55 res: ",res
                        if len(res):
                            sub_qty_quant_ids = [x[0] for x in res]
                            if len(sub_qty_quant_ids):
                                qty_updated=False
                                if quants_qty<=0:
                                    for q in stock_quant_sudo.browse(sub_qty_quant_ids):
                                        if qty_updated:
                                            continue
                                        if (q.qty<=0):
                                            print"1n"
                                            q.write({'qty':float(q.qty+diff)})
                                            qty_updated=True
                        else:
                            quant_created = stock_quant_sudo.create({'product_id':product.id,
                                            'location_id':location.id,
                                            'qty':moves_qty, 'in_date':'2020-12-29'})
                            print"quant_created yesssss else: ",quant_created
                            


                    print "mis/export_location_stock () updated"
            except Exception, e:
                print "mis/export_location_stock() Exception: ",str(e)
                continue
            print "mis/export_location_stock () End product: ",product.id
            
        return {'type':'ir.actions.act_window_close' }
    
    
    @api.multi
    def temp_get_invoice_and_picking_cost(self):
        output = StringIO.StringIO()
        output.write('"Invoice Date","Invoice","Invoice Cost","Picking","Move","Move Cost"')
        output.write("\n")

        Invoice = self.env['account.invoice']
        Picking = self.env['stock.picking']
        Move = self.env['account.move']
        
        all_locations = self.env['stock.location'].search([('id','=',31)])
        print'all_locations: ',all_locations
        
        all_locations = self.location_ids
        
        for location in all_locations:
            print"location: ",location
            domain = [('state','not in',('draft','cancel')), 
                ('location_id','=',location.id),
                ('type','=','out_invoice')
#                ('id','=',32627)
#                ('id','=',42066)
                ]
            invoices = Invoice.search(domain)
            print"len invoices: ",len(invoices)
            count=0
            for invoice in invoices:
                count += 1
                print"invoice start: ",invoice
#                try:
#                inv_cost = float(invoice.total_cost)
#                inv_cost = sum(((l.cost_price * ((l.quantity+l.free_qty)*l.uom_id.factor_inv))) for l in invoice.invoice_line_ids)
                inv_cost = sum((l.cost_price * (l.quantity+l.free_qty)) for l in invoice.invoice_line_ids)
#                t = 0
#                for l in invoice.invoice_line_ids:
#                    print"l.cost_price: ",l.cost_price
#                    print"l.quantity: ",l.quantity
#                    
#                    t += l.cost_price * (l.quantity)
#                    print"----"
#                ee
                inv_cost = float(round(inv_cost, 3))
                pickings = Picking.search([('origin','=',invoice.number), 
                        ('state','=','done')])
                if not len(pickings):
                    pickings = [invoice.invoice_picking_id]
                
                move_cost = 0
                move_name = ''
                picking_name = ''
                if len(pickings):
                    export_vals = []
                    total_move_cost = 0.0
                    for picking in pickings:
#                        move_cost = 0
                        v = {}
                        move = picking.account_move_id or False
                        if not move:
                            moves = Move.search([('ref','=',picking.name)])
                            if len(moves):
                                move = moves[0]
                        if move:
                            move_cost = move.amount
                            move_name = move.name

                        move_cost = float(round(move_cost, 3))
                        print"inv cost: ",inv_cost
                        print"move_cost: ",move_cost
                        if inv_cost == move_cost:
                            print"same cost continue00"
                            export_vals = []
                            continue

                        picking_name = picking.name
                        
                        v['invoice_date'] = invoice.date_invoice
                        v['invoice_number'] = invoice.number
                        v['inv_cost'] = inv_cost
                        v['picking_name'] = picking_name
                        v['move_name'] = move_name
                        v['move_cost'] = move_cost
                        export_vals.append(v)
                        total_move_cost += move_cost
                        
                    total_move_cost = float(round(total_move_cost, 3))
                    print"total_move_cost: ",total_move_cost
                    if inv_cost == total_move_cost:
                        print"same cost continue"
#                        export_vals = []
                        continue
                    else:
                        if len(export_vals):
                            for v in export_vals:
                                output.write('"%s","%s","%s","%s","%s","%s"' % 
                                    (v['invoice_date'], v['invoice_number'], v['inv_cost'], v['picking_name'], v['move_name'], v['move_cost']))
                                output.write("\n")
                                print"Exported00 "
                                print"invoice Remaining00 : ",len(invoices) - count
                else:
                    output.write('"%s","%s","%s","%s","%s","%s"' % 
                        (invoice.date_invoice, invoice.number, inv_cost, picking_name, move_name, move_cost))
                    output.write("\n")
                    print"Exported11 "
                    print"invoice Remaining11 : ",len(invoices) - count
#        ee
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
    def temp_get_picking_cost_and_journal_cost(self):
        output = StringIO.StringIO()
        output.write('"Picking","Picking Cost","Journal","Journal Cost"')
        output.write("\n")

        Move = self.env['account.move']
        Picking = self.env['stock.picking']
        
        all_locations = self.env['stock.location'].search([('id','=',31)])
        print'all_locations: ',all_locations
        
        all_locations = self.location_ids
        
        picking_ids = Picking.search([('picking_type_id','=',11)])
        count = 0
        for picking in picking_ids:
            print"picking start: ",picking
            count += 1
            move = picking.account_move_id or False
            if not move:
                moves = Move.search([('ref','=',picking.name)])
                if len(moves):
                    move = moves[0]
            picking_cost = picking.picking_cost or 0.0
            move_cost = 0
            move_name = ''
            if move:
                move_cost = move.amount
                move_name = move.name
                
            picking_cost = float(round(picking_cost, 3))
            move_cost = float(round(move_cost, 3))
            if picking_cost == move_cost:
                print"same conitinue"
                print"invoice Remaining000 : ",len(picking_ids) - count
                continue
                
            output.write('"%s","%s","%s","%s"' % 
                (picking.name, picking_cost, move_name, move_cost))
            output.write("\n")
            print"Exported "
            print"invoice Remaining : ",len(picking_ids) - count


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
    
    ########
    ## Temp script code ends
    ####    

    @api.multi
    def generate_stock_report(self):
        datas = {
            'id': self.id,
        }
        
        if self.partner_id:
            product_suppliers = self.env['product.supplierinfo'].search([('name','=',self.partner_id.id)])
            print"product_suppliers: ",product_suppliers
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
#        worksheet = workbook.add_sheet("Stock Report", cell_overwrite_ok=True)
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
        
        if not self.location_ids and self.internal_location:
            f_location_ids = [location.id for location in self.env['stock.location'].search([('usage', '=', 'internal')])]
        elif not self.location_ids and not self.internal_location:
            f_location_ids = [location.id for location in self.env['stock.location'].search([])]
        else:
            f_location_ids = [location.id for location in self.location_ids]        

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
            worksheet.col(2).width = 5000
            worksheet.col(10).width = 5000
            worksheet.col(11).width = 5000
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
                total_virtual_available = 0
                total_carton = 0
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
                    worksheet.write_merge(categ_row, categ_row, 9 + i, 9 + i, 'Forecast QTY', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 10 + i, 10 + i, 'Forecast CTN', style=stylePC)                    
                    worksheet.write_merge(categ_row, categ_row, 11 + i, 11 + i, 'Unit', style=stylePC)
                elif self.price_selection == 'show_price':
                    worksheet.write_merge(categ_row, categ_row, 5 + i, 5 + i, 'Public Price', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 6 + i, 6 + i, 'Total Value', style=stylePC)
                    
                    worksheet.write_merge(categ_row, categ_row, 7 + i, 7 + i, 'Forecast QTY', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 8 + i, 8 + i, 'Forecast CTN', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 9 + i, 9 + i, 'Unit', style=stylePC)
                elif self.price_selection == 'show_cost':
                    worksheet.write_merge(categ_row, categ_row, 5 + i, 5 + i, 'Cost', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 6 + i, 6 + i, 'Total Cost', style=stylePC)
                    
                    worksheet.write_merge(categ_row, categ_row, 7 + i, 7 + i, 'Forecast QTY', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 8 + i, 8 + i, 'Forecast CTN', style=stylePC)
                    worksheet.write_merge(categ_row, categ_row, 9 + i, 9 + i, 'Unit', style=stylePC)
                for k, v in value.items():
                    categ_row += 1
                    for each_value in v:
#                        print"each_value: ",each_value
                        product_dict = {}
#                        product = self.env['product.product'].search([('id', '=', each_value['product_id'])])
#                        qty_sum = sum(q['qty'] for q in v)
#                        if self.date and self.date_selection == 'on_date':
#                            to_date = datetime.strptime(self.date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
#                            SQL = """SELECT cost from product_price_history 
#                                where product_id = %s AND
#                                datetime <= '%s' order by id desc limit 1
                            #"""  % (product.id, to_date)
#                            
#                            SQL_old = """SELECT avg(cost) as cost from product_price_history 
#                                where product_id = %s AND
#                                datetime <= '%s' group by product_id
                            #""" % (product.id, to_date)
#                            self._cr.execute(SQL)
#                            cost_res = self._cr.dictfetchall()
#                            cost_sum = cost_res[0].get('cost') if cost_res and cost_res[0] and cost_res[0].get(
#                                'cost') else 0.0
#                        else:
#                            product_history = self.env['product.price.history'].search(
#                                [('product_id', '=', product.id)], order='id desc', limit=1)
#                            cost_sum = product_history and product_history.cost or 0.0
#
#                        value_sum = float(product.lst_price)  # sum(val['value'] for val in v)
#                        
#                        # forecast qty changes start
#                        product_virtual_available = product.with_context({'location': f_location_ids, 'compute_child': False})
#                        virtual_available  = float(product_virtual_available.virtual_available_inv)
#                        carton = float(qty_sum)
#                        if product.uom_po_id.uom_type == 'bigger':
#                            carton = virtual_available / product.uom_po_id.factor_inv
#                        if product.uom_po_id.uom_type == 'smaller':
#                            carton = virtual_available * product.uom_po_id.factor_inv                        
#                        # forecast qty changes ends                        
                        
#                        product_dict = {'product': k,
#                                        'description': each_value['description'],
#                                        'product_category': each_value['product_category'],
#                                        'item_code': each_value['item_code'],
#                                        'barcode': each_value['barcode'],
#                                        'qty': qty_sum,
#                                        'qty': qty_sum,
#                                        'cost': cost_sum,
#                                        'cost_total': cost_sum * qty_sum,
#                                        'value': value_sum,
#                                        'value_total': value_sum * qty_sum,
#                                        'serial_number': each_value['serial_number'],
#                                        'virtual_available': virtual_available,
#                                        'carton': carton,
#                                        'uom':product.uom_id.name,
#                                        }
                        product_dict = {'product': k,
                                        'description': each_value['description'],
                                        'product_category': each_value['product_category'],
                                        'item_code': each_value['item_code'],
                                        'barcode': each_value['barcode'],
                                        'qty': each_value['qty'],
                                        'cost': each_value['cost'],
                                        'cost_total': each_value['qty'] * each_value['cost'],
                                        'value': each_value['value'],
                                        'value_total': each_value['value'] * each_value['qty'],
                                        'serial_number': each_value['serial_number'],
                                        'virtual_available': each_value['virtual_available'],
                                        'carton': each_value['carton'],
                                        'uom':each_value['uom'],
                                        }
#                    if each_value['product'] == k:
                    if (each_value['item_code'] == k) or (each_value['product'] == k):

                        worksheet.write_merge(categ_row, categ_row, 0, 0, product_dict['item_code'])
                        worksheet.write_merge(categ_row, categ_row, 1, 1, product_dict['barcode'])
#                        worksheet.write_merge(categ_row, categ_row, 2, 2, product_dict['product'])
                        worksheet.write_merge(categ_row, categ_row, 2, 2, product_dict['description'])
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
                            worksheet.write_merge(categ_row, categ_row, 9 + i, 9 + i,
                                                  '%.3f' % product_dict['virtual_available'])
                            worksheet.write_merge(categ_row, categ_row, 10 + i, 10 + i,
                                                  '%.3f' % product_dict['carton'])
                            worksheet.write_merge(categ_row, categ_row, 11 + i, 11 + i,
                                                  product_dict['uom'])
                                                  
                        elif self.price_selection == 'show_price':
                            worksheet.write_merge(categ_row, categ_row, 5 + i, 5 + i, '%.3f' % product_dict['value'])
                            worksheet.write_merge(categ_row, categ_row, 6 + i, 6 + i,
                                                  '%.3f' % product_dict['value_total'])
                                                  
                            worksheet.write_merge(categ_row, categ_row, 7 + i, 7 + i,
                                                  '%.3f' % product_dict['virtual_available'])
                            worksheet.write_merge(categ_row, categ_row, 8 + i, 8 + i,
                                                  '%.3f' % product_dict['carton'])
                            worksheet.write_merge(categ_row, categ_row, 9 + i, 9 + i,
                                                  product_dict['uom'])                                                  
                        elif self.price_selection == 'show_cost':
                            worksheet.write_merge(categ_row, categ_row, 5 + i, 5 + i, '%.3f' % product_dict['cost'])
                            worksheet.write_merge(categ_row, categ_row, 6 + i, 6 + i,
                                                  '%.3f' % product_dict['cost_total'])
                                                  
                            worksheet.write_merge(categ_row, categ_row, 7 + i, 7 + i,
                                                  '%.3f' % product_dict['virtual_available'])
                            worksheet.write_merge(categ_row, categ_row, 8 + i, 8 + i,
                                                  '%.3f' % product_dict['carton'])
                            worksheet.write_merge(categ_row, categ_row, 9 + i, 9 + i,
                                                  product_dict['uom'])
                        qty_total += product_dict['qty']
                        cost_total += product_dict['cost']
                        total_cost_total += product_dict['cost_total']
                        value_total += product_dict['value']
                        total_value_total += product_dict['value_total']
                        total_virtual_available += product_dict['virtual_available']
                        total_carton += product_dict['carton']
                        
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
                    
                    worksheet.write(categ_row + 1, 7 + i, '%.3f' % total_virtual_available, style=styleBorder)
                    worksheet.write(categ_row + 1, 8 + i, '%.3f' % total_carton, style=styleBorder)
                if self.price_selection == 'both':
                    #                     worksheet.write(categ_row + 1, 5+i, '%.3f' %cost_total, style=styleBorder)
                    worksheet.write(categ_row + 1, 6 + i, '%.3f' % total_cost_total, style=styleBorder)
                    #                     worksheet.write(categ_row + 1, 7+i, '%.3f' %value_total, style=styleBorder)
                    worksheet.write(categ_row + 1, 8 + i, '%.3f' % total_value_total, style=styleBorder)
                    
                    worksheet.write(categ_row + 1, 9 + i, '%.3f' % total_virtual_available, style=styleBorder)
                    worksheet.write(categ_row + 1, 10 + i, '%.3f' % total_carton, style=styleBorder)
                if self.price_selection == 'show_price':
                    #                     worksheet.write(categ_row + 1, 5+i, '%.3f' %value_total, style=styleBorder)
                    worksheet.write(categ_row + 1, 6 + i, '%.3f' % total_value_total, style=styleBorder)
                    
                    worksheet.write(categ_row + 1, 7 + i, '%.3f' % total_virtual_available, style=styleBorder)
                    worksheet.write(categ_row + 1, 8 + i, '%.3f' % total_carton, style=styleBorder)
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
#                worksheet.write(categ_row + 1, 4 + i, '%.3f' % final_value_total, style=styleBorder)
#                worksheet.write(categ_row + 1, 5+i, '%.3f' %final_total_value, style=styleBorder)
                worksheet.write(categ_row + 1, 6+i, '%.3f' %final_total_value, style=styleBorder)
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
                            SQL = """SELECT cost from product_price_history 
                                where product_id = %s AND
                                datetime <= '%s' order by id desc limit 1
                            """  % (product.id, to_date)
                            
                            SQL_old = """SELECT avg(cost) as cost from product_price_history 
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
        # self.write({
        #     'state': 'get',
        #     'data': base64.encodestring(file_data.getvalue()),
        #     'name': 'stock_report.xls'
        # })
        self.write({
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
#        if not self.product_ids:
#            product_ids = [product.id for product in self.env['product.product'].search([('type', '=', 'product')])]
#        else:
#            product_ids = [product.id for product in self.product_ids]
        if self.partner_id:
            product_suppliers = self.env['product.supplierinfo'].search([('name','=',self.partner_id.id)])
            product_ids = []
            for product_supplier in product_suppliers:
                products = self.env['product.product'].search([('product_tmpl_id', '=', product_supplier.product_tmpl_id.id)])
                for product in products:
                    product_ids.append(product.id)
        else:
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
        location_obj = self.env['stock.location']
        product_obj = self.env['product.product']
        Move = self.env['stock.move']
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
#            new_category_ids = self.category_ids
#            category_ids = [prod_cat_id.id for prod_cat_id in self.category_ids]
            
            category_ids = self.env['product.category'].search([('id', 'child_of', self.category_ids.ids)])
            new_category_ids = category_ids
            category_ids = [c.id for c in category_ids]

        partner_product_ids = []
        if self.partner_id:
            product_suppliers = self.env['product.supplierinfo'].search([('name','=',self.partner_id.id)])
            product_ids = []
            for product_supplier in product_suppliers:
                products = self.env['product.product'].search([('product_tmpl_id', '=', product_supplier.product_tmpl_id.id)])
                for product in products:
                    product_ids.append(product.id)
            new_product_ids = product_ids
            partner_product_ids = product_ids
        else:
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
        include_zero = self.include_zero
        print"include_zero: ",include_zero

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
                SQL_old = """
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
                        pt.type = 'product' AND
                        %s
                    """ % (where_lot_id,)
                    
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
            if self.date_selection == 'upto_date':
                SQL += ",spl.name" if self.date_selection == 'upto_date' else ",sq.serial_number"
            SQL += " ORDER BY pt.name ASC"
            self._cr.execute(SQL)
            res = self._cr.dictfetchall()
            if res:
                used_product_ids = []
                for each in res:
                    used_product_ids.append(each['product_id'])
                used_product_ids = list(set(used_product_ids))
                
                if self.date_selection == 'on_date':
                    domain = [('product_id', 'in', tuple(used_product_ids)),
                            ('state', '=', 'done'),
                            ('date', '<=', self.date),
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
                    
                    if not self.group_by =='location':
                        ## Forecast qty
                        f_domain = [('product_id', 'in', tuple(used_product_ids)),
                                ('state', '=', 'done'),
                                ('date', '<=', self.date)]
                        domain_move_in = domain + [
                            ('location_dest_id', 'in', tuple(location_ids))]
                        domain_move_out = domain + [
                            ('location_id', 'in', tuple(location_ids))]
                        f_moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
                        f_moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
                
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
            else:
                print"elssssssssssssss part"
                product_ids = [product.id for product in self.env['product.product'].search([
                        ('type', '=', 'product'),
                        ('product_tmpl_id.categ_id','in',tuple(new_category_ids.ids))
                    ])]                
#                print"product_ids: ",product_ids
                used_product_ids = []
                final_dict = {}
                if self.group_by == 'category':
                    team_dict = defaultdict(list)
                    categ_ids_to_use = []
                    for category in new_category_ids:
                        product_dict = defaultdict(list)

                        templates = self.env['product.template'].search([('categ_id','=',category.id)])
                        for template in templates:
                            this_prods = self.env['product.product'].search([('product_tmpl_id','=',template.id)])
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
#                                product_dict[template.name].append(t_dict)                                
                                product_dict[template.default_code].append(t_dict)

                        if product_dict:
                            team_dict[category.name] = dict(product_dict)

                    final_dict = dict(team_dict)
                if self.group_by == 'location':
                    team_dict = defaultdict(list)
                    location_ids_to_use = []
                    for location in new_location_ids:
                        product_dict = defaultdict(list)
                        
                        for a_product in product_ids:
                            a_product = self.env['product.product'].browse(a_product)
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
#                            product_dict[template.name].append(t_dict)
                            product_dict[template.default_code].append(t_dict)

                        if product_dict:
                            team_dict[location.complete_name] = dict(product_dict)
                    final_dict = dict(team_dict)
                if self.group_by == 'brand':
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
                            this_prods = self.env['product.product'].search([
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
#                                product_dict[template.name].append(t_dict)
                                product_dict[template.default_code].append(t_dict)

                        if product_dict:
                            team_dict[brand.name] = dict(product_dict)
                    final_dict = dict(team_dict)
                    
                    
            ###### custom changes
            g_location = self.location_ids.ids or []
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
                            if self.date_selection == 'on_date':
                                
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
                                
                            if self.date_selection == 'upto_date':
                                stock = float(innerv['qty'])
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
                                if self.group_by == 'location':
                                    this_locations = location_obj.search([('complete_name','=',key)])
                                    if this_locations:
                                        domain = [('product_id', 'in', tuple([product.id])),
                                                ('state', '=', 'done'),
                                                ('date', '<=', self.date)
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
                                                ('date', '<=', self.date)
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
                                stock = in_qty - out_qty
                                
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
                            d['uom'] = product.uom_id.name
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
                
            ## sorting it by product
#            keys = final_dict.keys()
#            last_dict = {}
#            for key in final_dict.keys():
#                res = final_dict.get(key)
#                t = OrderedDict(sorted(res.items()))
#                last_dict[key]=t
                
#            return final_dict
#            return last_dict
            return final_dict
