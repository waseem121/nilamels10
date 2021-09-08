# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from openerp import fields, models, api, _
from datetime import date, time, datetime


class pos_order(models.Model):
    _inherit = 'pos.order'

    @api.one
    def apply_customer_pricelist(self):
    	#print "111111111111111111****************price_dictionaryyyyyyyyyyyyyyy",self
        partner_record = self
        main_dict = {}
        #print "partner_recordddddddddddddddddddddddddddddddddddddddddd",partner_record.id
        partner_record_browse =self.env['res.partner'].browse(partner_record.id)
        partner_price_list_id = partner_record_browse.property_product_pricelist.id
        #print "***************************************************partner_price_list_id",partner_price_list_id
        product_obj = self.env['product.product']
        product_ids = product_obj.search([])
        
        #print "producttttidss",product_ids
        product_pricelist = self.env['product.pricelist']
        product_pricelist.browse(partner_price_list_id)
        #print "product_pricelisttttttttttttttttttttttttttttt",product_pricelist
        for product_id in product_ids:
            
            price = product_pricelist.price_get(product_id.id, qty=1, partner=None)
            price.update({'product_id':product_id.id })
            main_dict.update({product_id.id : price})
        #print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~main_dict",main_dict
    	
    	return main_dict
    	


        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
