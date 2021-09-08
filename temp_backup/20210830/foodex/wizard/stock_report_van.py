import base64
import xlwt
import cStringIO
from odoo import fields, models, api, _
from collections import defaultdict
from datetime import datetime, date
from odoo.exceptions import ValidationError
import datetime
from datetime import datetime, timedelta

class StockReportVan(models.TransientModel):
    _name = 'stock.report.van'

    date_from = fields.Date(string="Date From", default=date.today())
    date_to = fields.Date(string="Date To", default=date.today())
    location_id = fields.Many2one('stock.location', string='Location',domain=[('usage', '=', 'internal')])
    
    def _get_report_lines(self):
        report_lines = []
        location = self.location_id
        date_from = self.date_from
        date_to = self.date_to
        print"upto dates"
        
        date_from = datetime.strptime(date_from, '%Y-%m-%d').replace(hour=00, minute=00, second=00)
        date_to = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        product_ids, move_product_ids, line_product_ids = [],[],[]
        # get products form moves
        self._cr.execute("select product_id from stock_move where date>=%s "\
            "and date<=%s and (location_id=%s or location_dest_id=%s)"\
            ,(date_from,date_to,location.id,location.id))
        res = self._cr.fetchall()
        if res:
            move_product_ids = [r[0] for r in res]
        
        # get products from invoices
        self._cr.execute("select l.product_id from account_invoice_line l, account_invoice a where l.invoice_id=a.id "\
            "and a.state in ('draft','proforma','proforma2','open','paid') and a.type in ('out_invoice', 'out_refund') and "\
            "a.location_id = %s and a.date_invoice>=%s and a.date_invoice<=%s",(location.id,date_from,date_to))
        res1 = self._cr.fetchall()
        if res1:
            line_product_ids = [r[0] for r in res1]
        product_ids = move_product_ids + line_product_ids
        product_ids = list(set(product_ids))
#        product_ids = [1387]
#        product_ids = [1365]
        
#        print"context: ",self._context
        Move = self.env['stock.move']
        Product = self.env['product.product']
        InvoiceLine = self.env['account.invoice.line']
        for product_id in product_ids:
            dict={}
            product = Product.browse(product_id)
            
            # call the compute quantities
#            self._cr.execute("select sum(product_uom_qty) from stock_move where date>=%s "\
#                "and date<=%s and product_id=%s and state='done' and location_id!=%s and location_dest_id=%s"\
#                ,(date_from,date_to,product_id,location.id,location.id))
            self._cr.execute("select id from stock_move where date>=%s "\
                "and date<=%s and product_id=%s and state!='cancel' and (location_id=%s or location_dest_id=%s)"\
                ,(date_from,date_to,product_id,location.id,location.id))
#            in_qty = self._cr.fetchone()[0] or 0.0
            move_res = self._cr.fetchall()
            in_qty,out_qty = 0.0, 0.0
            if move_res:
                move_ids = [r[0] for r in move_res]
    #            if product_id == 1809:
                if len(move_ids):
                    for move in Move.browse(move_ids):
                        if not move.picking_id:
                            continue
                        picking_type_id = move.picking_id and move.picking_id.picking_type_id or False
                        if not picking_type_id:
                            continue
                        if picking_type_id and picking_type_id.code != 'internal':
                            continue
                        
                        qty = move.product_uom_qty
                        
                        if move.product_uom.uom_type == 'bigger':
                            qty = qty * move.product_uom.factor_inv
                        if move.product_uom.uom_type == 'smaller':
                            qty = qty / move.product_uom.factor_inv
                        
                        if (move.location_id.id != location.id) and (move.location_dest_id.id == location.id):
                            in_qty+=qty
                        if (move.location_dest_id.id != location.id) and (move.location_id.id == location.id):
                            out_qty+=qty
                            
            
            # sales from invoices
            self._cr.execute("select l.id from account_invoice_line l, account_invoice a where l.invoice_id=a.id "\
                "and a.state in ('draft','proforma','proforma2','open','paid') and a.type in ('out_invoice', 'out_refund') and "\
                "a.location_id = %s and a.date_invoice>=%s and a.date_invoice<=%s and "\
                "l.product_id=%s and a.refund_without_invoice!=True",(location.id,date_from,date_to,product_id))
            line_res = self._cr.fetchall()
            line_ids = []
            if line_res:
                line_ids = [r[0] for r in line_res]
            total_draft_qty = 0.0
            if line_ids:
                for line in InvoiceLine.browse(line_ids):
                    qty = line.quantity+line.free_qty
#                    if line.price_unit>0:
#                        qty = line.quantity
#                    else:
#                        qty = line.free_qty
                    if line.uom_id.uom_type == 'bigger':
                        qty = qty * line.uom_id.factor_inv
                    if line.uom_id.uom_type == 'smaller':
                        qty = qty / line.uom_id.factor_inv
                    total_draft_qty+=qty
                    
           # Returns from refund invoices
            self._cr.execute("select l.id from account_invoice_line l, account_invoice a where l.invoice_id=a.id "\
                "and a.state in ('draft','proforma','proforma2','open','paid') and a.type in ('out_invoice', 'out_refund') and "\
                "a.location_id = %s and a.date_invoice>=%s and a.date_invoice<=%s and "\
                "l.product_id=%s and a.refund_without_invoice=True",(location.id,date_from,date_to,product_id))
            line_res = self._cr.fetchall()
            line_ids = []
            if line_res:
                line_ids = [r[0] for r in line_res]
            total_return_qty = 0.0
            if line_ids:
                for line in InvoiceLine.browse(line_ids):
                    qty = line.quantity+line.free_qty
#                    if line.price_unit>0:
#                        qty = line.quantity
#                    else:
#                        qty = line.free_qty
                    if line.uom_id.uom_type == 'bigger':
                        qty = qty * line.uom_id.factor_inv
                    if line.uom_id.uom_type == 'smaller':
                        qty = qty / line.uom_id.factor_inv
                    total_return_qty+=qty
            
            
            dict['item_code'] = product.barcode or ''
            dict['item_name'] = product.product_tmpl_id.name or ''
            dict['in_qty'] = in_qty
            dict['out_qty'] = out_qty
            dict['sales'] = total_draft_qty
            dict['returns'] = total_return_qty
            dict['balance_qty'] = (in_qty - out_qty - total_draft_qty + total_return_qty)
            dict['cost'] = product.product_tmpl_id.standard_price or 0.0
            dict['balance_cost'] = dict['cost'] * dict['balance_qty']
#            print"dict: ",dict
            report_lines.append(dict)


        return report_lines

    
    @api.multi
    def generate_stock_report_van(self):
        self.clear_caches()
        if self.date_to < self.date_from:
            raise Warning(_('Please enter proper date range.'))
        datas = {
            'model': self._name,
            'docids':self.id,
        }
        return self.env['report'].get_action(self, 'foodex.custom_stock_report_van_template', data=datas)

class report_foodex_custom_stock_report_van_template(models.AbstractModel):
    _name = 'report.foodex.custom_stock_report_van_template'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('foodex.custom_stock_report_van_template')
        docids = self.env[data['model']].browse(data['docids'])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docids,
        }
        return report_obj.render('foodex.custom_stock_report_van_template', docargs)
