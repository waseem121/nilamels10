# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.s

from odoo import api, fields, models, _
from lxml import etree

class StockPackOperationLot(models.Model):

    _inherit = 'stock.pack.operation.lot'

    life_date = fields.Datetime(string='Expiry Date',
                                help='This is the date on which the goods with this Serial Number may become dangerous and must not be consumed.')
    use_date = fields.Datetime(string='Best before Date',
                               help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.')
    removal_date = fields.Datetime(string='Removal Date',
                                   help='This is the date on which the goods with this Serial Number should be removed from the stock.')
    alert_date = fields.Datetime(string='Alert Date',
                                 help="This is the date on which an alert should be notified about the goods with this Serial Number.")




class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'
	
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        # print self._context
        res = super(StockPackOperation, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        active_id = self._context.get('active_id', False)
        if active_id and self._context.get('active_model', False)=='stock.pack.operation':
            pack_operation = self.browse(active_id)
            location_id = pack_operation.location_id
            picking_type = pack_operation.picking_id.picking_type_code
            if picking_type != 'incoming':
                # Put proper handling
                if 'pack_lot_ids' in res['fields']:
                    # print "res", res['fields']['pack_lot_ids']
                    lot_ids = []
                    quants = self.env['stock.quant'].search([('product_id', '=', pack_operation.product_id.id)])
                    if quants:
                        lot_ids = quants.filtered(lambda l: l.location_id == location_id and l.qty >= 1.0).mapped('lot_id').ids
                    lot_node = res['fields']['pack_lot_ids']['views']['tree']['arch']
                    doc = etree.XML(lot_node)
                    print doc.xpath("//field[@name='lot_id']")
                    for node in doc.xpath("//field[@name='lot_id']"):
                        node.set('widget','selection')
                        if node.get('domain', False):
                            domain = node.get('domain', '')
                            print "Lot_ids", lot_ids
                            if lot_ids:
                                domain = "[('id', 'in', %s)]" % lot_ids
                                node.set('domain', domain)
                            print node.get('domain', False)

                    res['fields']['pack_lot_ids']['views']['tree']['arch'] = etree.tostring(doc)

        return res

