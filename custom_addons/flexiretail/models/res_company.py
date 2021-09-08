# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from openerp import fields, models, api, _
from openerp.exceptions import  Warning

class res_company(models.Model):
    _inherit = 'res.company'

    pos_price = fields.Char(string="Pos Price", size=1)
    pos_quantity = fields.Char(string="Pos Quantity", size=1)
    pos_discount = fields.Char(string="Pos Discount", size=1)
    pos_search = fields.Char(string="Pos Search", size=1)
    pos_next = fields.Char(string="Pos Next order", size=1)
    pos_back = fields.Char(string="Back To Order", size=1)
    pos_validate = fields.Char(string="Validate", size=1)

    report_ip_address = fields.Char(string="Thermal Printer Proxy IP")

#     @api.multi
#     def write(self, vals):
#         if vals.get('pos_price'):
#             vals.update({ 'pos_price' : vals.get('pos_price').lower()})
#         if vals.get('pos_quantity'):
#             vals.update({ 'pos_quantity' : vals.get('pos_quantity').lower()})
#         if vals.get('pos_discount'):
#             vals.update({ 'pos_discount' : vals.get('pos_discount').lower()})
#         if vals.get('pos_search'):
#             vals.update({ 'pos_search' : vals.get('pos_search').lower()})
#         if vals.get('pos_next'):
#             vals.update({ 'pos_next' : vals.get('pos_next').lower()})
#         if vals.get('pos_back'):
#             vals.update({ 'pos_back' : vals.get('pos_back').lower()})
#         if vals.get('pos_validate'):
#             vals.update({ 'pos_validate' : vals.get('pos_validate').lower()})
#
#         AccJournal = self.env['account.journal']
#
#         price = vals.get('pos_price') or (self.pos_price.lower() if self.pos_price else False) or False
#         qty = vals.get('pos_quantity') or (self.pos_quantity.lower() if self.pos_quantity else False) or False
#         dis = vals.get('pos_discount') or (self.pos_discount.lower() if self.pos_discount else False) or False
#         search = vals.get('pos_search') or (self.pos_search.lower() if self.pos_search else False) or False
#         next = vals.get('pos_next') or (self.pos_next.lower() if self.pos_next else False) or False
#         back = vals.get('pos_back') or (self.pos_back.lower() if self.pos_back else False) or False
#         pos_validate = vals.get('pos_validate') or (self.pos_validate.lower() if self.pos_validate else False) or False
# #
#         if price:
#             if ((price in (qty,dis,search,next,pos_validate)) or AccJournal.search([('shortcut_key', '=', price)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if qty:
#             if ((qty in (price,dis,search,next,pos_validate)) or AccJournal.search([('shortcut_key', '=', qty)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if dis:
#             if ((dis in (price,qty,search,next,pos_validate)) or AccJournal.search([('shortcut_key', '=', dis)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if search:
#             if ((search in (price,qty,dis,next,pos_validate)) or AccJournal.search([('shortcut_key', '=', search)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if next:
#             if ((next in (price,qty,dis,search,back,pos_validate)) or AccJournal.search([('shortcut_key', '=', next)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if back:
#             if ((back in (price,qty,dis,search,next,pos_validate)) or AccJournal.search([('shortcut_key', '=', back)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if pos_validate:
#             if ((pos_validate in (price,qty,dis,search,next)) or AccJournal.search([('shortcut_key', '=', pos_validate)])):
#                 raise Warning(_('Similar value not allowed.'))
#         return super(res_company, self).write(vals)
#
#     @api.model
#     def create(self, vals):
#         if vals.get('pos_price'):
#             vals.update({ 'pos_price' : vals.get('pos_price').lower()})
#         if vals.get('pos_quantity'):
#             vals.update({ 'pos_quantity' : vals.get('pos_quantity').lower()})
#         if vals.get('pos_discount'):
#             vals.update({ 'pos_discount' : vals.get('pos_discount').lower()})
#         if vals.get('pos_search'):
#             vals.update({ 'pos_search' : vals.get('pos_search').lower()})
#         if vals.get('pos_next'):
#             vals.update({ 'pos_next' : vals.get('pos_next').lower()})
#         if vals.get('pos_back'):
#             vals.update({ 'pos_back' : vals.get('pos_back').lower()})
#         if vals.get('pos_validate'):
#             vals.update({ 'pos_validate' : vals.get('pos_validate').lower()})
#
#         AccJournal = self.env['account.journal']
#
#         price = vals.get('pos_price') or False
#         qty = vals.get('pos_quantity') or False
#         dis = vals.get('pos_discount') or False
#         search = vals.get('pos_search') or False
#         next = vals.get('pos_next') or False
#         back = vals.get('pos_back') or False
#         pos_validate = vals.get('pos_validate') or False
#
#         if price:
#             if ((price in (qty,dis,search,next,pos_validate)) or AccJournal.search([('shortcut_key', '=', price)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if qty:
#             if ((qty in (price,dis,search,next,pos_validate)) or AccJournal.search([('shortcut_key', '=', qty)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if dis:
#             if ((dis in (price,qty,search,next,pos_validate)) or AccJournal.search([('shortcut_key', '=', dis)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if search:
#             if ((search in (price,qty,dis,next,pos_validate)) or AccJournal.search([('shortcut_key', '=', search)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if next:
#             if ((next in (price,qty,dis,search,back,pos_validate)) or AccJournal.search([('shortcut_key', '=', next)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if back:
#             if ((back in (price,qty,dis,search,next,pos_validate)) or AccJournal.search([('shortcut_key', '=', back)])):
#                 raise Warning(_('Similar value not allowed.'))
#         if pos_validate:
#             if ((pos_validate in (price,qty,dis,search,next)) or AccJournal.search([('shortcut_key', '=', pos_validate)])):
#                 raise Warning(_('Similar value not allowed.'))
#         return super(res_company, self).create(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: